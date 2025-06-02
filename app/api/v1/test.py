# app/api/v1/test.py

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class TestResponse(BaseModel):
    content: str

@router.post("/test", response_model=TestResponse)
def test():
    """
    Simple endpoint to verify that the server is up and running.
    """
    return TestResponse(content="Hi! The server is up and running!")
