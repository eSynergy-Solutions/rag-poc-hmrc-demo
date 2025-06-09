# app/tests/unit/test_deps_success.py

import pytest
import importlib

from fastapi import HTTPException

# Import the modules under test
import core.config as config_mod
import core.deps as deps_mod

def reload_config_with_env(monkeypatch, **env):
    """
    Helper to monkey‐patch os.environ and reload the config module.
    """
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    importlib.reload(config_mod)

def test_get_vector_store_success(monkeypatch):
    # Arrange: valid AstraDB env vars
    reload_config_with_env(
        monkeypatch,
        ASTRA_DB_APPLICATION_TOKEN="token",
        ASTRA_DB_API_ENDPOINT="https://astra.example.com",
    )

    # Monkey‐patch the AstraStore constructor so it doesn't actually try to connect
    class DummyStore:
        pass

    monkeypatch.setattr(deps_mod, "AstraStore", lambda token, api_endpoint, keyspace, collection_name: DummyStore())

    # Act
    gen = deps_mod.get_vector_store(config=config_mod.settings)
    store = next(gen)

    # Assert
    assert isinstance(store, DummyStore)
    with pytest.raises(StopIteration):
        next(gen)

def test_get_chat_chain_success(monkeypatch):
    # Arrange: valid Azure OpenAI env vars
    reload_config_with_env(
        monkeypatch,
        AZURE_OPENAI_ENDPOINT="https://openai.example.com",
        AZURE_OPENAI_API_KEY="secret",
        AZURE_OPENAI_DEPLOYMENT="deploy-name",
    )

    # Dummy store with .as_retriever
    class DummyStore:
        def as_retriever(self, k):
            return "retriever"

    # Monkey‐patch build_chat_chain so it returns a sentinel
    monkeypatch.setattr(
        deps_mod,
        "build_chat_chain",
        lambda endpoint, api_key, deployment, retriever: "CHAIN-OBJECT"
    )

    # Act
    gen = deps_mod.get_chat_chain(config=config_mod.settings, store=DummyStore())
    chain = next(gen)

    # Assert
    assert chain == "CHAIN-OBJECT"
    with pytest.raises(StopIteration):
        next(gen)
