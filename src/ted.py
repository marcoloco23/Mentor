"""
Ted agent class — lifelong companion and confidant, delegating memory and LLM logic to separate modules.
"""

from typing import Any, Optional
from src.memory import MemoryManager
from src.llm import LLMClient
import logging
from concurrent.futures import ThreadPoolExecutor, Future
import uuid

from src.config import (
    DEFAULT_AGENT_ID,
    DEFAULT_MEMORIES_COUNT,
    DEFAULT_VERSION,
    MAX_THREAD_WORKERS,
    ASSISTANT_NAME,
    DEFAULT_USER_NAME,
)

logger = logging.getLogger("TedAgent")
_EXECUTOR = ThreadPoolExecutor(
    max_workers=MAX_THREAD_WORKERS, thread_name_prefix="ted-bg"
)


def _log_when_done(fut: Future) -> None:
    """Log exceptions from background memory.store() calls."""
    try:
        fut.result()
    except Exception as e:
        logger.exception("Background memory.store() failed: %s", e)


class Ted:
    """
    Ted agent – a lifelong companion and confidant, using memory and LLM modules.

    Attributes:
        memory (MemoryManager): The memory manager instance for retrieval and storage.
        llm (LLMClient): The LLM client for generating responses.
        user_id (str): The user identifier.
        agent_id (str): The agent identifier.
        k (int): Number of memories to retrieve.
        version (str): Version identifier for memory retrieval.
        assistant_name (str): Name of the assistant.
        user_name (str): Name of the user.
    """

    def __init__(
        self,
        memory: MemoryManager,
        llm: LLMClient,
        user_id: str,
        agent_id: str = DEFAULT_AGENT_ID,
        k: int = DEFAULT_MEMORIES_COUNT,
        assistant_name: str = ASSISTANT_NAME,
        user_name: str = DEFAULT_USER_NAME,
        version: str = DEFAULT_VERSION,
    ):
        """
        Initialize the Ted agent.

        Args:
            memory (MemoryManager): The memory manager instance.
            llm (LLMClient): The LLM client instance.
            user_id (str): The user identifier.
            agent_id (str, optional): The agent identifier. Defaults to DEFAULT_AGENT_ID.
            k (int, optional): Number of memories to retrieve. Defaults to DEFAULT_MEMORIES_COUNT.
            assistant_name (str, optional): Name of the assistant. Defaults to ASSISTANT_NAME.
            user_name (str, optional): Name of the user. Defaults to DEFAULT_USER_NAME.
            version (str, optional): Version identifier for memory retrieval. Defaults to DEFAULT_VERSION.
        """
        self.memory = memory
        self.llm = llm
        self.user_id = user_id
        # Ensure each user gets a unique and stable agent_id so that memories are not shared across users.
        # If the caller provided a custom agent_id we respect it. When the caller uses the default placeholder
        # (or omits the parameter entirely), we derive a deterministic identifier from the user_id so that
        # the same user keeps the same "Ted" across sessions while different users have isolated memories.
        #
        # Example: user_id="alice" → agent_id="ted-alice"
        if agent_id is None or agent_id == DEFAULT_AGENT_ID:
            self.agent_id = f"{DEFAULT_AGENT_ID}-{user_id}"
        else:
            self.agent_id = agent_id
        self.k = k
        self.version = version
        self.assistant_name = assistant_name
        self.user_name = user_name
        logger.info(
            f"Initialized Ted for user_id={user_id}, agent_id={self.agent_id}, k={k}"
        )

    def __call__(self, user_msg: str) -> str:
        """
        Generate a reply and store the conversation in memory.

        Args:
            user_msg (str): The user's message.

        Returns:
            str: The assistant's reply.
        """
        logger.info(f"Received user message: {user_msg}")

        # Retrieve memories and format recent messages
        mem_text = self.memory.retrieve(user_msg, self.user_id, self.k, self.version)
        recent_messages = self.memory.fetch_recent(self.user_id)

        # Filter out timestamps for LLM consumption
        llm_messages = [
            {"role": msg["role"], "content": msg["content"]} for msg in recent_messages
        ]

        # Generate reply
        reply = self.llm.chat(
            user_msg=user_msg,
            mem_text=mem_text,
            assistant_name=self.assistant_name,
            user_name=self.user_name,
            thread=llm_messages,
        )

        # Store conversation
        self.memory.store(user_msg, reply, self.user_id, self.agent_id)
        self.memory.append_message(self.user_id, "user", user_msg)
        self.memory.append_message(self.user_id, "assistant", reply)

        logger.info(f"Generated reply: {reply}")
        return reply

    def stream_reply(self, user_msg: str):
        """
        Yield reply tokens as they arrive and store the conversation in memory.

        Args:
            user_msg (str): The user's message.

        Yields:
            str: The next token in the assistant's reply.
        """
        logger.info(f"Streaming reply for: {user_msg!r}")

        # Retrieve memories and format recent messages
        mem_text = self.memory.retrieve(user_msg, self.user_id, self.k, self.version)
        recent_messages = self.memory.fetch_recent(self.user_id)

        # Filter out timestamps for LLM consumption
        llm_messages = [
            {"role": msg["role"], "content": msg["content"]} for msg in recent_messages
        ]

        # Stream reply
        chunks = []
        for token in self.llm.chat_stream(
            user_msg=user_msg,
            mem_text=mem_text,
            assistant_name=self.assistant_name,
            user_name=self.user_name,
            thread=llm_messages,
        ):
            chunks.append(token)
            yield token

        # Store conversation
        full_reply = "".join(chunks).strip()
        fut = _EXECUTOR.submit(
            self.memory.store,
            user_msg,
            full_reply,
            self.user_id,
            self.agent_id,
        )
        fut.add_done_callback(_log_when_done)
        self.memory.append_message(self.user_id, "user", user_msg)
        self.memory.append_message(self.user_id, "assistant", full_reply)

        logger.info("Reply streamed; memory.store() dispatched in background")
