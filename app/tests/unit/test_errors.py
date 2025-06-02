# app/tests/unit/test_errors.py

import pytest
from app.errors import StorageError, OASValidationError, ChatServiceError, FetchError


def test_storage_error_message_and_attributes():
    """
    StorageError should accept a message and optionally a code.
    """
    err = StorageError("Database unavailable", code=503)
    assert isinstance(err, Exception)
    assert "Database unavailable" in str(err)
    assert err.code == 503

    # Without code, should default to None
    err2 = StorageError("Timeout")
    assert err2.code is None
    assert "Timeout" in str(err2)


def test_oas_validation_error_contains_errors_and_diff():
    """
    OASValidationError takes a list of errors and optional diff_html.
    """
    errors = ["Missing 'openapi' field", "paths must be object"]
    html = "<h2>Diff</h2>"
    err = OASValidationError(errors=errors, diff_html=html)
    assert isinstance(err, Exception)
    # The repr or str should mention errors
    assert "Missing 'openapi' field" in str(err)
    assert err.errors == errors
    assert err.diff_html == html

    # When diff_html is omitted, it should default to None
    err2 = OASValidationError(errors=["Some error"])
    assert err2.diff_html is None
    assert err2.errors == ["Some error"]


def test_chat_service_error_wrapping():
    """
    ChatServiceError should accept an underlying message and preserve it.
    """
    err = ChatServiceError("LLM failed: timeout")
    assert isinstance(err, Exception)
    assert "LLM failed: timeout" in str(err)


def test_fetch_error_reports_status_and_message():
    """
    FetchError should accept status and message.
    """
    err = FetchError("Failed to fetch", status_code=502)
    assert isinstance(err, Exception)
    assert "Failed to fetch" in str(err)
    assert err.status_code == 502

    # Without status_code, default to None
    err2 = FetchError("Network down")
    assert err2.status_code is None
    assert "Network down" in str(err2)
