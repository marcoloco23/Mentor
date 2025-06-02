#!/usr/bin/env python3
"""
Test script to demonstrate the new time-aware features and smart message filtering.
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Add src to path
sys.path.insert(0, "src")

from src.utils import (
    get_time_context,
    filter_messages_by_time_gaps,
    detect_conversation_resumption,
    format_duration,
)
from src.config import USER_TZ


def test_time_context():
    """Test the time context generation."""
    print("=== Time Context Test ===")
    context = get_time_context()
    print(f"Current time context: {context}")
    print()


def test_message_filtering():
    """Test the message filtering with various time gaps."""
    print("=== Message Filtering Test ===")

    now = datetime.now(timezone.utc)

    # Create test messages with different time gaps
    messages = [
        {
            "role": "user",
            "content": "Good morning!",
            "timestamp": (now - timedelta(hours=10)).isoformat(),
        },
        {
            "role": "assistant",
            "content": "Good morning! How are you today?",
            "timestamp": (now - timedelta(hours=10)).isoformat(),
        },
        {
            "role": "user",
            "content": "I'm doing well, thanks",
            "timestamp": (now - timedelta(hours=9, minutes=58)).isoformat(),
        },
        {
            "role": "assistant",
            "content": "That's great to hear!",
            "timestamp": (now - timedelta(hours=9, minutes=57)).isoformat(),
        },
        # Big gap here (sleep/work)
        {
            "role": "user",
            "content": "Hey, I'm back",
            "timestamp": (now - timedelta(minutes=30)).isoformat(),
        },
        {
            "role": "assistant",
            "content": "Welcome back! How was your day?",
            "timestamp": (now - timedelta(minutes=29)).isoformat(),
        },
        {
            "role": "user",
            "content": "It was good, but I'm tired",
            "timestamp": (now - timedelta(minutes=5)).isoformat(),
        },
    ]

    print(f"Original messages: {len(messages)}")
    for i, msg in enumerate(messages):
        local_time = datetime.fromisoformat(
            msg["timestamp"].replace("Z", "+00:00")
        ).astimezone(USER_TZ)
        print(
            f"  {i+1}. [{local_time.strftime('%H:%M')}] {msg['role']}: {msg['content']}"
        )

    print()

    # Test filtering
    filtered = filter_messages_by_time_gaps(messages)
    print(f"Filtered messages: {len(filtered)}")
    for i, msg in enumerate(filtered):
        local_time = datetime.fromisoformat(
            msg["timestamp"].replace("Z", "+00:00")
        ).astimezone(USER_TZ)
        print(
            f"  {i+1}. [{local_time.strftime('%H:%M')}] {msg['role']}: {msg['content']}"
        )

    print()


def test_conversation_resumption():
    """Test conversation resumption detection."""
    print("=== Conversation Resumption Test ===")

    now = datetime.now(timezone.utc)

    # Test with recent conversation
    recent_messages = [
        {
            "role": "user",
            "content": "Hello",
            "timestamp": (now - timedelta(minutes=10)).isoformat(),
        }
    ]

    is_resumption, hint = detect_conversation_resumption(recent_messages)
    print(f"Recent conversation: is_resumption={is_resumption}, hint={hint}")

    # Test with old conversation (resumption)
    old_messages = [
        {
            "role": "user",
            "content": "Good night",
            "timestamp": (now - timedelta(hours=8)).isoformat(),
        }
    ]

    is_resumption, hint = detect_conversation_resumption(old_messages)
    print(f"Old conversation: is_resumption={is_resumption}, hint={hint}")

    print()


def test_duration_formatting():
    """Test duration formatting."""
    print("=== Duration Formatting Test ===")

    test_durations = [0.5, 1.5, 3.0, 12.0, 25.0, 72.0]

    for hours in test_durations:
        formatted = format_duration(hours)
        print(f"  {hours} hours -> {formatted}")

    print()


if __name__ == "__main__":
    print("Testing Ted's Time-Aware Features")
    print("=" * 50)
    print()

    test_time_context()
    test_message_filtering()
    test_conversation_resumption()
    test_duration_formatting()

    print("All tests completed!")
