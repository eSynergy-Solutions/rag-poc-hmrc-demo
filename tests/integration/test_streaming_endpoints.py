# app/tests/integration/test_streaming_endpoints.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.deps import get_chat_chain

# Use the same dummy chain you already have in test_api.py
class DummyChain:
    def __call__(self, inputs):
        return {"result": "ignored for streaming", "source_documents": []}

@pytest.fixture(autouse=True)
def override_dependencies():
    # Override the real chain so we never actually call Azure
    app.dependency_overrides[get_chat_chain] = lambda: DummyChain()
    yield
    app.dependency_overrides.clear()

def test_chat_streaming_not_implemented():
    client = TestClient(app)
    resp = client.post("/v1/chat", json={"content": "hello", "streaming": True})
    assert resp.status_code == 501
    body = resp.json()
    assert body["detail"] == "Streaming responses not implemented yet"

def test_discover_streaming_not_implemented():
    client = TestClient(app)
    resp = client.post("/v1/discover", json={"content": "hello", "streaming": True})
    assert resp.status_code == 501
    body = resp.json()
    assert body["detail"] == "Streaming not implemented for discovery"
