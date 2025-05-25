"""
Initializes and wires up the core dependencies for the Ted agent, including memory and LLM clients.
This module is intended to be imported by entry points to provide ready-to-use, preconfigured components.
"""

from mem0 import MemoryClient
from openai import OpenAI
import os
import dotenv
import logging

from src.memory import MemoryManager
from src.llm import LLMClient

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("TedBoot")

# Initialize API clients
mem0 = MemoryClient(os.environ["MEM0_API_KEY"])
logger.info("Initialized MemoryClient (mem0)")

openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
logger.info("Initialized OpenAI client")

# Create and export core components
memory_manager = MemoryManager(mem0)
llm_client = LLMClient(openai)
