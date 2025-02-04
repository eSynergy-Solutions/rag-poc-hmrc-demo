from src.chat.Chat import Chat
from src.schemas.ChatSchemas import ChatMessage


class TestChat(Chat):
    """
    This class implements the Chat interface in a trivial way for testing purposes
    """

    def chat_query(self, chat_history: list[ChatMessage]) -> ChatMessage:
        "Simply echoes back the last message in this history"
        if not chat_history:
            raise ValueError("TestChat expects non empty chat history")
        last_message = chat_history[-1]
        new_message = ChatMessage(
            role="assistant", content=f"Echo: {last_message.content}"
        )
        return new_message
