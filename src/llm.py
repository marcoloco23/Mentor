"""
Encapsulates LLM chat logic for the Mentor agent.
"""

from openai import OpenAI
import logging
from typing import Any, Optional, List, Dict

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
    """

    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client

    def chat(
        self,
        user_msg: str,
        mem_text: str,
        thread: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate a reply using the LLM, given the user message, memory text, and optional thread history.
        """
        logger.info("Invoking LLM chat completion")
        prompt = SYSTEM_TEMPLATE.format(memories=mem_text)
        messages = [{"role": "system", "content": prompt}]
        if thread:
            messages.extend(thread)
        messages.append({"role": "user", "content": user_msg})
        resp = self.llm.chat.completions.create(
            model="gpt-4o-mini", messages=messages, temperature=0.7
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
        """
        logger.info("Invoking LLM chat completion (streaming)")
        prompt = SYSTEM_TEMPLATE.format(memories=mem_text)
        messages = [{"role": "system", "content": prompt}]
        if thread:
            messages.extend(thread)
        messages.append({"role": "user", "content": user_msg})
        stream = self.llm.chat.completions.create(
            model="gpt-4o-mini", messages=messages, temperature=0.7, stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
