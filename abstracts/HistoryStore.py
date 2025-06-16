from abc import ABC, abstractmethod
from typing import List
from models.chat import ChatMessage


class HistoryStore(ABC):
    """
    Abstract base class for a history store.
    This class defines the interface for storing and retrieving chat history.
    Implementations should provide concrete storage mechanisms.
    """

    @abstractmethod
    def record_message(self, session_id: str, message: ChatMessage) -> None:
        """
        Append a ChatMessage to the history list for the given session_id.
        Raises TypeError if the session_id or message is invalid.
        """
        pass

    @abstractmethod
    def get_history(self, session_id: str) -> List[ChatMessage]:
        """
        Return the list of ChatMessage for the given session_id.
        If no history exists for session_id, returns an empty list.
        Raises TypeError if the session_id is invalid.
        """
        pass

    @abstractmethod
    def get_context_history(self, session_id: str) -> List[ChatMessage]:
        """
        Alias for get_history; reserved for any future context-specific behavior.
        """
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """
        Clear all histories from the store.
        """
        pass
