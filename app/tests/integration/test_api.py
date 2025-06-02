# app/tests/integration/test_api.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.deps import get_chat_chain
from app.models.chat import ChatMessage
from app.history.store import get_history_store
from app.errors import ChatServiceError

# -----------------------------------------------------------------------------------
# DummyChain definitions for overriding get_chat_chain dependency.
# One returns a fixed result; another yields a streaming generator.
# -----------------------------------------------------------------------------------
class DummyChain:
    def __call__(self, inputs):
        # Simulate RetrievalQA output dict
        return {"result": "Hello from dummy chain", "source_documents": []}


class DummyStreamChain:
    def __call__(self, inputs):
        # Simulate streaming generator of chunks for RetrievalQA
        def streamer():
            yield "chunk1-"
            yield "chunk2-"
            yield "chunk3"
        return streamer()


@pytest.fixture(autouse=True)
def override_dependencies():
    """
    By default, override get_chat_chain to use DummyChain (non‐streaming).
    For streaming tests, override locally in the test.
    """
    app.dependency_overrides[get_chat_chain] = lambda: DummyChain()
    # Clear in-memory history before each test
    store = get_history_store()
    # Assuming history is stored under a single session_id, e.g. "test-session"
    # For simplicity, we can just clear the entire private dict:
    store._store.clear()
    yield
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------------
# 1) Health endpoints
# -----------------------------------------------------------------------------------
def test_health_live_and_ready():
    client = TestClient(app)
    resp_live = client.get("/v1/health/live")
    assert resp_live.status_code == 200
    # CORS header present
    assert resp_live.headers.get("access-control-allow-origin") == "*"

    resp_ready = client.get("/v1/health/ready")
    assert resp_ready.status_code == 200
    assert resp_ready.headers.get("access-control-allow-origin") == "*"


# -----------------------------------------------------------------------------------
# 2) Test “/v1/test” endpoint
# -----------------------------------------------------------------------------------
def test_test_endpoint_returns_simple_message():
    client = TestClient(app)
    resp = client.post("/v1/test")
    assert resp.status_code == 200
    # Should return plain text or JSON string
    assert resp.json() == {"content": "Hi! The server is up and running!"}


# -----------------------------------------------------------------------------------
# 3) Chat endpoint (non-streaming)
# -----------------------------------------------------------------------------------
def test_chat_missing_body_returns_422():
    client = TestClient(app)
    resp = client.post("/v1/chat")
    assert resp.status_code == 422


def test_chat_incorrect_content_type_returns_422():
    client = TestClient(app)
    payload = {"content": 123, "streaming": False}
    resp = client.post("/v1/chat", json=payload)
    assert resp.status_code == 422


def test_chat_streaming_true_returns_501_by_default():
    """
    With DummyChain (non-streaming), streaming=True should still raise 501.
    We’ll override get_chat_chain locally in the next test to simulate streaming.
    """
    client = TestClient(app)
    payload = {"content": "hello", "streaming": True}
    resp = client.post("/v1/chat", json=payload)
    assert resp.status_code == 501
    assert resp.json()["detail"] == "Streaming responses not implemented yet"


