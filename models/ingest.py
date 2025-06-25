# app/models/ingest.py

from pydantic import BaseModel
from typing import List, Dict, Any


class Chunk(BaseModel):
    """
    A discrete piece of a larger API specification, ready for embedding and storage.

    Attributes:
        path (str): The file path or identifier for the chunk.
        content (str): The text content of the chunk.
        chunk_index (int): The index of the chunk within its parent document or file.
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
