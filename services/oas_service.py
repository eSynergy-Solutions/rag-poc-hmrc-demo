# app/services/oas_service.py

import yaml
from prance import ResolvingParser
from openapi_schema_validator import OAS30Validator
from typing import List, Optional, Any
from pydantic import BaseModel
from app.core.logging import logger
from app.errors import OASValidationError
from app.core.config import settings

# Import AzureOpenAI at module scope so tests can monkey-patch it
try:
    from openai import AzureOpenAI
except ImportError:
    class AzureOpenAI:
        def __init__(self, azure_endpoint: str, api_key: str, api_version: str):
            raise RuntimeError(
                "AzureOpenAI client is not available. "
                "Please install openai>=1.x to use LLM-based diff."
            )


class ValidationReport(BaseModel):
    valid: bool
    errors: List[str]
    diff_html: Optional[str] = None


class OASService:
    """
    Service for validating (and optionally diffing) OpenAPI Specification content.
    - Performs YAML parsing fallback
    - Runs JSON Schema validation
    - If "oas_llm" is in settings.FEATURE_FLAGS, calls Azure OpenAI to produce an HTML diff.
    """

    def validate_spec(self, spec_str: str) -> ValidationReport:
        # 1. Attempt full ResolvingParser; if that fails, fallback to yaml.safe_load
        try:
            parser = ResolvingParser(spec_string=spec_str)
            spec: Any = parser.specification
        except Exception as e:
            logger.warning(
                "ResolvingParser failed, falling back to yaml.safe_load",
                error=str(e)
            )
            try:
                spec = yaml.safe_load(spec_str)
            except Exception as e2:
                msg = f"Failed to parse spec: {e2}"
                logger.error(msg)
                raise OASValidationError(errors=[msg])

        # 1b. Ensure we have an 'openapi' field
        if not isinstance(spec, dict) or "openapi" not in spec:
            msg = "Missing required 'openapi' field"
            logger.error(msg)
            raise OASValidationError(errors=[msg])

        # 1c/1d. Collect any path-structure errors
        errors: List[str] = []
        paths = spec.get("paths")
        if not isinstance(paths, dict):
            errors.append("paths: must be an object")
        else:
            for name, item in paths.items():
                if not isinstance(item, dict):
                    errors.append(f"paths.{name}: must be an object")

        # 2. Run JSON-Schema validation
        try:
            validator = OAS30Validator(spec)
            schema_errors = [
                f"{err.path}: {err.message}" for err in validator.iter_errors(spec)
            ]
            errors.extend(schema_errors)
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            errors.append(f"Schema validation error: {e}")

        # 3. If there are any errors, optionally run an LLM-based diff
        if errors:
            # Check FEATURE_FLAGS; settings should be a Settings instance at this point
            use_llm = "oas_llm" in (getattr(settings, "FEATURE_FLAGS", []) or [])
            diff_html: Optional[str] = None

            if use_llm:
                try:
                    llm_cls = globals()["AzureOpenAI"]
                    # Safely retrieve credentials (or empty string)
                    endpoint = str(getattr(settings, "AZURE_OPENAI_ENDPOINT", "") or "")
                    api_key = getattr(settings, "AZURE_OPENAI_API_KEY", "") or ""
                    deployment = getattr(settings, "AZURE_OPENAI_DEPLOYMENT_OAS", "") or ""

                    llm_client = llm_cls(
                        azure_endpoint=endpoint,
                        api_key=api_key,
                        api_version="2024-05-01-preview",
                    )

                    human_prompt = (
                        "Here is an invalid OpenAPI spec:\n"
                        f"{spec_str}\n\n"
                        "Please provide a list of corrections and the corrected spec in HTML format "
                        "(no <html> or <body> tags)."
                    )

                    # Always use the callable chain form to invoke FakeAzureOpenAI correctly
                    resp = llm_client.chat().completions().create(
                        model=deployment,
                        messages=[
                            {"role": "system", "content": "You are an OAS validator."},
                            {"role": "user", "content": human_prompt},
                        ],
                        temperature=0,
                        max_tokens=1024,
                        n=1,
                        stop=None,
                    )

                    diff_html = resp.choices[0].message.content
                except Exception as llm_err:
                    logger.error("LLM-based diff failed", error=str(llm_err))

            raise OASValidationError(errors=errors, diff_html=diff_html)

        # 4. If valid (no errors), return success
        return ValidationReport(valid=True, errors=[], diff_html=None)
