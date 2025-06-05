# app/tests/unit/test_chat_chain_builder.py

import pytest
from langchain.schema import BaseRetriever
from langchain.chains import RetrievalQA

from llm.chat_chain import build_chat_chain


class DummyRetriever(BaseRetriever):
    def __init__(self):
        pass

    def get_relevant_documents(self, query: str):
        return []


def test_build_chat_chain_returns_RetrievalQA(monkeypatch):
    """
    Verify that build_chat_chain(...) returns a RetrievalQA whose retriever
    is exactly the DummyRetriever instance we pass in.
    """

    # Monkey-patch AzureChatOpenAI so that it doesn’t try to connect.
    from llm.chat_chain import AzureChatOpenAI

    class FakeLLM:
        def __init__(
            SELF, azure_deployment, azure_endpoint, openai_api_key, temperature, verbose
        ):
            # Just store the parameters, but no network calls
            SELF.deployment = azure_deployment
            SELF.endpoint = azure_endpoint
            SELF.api_key = openai_api_key
            SELF.temperature = temperature

        def __call__(self, *args, **kwargs):
            # stub: never used
            raise AssertionError("LLM should not be called in builder test")

    monkeypatch.setattr("app.llm.chat_chain.AzureChatOpenAI", FakeLLM)

    dummy_r = DummyRetriever()
    chain = build_chat_chain(
        endpoint="https://dummy.endpoint",
        api_key="dummy-key",
        deployment="dummy-deploy",
        retriever=dummy_r,
    )

    assert isinstance(chain, RetrievalQA)
    # Under the hood, RetrievalQA.retriever should be exactly dummy_r
    # (LangChain stores it as chain.retriever)
    assert getattr(chain, "retriever", None) is dummy_r
