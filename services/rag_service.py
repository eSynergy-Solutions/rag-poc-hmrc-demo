# app/services/discovery_service.py

from core.deps import get_chat_service
from abstracts.ServiceRag import ServiceRag
from llm.prompts import PROMPT_REGISTRY
from core.deps import get_logger
from vectorstore.pgvector import PGVectorStore
from services.oas_chunking import OpenAPIChunker
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import Literal
from models.chat import ChatEndpointRequest


class RagService(ServiceRag):
    def __init__(self):
        self.store = PGVectorStore()
        self.chunker = OpenAPIChunker()
        self.llm = get_chat_service()
        self._logger = get_logger()

    def query_vector_database(
        self,
        content: str | ChatEndpointRequest,
        service_name: Literal["discovery", "chat"],
    ) -> str:
        if isinstance(content, str):
            retrieved_docs = self.store.as_retriever().invoke(content)
        else:
            # Query the vector database with the user's latest query only
            retrieved_docs = self.store.as_retriever().invoke(
                content.messages[0].content
            )
        context = "\n".join([doc.page_content for doc in retrieved_docs])
        system_prompt: str = PROMPT_REGISTRY.get(f"{service_name}").template
        self._logger.info(f"Using system prompt:\n{system_prompt}")

        if isinstance(content, str):
            prompt = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=f"Here is the user's OAS file:\n{content}\n\nHere are the retrieved chunks:\n{context}"
                ),
            ]
        else:
            # Use the messages from the ChatEndpointRequest
            prompt = [
                SystemMessage(content=system_prompt),
            ]
            for message in content.messages[1:]:
                if message.role == "user":
                    prompt.append(HumanMessage(content=message.content))
                elif message.role == "assistant":
                    prompt.append(AIMessage(content=message.content))

        self._logger.info(f"Using prompt:\n{prompt}")

        return self.llm.invoke(prompt)
