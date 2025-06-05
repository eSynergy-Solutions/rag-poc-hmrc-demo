# app/tests/unit/test_config.py

import os
import pytest
from pydantic import ValidationError

from core.config import Settings, settings


def test_default_settings_load(tmp_path, monkeypatch):
    # 1) Create a temporary .env file with just the six “required” keys:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "AZURE_OPENAI_ENDPOINT=https://example.com",
                "AZURE_OPENAI_API_KEY=secret-key",
                "AZURE_OPENAI_DEPLOYMENT=deployment-name",
                "AZURE_OPENAI_DEPLOYMENT_OAS=oas-deployment",
                "ASTRA_DB_APPLICATION_TOKEN=token-value",
                "ASTRA_DB_API_ENDPOINT=https://astra.example.com",
            ]
        )
    )

    # 2) Move into that empty directory so that BaseSettings will read this .env
    monkeypatch.chdir(tmp_path)

    # 3) Remove any real‐world environment variables that would override our .env:
    for var in [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_DEPLOYMENT_OAS",
        "ASTRA_DB_APPLICATION_TOKEN",
        "ASTRA_DB_API_ENDPOINT",
        "ASTRA_DB_KEYSPACE",  # ← Also remove this so the default applies
    ]:
        monkeypatch.delenv(var, raising=False)

    # We only need to delete APP_NAME/APP_VERSION if they were explicitly set in OS env:
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_VERSION", raising=False)

    # 4) Now instantiate Settings()—it must load from our temporary .env
    s = Settings()
    assert s.APP_NAME == "rag-poc-hmrc-demo"
    assert s.APP_VERSION == "0.1.0"
    assert s.AZURE_OPENAI_ENDPOINT == "https://example.com"
    assert s.AZURE_OPENAI_API_KEY == "secret-key"
    assert s.AZURE_OPENAI_DEPLOYMENT == "deployment-name"
    assert s.AZURE_OPENAI_DEPLOYMENT_OAS == "oas-deployment"
    assert s.ASTRA_DB_APPLICATION_TOKEN == "token-value"
    assert s.ASTRA_DB_API_ENDPOINT == "https://astra.example.com"
    # Defaults:
    assert s.ASTRA_DB_KEYSPACE == "defra_chatbot_keyspace"
    assert isinstance(s.FEATURE_FLAGS, list)
    assert s.VECTOR_K == 3


def test_missing_required_env(monkeypatch, tmp_path):
    # Switch into an empty temp directory so no .env is visible:
    monkeypatch.chdir(tmp_path)

    # Ensure none of those six critical vars exist in OS env:
    for var in [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_DEPLOYMENT_OAS",
        "ASTRA_DB_APPLICATION_TOKEN",
        "ASTRA_DB_API_ENDPOINT",
    ]:
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(ValidationError):
        Settings()
