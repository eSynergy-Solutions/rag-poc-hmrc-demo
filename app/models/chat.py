# app/models/chat.py

from typing import Literal
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """
    A single message in the chat, with a role and content.
    """
    role: Literal["assistant", "user"]
    content: str


class QueryRequest(BaseModel):
    """
    Schema for incoming chat requests.
    """
    content: str
    streaming: bool = False


class QueryResponse(BaseModel):
    """
    Schema for outgoing chat responses.
    """
    content: ChatMessage
