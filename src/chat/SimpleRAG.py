"A simple minimal implementation of RAG that uses the AstraDB and AzureOpenAI APIs"

import litellm
from astrapy import DataAPIClient
from dotenv import load_dotenv
from src.chat.Chat import Chat
import os
from typing import Generator
from src.prompts import standard_rag_system_prompt
from src.schemas.ChatSchemas import ChatMessage

load_dotenv()


class RagChat(Chat):
    """
    This class offers a simple implementation of the Chat interface using a basic RAG workflow with Azure OpenAI as the LLM and AstraDB as the vector database.

    It is designed to be highly modular so that one can easily create a derived class and just change one part of it such as the retrieval strategy.
    """

    def __init__(self):
        "Initialises the various clients"
        client = DataAPIClient(os.getenv("ASTRA_DB_APPLICATION_TOKEN"))
        database = client.get_database(
            os.getenv("ASTRA_DB_API_ENDPOINT"), keyspace=os.getenv("ASTRA_DB_KEYSPACE")
        )
        self.vectordb = database.get_collection(
            os.getenv("DS_COLLECTION_NAME", "funding_for_farmers")
        )
        self.llm = litellm

    implements_streaming = True

    systemprompt = {
        "role": "system",
        "content": standard_rag_system_prompt,
    }

    def embed(self, input: str) -> list[float]:
        "A function that calls the embed client to get the vector embedding of a given string"
        embedding = self.llm.embedding(
            "azure/text-embedding-ada-002",
            input=input,
        ).data[0]["embedding"]
        return embedding

    def retrieve(self, input: str, chunk_limit=5) -> list[str]:
        embedding = self.embed(input)
        chunks = self.vectordb.find(
            {},
            sort={"$vector": embedding},
            limit=chunk_limit,
        )
        return [c["content"] for c in chunks]

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
        chunks = self.retrieve(
            str(
                chat_history
            )  # this is a kind of dodgy way of using the history for retrieval???
        )

        context = {"role": "user", "content": "context: " + str(chunks)}
        prompt = (
            [type(self).systemprompt]
            + [m.model_dump() for m in chat_history]
            + [context]
        )

        return prompt

    def chat_query(
        self, chat_history: list[ChatMessage], streamed=False
    ) -> ChatMessage | Generator[str, None, None]:
        """
        Queries the LLM with chat history augmented by retrieval.

        Args:
            chat_history (list[ChatMessage]): The conversation history.
            streamed (bool): whether or not to stream the response

        Returns:
            ChatMessage
        """

        prompt = self.get_context(chat_history)

        response = self.llm.completion(
            "azure/rag_pocs",
            messages=prompt,
            temperature=0.2,
            max_tokens=500,
            stream=streamed,
        )

        if not streamed:
            m: str = response.choices[0].message
            cm: ChatMessage = ChatMessage(role=m.role, content=m.content)
            return cm
        else:

            def stream_response():
                for chunk in response:
                    if chunk and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

            return stream_response()
