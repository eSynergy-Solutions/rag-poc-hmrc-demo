"A version of Simple RAG that intelligently creates the retrieval query for better retrieval in long chats"

from src.chat.SimpleRAG import RagChat
from src.prompts import HistoryRetrievalPrompt
from src.schemas.ChatSchemas import ChatMessage
from icecream import ic

# Chat -> SimpleRAG -> HistoryRAG -> HMRCRag


class HistoryRAG(RagChat):
    def get_context(self, chat_history: list[ChatMessage]) -> list[dict]:
        """
        Augments the chat history with the context and returns it in openai chat format to be passed to an llm:
        (mostly just does retreival and cleans up the chunks into a message format)

        Args:
            chat_history (list[ChatMessage]): The conversation history.
            streaming (bool): If True, streams the response asynchronously.

        Returns:
            list[dict]
        """
        if len(chat_history) > 2:
            prompt = [
                {"role": "user", "content": HistoryRetrievalPrompt + str(chat_history)}
            ]

            response = self.llm.completion(
                "azure/rag_pocs", messages=prompt, temperature=0, max_tokens=200
            )

            retrieval_query = response.choices[0].message.content

        else:
            retrieval_query = str(chat_history[0].content)

        ic(retrieval_query)
        chunks = self.retrieve(retrieval_query)

        context = {"role": "user", "content": "context: " + str(chunks)}
        prompt = (
            [type(self).systemprompt]
            + [m.model_dump() for m in chat_history]
            + [context]
        )

        return prompt
