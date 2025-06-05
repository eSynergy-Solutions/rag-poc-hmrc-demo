# app/tests/unit/test_cors.py

from fastapi.testclient import TestClient
import pytest
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.parametrize("path", ["/v1/health/live", "/v1/health/ready"])
def test_cors_headers_present(client, path):
    """
    Ensure that the CORS middleware is configured correctly by verifying
    that `Access-Control-Allow-Origin: *` appears on health endpoints.
    """
    resp = client.get(path)
    assert resp.status_code == 200
    # The header should be present and set to '*'
    assert resp.headers.get("access-control-allow-origin") == "*"
