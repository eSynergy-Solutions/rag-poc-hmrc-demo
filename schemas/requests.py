# app/schemas/requests.py

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """
    Schema for incoming chat requests.

    This schema defines the structure of a request containing user input
    and an optional flag for streaming responses.

    Attributes:
        content (str): The user's input message.
        streaming (bool): Whether the response should be streamed. Defaults to False.

    """

    content: str
    streaming: bool = False
