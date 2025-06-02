"""
FastAPI backend for the Ted mobile app.
Refactored into a clean, modular structure.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import DEFAULT_USER_ID
from src.chat import get_ted_instances_count
from src.api.chat_routes import router as chat_router
from src.api.transcription_routes import router as transcription_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ted_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifespan of the FastAPI application.
    """
    logger.info("Ted API is starting up")
    logger.info(f"Default user_id: {DEFAULT_USER_ID}")
    yield
    logger.info("Ted API is shutting down")
    logger.info(f"Served {get_ted_instances_count()} unique users")


# Create FastAPI app
app = FastAPI(
    title="Ted API",
    description="AI mentor backend for the Ted mobile app",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for all origins and methods (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(transcription_router)


# Health check endpoint
@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "Ted API"}


logger.info("Ted API service initialized")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
