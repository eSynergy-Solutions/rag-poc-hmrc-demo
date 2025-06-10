import sys
import os
import pytest
from fastapi.testclient import TestClient

# --- Path hack so we can import main.py directly ---
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# ----------------------------------------------------

from main import app  # now resolvable

@pytest.fixture(autouse=True)
def client():
    return TestClient(app)

# A minimal, valid OpenAPI 3.0 spec with required 'domain' & 'sub-domain'
VALID_OAS = """
openapi: 3.0.0
info:
  title: Sample API
  version: "1.0.0"
  domain: example
  sub-domain: demo
servers:
  - url: https://api.example.com/v1
    description: Production server
paths:
  /hello:
    get:
      summary: Greet the world
      responses:
        '200':
          description: Successful greeting
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: Hello, world!
"""

DEBUG = os.getenv("DEBUG_RESPONSES") == "1"

def test_oas_checker_one_shot_history(client):
    client.app.state.HistoryObjectOASChecker._history.clear()

    r1 = client.post("/oas-checker", json={"content": VALID_OAS, "streaming": False})
    assert r1.status_code == 200
    if DEBUG: print("OAS1→", r1.text)
    hist1 = client.app.state.HistoryObjectOASChecker.get_history()
    assert len(hist1) == 2
    assert client.app.state.HistoryObjectOASChecker.get_context_history()[0].content == VALID_OAS

    r2 = client.post("/oas-checker", json={"content": "not-an-oas", "streaming": False})
    assert r2.status_code == 200
    if DEBUG: print("OAS2→", r2.text)
    hist2 = client.app.state.HistoryObjectOASChecker.get_history()
    assert len(hist2) == 4
    assert client.app.state.HistoryObjectOASChecker.get_context_history()[0].content == "not-an-oas"

def test_oas_checker_valid_vs_gibberish(client):
    client.app.state.HistoryObjectOASChecker._history.clear()

    rv = client.post("/oas-checker", json={"content": VALID_OAS, "streaming": False})
    assert rv.status_code == 200
    if DEBUG: print("OAS VALID→", rv.text)
    assert "please provide" not in rv.json()["content"].lower()

    rv2 = client.post("/oas-checker", json={"content": "%%$$@@bad", "streaming": False})
    assert rv2.status_code == 200
    if DEBUG: print("OAS GIBBER→", rv2.text)
    txt = rv2.json()["content"].lower()
    assert "please provide" in txt and "open api specification" in txt

def test_discovery_one_shot_history(client):
    client.app.state.HistoryObjectDiscovery._history.clear()

    r1 = client.post("/discover", json={"content": VALID_OAS, "streaming": False})
    assert r1.status_code == 200
    if DEBUG: print("DISC1→", r1.text)
    hist1 = client.app.state.HistoryObjectDiscovery.get_history()
    assert len(hist1) == 2
    assert client.app.state.HistoryObjectDiscovery.get_context_history()[0].content == VALID_OAS

    r2 = client.post("/discover", json={"content": "some nonsense", "streaming": False})
    assert r2.status_code == 200
    if DEBUG: print("DISC2→", r2.text)
    hist2 = client.app.state.HistoryObjectDiscovery.get_history()
    assert len(hist2) == 4
    assert client.app.state.HistoryObjectDiscovery.get_context_history()[0].content == "some nonsense"
