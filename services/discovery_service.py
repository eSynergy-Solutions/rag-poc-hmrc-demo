# app/services/discovery_service.py

from core.deps import get_chat_service
from abstracts.ServiceDiscovery import ServiceDiscovery
from llm.prompts import PROMPT_REGISTRY
from core.deps import get_logger
from vectorstore.pgvector import PGVectorStore
from services.oas_chunking import OpenAPIChunker
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    SystemMessage, HumanMessage
)


class DiscoveryService(ServiceDiscovery):
    def __init__(self):
        self.store = PGVectorStore()
        self.chunker = OpenAPIChunker()
        self.llm = get_chat_service()
        self._logger = get_logger()

    def query_vector_database(self, content: str):
        retrieved_docs = self.store.as_retriever().invoke(content)
        context = "\n".join([doc.page_content for doc in retrieved_docs])
        system_prompt: str = PROMPT_REGISTRY.get("discover_v2").template
        self._logger.info(f"Using system prompt:\n{system_prompt}")

        prompt = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=
                f"Here is the user's OAS file:\n{content}\n\nHere are the retrieved chunks:\n{context}"
            ),
        ]
        
        self._logger.info(f"Using prompt:\n{prompt}")

        return self.llm.invoke(prompt)
