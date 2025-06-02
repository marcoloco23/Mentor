"""
Centralized configuration for the Ted application.

This module contains all configuration parameters used across the application,
including LLM settings, memory parameters, and application defaults.
"""

import os
from zoneinfo import ZoneInfo
from typing import Final


# LLM Configuration
LLM_MODEL: Final[str] = "gpt-4.1"
DEFAULT_TEMPERATURE: Final[float] = 0.7

# Memory Configuration
USER_TZ: Final[ZoneInfo] = ZoneInfo("Europe/Berlin")
RECENCY_HALFLIFE_DAYS: Final[int] = 30
MIN_SIMILARITY_THRESHOLD: Final[float] = 0.45
DEFAULT_MEMORIES_COUNT: Final[int] = 5
WINDOW_MESSAGES: Final[int] = 20  # number of recent messages to include in context

# Time-based filtering configuration
MESSAGE_FRESHNESS_HOURS: Final[int] = (
    8  # Messages older than this create a "break" in conversation
)
MAX_STALE_MESSAGES: Final[int] = (
    3  # Max messages to include when conversation is "stale"
)
TIME_BREAK_THRESHOLD_HOURS: Final[int] = (
    4  # Hours gap that indicates a conversation break
)

# File Paths
LOG_FILE: Final[str] = "data/chatlog.json"

# Agent Configuration
DEFAULT_AGENT_ID: Final[str] = "ted"
DEFAULT_VERSION: Final[str] = "v2"

# Application Defaults
DEFAULT_USER_ID: Final[str] = "u42"  # Default user ID for CLI interface
MAX_THREAD_WORKERS: Final[int] = 2

# Assistant Profile
ASSISTANT_NAME: Final[str] = "Ted"
DEFAULT_USER_NAME: Final[str] = "User"
