# app/workers/ingest_worker.py

import asyncio
from celery import Celery
from app.ingestion.client import APIOfAPIsClient
from app.ingestion.service import IngestionService
from app.vectorstore.astradb import AstraStore
from app.core.config import settings
from app.core.logging import logger

# -------------------------------------------------------------------------------
# Celery configuration
# -------------------------------------------------------------------------------
# Expect the following environment variables:
#   - CELERY_BROKER_URL (e.g. redis://localhost:6379/0)
#   - CELERY_RESULT_BACKEND (optional)
#
# In production, set these via your deployment or KeyVault.
#

celery_app = Celery(
    "ingest_worker",
    broker=getattr(settings, "CELERY_BROKER_URL", None) or "redis://localhost:6379/0",
    backend=getattr(settings, "CELERY_RESULT_BACKEND", None),
)

# -------------------------------------------------------------------------------
# Celery task
# -------------------------------------------------------------------------------
@celery_app.task(name="run_ingestion_job_task")
def run_ingestion_job_task():
    """
    Celery task wrapper to run the ingestion job asynchronously.
    This will call the async function `run_ingestion_job()` via asyncio.
    """
    asyncio.run(run_ingestion_job())

async def run_ingestion_job():
    """
    Fetch, chunk, embed, and upsert all API specs into the vector store.
    Intended to be called by the Celery task or as a standalone script.
    """
    client = APIOfAPIsClient()
    store = AstraStore(
        token=settings.ASTRA_DB_APPLICATION_TOKEN,
        api_endpoint=str(settings.ASTRA_DB_API_ENDPOINT),
        keyspace=settings.ASTRA_DB_KEYSPACE,
        collection_name=settings.DS_COLLECTION_NAME,
    )

    service = IngestionService(client, store)
    report = await service.run()

    logger.info(
        "Ingestion job completed",
        upserted_count=report.upserted_count,
        errors=report.errors
    )

# Expose a `.delay()` attribute on run_ingestion_job so that tests expecting
# a Celery‐style task can do `run_ingestion_job.delay()`.
run_ingestion_job.delay = run_ingestion_job_task.delay  # type: ignore[attr-defined]

if __name__ == "__main__":
    """
    When run as a script, execute ingestion immediately.
    """
    asyncio.run(run_ingestion_job())
