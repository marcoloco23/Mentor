"""
Application bootstrapping module for the Ted agent.

This module initializes and configures the core components of the Ted application,
including the LLM client and memory manager. It's responsible for setting up
the environment and creating the necessary instances for the agent to function.
"""

import os
import logging
from mem0 import MemoryClient

from src.llm import LLMClient
from src.memory import MemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize the LLM client
llm_client = LLMClient()

# Initialize memory client with environment variable
mem0_api_key = os.getenv("MEM0_API_KEY")
if not mem0_api_key:
    raise ValueError("MEM0_API_KEY environment variable is required")

memory_client = MemoryClient(api_key=mem0_api_key)
memory_manager = MemoryManager(memory_client)

logging.info("Application components initialized successfully")
