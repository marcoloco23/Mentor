"""
Mentor - An AI coaching system with long-term memory.

This package provides a powerful AI mentoring system that leverages LLMs
and long-term memory to provide personalized coaching.
"""

from src.mentor import Mentor
from src.memory import MemoryManager
from src.llm import LLMClient
from src.boot import memory_manager, llm_client

__version__ = "0.1.0"
__all__ = ["Mentor", "MemoryManager", "LLMClient", "memory_manager", "llm_client"]
