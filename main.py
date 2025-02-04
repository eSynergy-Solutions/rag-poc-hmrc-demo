from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.history.BasicHistory import BaseHistory
from src.schemas.ChatSchemas import ChatMessage
from src.chat.Chat import Chat
import importlib
import os
import logging
import uvicorn
from routers import chat, history, test

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input and output schemas


class QueryRequest(BaseModel):
    content: str


class QueryResponse(BaseModel):
    content: ChatMessage


class HistoryResponse(BaseModel):
    content: list[ChatMessage]


# Initialise History and RAG objects


def get_chat_instance() -> Chat:
    chat_class_path = "src.chat.HMRCRag.HMRCRAG"
    logger.info(f"Using chat implementation: {chat_class_path}")
    module_name, class_name = chat_class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    chat_class = getattr(module, class_name)
    return chat_class()


HistoryObject = BaseHistory()
logger.info("HistoryObject initialized.")

ChatObject: Chat = get_chat_instance()
logger.info("ChatObject initialized.")

app.state.HistoryObject = HistoryObject
app.state.ChatObject = ChatObject

app.include_router(chat.router)
app.include_router(history.router)
app.include_router(test.router)

# Startup script for direct running
if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)