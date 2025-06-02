"""
Chat-related API routes.
"""

from fastapi import APIRouter, Request, Query
from typing import List, Optional

from ..models import ChatRequest, ChatResponse, ChatLogMessage
from ..config import DEFAULT_USER_ID
from ..boot import memory_manager
from ..chat import handle_chat_request, handle_chat_stream

import logging

logger = logging.getLogger("ted_api.chat_routes")

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Simple chat endpoint. Replace with real Ted logic if needed.
    """
    return handle_chat_request(request)


@router.post("/chat/stream")
async def chat_stream(request: Request):
    """
    Streams the chat response using Server-Sent Events (SSE).
    """
    body = await request.json()
    message = body.get("message", "")
    user_id = body.get("user_id", DEFAULT_USER_ID)
    test_mode = body.get("test_mode", False)

    return await handle_chat_stream(message, user_id, test_mode)


@router.get("/chatlog", response_model=List[ChatLogMessage])
def chatlog_endpoint(
    user_id: Optional[str] = Query(None),
    limit: Optional[int] = Query(
        None, description="Maximum number of messages to return"
    ),
    offset: int = Query(0, description="Number of messages to skip from the end"),
) -> List[ChatLogMessage]:
    """
    Returns the recent chat log for the specified user or DEFAULT_USER_ID if not specified.
    Supports pagination via limit and offset parameters.
    """
    user = user_id if user_id else DEFAULT_USER_ID
    logger.info(f"Fetching chat log for user: {user}, limit: {limit}, offset: {offset}")

    try:
        # Pass pagination parameters to fetch_recent
        messages = memory_manager.fetch_recent(
            user,
            k=20,  # default fallback
            use_time_filtering=(
                offset == 0 and limit is None
            ),  # Only apply time filtering for legacy calls without pagination
            offset=offset,
            limit=limit,
        )
        logger.info(f"Retrieved {len(messages)} messages for user: {user}")
        return messages
    except Exception as e:
        logger.error(f"Error fetching chat log for user {user}: {str(e)}")
        raise
