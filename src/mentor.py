"""
Mentor agent class for coaching, delegating memory and LLM logic to separate modules.
"""

from typing import Any
from src.memory import MemoryManager
from src.llm import LLMClient
import logging

logger = logging.getLogger("MentorAgent")


class Mentor:
    """
    Mentor agent for coaching, using memory and LLM modules.
    """

    def __init__(
        self,
        memory: MemoryManager,
        llm: LLMClient,
        user_id: str,
        agent_id: str = "mentor",
        k: int = 5,
    ):
        self.memory = memory
        self.llm = llm
        self.user_id = user_id
        self.agent_id = agent_id
        self.k = k
        self.version = "v2"
        logger.info(
            f"Initialized Mentor for user_id={user_id}, agent_id={agent_id}, k={k}"
        )

    def __call__(self, user_msg: str) -> str:
        logger.info(f"Received user message: {user_msg}")
        mem_text = self.memory.retrieve(user_msg, self.user_id, self.k, self.version)
        reply = self.llm.chat(user_msg, mem_text)
        self.memory.store(user_msg, reply, self.user_id, self.agent_id)
        logger.info(f"Generated reply: {reply}")
        return reply
