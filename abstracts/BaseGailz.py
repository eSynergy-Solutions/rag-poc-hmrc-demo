from abc import ABC, abstractmethod
from typing import List, Any


class BaseLLM(ABC):
    """
    Abstract base class for interacting with an LLM service.
    """

    @abstractmethod
    def chat(self, messages: List[Any], streaming: bool = False) -> dict:
        """
        Sends a list of messages to the LLM API.

        Args:
            messages (List[Any]): List of message objects (e.g., SystemMessage, HumanMessage).
            streaming (bool): Whether to enable streaming response.

        Returns:
            dict: JSON response from the LLM API.
        """
        pass

    @abstractmethod
    def invoke(self, messages: List[Any], streaming: bool = False) -> dict:
        """
        Alias for chat, or alternate entry point if applicable.

        Args:
            messages (List[Any]): List of message objects.
            streaming (bool): Whether to enable streaming.

        Returns:
            dict: JSON response.
        """
        pass
