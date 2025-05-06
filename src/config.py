"""
Centralized configuration for the Mentor application.

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

# File Paths
LOG_FILE: Final[str] = "data/chatlog.json"

# Agent Configuration
DEFAULT_AGENT_ID: Final[str] = "mentor"
DEFAULT_VERSION: Final[str] = "v2"

# Application Defaults
DEFAULT_USER_ID: Final[str] = "u42"  # Default user ID for CLI interface
MAX_THREAD_WORKERS: Final[int] = 2

# Assistant Profile
ASSISTANT_NAME: Final[str] = "Mentor"
DEFAULT_USER_NAME: Final[str] = "User"
