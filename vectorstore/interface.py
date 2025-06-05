# app/vectorstore/interface.py

from typing import Protocol, List, Dict, Any
from langchain.schema import BaseRetriever
from app.models.ingest import Chunk


class VectorStore(Protocol):
    """
    Protocol defining storage and retrieval operations
    for vectorized document chunks.
    """

    def upsert(self, chunks: List[Chunk]) -> int:
        """
        Upsert the given chunks into the vector store.

        Returns:
            int: number of items successfully upserted.

        Complexity: O(n) for n chunks.
        """
        ...

    def query(self, embedding: List[float], k: int) -> List[Chunk]:
        """
        Query the store for the top-k most similar chunks to the given embedding.

        Args:
            embedding (List[float]): the query vector
            k (int): number of nearest neighbors to return

        Returns:
            List[Chunk]: the k most similar chunks.

        Complexity: O(log N + k) in typical vector indexes.
        """
        ...

    def delete(self, filter: Dict[str, Any]) -> int:
        """
        Delete entries matching the given filter criteria.

        Args:
            filter (Dict[str, Any]): query filter for deletion

        Returns:
            int: number of items deleted.
        """
        ...

    def as_retriever(self, k: int) -> BaseRetriever:
        """
        Return a LangChain-compatible retriever for RAG workflows.

        Args:
            k (int): number of documents to retrieve

        Returns:
            BaseRetriever: retriever instance wrapping this vector store.
        """
        ...
