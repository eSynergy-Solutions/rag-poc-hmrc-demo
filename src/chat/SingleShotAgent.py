import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from src.chat.Chat import Chat
from src.schemas.ChatSchemas import ChatMessage
from typing import Generator

load_dotenv()


class SingleShotAgent(Chat):
    """
    This class implements the Chat interface for OAS checking functionality.
    It uses Azure OpenAI to validate OAS specifications.
    """

    implements_streaming = True

    def __init__(self, sysPromptContent="No content"):
        """Initialize the Azure OpenAI client and set up the system prompt"""
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_OAS")
        self.subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

        # Initialize Azure OpenAI Service client with key-based authentication
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.subscription_key,
            api_version="2024-05-01-preview",
        )

        # Use the provided system prompt or the default OASCheckerPrompt
        self.systemprompt = {
            "role": "system",
            "content": [{"type": "text", "text": sysPromptContent}],
        }

    def chat_query(
        self, chat_history: list[ChatMessage], streamed=implements_streaming
    ) -> ChatMessage | Generator[str, None, None]:
        """
        Queries the LLM with chat history for OAS checking.

        Args:
            chat_history (list[ChatMessage]): The conversation history.
            streamed (bool): whether or not to stream the response

        Returns:
            ChatMessage
        """
        # Create messages from chat history
        messages = [self.systemprompt]

        for message in chat_history:
            messages.append({"role": message.role, "content": message.content})

        # Generate the completion
        completion = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=streamed,
        )

        if not streamed:
            response_content = completion.choices[0].message.content
            return ChatMessage(role="assistant", content=response_content)
        else:
            # Implement streaming if needed in the future
            def stream_response():
                for chunk in completion:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

            return stream_response()
