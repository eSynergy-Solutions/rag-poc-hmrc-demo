# app/main.py

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import chat, discover, oas, health, history, test
from core.logging import logger
from core.config import settings


# Build the FastAPI application (all routes are registered in build_api())
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url="/v1/openapi.json",
    docs_url="/v1/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- routers ----------------------------------------------------------
app.include_router(health.router, prefix="/v1", tags=["health"])
app.include_router(chat.router, prefix="/v1", tags=["chat"])
app.include_router(discover.router, prefix="/v1", tags=["discover"])
app.include_router(oas.router, prefix="/v1", tags=["oas"])
app.include_router(history.router, prefix="/v1", tags=["history"])
app.include_router(test.router, prefix="/v1", tags=["test"])

logger.info(
    "FastAPI app initialized",
    app_name=settings.APP_NAME,
    version=settings.APP_VERSION,
    routes=[
        "/v1/health/live",
        "/v1/health/ready",
        "/v1/chat",
        "/v1/discover",
        "/v1/oas-check",
        "/v1/history",
        "/v1/test",
    ],
)

if __name__ == "__main__":
    logger.info(
        "Starting Uvicorn",
        host="0.0.0.0",
        port=8000,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
    )
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
