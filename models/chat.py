# app/models/chat.py

from typing import Literal
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """
    A single message in the chat, with a role and content.

    Attributes:
        role (Literal["assistant", "user"]): The role of the message sender, either "assistant" or "user".
        content (str): The content of the message.
    """

    role: Literal["assistant", "user", "system"]
    content: str


class ChatHistory(BaseModel):
    """
    A collection of chat messages, representing the history of a conversation.

    Attributes:
        messages (list[ChatMessage]): A list of messages in the chat history.
    """

    messages: list[ChatMessage]


class ChatEndpointRequest(BaseModel):
    """
    Request schema for the chat endpoint.

    Attributes:
        messages (list[ChatMessage]): A list of messages to be sent to the chat model.
        streaming (bool): Whether the response should be streamed. Defaults to False.
    """

    messages: list[ChatMessage]
    streaming: bool = False
