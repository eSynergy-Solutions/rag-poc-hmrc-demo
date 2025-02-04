import pytest
from src.history.BasicHistory import BaseHistory
from src.schemas.ChatSchemas import ChatMessage
from pydantic import ValidationError


@pytest.fixture
def history_object():
    return BaseHistory()


def test_raises_type_error():
    with pytest.raises(TypeError):
        BaseHistory("RandomString")


def test_empty_history(history_object):
    assert history_object.get_history() == [], "History should be empty"


# TODO: Change this when get_context_history is implemented
def test_empty_context_history(history_object):
    assert history_object.get_context_history() == [], "Context history should be empty"


def test_record_message_no_message_error(history_object):
    with pytest.raises(TypeError):
        history_object.record_message("Hello")
    assert history_object.get_history() == [], "History should not contain any messages"


def test_record_message_incorrect_role_type_error(history_object):
    with pytest.raises(ValidationError):
        history_object.record_message(ChatMessage(role="ai", content="Hello"))
    assert history_object.get_history() == [], "History should not contain any messages"


def test_record_message_incorrect_message_type_error(history_object):
    with pytest.raises(ValidationError):
        history_object.record_message(ChatMessage(role="user", content=123))
    assert history_object.get_history() == [], "History should not contain any messages"


def test_record_message_no_error(history_object):
    history_object.record_message(ChatMessage(role="user", content="Hello"))
    current_history = history_object.get_history()
    assert len(current_history) == 1, "History should contain one message"
    assert current_history == [
        ChatMessage(role="user", content="Hello")
    ], "History should contain the correct message"
