# app/main.py

import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.api import build_api
from app.core.logging import logger
from app.core.config import settings

# Build the FastAPI application (all routes are registered in build_api())
app = build_api()

# ────────────────────────────────────────────────────────────────────────────────
# Add CORS middleware so that frontend or other domains can call our API without issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Allow all origins; tighten in prod as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info(
        "Starting Uvicorn",
        host="0.0.0.0",
        port=8000,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
    )
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_config=None,  # structlog handles logging
    )