def test_chat_success_returns_dummy_response_and_records_history():
    client = TestClient(app)
    # Use a consistent session identifier; assume router reads “session_id” from header or defaults
    headers = {"X-Session-Id": "test-session"}
    payload = {"content": "Test question", "streaming": False}
    resp = client.post("/v1/chat", json=payload, headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    assert "content" in data
    inner = data["content"]
    assert inner["role"] == "assistant"
    assert inner["content"] == "Hello from dummy chain"

    # Verify history store was updated: one user message + one assistant message
    store = get_history_store()
    history = store.get_history("test-session")
    assert len(history) == 2
    assert history[0] == ChatMessage(role="user", content="Test question")
    assert history[1] == ChatMessage(role="assistant", content="Hello from dummy chain")


# -----------------------------------------------------------------------------------
# 4) Chat endpoint (streaming) with DummyStreamChain
# -----------------------------------------------------------------------------------
def test_chat_streaming_generator_overridden_chain_records_history():
    # Override only for this test to use streaming chain
    app.dependency_overrides[get_chat_chain] = lambda: DummyStreamChain()

    client = TestClient(app)
    headers = {"X-Session-Id": "stream-session"}
    payload = {"content": "Stream me", "streaming": True}
    resp = client.post("/v1/chat", json=payload, headers=headers, stream=True)
    assert resp.status_code == 200
    # Collect chunks
    chunks = b"".join(resp.iter_content(chunk_size=None)).decode("utf-8")
    assert chunks == "chunk1-chunk2-chunk3"

    # Verify history store: once for user, once for assistant with full concatenated content
    store = get_history_store()
    history = store.get_history("stream-session")
    assert len(history) == 2
    assert history[0] == ChatMessage(role="user", content="Stream me")
    assert history[1] == ChatMessage(role="assistant", content="chunk1-chunk2-chunk3")


# -----------------------------------------------------------------------------------
# 5) Discover endpoint
# -----------------------------------------------------------------------------------
def test_discover_missing_body_returns_422():
    client = TestClient(app)
    resp = client.post("/v1/discover")
    assert resp.status_code == 422


def test_discover_incorrect_content_type_returns_422():
    client = TestClient(app)
    payload = {"content": 456, "streaming": False}
    resp = client.post("/v1/discover", json=payload)
    assert resp.status_code == 422


def test_discover_streaming_true_returns_501():
    client = TestClient(app)
    payload = {"content": "hello", "streaming": True}
    resp = client.post("/v1/discover", json=payload)
    assert resp.status_code == 501
    assert resp.json()["detail"] == "Streaming not implemented for discovery"


def test_discover_success_returns_dummy_response_and_records_history():
    client = TestClient(app)
    headers = {"X-Session-Id": "discover-session"}
    payload = {"content": "Some API spec text", "streaming": False}
    resp = client.post("/v1/discover", json=payload, headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    assert "content" in data
    inner = data["content"]
    assert inner["role"] == "assistant"
    assert isinstance(inner["content"], str)
    assert inner["content"] == "Hello from dummy chain"

    store = get_history_store()
    history = store.get_history("discover-session")
    assert len(history) == 2
    assert history[0] == ChatMessage(role="user", content="Some API spec text")
    assert history[1] == ChatMessage(role="assistant", content="Hello from dummy chain")


# -----------------------------------------------------------------------------------
# 6) OAS-check endpoint
# -----------------------------------------------------------------------------------
def test_oas_check_missing_body_returns_422():
    client = TestClient(app)
    resp = client.post("/v1/oas-check")
    assert resp.status_code == 422


def test_oas_check_invalid_spec_returns_400():
    client = TestClient(app)
    bad_spec = """
info:
  title: Bad API
  version: '1.0'
paths: {}
"""
    payload = {"content": bad_spec}
    resp = client.post("/v1/oas-check", json=payload)
    assert resp.status_code == 400
    assert "Specification Validation Failed" in resp.text


def test_oas_check_malformed_yaml_returns_400():
    client = TestClient(app)
    bad = "::: not valid yaml :::"
    payload = {"content": bad}
    resp = client.post("/v1/oas-check", json=payload)
    assert resp.status_code == 400
    assert "Specification Validation Failed" in resp.text
    # Should mention parse failure
    assert "Failed to parse spec" in resp.text or "paths: must be an object" in resp.text


def test_oas_check_minimal_valid_spec_returns_200():
    client = TestClient(app)
    minimal = """
openapi: 3.0.0
info:
  title: Valid API
  version: '1.0'
paths: {}
"""
    payload = {"content": minimal}
    resp = client.post("/v1/oas-check", json=payload)
    assert resp.status_code == 200
    assert "Specification is valid" in resp.text


# -----------------------------------------------------------------------------------
# 7) History endpoint
# -----------------------------------------------------------------------------------
def test_get_history_empty_returns_empty_list():
    client = TestClient(app)
    # No messages recorded
    resp = client.get("/v1/history", headers={"X-Session-Id": "nonexistent"})
    assert resp.status_code == 200
    assert resp.json() == {"content": []}


def test_get_history_after_chats_returns_messages():
    client = TestClient(app)
    session_header = {"X-Session-Id": "history-session"}
    # Send one chat, one discover sequence
    client.post("/v1/chat", json={"content": "Hello"}, headers=session_header)
    client.post("/v1/discover", json={"content": "World"}, headers=session_header)

    resp = client.get("/v1/history", headers=session_header)
    assert resp.status_code == 200
    data = resp.json().get("content")
    # Should have four total messages: chat-user, chat-assistant, discover-user, discover-assistant
    assert isinstance(data, list)
    assert len(data) == 4
    assert data[0]["role"] == "user"
    assert data[0]["content"] == "Hello"
    assert data[1]["role"] == "assistant"
    assert data[2]["role"] == "user"
    assert data[2]["content"] == "World"
    assert data[3]["role"] == "assistant"


# -----------------------------------------------------------------------------------
# 8) Non-existent routes under /v1 should return 404
# -----------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "method, path", [("GET", "/v1/nonexistent"), ("POST", "/v1/foo_bar"), ("PUT", "/v1/chat/extra")]
)
def test_unknown_v1_routes_return_404(method, path):
    client = TestClient(app)
    if method == "GET":
        resp = client.get(path)
    elif method == "POST":
        resp = client.post(path, json={})
    else:
        resp = client.put(path, json={})
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Not Found"}
