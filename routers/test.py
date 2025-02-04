from fastapi import APIRouter, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from src.schemas.ChatSchemas import ChatMessage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Input and output schemas


class QueryResponse(BaseModel):
    content: str


# Router


@router.post("/test")
def test():
    return "Hi! The server is up and running!"
