import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

SAMPLE_OAS = """\
openapi: 3.0.0
info:
  title: Sample API
  description: >
    Multi-line or single-line
  version: 0.1.9

servers:
  - url: http://api.example.com/v1
    description: Main server
paths:
  /users:
    get:
      summary: List users
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: array
                items:
                  type: string
"""

@pytest.mark.parametrize("endpoint", ["/v1/oas-check", "/v1/discover"])
def test_raw_yaml_body_is_unprocessable(endpoint):
    # Sending the YAML directly → FastAPI cannot bind it to QueryRequest
    resp = client.post(endpoint, data=SAMPLE_OAS, headers={"Content-Type": "text/plain"})
    assert resp.status_code == 422

@pytest.mark.parametrize("endpoint", ["/v1/oas-check", "/v1/discover"])
def test_json_wrapped_oas_is_accepted(endpoint):
    # Wrapping the same YAML in the expected JSON model → 200 (or 200+ for /discover)
    resp = client.post(
        endpoint,
        json={"content": SAMPLE_OAS, "streaming": False},
    )
    # oas-check → 200 OK with HTMLResponse
    # discover → 200 OK with QueryResponse
    assert resp.status_code == 200, resp.text
