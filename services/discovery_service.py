# app/services/discovery_service.py

from core.deps import get_chat_service
from abstracts.ServiceDiscovery import ServiceDiscovery
from llm.prompts import PROMPT_REGISTRY
from core.deps import get_logger
from vectorstore.pgvector import PGVectorStore
from services.oas_chunking import OpenAPIChunker
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import (
    SystemMessage, HumanMessage
)


class DiscoveryService(ServiceDiscovery):
    def __init__(self):
        self.store = PGVectorStore()
        self.chunker = OpenAPIChunker()
        self.llm = get_chat_service()
        self._logger = get_logger()

    def _log_retrieved_docs(self, retrieved_docs):
        """Log details about the retrieved documents"""
        self._logger.info(f"vectorStore returned {len(retrieved_docs)} documents")
        for i, doc in enumerate(retrieved_docs):
            source = doc.metadata.get('source', 'unknown')
            content_length = len(doc.page_content)
            self._logger.info(f"Doc {i+1}: {source} - {content_length} chars")
            self._logger.debug(f"Doc {i+1} content: {doc.page_content[:200]}...")

    def query_vector_database(self, content: str):
        self._logger.info("############### RAG ################")

        self._logger.info(f"User asks to be pased to VectorDb: {content}")

        retrieved_docs = self.store.as_retriever().invoke(content)
        
        # If no documents retrieved, try using the query method
        if len(retrieved_docs) == 0:
            self._logger.warning("No documents retrieved with as_retriever, trying query method")
            query_results = self.store.query(content)
            retrieved_docs = [doc for doc, score in query_results]
            self._logger.info(f"Query method returned {len(retrieved_docs)} documents")
        
        # Log the retrieved documents
        self._log_retrieved_docs(retrieved_docs)


        
        context = "\n".join([doc.page_content for doc in retrieved_docs])



        system_prompt: str = PROMPT_REGISTRY.get("discovery").template
        self._logger.info(f"Using system prompt:\n{system_prompt}")

        prompt = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=
                f"Here is the user's OAS file:\n{content}\n\nHere are the retrieved chunks:\n{context}"
            ),
        ]
        
        self._logger.info(f"Using prompt:\n{prompt}")

        self._logger.info("###################################")

        return self.llm.invoke(prompt)
