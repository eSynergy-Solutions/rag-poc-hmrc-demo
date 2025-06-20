from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.history.BasicHistory import BaseHistory, OneShotHistory
from src.schemas.ChatSchemas import ChatMessage
from src.chat.HMRCRag import HMRCRAG
from src.chat.SingleShotAgent import SingleShotAgent

from src.chat.SingleShotAgentOASCreate import SingleShotAgentCreate
from src.chat.Discovery import DiscoveryRAGChat
from src.prompts import OASCheckerPrompt, OASCreatePrompt
import logging
import uvicorn
from routers import chat, test, oasChecker, oasCreate, discovery

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


# def get_chat_instance_hmrc_api_agent() -> Chat:
#     chat_class_path = "src.chat.HMRCRag.HMRCRAG"
#     logger.info(f"Using chat implementation: {chat_class_path}")
#     module_name, class_name = chat_class_path.rsplit(".", 1)
#     module = importlib.import_module(module_name)
#     chat_class = getattr(module, class_name)
#     return chat_class()


# def get_chat_instance_oas_checker_agent() -> Chat:
#     chat_class_path = "src.chat.SingleShotAgent.SingleShotAgent"
#     logger.info(f"Using chat implementation: {chat_class_path}")
#     module_name, class_name = chat_class_path.rsplit(".", 1)
#     module = importlib.import_module(module_name)
#     chat_class = getattr(module, class_name)
#     return chat_class()


HistoryObjectHMRC = BaseHistory()
HistoryObjectOASChecker = OneShotHistory()  # one-shot: only last message used
HistoryObjectOASCreate = OneShotHistory()  # one-shot: only last message used
HistoryObjectDiscovery = OneShotHistory()  # one-shot: only last message used
logger.info("HistoryObject initialized.")

ChatObjectHmrcApiAgent: HMRCRAG = HMRCRAG()
ChatObjectOasAgent: SingleShotAgent = SingleShotAgent(sysPromptContent=OASCheckerPrompt)
ChatObjectOasCreate: SingleShotAgentCreate = SingleShotAgentCreate(
    sysPromptContent=OASCreatePrompt
)
ChatObjectDiscovery: DiscoveryRAGChat = DiscoveryRAGChat()
logger.info("ChatObjects initialized.")

app.state.HistoryObjectHMRC = HistoryObjectHMRC
app.state.HistoryObjectOASChecker = HistoryObjectOASChecker
app.state.HistoryObjectOASCreate = HistoryObjectOASCreate
app.state.HistoryObjectDiscovery = HistoryObjectDiscovery
app.state.ChatObjectHmrcApiAgent = ChatObjectHmrcApiAgent
app.state.ChatObjectOasAgent = ChatObjectOasAgent
app.state.ChatObjectOasCreate = ChatObjectOasCreate
app.state.ChatObjectDiscovery = ChatObjectDiscovery

app.include_router(chat.router)
# app.include_router(history.router)
app.include_router(test.router)
app.include_router(oasCreate.router)
app.include_router(oasChecker.router)
app.include_router(discovery.router)

# Startup script for direct running
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)
