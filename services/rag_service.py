# app/services/rag_service.py

from typing import Tuple, List, Optional
from langchain.chains.retrieval_qa.base import RetrievalQA
from models.chat import ChatMessage
from abstracts.ServiceRag import ServiceRag


class RAGService(ServiceRag):
    """
    High-level façade for RAG-based chat interactions.
    Can be initialized with an optional system_prompt to adjust “flavor.”
    """

    def __init__(
        self,
        chain: RetrievalQA,
        system_prompt: Optional[str] = None,
    ):
        """
        Args:
            chain: A LangChain RetrievalQA chain (or fallback).
            system_prompt: Optional override of the system prompt context.
                If provided, the chain should incorporate this prompt when invoked.
        """
        self.chain = chain
        self.system_prompt = system_prompt

    def retrieve_and_answer(
        self,
        history: List[ChatMessage],
        user_input: str,
    ) -> Tuple[str, List[dict]]:
        """
        Given conversation history and a new user message,
        run retrieval-augmented generation and return the answer
        along with the source documents (metadata).

        Returns:
            (answer_text, list_of_source_metadata)

        Note:
            We no longer wrap all exceptions in ChatServiceError so that
            downstream callers (and tests) can see raw errors if desired.
        """
        # 1) Build the inputs dict. Optionally, include system_prompt if given.
        inputs: dict = {"query": user_input, "chat_history": history}
        if self.system_prompt:
            # Some RetrievalQA implementations accept `system_prompt` key;
            # if not, the chain should already have been built with the correct prompt.
            inputs["system_prompt"] = self.system_prompt

        # 2) Invoke the chain directly, allowing raw exceptions to bubble up
        output = self.chain(inputs)

        # 3) If output is a dict, extract 'result' and 'source_documents'
        if isinstance(output, dict):
            answer = output.get("result", "")
            docs = output.get("source_documents", [])
            sources = [getattr(doc, "metadata", {}) for doc in docs]
            return answer, sources

        # 4) If chain returned a simple string, wrap as answer, no sources
        return str(output), []
