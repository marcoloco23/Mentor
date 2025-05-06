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
from src.boot import memory_manager, llm_client
from src.config import DEFAULT_USER_ID
from src.mentor import Mentor
import json

app = FastAPI()

# Enable CORS for all origins and methods (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None
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
    response = f"Echo: {message}"
    for chunk in [response[i : i + 8] for i in range(0, len(response), 8)]:
        yield sse_format(chunk)
        await asyncio.sleep(0.1)
    yield sse_format("[END]")


# Create a dictionary to store mentor instances for different users
mentor_instances = {}


def get_mentor_for_user(user_id: str) -> Mentor:
    """
    Returns a Mentor instance for the given user_id, creating one if it doesn't exist.
    """
    if user_id not in mentor_instances:
        mentor_instances[user_id] = Mentor(memory_manager, llm_client, user_id=user_id)
    return mentor_instances[user_id]


# Instantiate default Mentor agent
mentor_instances[DEFAULT_USER_ID] = Mentor(
    memory_manager, llm_client, user_id=DEFAULT_USER_ID
)


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Dummy chat endpoint. Replace with real Mentor logic.
    """
    return ChatResponse(response=f"Echo: {request.message}")


@app.post("/chat/stream")
async def chat_stream(request: Request):
    """
    Streams the chat response using Server-Sent Events (SSE).
    """
    body = await request.json()
    message = body.get("message", "")
    thread_id = body.get("thread_id")
    user_id = body.get("user_id", DEFAULT_USER_ID)
    # Respect test_mode from request, fallback to env
    test_mode = body.get("test_mode")
    # Use dummy streaming for testing
    if test_mode:
        return StreamingResponse(
            stream_response(message), media_type="text/event-stream"
        )
    else:
        # Get or create the mentor for this user
        user_mentor = get_mentor_for_user(user_id)

        # Use real Mentor streaming
        async def mentor_stream():
            for token in user_mentor.stream_reply(message, thread_id=thread_id):
                yield sse_format(token)
                await asyncio.sleep(0)  # let uvicorn flush immediately
            yield sse_format("[END]")

        return StreamingResponse(mentor_stream(), media_type="text/event-stream")


@app.get("/chatlog", response_model=List[ChatLogMessage])
def chatlog_endpoint(user_id: Optional[str] = Query(None)) -> List[ChatLogMessage]:
    """
    Returns the recent chat log for the specified user or DEFAULT_USER_ID if not specified.
    """
    user = user_id if user_id else DEFAULT_USER_ID
    messages = memory_manager.fetch_recent(user)
    return messages
