"""
Encapsulates LLM chat logic for the Ted agent.
Provides an LLMClient class for generating and streaming chat completions using an LLM backend.
"""

from openai import OpenAI
import logging
from typing import Any, Optional, List, Dict

from src.config import LLM_MODEL, DEFAULT_TEMPERATURE, ASSISTANT_NAME, DEFAULT_USER_NAME
from src.prompts import SYSTEM_TEMPLATE


logger = logging.getLogger("TedLLM")


class LLMClient:
    """
    Handles LLM chat completions for the Ted agent.

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
        assistant_name: str = ASSISTANT_NAME,
        user_name: str = DEFAULT_USER_NAME,
        thread: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate a reply using the LLM, given the user message, memory text, and optional thread history.

        Args:
            user_msg (str): The user's message.
            mem_text (str): The formatted memory text to provide as context.
            assistant_name (str): The name of the assistant.
            user_name (str): The name of the user.
            thread (Optional[List[Dict[str, Any]]], optional): Optional conversation thread history.

        Returns:
            str: The assistant's reply.
        """
        logger.info("Invoking LLM chat completion")
        prompt = SYSTEM_TEMPLATE.format(
            memories=mem_text or "[none]",
            assistant_name=assistant_name,
            user_name=user_name,
        )
        messages = [{"role": "system", "content": prompt}]
        if thread:
            messages.extend(thread)
        messages.append({"role": "user", "content": user_msg})
        resp = self.llm.chat.completions.create(
            model=LLM_MODEL, messages=messages, temperature=DEFAULT_TEMPERATURE
        )
        logger.info("LLM chat completion received")
        return resp.choices[0].message.content.strip()

    def chat_stream(
        self,
        user_msg: str,
        mem_text: str,
        assistant_name: str = ASSISTANT_NAME,
        user_name: str = DEFAULT_USER_NAME,
        thread: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Stream a reply using the LLM, yielding tokens as they arrive. Optionally include thread history.

        Args:
            user_msg (str): The user's message.
            mem_text (str): The formatted memory text to provide as context.
            assistant_name (str): The name of the assistant.
            user_name (str): The name of the user.
            thread (Optional[List[Dict[str, Any]]], optional): Optional conversation thread history.

        Yields:
            str: The next token in the assistant's reply.
        """
        logger.info("Invoking LLM chat completion (streaming)")
        prompt = SYSTEM_TEMPLATE.format(
            memories=mem_text or "[none]",
            assistant_name=assistant_name,
            user_name=user_name,
        )
        messages = [{"role": "system", "content": prompt}]
        if thread:
            messages.extend(thread)
        messages.append({"role": "user", "content": user_msg})

        logger.info("Streaming LLM chat completion")
        logger.debug(messages)

        stream = self.llm.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=DEFAULT_TEMPERATURE,
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
