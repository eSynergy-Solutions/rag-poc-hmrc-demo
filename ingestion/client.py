# app/ingestion/client.py

from typing import List, Dict, Any
import asyncio
import httpx
from fastapi import HTTPException
from app.core.config import settings
from app.errors import FetchError

class APIOfAPIsClient:
    """
    Asynchronous client to fetch raw specifications from the 'API-of-APIs'.
    Implements retry/back-off on 429 and 5xx responses.
    """

    def __init__(self) -> None:
        url = settings.SPEC_API_URL
        if not url:
            raise RuntimeError("SPEC_API_URL is not configured in settings")
        self._base_url: str = str(url)
        # Use a retryable HTTPX client without blocking
        self._client = httpx.AsyncClient(timeout=10.0)

    async def fetch_specs(self) -> List[Dict[str, Any]]:
        """
        Fetch the list of API specification documents, retrying on 429 or 5xx.
        Raises:
            FetchError on permanent failure after retries.
        """
        max_retries = 3
        backoff_seconds = 1

        for attempt in range(1, max_retries + 1):
            try:
                response = await self._client.get(self._base_url)
                status = response.status_code

                # Retry on 429 Too Many Requests or any 5xx server error
                if status == 429 or 500 <= status < 600:
                    if attempt == max_retries:
                        raise FetchError(status, f"Max retries exceeded with status {status}")
                    await asyncio.sleep(backoff_seconds * attempt)
                    continue

                # For 4xx (excluding 429), immediately raise HTTPException
                if 400 <= status < 500:
                    raise HTTPException(
                        status_code=status,
                        detail=f"Error fetching specs: {response.text}"
                    )

                # 2xx success
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                code = e.response.status_code
                detail = e.response.text
                if attempt == max_retries:
                    raise FetchError(code, detail)
                await asyncio.sleep(backoff_seconds * attempt)
                continue
            except httpx.HTTPError as e:
                # Network-level failure or invalid response
                if attempt == max_retries:
                    raise FetchError(502, f"Network error: {e}")
                await asyncio.sleep(backoff_seconds * attempt)
                continue

        # If somehow the loop exits, raise a generic FetchError
        raise FetchError(500, "Failed to fetch specs after retries")

    async def close(self) -> None:
        """Close underlying HTTPX client."""
        await self._client.aclose()
