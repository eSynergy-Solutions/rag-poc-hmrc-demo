from fastapi import APIRouter, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from src.schemas.ChatSchemas import ChatMessage
import logging
from src.chat.SingleShotAgent import SingleShotAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Input and output schemas


class QueryRequestCreate(BaseModel):
    content: str


class QueryResponse(BaseModel):
    content: ChatMessage


# Router


@router.post("/oas-create")
def oasCreate(query: QueryRequestCreate, request: Request):
    HistoryObject = request.app.state.HistoryObjectOASCreate
    ChatObject: SingleShotAgent = request.app.state.ChatObjectOasCreate
    logger.info(f"Received chat request: {query.content}")
    message = ChatMessage(role="user", content=query.content)
    HistoryObject.record_message(message)
    logger.info("Message recorded in history.")

    context_history = HistoryObject.get_context_history()
    logger.info(f"Context history retrieved: {context_history}")

    chat_response = ChatObject.chat_query(chat_history=context_history, streamed=False)
    logger.info("Chat response generated.")
    logger.info(f"Chat response content: {chat_response}")

    if not chat_response:
        logger.error("Chat response is empty or None.")
        return "The provided response is invalid or could not be processed"

    try:
        logger.info("content passed to yaml_to_json:")
        logger.info(chat_response.content)
        json_api_spec = ChatObject.yaml_to_json(chat_response.content)
        logger.info("Converted YAML to JSON successfully.")
        try:
            oas_validity = ChatObject.validate_oas_spec(json_api_spec)
        except Exception as e:
            logger.error(f"Failed to validate OAS spec: {e}")
            return "The provided OpenAPI Specification is invalid or could not be processed"
    except Exception as e:
        logger.error(f"Failed to convert YAML to JSON: {e}")
        return "The provided OpenAPI Specification is invalid or could not be processed"

    logger.info(f"Chat response generated: {chat_response}")

    HistoryObject.record_message(chat_response)
    logger.info("Chat response recorded in history.")
    return chat_response.content
