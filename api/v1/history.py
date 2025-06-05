# app/api/v1/history.py

from fastapi import APIRouter, Request, HTTPException
from models.chat import ChatMessage
from pydantic import BaseModel
from history.store import get_history_store

router = APIRouter()


class HistoryResponse(BaseModel):
    content: list[ChatMessage]


@router.get("/history", response_model=HistoryResponse)
def get_history(request: Request):
    """
    Retrieve the full chat history for the given session ID.
    """
    # 1) Extract session ID from headers; default to "default"
    session_id = request.headers.get("X-Session-ID", "default")

    # 2) Fetch from the centralized history store
    history_store = get_history_store()
    try:
        messages = history_store.get_history(session_id)
    except Exception as e:
        # Any unexpected error retrieving history → 500
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")

    # 3) Return as list of ChatMessage
    return HistoryResponse(content=messages)
