from fastapi import APIRouter
from pydantic import BaseModel
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
