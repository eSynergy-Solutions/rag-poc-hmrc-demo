# app/api/v1/discover.py

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import StreamingResponse
from models.chat import QueryRequest, QueryResponse, ChatMessage
from services.rag_service import RAGService
from core.deps import get_chat_chain
from history.store import get_history_store  # for stateful history
from errors import ChatServiceError

router = APIRouter()


@router.post("/discover", response_model=QueryResponse)
def discover(
    request: Request,
    payload: str = Body(..., media_type="text/plain"),
    chain=Depends(get_chat_chain),
):
    """
    Endpoint to run “discovery” queries using RAG, with stateful history.
    """

    # 1) Extract session ID from headers (default to "default")
    session_id = request.headers.get("X-Session-ID", "default")

    # 2) Record the incoming user message
    history_store = get_history_store()
    user_msg = ChatMessage(role="user", content=payload)
    history_store.record_message(session_id, user_msg)

    # 3) Get entire history for this session
    history = history_store.get_history(session_id)

    # 4) Handle streaming (not yet implemented)
    # if payload.streaming:
    #     raise HTTPException(
    #         status_code=501, detail="Streaming not implemented for discovery"
    #     )

    # 5) Non‐streaming: call the RAG service
    try:
        service = RAGService(chain)
        answer_text, sources = service.retrieve_and_answer(history, payload)
    except ChatServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    # 6) Wrap response
    assistant_msg = ChatMessage(role="assistant", content=answer_text)

    # 7) Record the assistant’s response
    history_store.record_message(session_id, assistant_msg)

    return QueryResponse(content=assistant_msg)
