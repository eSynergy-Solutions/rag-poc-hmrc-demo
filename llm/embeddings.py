# app/llm/embeddings.py

from functools import lru_cache
from typing import List
import os
from langchain_openai import AzureOpenAIEmbeddings
from llm.gailz_embedding import GailzEmbedding
from core.config import settings
from core.deps import get_logger


def get_embedding_client() -> GailzEmbedding:
    """
    Retrieve an embedding model via Gailz (using your GAILZ_EMBEDDING var).
    """

    # 1. Gather embedding‐specific settings
    embedding_url = str(getattr(settings, "GAILZ_EMBEDDING_STRING", "") or "")

    if not embedding_url:
        raise RuntimeError(
            "Embedding configuration is incomplete. "
            "Ensure GAILZ_EMBEDDING_STRING is not set."
        )

    # 2. Instantiate the Gailz client with the embedding‐specific settings
    try:
        client = GailzEmbedding(base_url=embedding_url, logger=get_logger())
        return client
    except Exception as e:
        raise RuntimeError(f"Client failed to initialise: {e}")


# def get_embedding_client() -> AzureOpenAIEmbeddings:
#     """
#     Retrieve an embedding model via Azure OpenAI (using your AZURE_OPENAI_EMB_… vars).
#     """

#     # 1. Gather embedding‐specific settings
#     emb_endpoint = str(getattr(settings, "AZURE_OPENAI_EMB_ENDPOINT", "") or "")
#     emb_api_key = str(getattr(settings, "AZURE_OPENAI_EMB_API_KEY", "") or "")
#     emb_api_version = str(getattr(settings, "AZURE_OPENAI_EMB_API_VERSION", "") or "")
#     emb_deployment = str(getattr(settings, "AZURE_OPENAI_EMB_DEPLOYMENT", "") or "")

#     if not emb_endpoint or not emb_api_key or not emb_api_version or not emb_deployment:
#         raise RuntimeError(
#             "Embedding configuration is incomplete. "
#             "Ensure AZURE_OPENAI_EMB_ENDPOINT, AZURE_OPENAI_EMB_API_KEY, AZURE_OPENAI_EMB_API_VERSION, and AZURE_OPENAI_EMB_DEPLOYMENT are set."
#         )

#     # 2. Instantiate the AzureOpenAI client with the embedding‐specific endpoint & version
#     try:
#         client = AzureOpenAIEmbeddings(
#             model=emb_deployment,
#             azure_endpoint=emb_endpoint,
#             api_key=emb_api_key,
#             openai_api_version=emb_api_version,
#         )
#         return client
#     except Exception as e:
#         raise RuntimeError(f"Client failed to initialise: {e}")


# @lru_cache(maxsize=1024)
# def get_embedding(text: str) -> List[float]:
#     """
#     Retrieve an embedding vector for the given text via Azure OpenAI (using your AZURE_OPENAI_EMB_… vars).
#     Caches up to 1024 distinct inputs in-process.

#     When AZURE_OPENAI_EMB_ENDPOINT=="dummy", behave as follows:
#       - If len(text) > 1, return [len(text), len(text)-1].
#       - If len(text) == 1, return [1, ASCII code of that one character].
#       - If empty text, return [0, 0].
#     """
#     # ---------- dummy‐mode for testing (if you set AZURE_OPENAI_EMB_ENDPOINT=dummy) ----------
#     if os.getenv("AZURE_OPENAI_EMB_ENDPOINT") == "dummy":
#         length = len(text)
#         if length > 1:
#             return [float(length), float(length - 1)]
#         elif length == 1:
#             return [1.0, float(ord(text[0]))]
#         else:
#             return [0.0, 0.0]

#     # ------------------------------ real Azure path -------------------------------
#     # 1. Gather embedding‐specific settings
#     emb_endpoint = str(getattr(settings, "AZURE_OPENAI_EMB_ENDPOINT", "") or "")
#     emb_api_key = str(getattr(settings, "AZURE_OPENAI_EMB_API_KEY", "") or "")
#     emb_api_version = str(getattr(settings, "AZURE_OPENAI_EMB_API_VERSION", "") or "")
#     emb_deployment = str(getattr(settings, "AZURE_OPENAI_EMB_DEPLOYMENT", "") or "")

#     if not emb_endpoint or not emb_api_key or not emb_api_version or not emb_deployment:
#         raise RuntimeError(
#             "Embedding configuration is incomplete. "
#             "Ensure AZURE_OPENAI_EMB_ENDPOINT, AZURE_OPENAI_EMB_API_KEY, AZURE_OPENAI_EMB_API_VERSION, and AZURE_OPENAI_EMB_DEPLOYMENT are set."
#         )

#     # 2. Instantiate the AzureOpenAI client with the embedding‐specific endpoint & version
#     client = AzureOpenAI(
#         azure_endpoint=emb_endpoint,
#         api_key=emb_api_key,
#         api_version=emb_api_version,
#     )
#     try:
#         # 3. Request embeddings using the embedding-specific deployment
#         resp = client.embeddings.create(
#             model=emb_deployment,
#             input=text,
#         )
#         # Assume resp.data is a list of objects with attribute 'embedding'
#         return resp.data[0].embedding  # type: ignore
#     except Exception as e:
#         raise RuntimeError(f"Embedding lookup failed: {e}")
