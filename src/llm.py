"""
OpenAI LLM client for Ted. Handles chat completions and streaming responses.
"""

import os
import logging
from typing import List, Dict, Any, Iterator
from openai import OpenAI

from .prompts import SYSTEM_TEMPLATE
from .config import LLM_MODEL, DEFAULT_TEMPERATURE
from .utils import get_time_context, detect_conversation_resumption

logger = logging.getLogger("TedLLM")


class LLMClient:
    """
    OpenAI LLM client wrapper that handles chat completions for the Ted agent.

    This class manages interactions with OpenAI's chat completion API, including
    both standard and streaming responses. It formats prompts according to Ted's
    personality and includes time-aware context.

    Attributes:
        client (OpenAI): The OpenAI client instance.
        model (str): The model name to use for completions.
        temperature (float): The temperature setting for response generation.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = LLM_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
    ):
        """
        Initialize the LLM client.

        Args:
            api_key (str | None, optional): OpenAI API key. If None, will use environment variable.
            model (str, optional): Model name. Defaults to LLM_MODEL.
            temperature (float, optional): Temperature for response generation. Defaults to DEFAULT_TEMPERATURE.
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature
        logger.info(
            f"Initialized LLM client with model={model}, temperature={temperature}"
        )

    def _format_system_prompt(
        self,
        mem_text: str,
        assistant_name: str,
        user_name: str,
        thread: List[Dict[str, str]] | None = None,
    ) -> str:
        """
        Format the system prompt with memories, time context, and conversation awareness.

        Args:
            mem_text (str): Formatted memory text to include.
            assistant_name (str): Name of the assistant.
            user_name (str): Name of the user.
            thread (List[Dict[str, str]] | None): Recent message thread for context detection.

        Returns:
            str: The formatted system prompt.
        """
        # Get current time context
        time_context = get_time_context()

        # Detect conversation resumption and build context
        conversation_context = ""
        if thread and len(thread) > 0:
            is_resumption, resumption_hint = detect_conversation_resumption(thread)
            if is_resumption and resumption_hint:
                conversation_context = f"<conversation_context>\nNote: This appears to be {resumption_hint}. Consider acknowledging this naturally if appropriate.\n</conversation_context>"

        # Format the complete system prompt
        return SYSTEM_TEMPLATE.format(
            assistant_name=assistant_name,
            user_name=user_name,
            memories=mem_text or "[no relevant memories found]",
            time_context=time_context,
            conversation_context=conversation_context,
        )

    def chat(
        self,
        user_msg: str,
        mem_text: str = "",
        assistant_name: str = "Ted",
        user_name: str = "User",
        thread: List[Dict[str, str]] | None = None,
    ) -> str:
        """
        Generate a single chat completion response.

        Args:
            user_msg (str): The user's message.
            mem_text (str, optional): Memory context. Defaults to "".
            assistant_name (str, optional): Assistant's name. Defaults to "Ted".
            user_name (str, optional): User's name. Defaults to "User".
            thread (List[Dict[str, str]] | None, optional): Recent message history. Defaults to None.

        Returns:
            str: The assistant's response.
        """
        logger.info(f"Generating chat completion for user message: {user_msg[:50]}...")

        # Build the message sequence
        messages = [
            {
                "role": "system",
                "content": self._format_system_prompt(
                    mem_text, assistant_name, user_name, thread
                ),
            }
        ]

        # Add thread messages if provided
        if thread:
            messages.extend(thread)

        # Add the current user message
        messages.append({"role": "user", "content": user_msg})

        logger.debug(f"Sending {len(messages)} messages to OpenAI API")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
            )

            reply = response.choices[0].message.content
            logger.info(f"Received completion: {len(reply)} characters")
            return reply

        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            raise

    def chat_stream(
        self,
        user_msg: str,
        mem_text: str = "",
        assistant_name: str = "Ted",
        user_name: str = "User",
        thread: List[Dict[str, str]] | None = None,
    ) -> Iterator[str]:
        """
        Generate a streaming chat completion response.

        Args:
            user_msg (str): The user's message.
            mem_text (str, optional): Memory context. Defaults to "".
            assistant_name (str, optional): Assistant's name. Defaults to "Ted".
            user_name (str, optional): User's name. Defaults to "User".
            thread (List[Dict[str, str]] | None, optional): Recent message history. Defaults to None.

        Yields:
            str: Each token in the assistant's response.
        """
        logger.info(
            f"Starting streaming completion for user message: {user_msg[:50]}..."
        )

        # Build the message sequence
        messages = [
            {
                "role": "system",
                "content": self._format_system_prompt(
                    mem_text, assistant_name, user_name, thread
                ),
            }
        ]

        # Add thread messages if provided
        if thread:
            messages.extend(thread)

        # Add the current user message
        messages.append({"role": "user", "content": user_msg})

        logger.debug(f"Streaming {len(messages)} messages to OpenAI API")

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                stream=True,
            )

            token_count = 0
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    token_count += 1
                    yield token

            logger.info(f"Streaming completed: {token_count} tokens")

        except Exception as e:
            logger.error(f"Error in streaming completion: {str(e)}")
            raise
