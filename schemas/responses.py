# app/schemas/responses.py

from pydantic import BaseModel
from models.chat import ChatMessage


class QueryResponse(BaseModel):
    """
    Schema for outgoing chat responses.
    This schema defines the structure of a response containing a list of messages.

    Attributes:
        messages (list[ChatMessage]): List of messages in the response.

    """

    messages: list[ChatMessage]
