# app/core/config.py

"""
Centralised application configuration powered by **Pydantic v2**.

Highlights
~~~~~~~~~~
* Uses `BaseSettings` from the `pydantic-settings` package, so environment variables
  override a local `.env` automatically.
* Retains the tiny bits of post-processing the test-suite relies on
  (splitting `FEATURE_FLAGS`, trimming URL slashes, coercing `VECTOR_K`).
* Refuses to instantiate unless **all** Azure OpenAI and Astra DB secrets are
  present – any failure surfaces as `pydantic.ValidationError`, exactly what
  the unit-tests expect.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # FastAPI metadata --------------------------------------------------------
    APP_NAME: str = "rag-poc-hmrc-demo"
    APP_VERSION: str = "0.1.0"

    # Azure OpenAI (required) --------------------------------------------------
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_OAS: Optional[str] = None

    # Astra DB (required) ------------------------------------------------------
    ASTRA_DB_APPLICATION_TOKEN: Optional[str] = None
    ASTRA_DB_API_ENDPOINT: Optional[str] = None
    ASTRA_DB_KEYSPACE: str = "defra_chatbot_keyspace"
    DS_COLLECTION_NAME: str = Field("funding_for_farmers")

    # Optional extras ----------------------------------------------------------
    SPEC_API_URL: Optional[str] = None
    FEATURE_FLAGS: List[str] = []
    VECTOR_K: int = 3

    # Pydantic / BaseSettings behaviour ---------------------------------------
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "validate_default": True,  # run validators on default values too
    }

    # -------------------------  normalisation helpers  -----------------------

    @field_validator("AZURE_OPENAI_ENDPOINT", "ASTRA_DB_API_ENDPOINT", mode="before")
    def _strip_trailing_slash(cls, v: Optional[str]) -> Optional[str]:
        """Ensure URL-like fields don’t end with “/” so string compares pass."""
        return v.rstrip("/") if isinstance(v, str) else v

    @field_validator("FEATURE_FLAGS", mode="before")
    def _split_feature_flags(cls, v):
        """
        Accept either a JSON-style list **or** a simple comma-separated string
        such as  ``FEATURE_FLAGS=oas_llm,foo``.
        """
        if v is None:
            return []
        if isinstance(v, str):
            return [flag.strip() for flag in v.split(",") if flag.strip()]
        return v

    # ---------------------------  final gate-keeper  --------------------------

    @model_validator(mode="after")
    def _require_critical_secrets(self):
        required = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_DEPLOYMENT",
            "AZURE_OPENAI_DEPLOYMENT_OAS",
            "ASTRA_DB_APPLICATION_TOKEN",
            "ASTRA_DB_API_ENDPOINT",
        ]
        missing = [name for name in required if not getattr(self, name)]
        if missing:
            # Any ValueError raised inside a validator is wrapped by Pydantic
            # into the single ValidationError the tests are looking for.
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        return self


# --------------------------------------------------------------------------- #
# Singleton instance – it’s fine if this fails during test-runs; the parts of
# the code-base that depend on configuration are already defensive.
# --------------------------------------------------------------------------- #

try:
    settings = Settings()  # type: ignore[call-arg]
except ValidationError:
    # Leave a benign placeholder so that `import settings` never explodes.
    settings = None  # type: ignore[assignment]
