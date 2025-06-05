import pytest
from services.rag_service import RAGService
from models.chat import ChatMessage


class DummyDoc:
    def __init__(self, metadata):
        self.metadata = metadata


class DummyChain:
    def __init__(self, output):
        self.output = output

    def __call__(self, inputs):
        # simulate RetrievalQA behaviour
        return self.output


def test_rag_service_with_dict_output():
    # simulate a dict‐style chain output
    docs = [DummyDoc({"foo": "bar"}), DummyDoc({"baz": 123})]
    output = {"result": "answer text", "source_documents": docs}
    service = RAGService(chain=DummyChain(output))

    answer, sources = service.retrieve_and_answer([], "hello")
    assert answer == "answer text"
    # we extract the metadata only
    assert sources == [{"foo": "bar"}, {"baz": 123}]


def test_rag_service_with_string_output():
    # simulate a chain that returns a plain string
    service = RAGService(chain=DummyChain("just a plain string"))
    answer, sources = service.retrieve_and_answer([], "ignored")
    assert answer == "just a plain string"
    # string outputs get no sources
    assert sources == []


def test_rag_service_raises_on_chain_error():
    # simulate an LLM error bubbling up
    class FailingChain:
        def __call__(self, inputs):
            raise RuntimeError("chain failure")

    service = RAGService(chain=FailingChain())
    with pytest.raises(RuntimeError) as exc:
        service.retrieve_and_answer([], "query")
    assert "chain failure" in str(exc.value)
