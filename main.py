"""
FastAPI backend for Mentor mobile app.
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, AsyncGenerator, List, Dict
import asyncio
from fastapi.middleware.cors import CORSMiddleware
import os
from src.boot import memory_manager, llm_client
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


# Instantiate Mentor agent (fixed user_id for now)
mentor = Mentor(memory_manager, llm_client, user_id="u42")


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
    # Respect test_mode from request, fallback to env
    test_mode = body.get("test_mode")
    # Use dummy streaming for testing
    if test_mode:
        return StreamingResponse(
            stream_response(message), media_type="text/event-stream"
        )
    else:
        # Use real Mentor streaming
        async def mentor_stream():
            for token in mentor.stream_reply(message, thread_id=thread_id):
                yield sse_format(token)
                await asyncio.sleep(0)  # let uvicorn flush immediately
            yield sse_format("[END]")

        return StreamingResponse(mentor_stream(), media_type="text/event-stream")


@app.get("/chatlog", response_model=List[ChatLogMessage])
def chatlog_endpoint() -> List[ChatLogMessage]:
    """
    Returns the recent chat log for the current user (u42).
    """
    # TODO: Replace 'u42' with real user_id from auth/session
    return memory_manager.fetch_recent("u42")
