"""
FastAPI backend for the Ted mobile app.
"""

from fastapi import FastAPI, Request, Query, UploadFile, File, HTTPException, status
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
from src.ted import Ted
import json
import io

# Supported MIME types your mobile app is likely to send
SUPPORTED_AUDIO_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/webm",
    "audio/ogg",
}

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
    logger.info(f"Served {len(ted_instances)} unique users")


app = FastAPI(lifespan=lifespan)

# Enable CORS for all origins and methods (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Starting Ted API service")


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


class TranscriptionResponse(BaseModel):
    model: str
    language: str | None
    transcription: str


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


# Create a dictionary to store Ted instances for different users
ted_instances = {}
logger.info(f"Initialized with default user_id: {DEFAULT_USER_ID}")


def get_ted_for_user(user_id: str) -> Ted:
    """
    Returns a Ted instance for the given user_id, creating one if it doesn't exist.
    """
    if user_id not in ted_instances:
        logger.info(f"Creating new Ted instance for user_id: {user_id}")
        ted_instances[user_id] = Ted(memory_manager, llm_client, user_id=user_id)
    else:
        logger.debug(f"Using existing Ted instance for user_id: {user_id}")
    return ted_instances[user_id]


# Instantiate default Ted agent
ted_instances[DEFAULT_USER_ID] = Ted(
    memory_manager, llm_client, user_id=DEFAULT_USER_ID
)
logger.info(f"Active Ted instances: {list(ted_instances.keys())}")


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Dummy chat endpoint. Replace with real Ted logic.
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
        # Get or create the Ted for this user
        user_mentor = get_ted_for_user(user_id)

        # Use real Ted streaming
        async def mentor_stream():
            logger.debug(f"Starting ted stream for user_id: {user_id}")
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


@app.post("/transcribe_audio", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Query(None, description="ISO-639-1 code, e.g. 'de'"),
    model: str = Query("gpt-4o-transcribe", description="or gpt-4o-mini-transcribe"),
) -> TranscriptionResponse:
    """
    Speech-to-text via GPT-4o.
    * `language` — pass if known for lower latency.
    * `model` — choose mini for cheaper bulk runs.
    """
    if file.content_type not in SUPPORTED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(SUPPORTED_AUDIO_TYPES))}",
        )

    audio_bytes = await file.read()
    logger.info(
        f"Transcribing {file.filename} ({len(audio_bytes)} bytes) "
        f"with {model}, lang={language}"
    )

    # Wrap bytes in a file-like object as the SDK expects
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = file.filename

    # Build the request payload
    kwargs: Dict[str, Any] = {
        "file": audio_file,
        "model": model,
        "prompt": "Transcribe accurately; keep English parts in English.",
        "language": language,
        "temperature": 0.0,
    }
    # Strip None values to avoid API complaints
    clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    try:
        logger.info(f"Sending transcription request with kwargs: {clean_kwargs}")
        response = llm_client.llm.audio.transcriptions.create(**clean_kwargs)
        logger.info(f"Transcription successful, response type: {type(response)}")

        # Extract the text from the response object if it's not already a string
        transcription_text = (
            response.text if hasattr(response, "text") else str(response)
        )
    except Exception as e:
        logger.exception(
            f"OpenAI transcription failed with error type {type(e)}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transcription error: {str(e)}",
        )

    return TranscriptionResponse(
        model=model,
        language=language,
        transcription=transcription_text,
    )
