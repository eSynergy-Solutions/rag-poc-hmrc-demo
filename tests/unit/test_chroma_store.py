# app/tests/unit/test_chroma_store.py

import os
import shutil
import pytest
import tempfile

from vectorstore.chroma import ChromaStore
from models.ingest import Chunk

import numpy as np


@pytest.fixture(autouse=True)
def patch_get_embedding(monkeypatch):
    """
    Monkey‐patch get_embedding so that:
      - if text starts with "alpha", embedding = [1,0,0,...]
      - if text starts with "beta",  embedding = [0,1,0,...]
      - else zeros
    We only care about cosine distances, so a 2-D vector suffices.
    """

    def fake_get_embedding(text: str):
        if text.startswith("alpha"):
            return [1.0, 0.0]
        if text.startswith("beta"):
            return [0.0, 1.0]
        return [0.0, 0.0]

    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "dummy")  # used by get_embedding import
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "dummy")
    # Reload the embeddings module so that _azure_client initialization does not break
    import importlib
    import app.llm.embeddings as emb_mod

    importlib.reload(emb_mod)

    monkeypatch.setattr(emb_mod, "get_embedding", fake_get_embedding)
    yield


@pytest.fixture
def tmp_chroma_dir(tmp_path):
    """
    Create a temporary directory for Chroma to persist to.
    Clean up afterward.
    """
    d = tmp_path / "chroma_test"
    yield str(d)
    # cleanup is automatic with tmp_path, but explicit in case
    if os.path.isdir(str(d)):
        shutil.rmtree(str(d), ignore_errors=True)


def test_chroma_upsert_and_query(tmp_chroma_dir):
    """
    Insert three documents:
     - chunk A1: content="alpha doc"
     - chunk B1: content="beta doc"
     - chunk C1: content="something else"
    Query with "alpha query": embedding→[1,0] → should return "alpha doc" first, then others.
    """
    store = ChromaStore(persist_directory=tmp_chroma_dir)

    # Create three chunks
    chunks = [
        Chunk(path="path1", content="alpha first document", chunk_index=0),
        Chunk(path="path2", content="beta second document", chunk_index=0),
        Chunk(path="path3", content="something else", chunk_index=0),
    ]
    # Upsert them
    inserted = store.upsert(chunks)
    assert inserted == 3

    # Build an “alpha” query → get_embedding returns [1,0] → nearest to chunk1
    query_emb = [1.0, 0.0]  # same as fake_get_embedding("alpha …")
    results = store.query(query_emb, k=2)

    # results is a list of Chunk; the first one’s content should contain "alpha"
    assert len(results) == 2
    assert "alpha first document" in results[0].content

    # The second in ranking should be the “beta” or “something else” whichever close
    # Because "beta"→[0,1], its dot with [1,0] is 0, same as something else→[0,0], but
    # Chroma might tie-break arbitrarily. We check no exceptions and that the items are from our set:
    returned_paths = {c.path for c in results}
    assert "path1" in returned_paths


def test_chroma_delete(tmp_chroma_dir):
    """
    Ensure that delete(filter) actually removes matching entries.
    We'll insert two documents with different metadata and then delete one.
    """
    store = ChromaStore(persist_directory=tmp_chroma_dir)

    chunks = [
        Chunk(path="foo", content="alpha foo", chunk_index=0),
        Chunk(path="bar", content="beta bar", chunk_index=0),
    ]
    store.upsert(chunks)

    # Delete everything where metadata.path == "foo"
    deleted_count = store.delete(filter={"path": "foo"})
    assert deleted_count >= 1

    # Now query with alpha embedding, should not return path="foo"
    query_emb = [1.0, 0.0]
    results = store.query(query_emb, k=2)
    for c in results:
        assert c.path != "foo"
