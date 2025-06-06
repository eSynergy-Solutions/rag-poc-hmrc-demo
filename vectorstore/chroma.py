# app/vectorstore/chroma.py

from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from langchain.schema import BaseRetriever, Document
from vectorstore.interface import VectorStore
from models.ingest import Chunk
from errors import StorageError

# Cache one persistent Chroma client per directory
_CLIENTS: Dict[str, chromadb.PersistentClient] = {}


class ChromaStore(VectorStore):
    """
    Chroma-backed implementation of VectorStore, for local or hosted Chroma instances.
    Internally computes embeddings via Azure OpenAI to match AstraStore behavior.
    """

    def __init__(self, persist_directory: str = ".chromadb"):
        try:
            # Reuse or create a PersistentClient for this directory
            if persist_directory not in _CLIENTS:
                _CLIENTS[persist_directory] = chromadb.PersistentClient(
                    path=persist_directory  # type: ignore[arg-type]
                )
            self._client = _CLIENTS[persist_directory]
            # get_or_create_collection will work on a PersistentClient as well
            self._collection = self._client.get_or_create_collection("default")
        except Exception as e:
            raise StorageError(f"ChromaStore initialization failed: {e}")

    def upsert(self, chunks: List[Chunk]) -> int:
        """
        Upsert chunks into Chroma; computes embeddings internally.
        Returns the number of items upserted. Raises StorageError on failure.
        """
        try:
            # Import get_embedding at runtime so that any test-patched version is used
            from llm.embeddings import get_embedding

            ids = [f"{chunk.path}-{chunk.chunk_index}" for chunk in chunks]
            metadatas = [
                {"path": chunk.path, "chunk_index": chunk.chunk_index}
                for chunk in chunks
            ]
            documents = [chunk.content for chunk in chunks]
            embeddings = [get_embedding(chunk.content) for chunk in chunks]

            self._collection.add(
                ids=ids,
                metadatas=metadatas,
                documents=documents,
                embeddings=embeddings,
            )
            return len(chunks)
        except Exception as e:
            raise StorageError(f"ChromaStore.upsert failed: {e}")

    def query(self, embedding: List[float], k: int) -> List[Chunk]:
        """
        Retrieve top-k nearest neighbors from Chroma.
        Returns a list of Chunk objects. Raises StorageError on failure.
        """
        try:
            results = self._collection.query(
                query_embeddings=[embedding],
                n_results=k,
                include=["metadatas", "documents"],
            )
            chunks: List[Chunk] = []
            for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
                chunks.append(
                    Chunk(
                        path=meta["path"],
                        content=doc,
                        chunk_index=meta["chunk_index"],
                    )
                )
            return chunks
        except Exception as e:
            raise StorageError(f"ChromaStore.query failed: {e}")

    def delete(self, filter: Dict[str, Any]) -> int:
        """
        Delete entries matching metadata filter. Returns number of deleted items.
        Raises StorageError on failure.
        """
        try:
            # Measure count before deletion
            pre_count = self._collection.count()

            # Perform deletion
            self._collection.delete(where=filter)

            # Measure count after deletion
            post_count = self._collection.count()
            return pre_count - post_count
        except Exception as e:
            raise StorageError(f"ChromaStore.delete failed: {e}")

    def as_retriever(self, k: int) -> BaseRetriever:
        """
        Return a LangChain-compatible retriever for RAG workflows.
        """

        class _ChromaRetriever(BaseRetriever):
            def __init__(self, store: "ChromaStore", k: int):
                # Bypass Pydantic’s field restrictions for undeclared fields
                object.__setattr__(self, "store", store)
                object.__setattr__(self, "k", k)
                object.__setattr__(self, "tags", [])
                # LangChain’s BaseRetriever expects a `metadata` field
                object.__setattr__(self, "metadata", {})

            def get_relevant_documents(self, query: str) -> List[Document]:
                """
                Use get_embedding on the query, then call store.query,
                converting each Chunk into a Document. Raises StorageError on failure.
                """
                try:
                    from llm.embeddings import get_embedding

                    emb = get_embedding(query)
                    chunks = self.store.query(emb, k=self.k)
                    return [
                        Document(
                            page_content=c.content,
                            metadata={"path": c.path, "chunk_index": c.chunk_index},
                        )
                        for c in chunks
                    ]
                except Exception as e:
                    raise StorageError(
                        f"ChromaRetriever.get_relevant_documents failed: {e}"
                    )

        return _ChromaRetriever(self, k)
