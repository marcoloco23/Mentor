"""
Mentor agent class for coaching, delegating memory and LLM logic to separate modules.
"""

from typing import Any, Optional
from src.memory import MemoryManager
from src.llm import LLMClient
import logging
from concurrent.futures import ThreadPoolExecutor, Future
import uuid

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

    def __call__(self, user_msg: str, thread_id: Optional[str] = None) -> str:
        """
        Generate a reply and store the conversation in memory and thread history.
        If thread_id is not provided, a new thread is started.
        """
        logger.info(f"Received user message: {user_msg}")
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        mem_text = self.memory.retrieve(user_msg, self.user_id, self.k, self.version)
        thread = self.memory.get_thread(thread_id) or []
        reply = self.llm.chat(user_msg, mem_text, thread=thread)
        self.memory.store(user_msg, reply, self.user_id, self.agent_id)
        self.memory.append_to_thread(thread_id, self.user_id, "user", user_msg)
        self.memory.append_to_thread(thread_id, self.user_id, "assistant", reply)
        logger.info(f"Generated reply: {reply}")
        return reply

    def stream_reply(self, user_msg: str, thread_id: Optional[str] = None):
        """
        Yields reply tokens as they arrive; stores conversation in thread history.
        If thread_id is not provided, a new thread is started.
        """
        logger.info(f"Streaming reply for: {user_msg!r}")
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        mem_text = self.memory.retrieve(user_msg, self.user_id, self.k, self.version)
        thread = self.memory.get_thread(thread_id) or []
        chunks = []
        for token in self.llm.chat_stream(user_msg, mem_text, thread=thread):
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
        self.memory.append_to_thread(thread_id, self.user_id, "user", user_msg)
        self.memory.append_to_thread(thread_id, self.user_id, "assistant", full_reply)
        logger.info("Reply streamed; memory.store() dispatched in background")
