from abc import ABC, abstractmethod
from src.schemas.ChatSchemas import ChatMessage
from typing import Generator, Optional

# Chat -> SimpleRAG -> HistoryRAG -> HMRCRag


class Chat(ABC):
    """
    This is the Abstract Base Class for all Chat objects
    Any chat interfaces we define in this project should inherit from this class and implement its methods
    """

    implements_streaming = False

    @abstractmethod
    def chat_query(
        self, chat_history: list[ChatMessage], streaming: Optional[bool]
    ) -> ChatMessage | Generator:
        """
        This is the main method of the chat class.

        Implementing classes must define this method to handle a conversation query
        based on the provided chat history. The method processes the chat history
        and generates a response to the latest user input or query.
        Can return a generator for streaming.

        Parameters:
        -----------
        chat_history : list[ChatMessage]
            A list of ChatMessage objects representing the conversation history,
            including both user messages and system responses. The latest entry
            in the list typically represents the user's most recent input.

        Returns:
        --------
        ChatMessage | Generator
            A ChatMessage object containing the response to the latest user query.
        """
        pass
