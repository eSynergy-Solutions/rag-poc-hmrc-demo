# app/tests/unit/test_deps.py

import pytest
from fastapi import HTTPException
from app.core.deps import (
    get_settings,
    get_logger,
    get_embedding_fn,
    get_vector_store,
    get_chat_chain,
)
from app.core.config import settings
from app.core.logging import logger

def test_get_settings():
    gen = get_settings()
    s = next(gen)
    assert s is settings
    with pytest.raises(StopIteration):
        next(gen)

def test_get_logger():
    gen = get_logger()
    log = next(gen)
    assert log is logger
    with pytest.raises(StopIteration):
        next(gen)

def test_get_embedding_fn():
    gen = get_embedding_fn()
    fn = next(gen)
    from app.llm.embeddings import get_embedding
    assert fn is get_embedding
    with pytest.raises(StopIteration):
        next(gen)

def test_get_vector_store_failure(monkeypatch):
    # Monkeypatch settings to invalid token
    monkeypatch.setenv("ASTRA_DB_APPLICATION_TOKEN", "")
    # Reload settings singleton to pick up change
    from importlib import reload
    import app.core.config as config_mod
    reload(config_mod)
    # Expect HTTPException due to init failure
    gen = get_vector_store(config=config_mod.settings)
    with pytest.raises(HTTPException):
        next(gen)

def test_get_chat_chain_failure(monkeypatch):
    # Monkeypatch settings to invalid OpenAI config
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
    reload = __import__("importlib").reload
    import app.core.config as config_mod
    reload(config_mod)
    # Provide a dummy vector store that won't matter
    class DummyStore:
        def as_retriever(self, k):
            raise RuntimeError("no retriever")
    with pytest.raises(HTTPException):
        gen = get_chat_chain(config=config_mod.settings, store=DummyStore())
        next(gen)
