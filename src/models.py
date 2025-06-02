"""
Pydantic models for the Ted API.
"""

from pydantic import BaseModel
from typing import Any, Optional


class ChatRequest(BaseModel):
    """Request model for chat endpoints."""

    message: str
    user_id: str | None = None


class ChatResponse(BaseModel):
    """Response model for chat endpoints."""

    response: str
    data: Any = None


class ChatLogMessage(BaseModel):
    """Model for individual chat log messages."""

    role: str
    content: str
    timestamp: str


class TranscriptionResponse(BaseModel):
    """Response model for audio transcription."""

    model: str
    language: str | None
    transcription: str
