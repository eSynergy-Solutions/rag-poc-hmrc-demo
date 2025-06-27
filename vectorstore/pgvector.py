# app/vectorstore/pgvector.py

from langchain_postgres.vectorstores import PGVector
from langchain_core.documents import Document
from vectorstore.interface import VectorStore
from models.ingest import Chunk
from core.deps import get_vector_store
from errors import StorageError
from typing import List, Tuple


class PGVectorStore(VectorStore):
    """
    Postgres-backed implementation of the VectorStore protocol.
    Embeds each chunk internally using get_embedding before upsert.

    Supports:
    - upsert: Adds or updates chunks in the PGVector collection.
    - query: Searches for top-k nearest neighbors based on text query or vector.
    - delete: Removes entries by ID or metadata filter.
    - as_retriever: Returns a LangChain-compatible retriever for RAG workflows.
    """

    def __init__(self):
        try:
            client = get_vector_store()
            if not isinstance(client, PGVector):
                raise StorageError("Expected PGVector instance")
            self._db: PGVector = client
        except Exception as e:
            raise StorageError(f"PGVector initialization failed: {e}")

    def upsert(self, chunks: List[Chunk]) -> int:
        """
        Upsert chunks into PGVector. PGVector handles embeddings internally.
        Returns the number of documents upserted.
        Raises StorageError on failure.
        """
        try:
            docs: List[Document] = []
            for chunk in chunks:
                docs.append(
                    Document(
                        page_content=chunk.content,
                        metadata={
                            "path": chunk.path,
                            "chunk_index": chunk.chunk_index,
                        },
                    )
                )

            self._db.add_documents(docs, ids=[doc.metadata["id"] for doc in docs])
            return len(docs)

        except Exception as e:
            raise StorageError(f"Upsert failed: {e}")

    def query(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """
        Query the PGVector DB collection for top-k nearest neighbors.
        Returns a list of Chunk objects. Raises StorageError on failure.
        """
        try:
            query_result = self._db.similarity_search_with_score(query=query, k=k)
            return query_result
        except Exception as e:
            raise StorageError(f"Query failed: {e}")

    def query_with_vector(
        self, query_vector: List[float], k: int = 4
    ) -> List[Tuple[Document, float]]:
        """
        Query the PGVector DB collection for top-k nearest neighbors.
        Returns a list of Chunk objects. Raises StorageError on failure.
        """
        try:
            query_result = self._db.similarity_search_with_score_by_vector(
                embeddings=query_vector, k=k
            )
            return query_result
        except Exception as e:
            raise StorageError(f"Query failed: {e}")

    def delete(self, ids: List[str], collection_only: bool = True) -> bool:
        """
        Delete entries matching the metadata filter. Returns deleted count.
        Raises StorageError on failure.
        """
        try:
            self._db.delete(ids, collection_only=collection_only)
            return True
        except Exception as e:
            raise StorageError(f"Delete failed: {e}")

    def as_retriever(self, k: int = 4):
        """
        Return a LangChain-compatible retriever for RAG workflows.
        Call the retrieved instance with the .invoke(query: str) method to get results.
        """

        return self._db.as_retriever(search_kwargs={"k": k})
