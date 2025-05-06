"""
Utility functions and helpers for the Mentor application.

This module contains various utility functions that are used across the application.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("MentorUtils")


def format_timestamp(timestamp: str) -> str:
    """
    Format an ISO timestamp to human-readable format.

    Args:
        timestamp (str): ISO formatted timestamp string

    Returns:
        str: Human-readable timestamp
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        logger.warning(f"Failed to parse timestamp: {timestamp}, error: {e}")
        return timestamp


def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing excessive whitespace and newlines.

    Args:
        text (str): Text to sanitize

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    # Replace multiple newlines with a single newline
    text = re.sub(r"\n\s*\n", "\n", text)
    # Trim leading/trailing whitespace
    return text.strip()


def chunk_text(text: str, max_chunk_size: int = 1000) -> List[str]:
    """
    Split text into chunks of approximately max_chunk_size characters.
    Tries to split on sentence boundaries when possible.

    Args:
        text (str): Text to chunk
        max_chunk_size (int, optional): Maximum chunk size. Defaults to 1000.

    Returns:
        List[str]: List of text chunks
    """
    if not text or len(text) <= max_chunk_size:
        return [text] if text else []

    # Try to split on sentence boundaries (period followed by space)
    chunks = []
    current_chunk = ""

    sentences = re.split(r"(\.|\?|!)\s+", text)
    # This creates pairs of sentences and their ending punctuation
    i = 0
    while i < len(sentences):
        if i + 1 < len(sentences):
            # Combine sentence with its punctuation
            sentence = sentences[i] + sentences[i + 1]
            i += 2
        else:
            # Last element might not have punctuation
            sentence = sentences[i]
            i += 1

        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += sentence + " "
        else:
            # If current chunk is not empty, add it to chunks
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
