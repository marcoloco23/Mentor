"""
Encapsulates LLM chat logic for the Mentor agent.
Provides an LLMClient class for generating and streaming chat completions using an LLM backend.
"""

from openai import OpenAI
import logging
from typing import Any, Optional, List, Dict

MODEL = "gpt-4.1"
SYSTEM_TEMPLATE = """You are \"Mentor\", a seasoned coach who helps the user grow.
You have access to stored memories:

<memory>
{memories}
</memory>

Rules:
- Ask thoughtful, digging questions when context is sparse.
- Use memories naturally but never reveal them verbatim.
- Be concise and direct – no sugar-coating.
"""

logger = logging.getLogger("MentorLLM")


class LLMClient:
    """
    Handles LLM chat completions for the Mentor agent.

    Attributes:
        llm (OpenAI): The OpenAI client instance for chat completions.
    """

    def __init__(self, llm_client: OpenAI):
        """
        Initialize the LLMClient.

        Args:
            llm_client (OpenAI): The OpenAI client instance.
        """
        self.llm = llm_client

    def chat(
        self,
        user_msg: str,
        mem_text: str,
        thread: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate a reply using the LLM, given the user message, memory text, and optional thread history.

        Args:
            user_msg (str): The user's message.
            mem_text (str): The formatted memory text to provide as context.
            thread (Optional[List[Dict[str, Any]]], optional): Optional conversation thread history.

        Returns:
            str: The assistant's reply.
        """
        logger.info("Invoking LLM chat completion")
        prompt = SYSTEM_TEMPLATE.format(memories=mem_text)
        messages = [{"role": "system", "content": prompt}]
        if thread:
            messages.extend(thread)
        messages.append({"role": "user", "content": user_msg})
        resp = self.llm.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.7
        )
        logger.info("LLM chat completion received")
        return resp.choices[0].message.content.strip()

    def chat_stream(
        self,
        user_msg: str,
        mem_text: str,
        thread: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Stream a reply using the LLM, yielding tokens as they arrive. Optionally include thread history.

        Args:
            user_msg (str): The user's message.
            mem_text (str): The formatted memory text to provide as context.
            thread (Optional[List[Dict[str, Any]]], optional): Optional conversation thread history.

        Yields:
            str: The next token in the assistant's reply.
        """
        logger.info("Invoking LLM chat completion (streaming)")
        prompt = SYSTEM_TEMPLATE.format(memories=mem_text)
        messages = [{"role": "system", "content": prompt}]
        if thread:
            messages.extend(thread)
        messages.append({"role": "user", "content": user_msg})
        stream = self.llm.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.7, stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
