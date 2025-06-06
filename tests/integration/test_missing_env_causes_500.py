# app/tests/integration/test_missing_env_causes_500.py

import os
import pytest

from fastapi.testclient import TestClient
from importlib import reload

import main as main_mod
import core.config as config_mod

@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """
    Ensure that the required env vars are not set. Then reload config so that
    get_chat_chain and get_vector_store will fail.
    """
    for var in [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_DEPLOYMENT_OAS",
        "ASTRA_DB_APPLICATION_TOKEN",
        "ASTRA_DB_API_ENDPOINT",
    ]:
        monkeypatch.delenv(var, raising=False)

    # Reload config so that settings are re‐instantiated with missing fields
    reload(config_mod)
    # Also rebuild the app, in case get_chat_chain is already cached
    reload(main_mod)
    yield

def test_chat_endpoint_without_env_returns_500():
    client = TestClient(main_mod.app)
    payload = {"content": "hi", "streaming": False}
    resp = client.post("/v1/chat", json=payload)
    # Because get_chat_chain will hit its sanity check and raise HTTPException(500)
    assert resp.status_code == 500

def test_discover_endpoint_without_env_returns_500():
    client = TestClient(main_mod.app)
    payload = {"content": "hi", "streaming": False}
    resp = client.post("/v1/discover", json=payload)
    assert resp.status_code == 500
