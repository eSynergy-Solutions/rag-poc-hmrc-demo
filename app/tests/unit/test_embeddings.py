# app/tests/unit/test_embeddings.py

import pytest
from functools import partial

import app.llm.embeddings as emb_mod

class DummyEmbeddingResponse:
    """
    Mimics the AzureOpenAI embeddings.create(...) response structure:
      resp.data is a list of objects, each with an .embedding attribute.
    """
    def __init__(self, vec):
        class Item:
            def __init__(self, embedding):
                self.embedding = embedding
        self.data = [Item(vec)]

@pytest.fixture(autouse=True)
def patch_azure_client(monkeypatch):
    """
    Monkey-patch the _azure_client so that embeddings.create returns a fixed vector.
    """
    # Create a dummy AzureOpenAI client with an `embeddings` attribute
    class FakeEmbeddingsAPI:
        def __init__(SELF):
            pass

        def create(SELF, model, input):
            # Return a DummyEmbeddingResponse whose embedding is simply the reversed input length
            # (just anything deterministic)
            length = len(input)
            # e.g. return [ length, length-1, length-2 ]
            vec = [float(length), float(length - 1)]
            return DummyEmbeddingResponse(vec)

    class FakeAzureClient:
        def __init__(SELF, azure_endpoint, api_key, api_version):
            SELF.embeddings = FakeEmbeddingsAPI()

    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "dummy")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "dummy-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "dummy-model")
    # Reload so that emb_mod._azure_client is instantiated with our test env
    import importlib
    importlib.reload(emb_mod)

    # Replace the real AzureOpenAI with our Fake
    monkeypatch.setattr(emb_mod, "AzureOpenAI", FakeAzureClient)
    # Re‐initialize the module (so that _azure_client = FakeAzureClient(...))
    importlib.reload(emb_mod)
    yield

def test_get_embedding_returns_expected_length_vector():
    """
    Given input text of length N, our Fake returns a vector [N, N-1].
    """
    txt = "hello"
    vec = emb_mod.get_embedding(txt)
    # Since len("hello")==5, our fake returns [5.0,4.0]
    assert isinstance(vec, list)
    assert vec == [5.0, 4.0]

    # Repeated calls with the same text should come from LRU cache
    # (i.e. no change, and the result is exactly the same object)
    vec2 = emb_mod.get_embedding(txt)
    assert vec2 is vec  # cached

def test_get_embedding_different_inputs_are_cached_separately():
    v1 = emb_mod.get_embedding("a")
    v2 = emb_mod.get_embedding("b")
    assert v1 != v2
