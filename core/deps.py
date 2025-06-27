# app/core/deps.py

from fastapi import HTTPException
from core.custom_logging import logger

# from langchain_community.chat_models import AzureChatOpenAI
from langchain_postgres.vectorstores import PGVector, DistanceStrategy
from llm.single_call import build_chat_instance
from llm.embeddings import get_embedding, get_embedding_client
from core.config import settings


def get_settings():
    """
    Dynamically import and return the latest Settings instance.
    This ensures that after a reload(core.config), we pick up
    None (or the updated Settings) as intended.
    """

    return settings


def get_logger():
    return logger


def get_vector_store(
    config=get_settings(),
):
    # If settings failed to load, `config` is None
    if config is None:
        raise HTTPException(
            status_code=500,
            detail="Vector store unavailable; configurations failed to load",
        )

    # explicit sanity check for required fields
    if (
        not config.PGVECTOR_USER
        or not config.PGVECTOR_PASSWORD
        or not config.PGVECTOR_HOST
    ):
        raise HTTPException(
            status_code=500,
            detail="Vector store unavailable; Username, password or host string is unavailable",
        )

    try:
        connection_string = PGVector.connection_string_from_db_params(
            driver=config.PGVECTOR_DRIVER,
            host=config.PGVECTOR_HOST,
            port=config.PGVECTOR_PORT,
            database=config.PGVECTOR_DATABASE,
            user=config.PGVECTOR_USER,
            password=config.PGVECTOR_PASSWORD,
        )

        embeddings = get_embedding_client()

        store = PGVector(
            collection_name=config.PGVECTOR_COLLECTION,
            connection=connection_string,
            embeddings=embeddings,
            use_jsonb=True,
            distance_strategy=DistanceStrategy.COSINE,
        )

        logger.info("Vector store successfully loaded.")
        return store
    except Exception as e:
        logger.error("Failed to initialize Postgres VectorDB:\n", error=str(e))
        raise HTTPException(status_code=500, detail="Vector store unavailable")


def get_embedding_fn(
    config=get_settings(),
):
    # return the single canonical function object from llm.embeddings

    return get_embedding


def get_chat_service(
    config=get_settings(),
):
    """
    Provides a chat service that does not require a vector store.
    This is useful for scenarios where chat capabilities are needed
    without retrieval from a vector store.
    """
    if config is None:
        raise HTTPException(
            status_code=500,
            detail="Chat chain unavailable; config file did not oad env vars successfully",
        )

    # api_version = os.getenv("OPENAI_API_VERSION", None)
    # if api_version is None:
    #     raise ValueError(
    #         "OPENAI_API_VERSION environment variable must be set for AzureChatOpenAI"
    #     )

    # explicit sanity check for required config
    if (
        not config.GAILZ_BASE_URL
        or not config.GAILZ_DEPLOYMENT_NAME
        or not config.GAILZ_MISC_STRING
        or not config.GAILZ_DEPLOYMENT_VERSION
    ):
        raise HTTPException(
            status_code=500, detail="Chat chain unavailable; Gailz env vars not loaded"
        )

    try:
        llm = build_chat_instance(
            base_url=config.GAILZ_BASE_URL,
            deployment=config.GAILZ_DEPLOYMENT_NAME,
            misc_string=config.GAILZ_MISC_STRING,
            deployment_version=config.GAILZ_DEPLOYMENT_VERSION,
            deployment_model=config.GAILZ_DEPLOYMENT_MODEL,
            logger=get_logger(),
        )
        # llm = build_chat_instance(
        #     deployment=config.AZURE_OPENAI_DEPLOYMENT,
        #     endpoint=str(config.AZURE_OPENAI_ENDPOINT),
        #     api_key=config.AZURE_OPENAI_API_KEY,
        # )

        return llm
    except Exception as e:
        # logger.error("Failed to initialise Azure client", error=str(e))
        # raise HTTPException(status_code=500, detail="Failed to initialise Azure client")
        logger.error("Failed to initialise Gailz client", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to initialise Gailz client")
