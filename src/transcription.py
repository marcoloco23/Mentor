"""
Audio transcription service using OpenAI's Whisper and GPT-4o models.
Includes hallucination detection and validation for better transcription quality.
"""

import io
import logging
from typing import Dict, Any

from fastapi import UploadFile, HTTPException, status

from .models import TranscriptionResponse
from .boot import llm_client

logger = logging.getLogger("ted_api.transcription")

# Supported MIME types for audio uploads
SUPPORTED_AUDIO_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/m4a",
    "audio/webm",
    "audio/ogg",
}


def is_transcription_valid(
    transcription: str, prompt: str, audio_duration_seconds: float = None
) -> bool:
    """
    Validate that the transcription is actual speech content and not hallucinated prompt text.

    Returns False if:
    - Transcription contains significant portions of the prompt
    - Transcription is suspiciously long for short audio
    - Transcription contains known hallucination patterns
    """
    if not transcription or not transcription.strip():
        return False

    transcription_clean = transcription.lower().strip()
    prompt_clean = prompt.lower().strip()

    # Check if transcription contains large portions of the prompt
    prompt_words = set(prompt_clean.split())
    transcription_words = set(transcription_clean.split())

    # If more than 30% of prompt words appear in transcription, likely hallucination
    if len(prompt_words) > 0:
        overlap_ratio = len(prompt_words.intersection(transcription_words)) / len(
            prompt_words
        )
        if overlap_ratio > 0.3:
            return False

    # Check for common hallucination patterns
    hallucination_patterns = [
        "this is a high-quality",
        "complete transcription",
        "every spoken word is captured",
        "speaker communicates clearly",
        "transcription preserves all content",
        "clear pronunciation and enunciation",
        "speaker is using clear",
        "perfect accuracy throughout",
        "without omitting any segments",
        # Common Whisper hallucinations
        "thank you for watching",
        "like and subscribe",
        "don't forget to like",
        "thanks for listening",
        "i hope you enjoyed",
        "see you in the next",
        "www.beadaholique.com",  # Known spam hallucination
        "find out more at",
        "visit our website",
        # Repetitive patterns that indicate hallucination
        "the the the",
        "and and and",
        "but but but",
        # Language detection fallbacks that aren't actual speech
        "clear speech transcription",
        "english speech",
        "speech transcription",
    ]

    for pattern in hallucination_patterns:
        if pattern in transcription_clean:
            return False

    # Check for suspiciously long transcription on short audio
    if audio_duration_seconds and audio_duration_seconds < 2.0:
        # For very short clips, transcription shouldn't be more than ~150 words per minute
        expected_max_words = max(5, int(audio_duration_seconds * 2.5))  # ~150 WPM
        actual_words = len(transcription.split())
        if actual_words > expected_max_words:
            return False

    return True


def get_audio_duration(audio_bytes: bytes) -> float:
    """
    Estimate audio duration from audio bytes.
    This is a rough estimation for validation purposes.
    """
    try:
        # For basic estimation, assume common audio formats
        # This is rough but good enough for validation
        estimated_duration = len(audio_bytes) / (16000 * 2)  # Assume 16kHz, 16-bit
        return max(0.1, estimated_duration)  # Minimum 0.1 seconds
    except:
        return 1.0  # Default fallback


def generate_transcription_prompt(
    language: str | None = None, audio_duration: float = None
) -> str:
    """
    Generate a context-aware prompt for better transcription quality.

    For very short clips, use a minimal prompt to avoid hallucination.
    Based on OpenAI's research, longer, more contextual prompts work better than simple instructions.
    This helps especially with quiet speech and ensuring complete transcription.
    """
    # For very short audio (< 3 seconds), use minimal prompt to avoid hallucination
    if audio_duration and audio_duration < 3.0:
        base_prompt = "Clear speech transcription."
        if language:
            simple_context = {
                "en": "English speech.",
                "es": "Habla en español.",
                "fr": "Parole française.",
                "de": "Deutsche Sprache.",
                "it": "Parlato italiano.",
                "pt": "Fala portuguesa.",
                "ru": "Русская речь.",
                "ja": "日本語の音声。",
                "ko": "한국어 음성.",
                "zh": "中文语音。",
            }
            if language.lower() in simple_context:
                base_prompt = simple_context[language.lower()]
        return base_prompt

    # For longer audio, use the enhanced prompt
    base_prompt = "This is a high-quality, complete transcription where every spoken word is captured with perfect accuracy. The speaker communicates clearly and deliberately, and even during quiet moments, soft speech, or brief pauses, every word and phrase is transcribed in full. The transcription preserves all content without omitting any segments, ensuring completeness throughout the entire recording. All speech is transcribed verbatim, including quiet or softly spoken words."

    # Add language-specific context if provided
    if language:
        language_context = {
            "en": "The speaker is using clear English pronunciation and enunciation.",
            "es": "El hablante usa una pronunciación y enunciación clara en español.",
            "fr": "Le locuteur utilise une prononciation et une énonciation claires en français.",
            "de": "Der Sprecher verwendet eine klare deutsche Aussprache und Artikulation.",
            "it": "Il parlante usa una pronunciazione e enunciazione italiana chiara.",
            "pt": "O falante usa pronúncia e enunciação claras em português.",
            "ru": "Говорящий использует четкое русское произношение и артикуляцию.",
            "ja": "話者は明確な日本語の発音と話し方を使用しています。",
            "ko": "화자는 명확한 한국어 발음과 구사를 사용합니다.",
            "zh": "说话者使用清晰的中文发音和表达。",
        }
        if language.lower() in language_context:
            base_prompt += f" {language_context[language.lower()]}"

    return base_prompt


