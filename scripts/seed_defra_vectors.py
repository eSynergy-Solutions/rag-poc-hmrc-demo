# scripts/seed_defra_vectors.py

"""
One-off script to seed the AstraDB vector store with DEFRA API specs
from a local directory of YAML/JSON files.

Usage:
    python scripts/seed_defra_vectors.py --spec-dir /path/to/specs
"""

import asyncio
import argparse
import os
from pathlib import Path
import yaml

from app.core.config import settings
from app.vectorstore.astradb import AstraStore
from app.ingestion.chunker import chunk_spec
from app.core.logging import logger

async def seed(spec_dir: Path):
    # Initialize Astra store
    store = AstraStore(
        token=settings.ASTRA_DB_APPLICATION_TOKEN,
        api_endpoint=str(settings.ASTRA_DB_API_ENDPOINT),
        keyspace=settings.ASTRA_DB_KEYSPACE,
        collection_name=settings.DS_COLLECTION_NAME,
    )

    total = 0
    for file_path in spec_dir.iterdir():
        if file_path.suffix.lower() not in {".yml", ".yaml", ".json"}:
            continue

        logger.info("Processing spec file", path=str(file_path))
        # Load spec content
        text = file_path.read_text(encoding="utf-8")
        try:
            spec_obj = yaml.safe_load(text)
        except Exception:
            spec_obj = text  # fallback to raw

        # Chunk & upsert
        chunks = chunk_spec(path=file_path.stem, spec=spec_obj)
        count = store.upsert(chunks)
        total += count
        logger.info("Upserted chunks for file", file=file_path.name, count=count)

    logger.info("Seeding complete", total_chunks=total)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed DEFRA specs into AstraDB")
    parser.add_argument(
        "--spec-dir",
        type=Path,
        required=True,
        help="Directory containing spec YAML/JSON files",
    )
    args = parser.parse_args()

    if not args.spec_dir.is_dir():
        logger.error("Spec directory not found", path=str(args.spec_dir))
        exit(1)

    asyncio.run(seed(args.spec_dir))
