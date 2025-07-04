# app/api/v1/discover.py

from fastapi import APIRouter, HTTPException, Request, Body
from models.chat import ChatMessage
from schemas.responses import QueryResponse
from schemas.requests import QueryRequest
from services.rag_service import RagService
from errors import ChatServiceError

router = APIRouter()

response_examples = {
    200: {
        "description": "Successful discovery response",
        "content": {
            "application/json": {
                "examples": {
                    "BasicSuccess": {
                        "summary": "Similar APIs with suggestions",
                        "value": {
                            "messages": [
                                {
                                    "role": "assistant",
                                    "content": "Here are some similar APIs I found that are relevant to your query. You can explore them further for more details.",
                                }
                            ]
                        },
                    }
                }
            }
        },
    },
    422: {
        "description": "Validation error",
        "content": {
            "application/json": {
                "examples": {
                    "MissingContent": {
                        "summary": "Missing 'content' field",
                        "value": {
                            "detail": [
                                {
                                    "loc": ["body", "content"],
                                    "msg": "field required",
                                    "type": "value_error.missing",
                                }
                            ]
                        },
                    }
                }
            }
        },
    },
}


@router.post("/discover", response_model=QueryResponse, responses=response_examples)
def discover(
    request: Request,
    payload: QueryRequest = Body(
        ...,
        examples=[
            {
                "content": "openapi: 3.0.3\ninfo:\n  title: Hello World API\n  version: '1.0'\npaths:....",
                "streaming": False,
            },
        ],
    ),
):
    """
    Endpoint to run “discovery” queries using RAG, without history.
    """

    user_query: str = payload.content
    if not user_query:
        raise HTTPException(status_code=422, detail="Query content cannot be empty")
    try:
        service = RagService()
        answer_text = service.query_vector_database(
            user_query, service_name="discovery"
        )
    except ChatServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    # 3) Wrap response
    assistant_msg = ChatMessage(role="assistant", content=answer_text)

    return assistant_msg
