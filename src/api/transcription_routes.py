"""
Audio transcription API routes.
"""

from fastapi import APIRouter, Query, UploadFile, File

from ..models import TranscriptionResponse
from ..transcription import transcribe_audio

router = APIRouter(tags=["transcription"])


@router.post("/transcribe_audio", response_model=TranscriptionResponse)
async def transcribe_audio_endpoint(
    file: UploadFile = File(...),
    language: str | None = Query(None, description="ISO-639-1 code, e.g. 'de'"),
    model: str = Query("gpt-4o-transcribe", description="or gpt-4o-mini-transcribe"),
) -> TranscriptionResponse:
    """
    Speech-to-text via GPT-4o with fallback to Whisper.
    * `language` — pass if known for lower latency.
    * `model` — choose mini for cheaper bulk runs.
    """
    return await transcribe_audio(file, language, model)
