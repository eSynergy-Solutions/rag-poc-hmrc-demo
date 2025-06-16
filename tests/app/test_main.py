from fastapi.testclient import TestClient
from random import randint
import pytest

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_non_existent_endpoint(client):
    response = client.get("/non_existent")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_read_empty_history(client):
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json() == {"content": []}


def test_non_existent_history_route(client):
    response = client.get("/history/non_existent")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_chat_incorrect_chat_no_body(client):
    response = client.post("/chat")
    assert response.status_code == 422


def test_chat_incorrect_chat_incorrect_content_type(client):
    response = client.post("/chat", json={"content": 123})
    assert response.status_code == 422


def test_chat_correct_chat(client):
    response = client.post("/chat", json={"content": "Hello", "streaming": False})
    assert response.status_code == 200
    assert "role" in response.json()
    assert "content" in response.json()
    assert response.json().get("role") == ("assistant" or "user")
    assert isinstance(response.json().get("content"), str)


def test_populated_history(client):
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json().get("content") != []
    num_user = 0
    num_assistant = 0
    for message in response.json().get("content"):
        if message.get("role") == "user":
            num_user += 1
        elif message.get("role") == "assistant":
            num_assistant += 1
    assert num_user > 0
    assert num_assistant > 0
    assert num_user == num_assistant == 1


def test_populated_history_multiple_messages(client):
    num_messages = randint(2, 10)
    for _ in range(num_messages):
        response = client.post("/chat", json={"content": "Hello"})
        assert response.status_code == 200
        assert "role" in response.json()
        assert "content" in response.json()
        assert response.json().get("role") == ("assistant" or "user")
        assert isinstance(response.json().get("content"), str)
    response = client.get("/history")
    assert response.status_code == 200
    assert response.json().get("content") != []
    num_user = 0
    num_assistant = 0
    for message in response.json().get("content"):
        if message.get("role") == "user":
            num_user += 1
        elif message.get("role") == "assistant":
            num_assistant += 1
    assert num_user > 0
    assert num_assistant > 0
    assert num_user == num_assistant == num_messages + 1
