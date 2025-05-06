"""
FastAPI backend for Mentor mobile app.
"""

from fastapi import FastAPI, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, AsyncGenerator, List, Dict, Optional
import asyncio
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from contextlib import asynccontextmanager
from src.boot import memory_manager, llm_client
from src.config import DEFAULT_USER_ID
from src.mentor import Mentor
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mentor_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifespan of the FastAPI application.
    """
    logger.info("Mentor API is starting up")
    logger.info(f"Default user_id: {DEFAULT_USER_ID}")
    yield
    logger.info("Mentor API is shutting down")
    logger.info(f"Served {len(mentor_instances)} unique users")


app = FastAPI(lifespan=lifespan)

# Enable CORS for all origins and methods (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Starting Mentor API service")


class ChatRequest(BaseModel):
    message: str
    user_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    data: Any = None


class ChatLogMessage(BaseModel):
    role: str
    content: str
    timestamp: str


def sse_format(data: str) -> str:
    """
    Wrap each chunk in JSON so leading spaces survive the SSE parser.
    """
    return f"data:{json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_response(message: str) -> AsyncGenerator[str, None]:
    """
    Simulates streaming a response in chunks for SSE.
    """
    logger.debug(f"Starting test mode stream for message: {message[:30]}...")
    response = f"Echo: {message}"
    for chunk in [response[i : i + 8] for i in range(0, len(response), 8)]:
        yield sse_format(chunk)
        await asyncio.sleep(0.1)
    yield sse_format("[END]")
    logger.debug("Test mode stream complete")


# Create a dictionary to store mentor instances for different users
mentor_instances = {}
logger.info(f"Initialized with default user_id: {DEFAULT_USER_ID}")


def get_mentor_for_user(user_id: str) -> Mentor:
    """
    Returns a Mentor instance for the given user_id, creating one if it doesn't exist.
    """
    if user_id not in mentor_instances:
        logger.info(f"Creating new Mentor instance for user_id: {user_id}")
        mentor_instances[user_id] = Mentor(memory_manager, llm_client, user_id=user_id)
    else:
        logger.debug(f"Using existing Mentor instance for user_id: {user_id}")
    return mentor_instances[user_id]


# Instantiate default Mentor agent
mentor_instances[DEFAULT_USER_ID] = Mentor(
    memory_manager, llm_client, user_id=DEFAULT_USER_ID
)
logger.info(f"Active mentor instances: {list(mentor_instances.keys())}")


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Dummy chat endpoint. Replace with real Mentor logic.
    """
    user_id = request.user_id or DEFAULT_USER_ID
    logger.info(f"Chat request received from user_id: {user_id}")
    return ChatResponse(response=f"Echo: {request.message}")


@app.post("/chat/stream")
async def chat_stream(request: Request):
    """
    Streams the chat response using Server-Sent Events (SSE).
    """
    body = await request.json()
    message = body.get("message", "")
    user_id = body.get("user_id", DEFAULT_USER_ID)

    logger.info(f"Stream chat request received - user_id: {user_id}")
    logger.debug(f"Message content ({len(message)} chars): {message[:50]}...")

    # Respect test_mode from request, fallback to env
    test_mode = body.get("test_mode")

    # Use dummy streaming for testing
    if test_mode:
        logger.info(f"Using test mode for user_id: {user_id}")
        return StreamingResponse(
            stream_response(message), media_type="text/event-stream"
        )
    else:
        logger.info(f"Streaming real chat for user_id: {user_id}")
        # Get or create the mentor for this user
        user_mentor = get_mentor_for_user(user_id)

        # Use real Mentor streaming
        async def mentor_stream():
            logger.debug(f"Starting mentor stream for user_id: {user_id}")
            token_count = 0
            try:
                for token in user_mentor.stream_reply(message):
                    token_count += 1
                    yield sse_format(token)
                    await asyncio.sleep(0)  # let uvicorn flush immediately

                logger.info(
                    f"Stream complete for user_id: {user_id} - sent {token_count} tokens"
                )
            except Exception as e:
                logger.error(f"Error during streaming for user_id {user_id}: {str(e)}")
                # Send error message to client
                yield sse_format(f"Error: {str(e)}")

            yield sse_format("[END]")

        return StreamingResponse(mentor_stream(), media_type="text/event-stream")


@app.get("/chatlog", response_model=List[ChatLogMessage])
def chatlog_endpoint(user_id: Optional[str] = Query(None)) -> List[ChatLogMessage]:
    """
    Returns the recent chat log for the specified user or DEFAULT_USER_ID if not specified.
    """
    user = user_id if user_id else DEFAULT_USER_ID
    logger.info(f"Fetching chat log for user: {user}")

    try:
        messages = memory_manager.fetch_recent(user)
        logger.info(f"Retrieved {len(messages)} messages for user: {user}")
        return messages
    except Exception as e:
        logger.error(f"Error fetching chat log for user {user}: {str(e)}")
        raise
