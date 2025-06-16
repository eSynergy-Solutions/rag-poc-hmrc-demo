# app/services/oas_service.py

import yaml
from prance import ResolvingParser
from openapi_spec_validator import validate
from typing import List, Optional, Any
from core.logging import logger
from core.deps import get_chat_service
from errors import OASValidationError
from core.config import settings
from models.oas import ValidationReport
from abstracts.ServiceOas import ServiceOAS
from llm.prompts import PROMPT_REGISTRY
from langchain_core.messages import HumanMessage, SystemMessage

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


class OASService(ServiceOAS):
    """
    Service for validating (and optionally diffing) OpenAPI Specification content.
    - Performs YAML parsing fallback
    - Runs JSON Schema validation
    - If "oas_llm" is in settings.FEATURE_FLAGS, calls Azure OpenAI to produce an HTML diff.
    """

    def yaml_to_json(self, yaml_string):
        """
        Convert a YAML string to JSON string

        Parameters:
        yaml_string (str): The YAML content as a string

        Returns:
        str: The converted JSON string
        """
        try:
            # Parse YAML string to Python dictionary
            yaml_dict: dict = yaml.safe_load(yaml_string)
            return yaml_dict
        except Exception as e:
            return f"Error converting YAML to JSON: {str(e)}"

    def validate_spec(self, oas_spec: dict) -> ValidationReport:
        """
        Validate an OpenAPI Specification (OAS) string.

        Args:
            oas_spec (dict): The OAS content as a dict.

        Returns:
            bool: True if the OAS is valid, False otherwise.
        """
        try:
            # Parse the OAS spec
            # Validate the OAS spec
            validate(oas_spec)
            return True
        except Exception as e:
            logger.error(f"OpenAPI Specification validation error: {e}")
            return False

    def enforce_specific_fields(self, field: str, spec: dict) -> bool:
        if field not in spec:
            msg = f"Missing required {field} field"
            logger.error(msg)
            return False
        return True

    def run_oas_check_llm(self, oas_spec: dict) -> str:
        llm_instance = get_chat_service()
        if not llm_instance:
            raise RuntimeError("Chat service is not available")
        # Prepare the system prompt
        system_prompt = PROMPT_REGISTRY.get(
            "oas_validator_prompt", "Default OAS Check Prompt"
        )
        if not system_prompt:
            raise RuntimeError("OAS validation prompt not found in registry")

        # Prepare the messages for the LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=yaml.dump(oas_spec, default_flow_style=False)),
        ]
        # Call the LLM with the messages
        response = llm_instance.invoke(messages)
        return response.content if response else "No response from LLM"
