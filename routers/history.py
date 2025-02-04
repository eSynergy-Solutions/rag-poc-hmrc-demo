from fastapi import Request
from fastapi.routing import APIRouter
from pydantic import BaseModel
from src.schemas.ChatSchemas import ChatMessage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Input and output schemas


class HistoryResponse(BaseModel):
    content: list[ChatMessage]


# Router


@router.get("/history", response_model=HistoryResponse)
def history_request(request: Request) -> HistoryResponse:
    HistoryObject = request.app.state.HistoryObject
    logger.info("Received history request.")
    history_list = HistoryObject.get_history()
    logger.info(f"History retrieved: {history_list}")
    return HistoryResponse(content=history_list)
