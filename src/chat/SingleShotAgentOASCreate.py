import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from src.chat.Chat import Chat
from src.schemas.ChatSchemas import ChatMessage
from typing import Generator, List, Union
import logging
import yaml
import json
from openapi_spec_validator import validate

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    import sys

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)


class SingleShotAgentCreate(Chat):
    """
    This class implements the Chat interface for OAS checking functionality.
    It uses Azure OpenAI to validate OAS specifications.
    """

    implements_streaming = False

    def __init__(self, sysPromptContent="No content"):
        """Initialize the Azure OpenAI client and set up the system prompt"""
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_OAS")
        self.subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

        if not self.endpoint or not self.deployment or not self.subscription_key:
            logger.error("Missing Azure OpenAI environment variables.")
            raise ValueError("Missing Azure OpenAI environment variables.")

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

    def yaml_to_json(self, yaml_string):
        """
        Convert a YAML string to JSON string

        Parameters:
        yaml_string (str): The YAML content as a string

        Returns:
        str: The converted JSON string
        """
        try:
            # Parse YAML string to Python dictionary
            yaml_dict: dict = yaml.safe_load(yaml_string)
            return yaml_dict
        except Exception as e:
            return f"Error converting YAML to JSON: {str(e)}"

    def validate_oas_spec(self, oas_spec: dict) -> bool:
        """
        Validate an OpenAPI Specification (OAS) string.

        Args:
            oas_spec (dict): The OAS content as a dict.

        Returns:
            bool: True if the OAS is valid, False otherwise.
        """
        try:
            # Parse the OAS spec
            # Validate the OAS spec
            validate(oas_spec)
            return True
        except Exception as e:
            logger.error(f"OpenAPI Specification validation error: {e}")
            return False

    def chat_query(
        self, chat_history: List[ChatMessage], streamed: bool = False
    ) -> Union[ChatMessage, Generator[str, None, None]]:
        """
        Queries the LLM with chat history for OAS checking.

        Args:
            chat_history (list[ChatMessage]): The conversation history.
            streamed (bool): whether or not to stream the response

        Returns:
            ChatMessage or generator for streaming
        """
        messages = [self.systemprompt]
        for message in chat_history:
            messages.append({"role": message.role, "content": message.content})

        try:
            completion = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=800,
                temperature=0.7,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
            )
        except Exception as e:
            logger.exception("Error during OpenAI completion call")
            raise RuntimeError(f"OpenAI completion error: {e}")

        if not streamed:
            try:
                response_content = completion.choices[0].message.content
                return ChatMessage(role="assistant", content=response_content)
            except Exception as e:
                logger.exception("Error parsing OpenAI response")
                raise RuntimeError(f"Error parsing OpenAI response: {e}")
        else:

            def stream_response():
                try:
                    for chunk in completion:
                        if chunk.choices and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                except Exception as e:
                    logger.exception("Error during streaming OpenAI response")
                    raise RuntimeError(f"Error during streaming OpenAI response: {e}")

            return stream_response()
