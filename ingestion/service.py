# app/ingestion/service.py

import asyncio
from typing import List
from ingestion.client import APIOfAPIsClient
from ingestion.chunker import chunk_spec
from vectorstore.interface import VectorStore
from models.ingest import IngestionReport
from core.logging import logger
from errors import FetchError, StorageError


class IngestionService:
    """
    Orchestrates fetching raw specs, splitting into chunks,
    embedding & upserting into the vector store, and reporting.
    """

    def __init__(self, client: APIOfAPIsClient, store: VectorStore):
        self.client = client
        self.store = store

    async def run(self) -> IngestionReport:
        upserted_total = 0
        errors: List[str] = []

        # 1) Fetch raw specs, handling FetchError explicitly
        try:
            specs = await self.client.fetch_specs()
        except FetchError as fe:
            msg = f"Failed to fetch specs: {fe}"
            logger.error(msg)
            # Return report with zero upsert and the fetch error
            return IngestionReport(upserted_count=0, errors=[msg])
        except Exception as e:
            msg = f"Unexpected error fetching specs: {e}"
            logger.error(msg)
            return IngestionReport(upserted_count=0, errors=[msg])

        # 2) Process specs concurrently
        async def process_one(spec: dict):
            nonlocal upserted_total
            # Determine a path/id for this spec; adjust as needed
            path = spec.get("path") or spec.get("id") or spec.get("name", "unknown")
            try:
                # 2a) Chunk the spec
                chunks = chunk_spec(path, spec)
                # 2b) Attempt to upsert; catch any StorageError
                try:
                    count = self.store.upsert(chunks)
                    upserted_total += count
                    logger.info("Upserted chunks", path=path, count=count)
                except StorageError as se:
                    # Log the storage failure and append to errors
                    err_msg = f"{path}: StorageError: {se}"
                    errors.append(err_msg)
                    logger.error("Error upserting chunks", path=path, error=str(se))
                except Exception as e_inner:
                    # Catch unexpected exceptions from upsert
                    err_msg = f"{path}: Unexpected storage failure: {e_inner}"
                    errors.append(err_msg)
                    logger.error(
                        "Error upserting chunks", path=path, error=str(e_inner)
                    )
            except Exception as e_chunk:
                # If chunking itself fails, record an error
                err_msg = f"{path}: Chunking error: {e_chunk}"
                errors.append(err_msg)
                logger.error("Error chunking spec", path=path, error=str(e_chunk))

        tasks = [process_one(spec) for spec in specs]
        # Await all processing (concurrent)
        await asyncio.gather(*tasks, return_exceptions=True)

        # 3) Close the client (clean up)
        await self.client.close()

        # 4) Return final report
        return IngestionReport(upserted_count=upserted_total, errors=errors)
