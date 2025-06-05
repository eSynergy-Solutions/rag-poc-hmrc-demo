# app/tests/unit/test_history_store.py

import pytest
from history.store import get_history_store, InMemoryHistoryStore
from models.chat import ChatMessage


@pytest.fixture(autouse=True)
def clear_store():
    """
    Before each test, ensure the in-memory store is cleared.
    """
    store = get_history_store()
    store.clear_all()  # Wipe every session’s history
    yield
    store.clear_all()


def test_record_and_get_history_single_session():
    """
    Record two messages under 'session1' and verify get_history and get_context_history.
    """
    store: InMemoryHistoryStore = get_history_store()

    msg1 = ChatMessage(role="user", content="Hello")
    msg2 = ChatMessage(role="assistant", content="Hi there")

    store.record_message("session1", msg1)
    store.record_message("session1", msg2)

    # get_history should return both messages in order
    history = store.get_history("session1")
    assert history == [msg1, msg2]

    # get_context_history (default) returns same
    context_history = store.get_context_history("session1")
    assert context_history == [msg1, msg2]


def test_record_multiple_sessions_isolated():
    """
    Recording in different sessions should not mix histories.
    """
    store: InMemoryHistoryStore = get_history_store()

    s1_msg = ChatMessage(role="user", content="User 1")
    s2_msg = ChatMessage(role="user", content="User 2")

    store.record_message("s1", s1_msg)
    store.record_message("s2", s2_msg)

    assert store.get_history("s1") == [s1_msg]
    assert store.get_history("s2") == [s2_msg]


def test_get_history_empty_session_returns_empty_list():
    """
    If no messages recorded under a session, get_history returns empty list.
    """
    store: InMemoryHistoryStore = get_history_store()
    assert store.get_history("nonexistent") == []
    assert store.get_context_history("nonexistent") == []


def test_record_message_invalid_session_key_raises_type_error():
    """
    Passing a non-string session key should raise TypeError.
    """
    store: InMemoryHistoryStore = get_history_store()
    msg = ChatMessage(role="user", content="Hello")
    with pytest.raises(TypeError):
        store.record_message(123, msg)  # session_id must be a string


def test_record_message_invalid_message_type_raises_type_error():
    """
    Passing a non-ChatMessage object should raise TypeError.
    """
    store: InMemoryHistoryStore = get_history_store()
    with pytest.raises(TypeError):
        store.record_message("session1", "not a ChatMessage")


def test_history_persists_order_correctly():
    """
    Verify that recording multiple messages preserves chronological order.
    """
    store: InMemoryHistoryStore = get_history_store()
    messages = [
        ChatMessage(role="user", content="First"),
        ChatMessage(role="assistant", content="Second"),
        ChatMessage(role="user", content="Third"),
    ]
    for msg in messages:
        store.record_message("sessionX", msg)

    assert store.get_history("sessionX") == messages
