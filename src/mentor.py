"""
Mentor agent class for coaching, delegating memory and LLM logic to separate modules.
"""

from typing import Any
from src.memory import MemoryManager
from src.llm import LLMClient
import logging
from concurrent.futures import ThreadPoolExecutor, Future

logger = logging.getLogger("MentorAgent")
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mentor-bg")

def _log_when_done(fut: Future) -> None:
    """Log exceptions from background memory.store() calls."""
    try:
        fut.result()
    except Exception as e:
        logger.exception("Background memory.store() failed: %s", e)

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

    def stream_reply(self, user_msg: str):
        """
        Yields reply tokens as they arrive; kicks off memory.store() in the background
        once the full reply has been assembled.
        """
        logger.info(f"Streaming reply for: {user_msg!r}")
        mem_text = self.memory.retrieve(user_msg, self.user_id, self.k, self.version)
        chunks = []
        for token in self.llm.chat_stream(user_msg, mem_text):
            chunks.append(token)
            yield token
        full_reply = "".join(chunks).strip()
        fut = _EXECUTOR.submit(
            self.memory.store,
            user_msg,
            full_reply,
            self.user_id,
            self.agent_id,
        )
        fut.add_done_callback(_log_when_done)
        logger.info("Reply streamed; memory.store() dispatched in background")
