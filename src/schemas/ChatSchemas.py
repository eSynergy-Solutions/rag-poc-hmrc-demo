from pydantic import BaseModel
from typing import Literal


class ChatMessage(BaseModel):
    """
    The standard schema for a chat message to be used throughout the system (compliant with the OpenAI chat completions interface which has become an industry standard)

    Attributes:
        role (Literal['assistant', 'user']): The role of the message sender, either 'assistant' for the ai system or 'user'.
        content (str): The content of the message.
    """

    role: Literal["assistant", "user"]
    content: str
