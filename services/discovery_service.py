# app/services/discovery_service.py

from core.deps import get_chat_service
from abstracts.ServiceDiscovery import ServiceDiscovery
from llm.prompts import PROMPT_REGISTRY
from vectorstore.pgvector import PGVectorStore
from services.oas_chunking import OpenAPIChunker
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


class DiscoveryService(ServiceDiscovery):
    def __init__(self):
        self.store = PGVectorStore()
        self.chunker = OpenAPIChunker()
        self.llm = get_chat_service()

    def query_vector_database(self, yaml_string: str):
        retrieved_docs = self.store.as_retriever().invoke(yaml_string)
        context = "\n".join([doc.page_content for doc in retrieved_docs])
        final_input = {
            "context": context,
            "yaml_string": yaml_string,
        }
        system_prompt: str = PROMPT_REGISTRY.get("discover_v2").template
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_prompt),
                HumanMessagePromptTemplate.from_template(
                    "{context}\n\nHere is the new OAS:\n{yaml_string}"
                ),
            ]
        )
        qa_chain = prompt | self.llm | StrOutputParser()

        return qa_chain.invoke(final_input)
