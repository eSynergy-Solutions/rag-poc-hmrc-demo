# app/core/config.py

"""
Centralized application configuration powered by **Pydantic v2**.

Highlights
~~~~~~~~~~
* Uses `BaseSettings` from the `pydantic-settings` package, so environment variables
  override a local `.env` automatically.
* Retains the tiny bits of post-processing the test-suite relies on
  (splitting `FEATURE_FLAGS`, trimming URL slashes, coercing `VECTOR_K`).
* Refuses to instantiate unless all Azure OpenAI (chat + embeddings) and Astra DB
  secrets are present – any failure surfaces as `pydantic.ValidationError`.
"""

from __future__ import annotations

from typing import List, Optional
from core.custom_logging import logger


from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # FastAPI metadata --------------------------------------------------------
    APP_NAME: str = "rag-poc-hmrc-demo"
    APP_VERSION: str = "0.1.0"

    # Azure OpenAI (chat model) ----------------------------------------------
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_OAS: Optional[str] = None

    # Azure OpenAI (embedding model) — using your existing env names ------------
    AZURE_OPENAI_EMB_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_EMB_API_KEY: Optional[str] = None
    AZURE_OPENAI_EMB_API_VERSION: Optional[str] = None
    AZURE_OPENAI_EMB_DEPLOYMENT: Optional[str] = None

    # Astra DB (required) -----------------------------------------------------
    ASTRA_DB_APPLICATION_TOKEN: Optional[str] = None
    ASTRA_DB_API_ENDPOINT: Optional[str] = None
    ASTRA_DB_KEYSPACE: str = "defra_chatbot_keyspace"
    DS_COLLECTION_NAME: str = Field("funding_for_farmers")

    # AWS Aurora RDS Postgres VectorDB (required) -----------------------------------------------------
    PGVECTOR_DRIVER: Optional[str] = "psycopg"
    PGVECTOR_USER: Optional[str] = None
    PGVECTOR_PASSWORD: Optional[str] = None
    PGVECTOR_HOST: Optional[str] = None
    PGVECTOR_PORT: Optional[int] = 5432
    PGVECTOR_DATABASE: Optional[str] = "postgres"
    PGVECTOR_COLLECTION: Optional[str] = "HMRC_APIS"

    # GAILZ (Required) -----------------------------------------------------
    GAILZ_BASE_URL: Optional[str] = None
    GAILZ_DEPLOYMENT_NAME: Optional[str] = None
    GAILZ_MISC_STRING: Optional[str] = None
    GAILZ_DEPLOYMENT_VERSION: Optional[str] = None
    GAILZ_DEPLOYMENT_MODEL: Optional[str] = None

    # Optional extras ---------------------------------------------------------
    SPEC_API_URL: Optional[str] = None
    FEATURE_FLAGS: List[str] = ["oas_llm"]
    VECTOR_K: int = 3
    INGESTION_URL: Optional[str] = None

    # Pydantic / BaseSettings behavior ---------------------------------------
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "validate_default": True,
    }

    # ------------------------- Normalization Helpers -------------------------

    @field_validator(
        "AZURE_OPENAI_ENDPOINT",
        "ASTRA_DB_API_ENDPOINT",
        "AZURE_OPENAI_EMB_ENDPOINT",
        "PGVECTOR_HOST",
        "PGVECTOR_USER",
        "PGVECTOR_PASSWORD",
        "GAILZ_BASE_URL",
        "GAILZ_DEPLOYMENT_NAME",
        "GAILZ_MISC_STRING",
        "GAILZ_DEPLOYMENT_VERSION",
        "GAILZ_DEPLOYMENT_MODEL",
        mode="before",
    )
    def _strip_trailing_slash(cls, v: Optional[str]) -> Optional[str]:
        """Ensure URL-like fields don’t end with “/” so string compares pass."""
        return v.rstrip("/") if isinstance(v, str) else v

    @field_validator("INGESTION_URL", mode="before")
    def _strip_ingestion_url_slash(cls, v: Optional[str]) -> Optional[str]:
        """Ensure INGESTION_URL doesn’t end with a slash."""
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

    # --------------------------- Final Gate-keeper ---------------------------

    @model_validator(mode="after")
    def _require_critical_secrets(self):
        required = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_DEPLOYMENT",
            "AZURE_OPENAI_DEPLOYMENT_OAS",
            "AZURE_OPENAI_EMB_ENDPOINT",
            "AZURE_OPENAI_EMB_API_KEY",
            "AZURE_OPENAI_EMB_API_VERSION",
            "AZURE_OPENAI_EMB_DEPLOYMENT",
            "ASTRA_DB_APPLICATION_TOKEN",
            "ASTRA_DB_API_ENDPOINT",
            "PGVECTOR_DRIVER",
            "PGVECTOR_USER",
            "PGVECTOR_PASSWORD",
            "PGVECTOR_HOST",
            "PGVECTOR_PORT",
            "PGVECTOR_DATABASE",
            "PGVECTOR_COLLECTION",
            "GAILZ_BASE_URL",
            "GAILZ_DEPLOYMENT_NAME",
            "GAILZ_MISC_STRING",
            "GAILZ_DEPLOYMENT_VERSION",
            "GAILZ_DEPLOYMENT_MODEL",
        ]
        missing = [name for name in required if not getattr(self, name)]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        return self


try:
    settings = Settings()  # type: ignore[call-arg]
    logger.info(
        "Configuration loaded successfully",
    )
except ValidationError as e:
    # Leave a benign placeholder so that `import settings` never explodes.

    logger.error("Configuration validation failed", error=str(e))
    settings = None  # type: ignore[assignment]
