"""
Ted – A lifelong AI companion with long-term memory.

This package provides an empathetic, insightful companion that leverages LLMs
and persistent memory to offer personalized guidance.
"""

from src.ted import Ted
from src.memory import MemoryManager
from src.llm import LLMClient
from src.boot import memory_manager, llm_client

__version__ = "0.1.0"
__all__ = ["Ted", "MemoryManager", "LLMClient", "memory_manager", "llm_client"]
