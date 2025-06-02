# app/tests/integration/test_full_endpoints.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.deps import get_chat_chain

from app.models.chat import QueryRequest

# ────────────────────────────────────────────────────────────────────────────────
# Whenever we call /v1/chat or /v1/discover, we need a "chain" that returns
# a predictable result. We override get_chat_chain with a dummy here.
# ────────────────────────────────────────────────────────────────────────────────

class DummyChain:
    def __call__(self, inputs):
        # Simulate RetrievalQA returning a dict with "result" and no source_documents
        return {"result": "dummy‐response", "source_documents": []}


@pytest.fixture(autouse=True)
def override_chain_dependency():
    """
    Override the real get_chat_chain dependency for the duration of these tests,
    so that calls to /v1/chat and /v1/discover always get DummyChain().
    """
    app.dependency_overrides[get_chat_chain] = lambda: DummyChain()
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


# ────────────────────────────────────────────────────────────────────────────────
# 1) Health endpoints
# ────────────────────────────────────────────────────────────────────────────────

def test_health_live_and_ready():
    resp_live = client.get("/v1/health/live")
    assert resp_live.status_code == 200

    resp_ready = client.get("/v1/health/ready")
    assert resp_ready.status_code == 200


# ────────────────────────────────────────────────────────────────────────────────
# 2) Chat endpoint
# ────────────────────────────────────────────────────────────────────────────────

def test_chat_missing_body_returns_422():
    # No JSON body at all → FastAPI should respond with 422 Unprocessable Entity
    resp = client.post("/v1/chat")
    assert resp.status_code == 422

def test_chat_incorrect_content_type_returns_422():
    # "content" must be a string; if we send an integer, Pydantic will reject
    payload = {"content": 123, "streaming": False}
    resp = client.post("/v1/chat", json=payload)
    assert resp.status_code == 422

def test_chat_streaming_true_returns_501():
    # streaming=True is not implemented → 501 Not Implemented
    payload = {"content": "hello", "streaming": True}
    resp = client.post("/v1/chat", json=payload)
    assert resp.status_code == 501
    assert resp.json()["detail"] == "Streaming responses not implemented yet"

def test_chat_success_returns_dummy_response():
    # Proper usage: content is a string, streaming omitted or False
    payload = {"content": "Test question"}
    resp = client.post("/v1/chat", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    # Should have {"content": {"role": "assistant", "content": "dummy‐response"}}
    assert "content" in data
    inner = data["content"]
    assert inner["role"] == "assistant"
    assert inner["content"] == "dummy‐response"


# ────────────────────────────────────────────────────────────────────────────────
# 3) Discover endpoint
# ────────────────────────────────────────────────────────────────────────────────

def test_discover_missing_body_returns_422():
    resp = client.post("/v1/discover")
    assert resp.status_code == 422

def test_discover_incorrect_content_type_returns_422():
    payload = {"content": 456, "streaming": False}
    resp = client.post("/v1/discover", json=payload)
    assert resp.status_code == 422

def test_discover_streaming_true_returns_501():
    payload = {"content": "hello", "streaming": True}
    resp = client.post("/v1/discover", json=payload)
    assert resp.status_code == 501
    assert resp.json()["detail"] == "Streaming not implemented for discovery"

def test_discover_success_returns_dummy_response():
    payload = {"content": "Some API spec text", "streaming": False}
    resp = client.post("/v1/discover", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert "content" in data
    inner = data["content"]
    assert inner["role"] == "assistant"
    assert isinstance(inner["content"], str)
    # Because our DummyChain returns "dummy‐response"
    assert inner["content"] == "dummy‐response"


# ────────────────────────────────────────────────────────────────────────────────
# 4) OAS‐check endpoint
# ────────────────────────────────────────────────────────────────────────────────

def test_oas_check_missing_body_returns_422():
    resp = client.post("/v1/oas-check")
    assert resp.status_code == 422

def test_oas_check_invalid_spec_returns_400():
    # Missing the top‐level "openapi" field
    bad_spec = """
info:
  title: Incomplete
  version: '1.0'
paths: {}
"""
    payload = {"content": bad_spec}
    resp = client.post("/v1/oas-check", json=payload)
    assert resp.status_code == 400
    text = resp.text
    assert "Specification Validation Failed" in text

def test_oas_check_malformed_yaml_returns_400():
    # Unparsable YAML → should surface parse error in response.errors
    bad = "::: not valid yaml :::"
    payload = {"content": bad}
    resp = client.post("/v1/oas-check", json=payload)
    assert resp.status_code == 400
    assert "Specification Validation Failed" in resp.text
    # Might contain "Failed to parse spec"
    assert "Failed to parse spec" in resp.text or "paths: must be an object" in resp.text

def test_oas_check_minimal_valid_spec_returns_200():
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


# ────────────────────────────────────────────────────────────────────────────────
# 5) Non‐existent routes under /v1 should return 404
# ────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("method, path", [
    ("GET",  "/v1/nonexistent"),
    ("POST", "/v1/foo_bar"),
    ("PUT",  "/v1/chat/extra"),
])
def test_unknown_v1_routes_return_404(method, path):
    client_method = getattr(client, method.lower())
    if method == "GET":
        resp = client.get(path)
    elif method == "POST":
        resp = client.post(path, json={})
    else:
        resp = client.put(path, json={})
    assert resp.status_code == 404
    # FastAPI’s default JSON payload for 404 is {"detail":"Not Found"}
    assert resp.json() == {"detail": "Not Found"}
