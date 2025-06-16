# app/core/deps.py

from typing import Generator
from fastapi import Depends, HTTPException

from core.logging import logger
from llm.embeddings import get_embedding
from langchain_community.chat_models import AzureChatOpenAI
from llm.chat_chain import build_chat_chain
from vectorstore.interface import VectorStore
from vectorstore.astradb import AstraStore
import os
from core.config import settings


def get_settings() -> Generator:
    """
    Dynamically import and yield the latest Settings instance.
    This ensures that after a reload(core.config), we pick up
    None (or the updated Settings) as intended.
    """

    yield settings


def get_logger() -> Generator:
    yield logger


def get_vector_store(
    config=Depends(get_settings),
) -> Generator[VectorStore, None, None]:
    # If settings failed to load, `config` is None
    if config is None:
        raise HTTPException(status_code=500, detail="Vector store unavailable")

    # explicit sanity check for required fields
    if not config.ASTRA_DB_APPLICATION_TOKEN or not config.ASTRA_DB_API_ENDPOINT:
        raise HTTPException(status_code=500, detail="Vector store unavailable")

    try:
        store = AstraStore(
            token=config.ASTRA_DB_APPLICATION_TOKEN,
            api_endpoint=str(config.ASTRA_DB_API_ENDPOINT),
            keyspace=config.ASTRA_DB_KEYSPACE,
            collection_name=config.DS_COLLECTION_NAME,
        )
        yield store
    except Exception as e:
        logger.error("Failed to initialize AstraStore", error=str(e))
        raise HTTPException(status_code=500, detail="Vector store unavailable")


def get_embedding_fn(
    config=Depends(get_settings),
) -> Generator:
    # Yield the single canonical function object from llm.embeddings
    import llm.embeddings as _emb_mod

    yield _emb_mod.get_embedding


def get_chat_chain(
    config=Depends(get_settings),
    store: VectorStore = Depends(get_vector_store),
) -> Generator:
    # If settings failed to load, `config` is None
    if config is None:
        raise HTTPException(status_code=500, detail="Chat chain unavailable")

    # explicit sanity check for required config
    if (
        not config.AZURE_OPENAI_ENDPOINT
        or not config.AZURE_OPENAI_API_KEY
        or not config.AZURE_OPENAI_DEPLOYMENT
    ):
        raise HTTPException(status_code=500, detail="Chat chain unavailable")

    try:
        chain = build_chat_chain(
            endpoint=str(config.AZURE_OPENAI_ENDPOINT),
            api_key=config.AZURE_OPENAI_API_KEY,
            deployment=config.AZURE_OPENAI_DEPLOYMENT,
            retriever=store.as_retriever(config.VECTOR_K),
        )
        yield chain
    except Exception as e:
        logger.error("Failed to build chat chain", error=str(e))
        raise HTTPException(status_code=500, detail="Chat chain unavailable")


def get_chat_service(
    config=settings,
) -> AzureChatOpenAI:
    """
    Provides a chat service that does not require a vector store.
    This is useful for scenarios where chat capabilities are needed
    without retrieval from a vector store.
    """
    if config is None:
        raise HTTPException(status_code=500, detail="Chat chain unavailable")

    api_version = os.getenv("OPENAI_API_VERSION", None)
    if api_version is None:
        raise ValueError(
            "OPENAI_API_VERSION environment variable must be set for AzureChatOpenAI"
        )

    # explicit sanity check for required config
    if (
        not config.AZURE_OPENAI_ENDPOINT
        or not config.AZURE_OPENAI_API_KEY
        or not config.AZURE_OPENAI_DEPLOYMENT
    ):
        raise HTTPException(status_code=500, detail="Chat chain unavailable")

    try:
        llm = AzureChatOpenAI(
            azure_deployment=config.AZURE_OPENAI_DEPLOYMENT,
            azure_endpoint=str(config.AZURE_OPENAI_ENDPOINT),
            openai_api_key=config.AZURE_OPENAI_API_KEY,
            api_version=api_version,
            temperature=0.2,
            verbose=False,
        )

        return llm
    except Exception as e:
        logger.error("Failed to initialise Azure client", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to initialise Azure client")