async def transcribe_audio(
    file: UploadFile, language: str | None = None, model: str = "gpt-4o-transcribe"
) -> TranscriptionResponse:
    """
    Transcribe audio using OpenAI's models with fallback and validation.

    Args:
        file: The uploaded audio file
        language: Optional language hint (ISO-639-1 code)
        model: The model to use for transcription

    Returns:
        TranscriptionResponse with the transcribed text

    Raises:
        HTTPException: If the file type is unsupported or transcription fails
    """
    if file.content_type not in SUPPORTED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(SUPPORTED_AUDIO_TYPES))}",
        )

    audio_bytes = await file.read()
    logger.info(
        f"Transcribing {file.filename} ({len(audio_bytes)} bytes) "
        f"with {model}, lang={language}, content_type={file.content_type}"
    )

    # Estimate audio duration for validation
    estimated_duration = get_audio_duration(audio_bytes)
    logger.debug(f"Estimated audio duration: {estimated_duration:.2f} seconds")

    # Wrap bytes in a file-like object as the SDK expects
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = file.filename

    # Generate appropriate prompt based on audio duration
    prompt_text = generate_transcription_prompt(language, estimated_duration)

    # Build the request payload
    kwargs: Dict[str, Any] = {
        "file": audio_file,
        "model": model,
        "prompt": prompt_text,
        "language": language,
        "temperature": 0.0,
        "response_format": "json",  # Use 'json' format for compatibility with gpt-4o models
    }
    # Strip None values to avoid API complaints
    clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    try:
        logger.info(f"Sending transcription request with kwargs: {clean_kwargs}")
        response = llm_client.client.audio.transcriptions.create(**clean_kwargs)
        logger.info(f"Transcription successful with {model}")

        # Extract the text from the response object - handle both text and json formats
        if hasattr(response, "text") and response.text:
            transcription_text = response.text
        elif hasattr(response, "__dict__") and "text" in response.__dict__:
            # Handle json format response
            transcription_text = response.__dict__.get("text", str(response))
        else:
            # Fallback to string conversion
            transcription_text = str(response)

        # Validate the transcription to detect hallucinations
        if not is_transcription_valid(
            transcription_text, prompt_text, estimated_duration
        ):
            logger.warning(
                f"Invalid transcription detected (likely hallucination): {transcription_text[:100]}..."
            )

            # For very short audio or no speech detected, return empty result
            if (
                estimated_duration < 1.0 or len(audio_bytes) < 5000
            ):  # Less than 1 second or very small file
                logger.info(
                    "Audio too short or no speech detected, returning empty transcription"
                )
                return TranscriptionResponse(
                    model=model,
                    language=language,
                    transcription="",
                )

            # Try again with minimal prompt to avoid hallucination
            logger.info("Retrying with minimal prompt to avoid hallucination")
            audio_file.seek(0)
            minimal_kwargs = clean_kwargs.copy()
            minimal_kwargs["prompt"] = "Speech transcription."

            try:
                response = llm_client.client.audio.transcriptions.create(
                    **minimal_kwargs
                )
                retry_transcription = (
                    response.text if hasattr(response, "text") else str(response)
                )

                # Validate the retry
                if is_transcription_valid(
                    retry_transcription, "Speech transcription.", estimated_duration
                ):
                    transcription_text = retry_transcription
                    logger.info("Retry with minimal prompt successful")
                else:
                    logger.warning(
                        "Retry also produced invalid transcription, returning empty result"
                    )
                    transcription_text = ""

            except Exception as retry_error:
                logger.warning(f"Retry with minimal prompt failed: {str(retry_error)}")
                transcription_text = ""

        return TranscriptionResponse(
            model=model,
            language=language,
            transcription=transcription_text,
        )

    except Exception as e:
        error_str = str(e).lower()

        # Check if it's a format error and we're using gpt-4o models
        if (
            "unsupported_format" in error_str or "format you provided" in error_str
        ) and model.startswith("gpt-4o"):
            logger.warning(
                f"Format error with {model}, falling back to whisper-1: {str(e)}"
            )

            # Reset the file pointer for retry
            audio_file.seek(0)

            # Retry with whisper-1
            fallback_kwargs = clean_kwargs.copy()
            fallback_kwargs["model"] = "whisper-1"
            # Remove response_format for whisper-1 compatibility
            if "response_format" in fallback_kwargs:
                del fallback_kwargs["response_format"]

            try:
                logger.info(f"Retrying transcription with whisper-1")
                response = llm_client.client.audio.transcriptions.create(
                    **fallback_kwargs
                )
                logger.info(f"Transcription successful with whisper-1 fallback")

                fallback_transcription = (
                    response.text if hasattr(response, "text") else str(response)
                )

                # Validate the fallback transcription as well
                fallback_prompt = fallback_kwargs.get("prompt", "")
                if not is_transcription_valid(
                    fallback_transcription, fallback_prompt, estimated_duration
                ):
                    logger.warning(
                        "Whisper-1 fallback also produced invalid transcription"
                    )
                    fallback_transcription = ""

                return TranscriptionResponse(
                    model="whisper-1",  # Return the actual model used
                    language=language,
                    transcription=fallback_transcription,
                )

            except Exception as fallback_error:
                logger.exception(
                    f"Whisper-1 fallback also failed: {str(fallback_error)}"
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Transcription failed with both {model} and whisper-1: {str(fallback_error)}",
                )
        else:
            logger.exception(
                f"OpenAI transcription failed with error type {type(e)}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Transcription error: {str(e)}",
            )
