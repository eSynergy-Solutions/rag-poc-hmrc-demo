# app/tests/unit/test_ingestion_client.py

import pytest
import httpx
import asyncio
from respx import mock
from httpx import Response, RequestError
from ingestion.client import APIOfAPIsClient
from errors import FetchError

# We will use respx to mock httpx.AsyncClient.get and test retry logic.


@pytest.mark.asyncio
async def test_fetch_specs_two_429_then_success(monkeypatch):
    """
    Simulate two consecutive 429 responses followed by a 200.
    Verify that fetch_specs retries and eventually returns JSON payload.
    """
    test_url = "https://example.com/specs"
    payload = [{"id": 1}, {"id": 2}]

    # 1) Ensure settings.SPEC_API_URL is set to our test URL
    import app.core.config as config_mod

    monkeypatch.setenv("SPEC_API_URL", test_url)
    # Reload the config so that the new URL is used
    import importlib

    importlib.reload(config_mod)

    client = APIOfAPIsClient()

    # 2) Prepare a respx mock server
    async with mock:
        # First two attempts return 429
        mock.get(test_url).respond(
            StatusCode=429,
            content=b"Too Many Requests",
            headers={"Retry-After": "0"},
        )
        mock.get(test_url).respond(
            StatusCode=429,
            content=b"Too Many Requests",
            headers={"Retry-After": "0"},
        )
        # Third attempt returns 200 with JSON
        mock.get(test_url).respond(
            StatusCode=200,
            json=payload,
        )

        # 3) Call fetch_specs() and verify it returns the payload
        result = await client.fetch_specs()
        assert result == payload


@pytest.mark.asyncio
async def test_fetch_specs_permanent_4xx_raises(monkeypatch):
    """
    Simulate a permanent 404. Verify that fetch_specs raises FetchError
    with appropriate detail.
    """
    test_url = "https://example.com/specs"
    import app.core.config as config_mod

    monkeypatch.setenv("SPEC_API_URL", test_url)
    import importlib

    importlib.reload(config_mod)

    client = APIOfAPIsClient()

    async with mock:
        mock.get(test_url).respond(
            StatusCode=404,
            json={"detail": "Not Found"},
        )

        with pytest.raises(FetchError) as exc_info:
            await client.fetch_specs()
        err = exc_info.value
        assert "404" in str(err)


@pytest.mark.asyncio
async def test_fetch_specs_network_error_raises(monkeypatch):
    """
    Simulate a network-level httpx.RequestError. Verify that fetch_specs raises FetchError.
    """
    test_url = "https://example.com/specs"

    import app.core.config as config_mod

    monkeypatch.setenv("SPEC_API_URL", test_url)
    import importlib

    importlib.reload(config_mod)

    client = APIOfAPIsClient()

    # Monkeypatch AsyncClient.get to raise a RequestError
    async def fake_get(url):
        raise RequestError("Network down")

    monkeypatch.setattr(client._client, "get", fake_get)

    with pytest.raises(FetchError) as exc_info:
        await client.fetch_specs()
    err = exc_info.value
    assert "Network down" in str(err)
