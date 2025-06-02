"""
Utility functions and helpers for the Ted application.

This module contains various utility functions that are used across the application.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

from .config import (
    USER_TZ,
    MESSAGE_FRESHNESS_HOURS,
    MAX_STALE_MESSAGES,
    TIME_BREAK_THRESHOLD_HOURS,
)

logger = logging.getLogger("TedUtils")


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


def get_time_context() -> str:
    """
    Generate time-aware context for the agent to make responses more human-like.

    Returns:
        str: Formatted time context string including current time, date, and situational context
    """
    now_utc = datetime.now(timezone.utc)
    local_time = now_utc.astimezone(USER_TZ)

    # Format components
    weekday = local_time.strftime("%A")
    date_str = local_time.strftime("%B %d, %Y")
    time_str = local_time.strftime("%H:%M")

    # Determine time of day context
    hour = local_time.hour
    if 5 <= hour < 12:
        time_period = "morning"
    elif 12 <= hour < 17:
        time_period = "afternoon"
    elif 17 <= hour < 21:
        time_period = "evening"
    else:
        time_period = "night"

    # Add seasonal context
    month = local_time.month
    if month in [12, 1, 2]:
        season = "winter"
    elif month in [3, 4, 5]:
        season = "spring"
    elif month in [6, 7, 8]:
        season = "summer"
    else:
        season = "autumn"

    # Format the complete context
    time_context = (
        f"It's {time_period} on {weekday}, {date_str} at {time_str} ({season})"
    )

    # Add situational hints based on time
    if time_period == "morning" and hour < 8:
        time_context += " - early morning"
    elif time_period == "night" and hour >= 23:
        time_context += " - late night"
    elif weekday in ["Saturday", "Sunday"]:
        time_context += " - weekend"

    return time_context


def filter_messages_by_time_gaps(
    messages: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Filter messages to handle time gaps intelligently - avoid including stale conversation
    after long breaks (like overnight).

    Args:
        messages: List of message dictionaries with 'timestamp', 'role', and 'content'

    Returns:
        List of filtered messages that respect conversation breaks
    """
    if not messages:
        return []

    now_utc = datetime.now(timezone.utc)

    # Convert timestamps and add time deltas
    processed_messages = []
    for msg in messages:
        try:
            # Parse the timestamp
            ts_str = msg.get("timestamp", "")
            if ts_str:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = now_utc  # Fallback for messages without timestamps

            processed_messages.append(
                {
                    **msg,
                    "parsed_timestamp": ts,
                    "age_hours": (now_utc - ts).total_seconds() / 3600,
                }
            )
        except Exception as e:
            logger.warning(f"Error parsing timestamp {ts_str}: {e}")
            # Include message with current time as fallback
            processed_messages.append(
                {**msg, "parsed_timestamp": now_utc, "age_hours": 0}
            )

    # If all messages are recent, return all (up to limit)
    if all(msg["age_hours"] <= MESSAGE_FRESHNESS_HOURS for msg in processed_messages):
        return [
            {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"],
            }
            for msg in processed_messages[-20:]
        ]  # Keep last 20 if all fresh

    # Find conversation breaks
    breaks = []
    for i in range(1, len(processed_messages)):
        prev_msg = processed_messages[i - 1]
        curr_msg = processed_messages[i]

        # Calculate gap between messages
        gap = (
            curr_msg["parsed_timestamp"] - prev_msg["parsed_timestamp"]
        ).total_seconds() / 3600

        if gap >= TIME_BREAK_THRESHOLD_HOURS:
            breaks.append(i)
            logger.debug(f"Found conversation break at index {i}, gap: {gap:.1f} hours")

    # If there are breaks, start from the most recent conversation segment
    if breaks:
        # Start from the last break point
        start_index = breaks[-1]
        recent_segment = processed_messages[start_index:]

        # If the recent segment is very stale, limit to fewer messages
        if recent_segment and recent_segment[0]["age_hours"] > MESSAGE_FRESHNESS_HOURS:
            recent_segment = recent_segment[-MAX_STALE_MESSAGES:]
            logger.info(f"Limited stale conversation to {len(recent_segment)} messages")
    else:
        # No major breaks, but check overall freshness
        if (
            processed_messages
            and processed_messages[-1]["age_hours"] > MESSAGE_FRESHNESS_HOURS
        ):
            # Conversation is stale, limit number of messages
            recent_segment = processed_messages[-MAX_STALE_MESSAGES:]
            logger.info(
                f"Conversation is stale, limited to {len(recent_segment)} messages"
            )
        else:
            # Recent conversation, include more context
            recent_segment = processed_messages[
                -20:
            ]  # Include up to 20 recent messages

    # Clean up the returned messages
    result = [
        {"role": msg["role"], "content": msg["content"], "timestamp": msg["timestamp"]}
        for msg in recent_segment
    ]

    logger.info(
        f"Filtered {len(messages)} messages down to {len(result)} based on time gaps"
    )
    return result


def detect_conversation_resumption(
    messages: List[Dict[str, str]],
) -> Tuple[bool, Optional[str]]:
    """
    Detect if this is a conversation resumption after a break and provide context.

    Args:
        messages: List of message dictionaries

    Returns:
        Tuple of (is_resumption, context_hint)
    """
    if len(messages) < 2:
        return False, None

    try:
        # Get the gap between the last two conversation segments
        now_utc = datetime.now(timezone.utc)
        last_msg_ts = datetime.fromisoformat(
            messages[-1]["timestamp"].replace("Z", "+00:00")
        )
        if last_msg_ts.tzinfo is None:
            last_msg_ts = last_msg_ts.replace(tzinfo=timezone.utc)

        gap_hours = (now_utc - last_msg_ts).total_seconds() / 3600

        if gap_hours > TIME_BREAK_THRESHOLD_HOURS:
            local_time = now_utc.astimezone(USER_TZ)

            if gap_hours >= 12:  # More than 12 hours
                if 6 <= local_time.hour <= 11:
                    return True, "morning after a break"
                elif gap_hours >= 20:
                    return True, "resuming after a long break"
                else:
                    return True, "resuming conversation"
            else:
                return True, "continuing after a short break"

    except Exception as e:
        logger.warning(f"Error detecting conversation resumption: {e}")

    return False, None


def clean_dict_for_json(data: dict) -> dict:
    """
    Clean a dictionary for JSON serialization by handling datetime objects.

    Args:
        data: Dictionary that may contain non-serializable objects

    Returns:
        Dictionary safe for JSON serialization
    """
    if isinstance(data, dict):
        return {k: clean_dict_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_dict_for_json(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data


def format_duration(hours: float) -> str:
    """
    Format a duration in hours to a human-readable string.

    Args:
        hours: Duration in hours

    Returns:
        Human-readable duration string
    """
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif hours < 24:
        hours_int = int(hours)
        return f"{hours_int} hour{'s' if hours_int != 1 else ''}"
    else:
        days = int(hours / 24)
        return f"{days} day{'s' if days != 1 else ''}"
