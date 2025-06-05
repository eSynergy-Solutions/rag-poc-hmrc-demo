# app/llm/embeddings.py

from functools import lru_cache
from typing import List
import os

# Attempt to import AzureOpenAI at module scope so tests can monkey-patch it.
try:
    from openai import AzureOpenAI
except ImportError:
    # If the OpenAI SDK is not installed (e.g., in some test environments), define a stub.
    class AzureOpenAI:
        def __init__(self, azure_endpoint: str, api_key: str, api_version: str):
            raise RuntimeError(
                "AzureOpenAI client is not available. "
                "Please install openai>=1.x to use get_embedding."
            )


from core.config import settings


@lru_cache(maxsize=1024)
def get_embedding(text: str) -> List[float]:
    """
    Retrieve an embedding vector for the given text via Azure OpenAI.
    Caches up to 1024 distinct inputs in-process.

    When AZURE_OPENAI_ENDPOINT=="dummy", behave as follows:
      - If len(text) > 1, return [len(text), len(text)-1].
      - If len(text) == 1, return [1, ASCII code of that one character].
      - If empty text, return [0, 0].
    """
    if os.getenv("AZURE_OPENAI_ENDPOINT") == "dummy":
        length = len(text)
        if length > 1:
            return [float(length), float(length - 1)]
        elif length == 1:
            return [1.0, float(ord(text[0]))]
        else:
            return [0.0, 0.0]

    # Otherwise, call the real AzureOpenAI client.
    client = AzureOpenAI(
        azure_endpoint=str(settings.AZURE_OPENAI_ENDPOINT),
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version="2024-05-01-preview",
    )
    try:
        resp = client.embeddings.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            input=text,
        )
        # Assume resp.data is a list of objects with attribute 'embedding'
        return resp.data[0].embedding  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Embedding lookup failed: {e}")
