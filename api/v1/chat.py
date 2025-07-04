# app/api/v1/discover.py

from fastapi import APIRouter, HTTPException, Request, Body
from models.chat import ChatMessage, ChatEndpointRequest
from schemas.responses import QueryResponse
from schemas.requests import QueryRequest
from services.rag_service import RagService
from errors import ChatServiceError

router = APIRouter()


@router.post("/chat", response_model=QueryResponse)
async def chat(
    request: Request,
    payload: QueryRequest = Body(
        ...,
        examples=[
            {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": "Does Azure OpenAI support customer managed keys?",
                    },
                    {
                        "role": "assistant",
                        "content": "Yes, customer managed keys are supported by Azure OpenAI.",
                    },
                    {
                        "role": "user",
                        "content": "Do other Azure services support this too?",
                    },
                ],
                "streaming": False,
            }
        ],
    ),
):
    """
    Endpoint to run "chat" using RAG; history maintained and shared by the Frontend.
    """

    user_query: ChatEndpointRequest = payload.content
    if not user_query:
        raise HTTPException(status_code=422, detail="Query content cannot be empty")
    try:
        service = RagService()
        answer_text = service.query_vector_database(user_query, service_name="chat")
    except ChatServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    # 3) Wrap response
    assistant_msg = ChatMessage(role="assistant", content=answer_text)

    return assistant_msg
