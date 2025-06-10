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


class QueryRequest(BaseModel):
    content: str
    streaming: bool


class QueryResponse(BaseModel):
    content: ChatMessage


# Router


@router.post("/oas-checker")
def oasChecker(query: QueryRequest, request: Request):
    HistoryObject = request.app.state.HistoryObjectOASChecker
    ChatObject: SingleShotAgent = request.app.state.ChatObjectOasAgent
    logger.info(f"Received chat request: {query.content} streaming={query.streaming}")
    message = ChatMessage(role="user", content=query.content)
    HistoryObject.record_message(message)
    logger.info("Message recorded in history.")

    context_history = HistoryObject.get_context_history()
    logger.info(f"Context history retrieved: {context_history}")

    try:
        logger.info("content passed to yaml_to_json:")
        logger.info(query.content)
        json_api_spec = ChatObject.yaml_to_json(query.content)
        logger.info("Converted YAML to JSON successfully.")
        try:
            oas_validity = ChatObject.validate_oas_spec(json_api_spec)
        except Exception as e:
            logger.error(f"Failed to validate OAS spec: {e}")
            return "The provided OpenAPI Specification is invalid or could not be processed"
    except Exception as e:
        logger.error(f"Failed to convert YAML to JSON: {e}")
        return "The provided OpenAPI Specification is invalid or could not be processed"

    chat_response = ChatObject.chat_query(
        chat_history=context_history, streamed=query.streaming
    )

    if not query.streaming:
        logger.info(f"Chat response generated: {chat_response}")

        HistoryObject.record_message(chat_response)
        logger.info("Chat response recorded in history.")
        return chat_response

    def stream_chat():
        response_content = ""
        for chunk in chat_response:
            yield chunk
            response_content += chunk

        logger.info(f"Chat response generated: {response_content}")
        HistoryObject.record_message(
            ChatMessage(role="assistant", content=response_content)
        )

    return StreamingResponse(stream_chat(), media_type="text/plain")
