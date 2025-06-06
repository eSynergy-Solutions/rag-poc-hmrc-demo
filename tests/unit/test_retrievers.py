# app/tests/unit/test_retrievers.py

import pytest

# Import the classes under test
from vectorstore.astradb import AstraStore
from vectorstore.chroma import ChromaStore
from errors import StorageError


class DummyAstra(AstraStore):
    """
    Subclass of AstraStore that bypasses real __init__, 
    so we can test as_retriever without connecting to AstraDB.
    """

    def __init__(self):
        # Skip calling super().__init__, so no DataAPIClient is used
        pass


def test_astra_retriever_instantiation():
    dummy_store = DummyAstra()
    # Instantiating the retriever should not raise, and should set the attributes correctly
    retriever = dummy_store.as_retriever(k=5)

    # Verify that the retriever has the expected attributes
    assert hasattr(retriever, "store")
    assert retriever.store is dummy_store
    assert hasattr(retriever, "k")
    assert retriever.k == 5


def test_chroma_retriever_instantiation(monkeypatch):
    """
    Monkey-patch chromadb.PersistentClient so that ChromaStore __init__ does not try 
    to open a real directory. Then verify as_retriever(...) returns an object with the 
    expected attributes.
    """
    # 1) Create a dummy PersistentClient class with get_or_create_collection member
    class FakePersistentClient:
        def __init__(self, path):
            pass

        def get_or_create_collection(self, name):
            # Return any object—ChromaStore only uses .query(), .add(), and .count() inside its methods,
            # but we won’t call those in this test.
            return object()

    # 2) Monkey-patch chromadb.PersistentClient
    import chromadb

    monkeypatch.setattr(chromadb, "PersistentClient", FakePersistentClient)

    # 3) Now instantiating ChromaStore should succeed without raising
    try:
        store = ChromaStore(persist_directory=".dummy_dir")
    except Exception as e:
        pytest.fail(f"ChromaStore __init__ raised unexpectedly: {e}")

    # 4) Calling as_retriever(k) should not raise, and should set attributes correctly
    retriever = store.as_retriever(k=10)
    assert hasattr(retriever, "store")
    assert retriever.store is store
    assert hasattr(retriever, "k")
    assert retriever.k == 10
