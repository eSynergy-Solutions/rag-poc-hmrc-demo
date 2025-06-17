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

    role: Literal["assistant", "user"]
    content: str
