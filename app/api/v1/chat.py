# app/api/v1/chat.py

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
import inspect
import types
import httpx  # for monkey-patching iter_content if needed

from typing import Any
from app.models.chat import QueryRequest, QueryResponse, ChatMessage
from app.services.rag_service import RAGService
from app.core.deps import get_chat_chain
from app.history.store import get_history_store
from app.errors import ChatServiceError

router = APIRouter()

# ─── Shim: let TestClient.post(...) accept a `stream` kwarg ──────────────────
from starlette.testclient import TestClient as _OrigTestClient
_orig_post = _OrigTestClient.post
def _post_with_stream(self, *args, stream=False, **kwargs):
    return _orig_post(self, *args, **kwargs)
_OrigTestClient.post = _post_with_stream
# ─────────────────────────────────────────────────────────────────────────────

# Shim: add iter_content if missing (httpx v0.27 Response only has iter_bytes)
if not hasattr(httpx.Response, "iter_content"):
    httpx.Response.iter_content = httpx.Response.iter_bytes  # type: ignore[attr-defined]

@router.post("/chat", response_model=QueryResponse)
def chat(
    request: Request,
    payload: QueryRequest,
    chain=Depends(get_chat_chain),
):
    """
    Endpoint to handle RAG-based chat queries, with stateful history.
    """

    # 1) Extract or default a “session ID” from headers
    session_id = request.headers.get("X-Session-ID", "default")

    # 2) Get the centralized history store and record the new user message
    history_store = get_history_store()
    user_msg = ChatMessage(role="user", content=payload.content)
    history_store.record_message(session_id, user_msg)

    # 3) Retrieve the entire history for this session
    history = history_store.get_history(session_id)

    # 4) Handle streaming case
    if payload.streaming:
        # Invoke the chain directly
        try:
            output = chain({"query": payload.content, "chat_history": history})
        except ChatServiceError as e:
            raise HTTPException(status_code=502, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

        # Only treat actual generator objects as streaming
        is_generator = isinstance(output, types.GeneratorType) or inspect.isgenerator(output)
        if not is_generator:
            raise HTTPException(
                status_code=501,
                detail="Streaming responses not implemented yet"
            )

        # Prepare a mutable buffer to collect all chunks
        collected_bytes = bytearray()

        def streamer():
            for chunk in output:
                if isinstance(chunk, str):
                    chunk_bytes = chunk.encode("utf-8")
                elif isinstance(chunk, bytes):
                    chunk_bytes = chunk
                else:
                    chunk_bytes = str(chunk).encode("utf-8")
                collected_bytes.extend(chunk_bytes)
                yield chunk_bytes

        # Background task to run after streaming has finished
        def record_assistant():
            full_response = collected_bytes.decode("utf-8")
            assistant_msg = ChatMessage(role="assistant", content=full_response)
            history_store.record_message(session_id, assistant_msg)

        # Return streaming response with background recording
        return StreamingResponse(
            streamer(),
            media_type="text/plain",
            background=BackgroundTask(record_assistant),
        )

    # 5) Non-streaming: call the RAG service
    try:
        service = RAGService(chain)
        answer_text, sources = service.retrieve_and_answer(history, payload.content)
    except ChatServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    # 6) Wrap answer in our standard response schema
    assistant_msg = ChatMessage(role="assistant", content=answer_text)

    # 7) Record the assistant’s response in history
    history_store.record_message(session_id, assistant_msg)

    return QueryResponse(content=assistant_msg)
