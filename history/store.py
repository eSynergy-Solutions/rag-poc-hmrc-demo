# app/history/store.py

from threading import Lock
from typing import Dict, List
from app.models.chat import ChatMessage
from app.errors import StorageError

class InMemoryHistoryStore:
    """
    Simple in-memory store for chat history, keyed by session ID.
    Not persistent across restarts; intended as a lightweight default.
    """

    def __init__(self):
        # Internal mapping: session_id -> list of ChatMessage
        self._store: Dict[str, List[ChatMessage]] = {}
        self._lock = Lock()

    def record_message(self, session_id: str, message: ChatMessage) -> None:
        """
        Append a ChatMessage to the history list for the given session_id.
        Raises TypeError if the session_id or message is invalid.
        """
        if not isinstance(session_id, str) or not session_id:
            raise TypeError(f"Invalid session_id: {session_id}")

        if not isinstance(message, ChatMessage):
            raise TypeError("message must be a ChatMessage instance")

        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = []
            self._store[session_id].append(message)

    def get_history(self, session_id: str) -> List[ChatMessage]:
        """
        Return the list of ChatMessage for the given session_id.
        If no history exists for session_id, returns an empty list.
        Raises TypeError if the session_id is invalid.
        """
        if not isinstance(session_id, str) or not session_id:
            raise TypeError(f"Invalid session_id: {session_id}")

        with self._lock:
            return list(self._store.get(session_id, []))

    def get_context_history(self, session_id: str) -> List[ChatMessage]:
        """
        Alias for get_history; reserved for any future context-specific behavior.
        """
        return self.get_history(session_id)

    def clear_all(self) -> None:
        """
        Clear all histories from the store.
        """
        with self._lock:
            self._store.clear()


# Singleton instance and accessor ------------------------------------------------

_history_store_instance: InMemoryHistoryStore = InMemoryHistoryStore()

def get_history_store() -> InMemoryHistoryStore:
    """
    Retrieve the singleton InMemoryHistoryStore. In future, this could
    be extended to return a Redis-backed store if configured.
    """
    return _history_store_instance
