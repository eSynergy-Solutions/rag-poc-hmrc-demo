# File: app/clients/ingestion_client.py

import os
import httpx
from typing import Any, Dict, Optional

# Read the base URL of the ingestion service from the environment.
# Example: INGESTION_URL="https://ingestion.example.com"
INGESTION_URL = os.getenv("INGESTION_URL", "").rstrip("/")

class IngestionClientError(Exception):
    """Raised if ingestion service returns non-2xx or a network error occurs."""

def trigger_ingestion(specs: Any, timeout: Optional[float] = 10.0) -> Dict[str, Any]:
    """
    Trigger the ingestion micro-service with a batch of OAS specs.

    Args:
        specs: Any structure that matches the IngestOASSpecsRequest schema:
               { "specs": [ {"id": "...", "spec": { … }}, … ] }
        timeout: Optional timeout (in seconds) for the HTTP request.

    Returns:
        The JSON-decoded response from the ingestion service, e.g.
        { "status": "ingested", "count": N }

    Raises:
        IngestionClientError: if INGESTION_URL is not set, if the request fails,
                              or if the response status code != 200.
    """
    if not INGESTION_URL:
        raise IngestionClientError("INGESTION_URL not configured")

    # The ingestion API is expected to live under /v1/ingest-oas-specs
    url = f"{INGESTION_URL}/v1/ingest-oas-specs"

    try:
        client = httpx.Client(timeout=timeout)
        response = client.post(url, json={"specs": specs})
        client.close()
    except Exception as exc:
        raise IngestionClientError(f"Network error when calling ingestion: {exc}")

    if response.status_code != 200:
        raise IngestionClientError(
            f"Ingestion service returned {response.status_code}: {response.text}"
        )

    return response.json()
