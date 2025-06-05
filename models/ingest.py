# app/models/ingest.py

from pydantic import BaseModel
from typing import List, Dict, Any


class Chunk(BaseModel):
    """
    A discrete piece of a larger API specification, ready for embedding and storage.
    """
    path: str
    content: str
    chunk_index: int


class IngestionReport(BaseModel):
    """
    Summary of an ingestion run.
    """
    upserted_count: int
    errors: List[str] = []
