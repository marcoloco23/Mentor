"""
Chat service for managing Ted instances and handling chat interactions.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict

from fastapi.responses import StreamingResponse

from .config import DEFAULT_USER_ID
from .boot import memory_manager, llm_client
from .ted import Ted
from .models import ChatRequest, ChatResponse

logger = logging.getLogger("ted_api.chat")

# Create a dictionary to store Ted instances for different users
ted_instances: Dict[str, Ted] = {}

# Instantiate default Ted agent
ted_instances[DEFAULT_USER_ID] = Ted(
    memory_manager, llm_client, user_id=DEFAULT_USER_ID
)
logger.info(f"Initialized Ted instances: {list(ted_instances.keys())}")


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


def handle_chat_request(request: ChatRequest) -> ChatResponse:
    """
    Handle a simple chat request (non-streaming).
    """
    user_id = request.user_id or DEFAULT_USER_ID
    logger.info(f"Chat request received from user_id: {user_id}")
    # For now, just return an echo. In the future, you might want to integrate Ted here too
    return ChatResponse(response=f"Echo: {request.message}")


async def handle_chat_stream(
    message: str, user_id: str, test_mode: bool = False
) -> StreamingResponse:
    """
    Handle a streaming chat request.

    Args:
        message: The user's message
        user_id: The user ID
        test_mode: Whether to use test mode (simple echo)

    Returns:
        StreamingResponse with the chat stream
    """
    logger.info(f"Stream chat request received - user_id: {user_id}")
    logger.debug(f"Message content ({len(message)} chars): {message[:50]}...")

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


def get_ted_instances_count() -> int:
    """Get the current number of Ted instances for logging purposes."""
    return len(ted_instances)
