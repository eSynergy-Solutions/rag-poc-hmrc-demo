# app/vectorstore/astradb.py

from typing import List, Dict, Any
from astrapy import DataAPIClient
from langchain.schema import BaseRetriever, Document
from app.vectorstore.interface import VectorStore
from app.models.ingest import Chunk
from app.llm.embeddings import get_embedding
from app.errors import StorageError


class AstraStore(VectorStore):
    """
    AstraDB-backed implementation of the VectorStore protocol.
    Embeds each chunk internally using get_embedding before upsert.
    """

    def __init__(
        self,
        token: str,
        api_endpoint: str,
        keyspace: str,
        collection_name: str,
    ):
        try:
            client = DataAPIClient(token)
            self._db = client.get_database(api_endpoint, keyspace=keyspace)
            self._collection = self._db.get_collection(collection_name)
        except Exception as e:
            raise StorageError(f"AstraStore initialization failed: {e}")

    def upsert(self, chunks: List[Chunk]) -> int:
        """
        Upsert chunks into AstraDB, embedding each via get_embedding.
        Returns the number of documents upserted.
        Raises StorageError on failure.
        """
        try:
            docs: List[Dict[str, Any]] = []
            for chunk in chunks:
                vector = get_embedding(chunk.content)
                docs.append({
                    "path": chunk.path,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "$vector": vector,
                })

            self._collection.insert_many(docs)
            return len(docs)

        except Exception as e:
            raise StorageError(f"AstraStore.upsert failed: {e}")

    def query(self, embedding: List[float], k: int) -> List[Chunk]:
        """
        Query the AstraDB collection for top-k nearest neighbors.
        Returns a list of Chunk objects. Raises StorageError on failure.
        """
        try:
            cursor = self._collection.find(
                {},
                sort={"$vector": embedding},
                limit=k,
            )
            results: List[Chunk] = []
            for doc in cursor:
                results.append(
                    Chunk(
                        path=doc["path"],
                        content=doc["content"],
                        chunk_index=doc.get("chunk_index", 0),
                    )
                )
            return results

        except Exception as e:
            raise StorageError(f"AstraStore.query failed: {e}")

    def delete(self, filter: Dict[str, Any]) -> int:
        """
        Delete entries matching the metadata filter. Returns deleted count.
        Raises StorageError on failure.
        """
        try:
            result = self._collection.delete_many(filter)
            return getattr(result, "deleted_count", 0)
        except Exception as e:
            raise StorageError(f"AstraStore.delete failed: {e}")

    def as_retriever(self, k: int) -> BaseRetriever:
        """
        Return a LangChain-compatible retriever for RAG workflows.
        """

        class _AstraRetriever(BaseRetriever):
            def __init__(self, store: "AstraStore", k: int):
                self.store = store
                self.k = k

            def get_relevant_documents(self, query: str) -> List[Document]:
                """
                Use get_embedding on the query, then call store.query,
                converting each Chunk into a Document. Raises StorageError on failure.
                """
                try:
                    emb = get_embedding(query)
                    chunks = self.store.query(emb, k=self.k)
                    docs: List[Document] = []
                    for c in chunks:
                        docs.append(
                            Document(
                                page_content=c.content,
                                metadata={"path": c.path, "chunk_index": c.chunk_index},
                            )
                        )
                    return docs
                except Exception as e:
                    raise StorageError(f"AstraRetriever.get_relevant_documents failed: {e}")

        return _AstraRetriever(self, k)
