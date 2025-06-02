# app/ingestion/chunker.py

import json
import yaml
from typing import List, Any
from app.models.ingest import Chunk

# Maximum characters per chunk (approximate guidance for embedding token limits)
MAX_CHUNK_SIZE = 3000


def chunk_spec(path: str, spec: Any) -> List[Chunk]:
    """
    Split a raw API specification (dict or YAML/JSON string) into
    deterministic, idempotent chunks for ingestion.

    Args:
        path: identifier for the spec (e.g. filename or API path)
        spec: the OpenAPI spec, as a dict or raw string

    Returns:
        List[Chunk]: list of Chunk models ready for embedding & upsert
    """
    # Determine the base text:
    if not isinstance(spec, str):
        # For non‐string specs, dump to JSON then re‐dump to YAML for readability
        text = json.dumps(spec, ensure_ascii=False)
        try:
            obj = yaml.safe_load(text)
            dumped = yaml.safe_dump(obj, sort_keys=False)
            # strip YAML document‐end marker if present
            if dumped.endswith("...\n"):
                dumped = dumped[:-4]
            text = dumped
        except Exception:
            # fallback to JSON string
            pass

    else:
        # spec is a string
        if spec == "":
            # special case: empty string → valid YAML null
            text = "null\n"
        else:
            # non‐empty string → leave exactly as given
            text = spec

    # Now split into fixed‐size chunks
    chunks: List[Chunk] = []
    for idx in range(0, len(text), MAX_CHUNK_SIZE):
        chunk_content = text[idx : idx + MAX_CHUNK_SIZE]
        chunks.append(
            Chunk(
                path=path,
                content=chunk_content,
                chunk_index=idx // MAX_CHUNK_SIZE,
            )
        )

    return chunks
