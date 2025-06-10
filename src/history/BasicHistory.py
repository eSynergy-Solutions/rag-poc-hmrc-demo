from src.schemas.ChatSchemas import ChatMessage


class BaseHistory:
    """
    A class that implements chat history by simply storing a list of chat messages in
    memory and returning them fully. This can be used as is or as a baseclass to define
    other history implementations

    The generic class T is used so ChatMessages can be defined elsewhere
    """

    def __init__(self):
        self._history: list[ChatMessage] = []

    def record_message(self, message: ChatMessage):
        "Add a message to the history"
        if not isinstance(message, ChatMessage):
            raise TypeError("Message must be of type ChatMessage")
        self._history.append(message)

    def get_history(self) -> list[ChatMessage]:
        "Return the full history"
        return self._history

    def get_context_history(self) -> list[ChatMessage]:
        """
        This method can be used to define a different behaviour for getting to history
        to use as context in RAG (such as returning a summary of the chat history).
        In the BaseHistory class this just returns the full history
        """
        return self.get_history()


class OneShotHistory(BaseHistory):
    """
    A History implementation for one-shot endpoints (OAS-checker, discovery).
    Always returns only the most recent user message as context.
    """

    def get_context_history(self) -> list[ChatMessage]:
        """
        Return only the most recent user message as context.
        Scan history in reverse to find the last ChatMessage(role='user').
        """
        for msg in reversed(self._history):
            if msg.role == "user":
                return [msg]
        return []
