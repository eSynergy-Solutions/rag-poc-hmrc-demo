# app/api/v1/discover.py

from fastapi import APIRouter, HTTPException, Request, Body
from models.chat import ChatMessage
from schemas.responses import QueryResponse
from schemas.requests import QueryRequest
from services.rag_service import RagService
from errors import ChatServiceError

router = APIRouter()


@router.post("/chat", response_model=QueryResponse)
def chat(
    request: Request,
    payload: QueryRequest = Body(
        ...,
        examples=[
            {
                "content": "Hi! Can you help me find similar APIs?",
                "streaming": False,
            },
            {
                "content": "Help me debug this code snippet...",
                "streaming": False,
            },
            {
                "content": "I am new to this API, can you guide me with some code examples in Java?",
                "streaming": False,
            },
        ],
    ),
):
    """
    Endpoint to run "chat" using RAG; history maintained and shared by the Frontend.
    """

    user_query: str = payload.content
    if not user_query:
        raise HTTPException(status_code=422, detail="Query content cannot be empty")
    try:
        service = RagService()
        answer_text = service.query_vector_database(user_query)
    except ChatServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    # 3) Wrap response
    assistant_msg = ChatMessage(role="assistant", content=answer_text)

    return assistant_msg
