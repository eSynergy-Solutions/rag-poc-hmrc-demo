# app/errors.py

from typing import List, Optional

class StorageError(Exception):
    """
    raised when an underlying vector store (AstraDB or Chroma) operation fails.
    Optionally carries an HTTP-style error code.
    """

    def __init__(self, message: str, code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.code = code

class FetchError(Exception):
    """
    Raised when `APIOfAPIsClient` fails to fetch specs after retries.
    Carries an optional status_code and detail message.
    """

    def __init__(self, detail: str, status_code: Optional[int] = None):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code

class ChatServiceError(Exception):
    """
    Raised when the RAG service or LLM chain fails in unexpected ways.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class OASValidationError(Exception):
    """
    Raised when an OpenAPI Spec fails validation or cannot be parsed.
    Carries the list of error messages encountered and optional HTML diff.
    """

    def __init__(self, errors: List[str], diff_html: Optional[str] = None):
        super_msg = "OpenAPI validation failed"
        if diff_html:
            super_msg += " (with LLM-based diff)"
        super().__init__(super_msg)
        self.errors = errors
        self.diff_html = diff_html

    def __str__(self):
        base = super().__str__()
        if self.errors:
            # Append each error, separated by "; "
            joined = "; ".join(self.errors)
            return f"{base}: {joined}"
        return base

class DependencyError(Exception):
    """
    Raised when a required dependency (e.g., environment variable) is missing.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
