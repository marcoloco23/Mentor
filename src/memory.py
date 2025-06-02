"""
Encapsulates memory retrieval, storage, and thread management logic for the Ted agent.
Provides a MemoryManager class for handling user memories and conversations.
"""

from mem0 import MemoryClient
from collections import OrderedDict
from datetime import UTC, datetime, timezone
import re
import logging
from typing import Any, Optional, List, Dict
import json
import os
from threading import Lock

from src.config import (
    USER_TZ,
    RECENCY_HALFLIFE_DAYS,
    MIN_SIMILARITY_THRESHOLD,
    WINDOW_MESSAGES,
    LOG_FILE,
)
from src.utils import filter_messages_by_time_gaps

_DUPLICATE_REGEX = re.compile(r"\W+")
_log_lock = Lock()

logger = logging.getLogger("TedMemory")


class MemoryManager:
    """
    Handles retrieval and storage of user memories, as well as thread management.

    Attributes:
        memory (MemoryClient): The underlying memory client for storage and retrieval.
    """

    def __init__(self, memory_client: MemoryClient):
        """
        Initialize the MemoryManager.

        Args:
            memory_client (MemoryClient): The memory client instance to use for storage and retrieval.
        """
        self.memory = memory_client

    def retrieve(
        self, query: str, user_id: str, k: Optional[int] = 5, version: str = "v2"
    ) -> str:
        """
        Return memories grouped by local date with time-stamped bullets.

        Args:
            query (str): The search query for memory retrieval.
            user_id (str): The user identifier.
            k (Optional[int], optional): Number of memories to retrieve. Defaults to 5.
            version (str, optional): Version identifier for memory retrieval. Defaults to 'v2'.

        Returns:
            str: Formatted string of retrieved memories grouped by date.
        """
        query = (query or "").strip()
        if not query:
            logger.debug("Blank query – skipping memory retrieval")
            return ""

        logger.info(f"Retrieving memories for query: {query!r} and user_id: {user_id}")

        # For v2, we need to use proper filters structure as per documentation
        if version == "v2":
            # Create a proper filter structure to filter by user_id
            filters = {"AND": [{"user_id": user_id}]}

            raw_hits = self.memory.search(
                query,
                version=version,
                filters=filters,
                keyword_search=False,
                rerank=True,
                filter_memories=False,
                top_k=k * 3,
            )
        else:
            # For v1, keep the old format
            raw_hits = self.memory.search(
                query,
                version=version,
                user_id=user_id,
                keyword_search=False,
                rerank=True,
                filter_memories=False,
                top_k=k * 3,
            )

        logger.info(f"Retrieved {len(raw_hits)} raw hits from memory search")
        now_utc = datetime.now(timezone.utc)

        def score(hit: dict) -> float:
            sim = hit["score"]
            if sim < MIN_SIMILARITY_THRESHOLD:
                return 0.0
            ts_iso = hit.get("metadata", {}).get("ts") or hit["created_at"]
            try:
                ts = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                ts = now_utc
            age_days = (now_utc - ts.astimezone(timezone.utc)).days
            recency = 0.5 ** (age_days / RECENCY_HALFLIFE_DAYS)
            return sim * recency

        ranked = sorted(raw_hits, key=score, reverse=True)
        picked: "OrderedDict[str, dict]" = OrderedDict()
        for hit in ranked:
            if len(picked) >= k:
                break
            sig = _DUPLICATE_REGEX.sub("", hit["memory"].lower())
            if sig and sig not in picked:
                picked[sig] = hit

        grouped: "OrderedDict[str, list[tuple[str,str]]]" = OrderedDict()
        for hit in picked.values():
            ts_iso = hit.get("metadata", {}).get("ts") or hit["created_at"]
            ts = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            local_ts = ts.astimezone(USER_TZ)
            date_hdr = local_ts.strftime("%Y-%m-%d (%a)")
            time_str = local_ts.strftime("%H:%M")
            grouped.setdefault(date_hdr, []).append((time_str, hit["memory"].strip()))

        lines: list[str] = []
        for date_hdr, items in grouped.items():
            lines.append(date_hdr)
            for tm, txt in items:
                lines.append(f"  • {tm} – {txt}")

        return "\n".join(lines)

    def store(
        self, user_msg: str, assistant_msg: str, user_id: str, agent_id: str
    ) -> None:
        """
        Store the conversation to memory.

        Args:
            user_msg (str): The user's message.
            assistant_msg (str): The assistant's reply.
            user_id (str): The user identifier.
            agent_id (str): The agent identifier.
        """
        logger.info(
            f"Storing conversation to memory for user_id: {user_id}, agent_id: {agent_id}"
        )

        try:
            self.memory.add(
                [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg},
                ],
                user_id=user_id,
                agent_id=agent_id,
                metadata={"ts": datetime.now(UTC).isoformat()},
            )
            logger.info("Conversation stored successfully")
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            raise

    # ──────────────────────────────────────────────────────────
    #  Single-log storage  (one list per user_id)              │
    # ──────────────────────────────────────────────────────────
    def _load_log(self) -> dict:
        if not os.path.exists(LOG_FILE):
            return {}
        with _log_lock, open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}

    def _save_log(self, data: dict) -> None:
        with _log_lock, open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def append_message(
        self,
        user_id: str,
        role: str,
        content: str,
        ts: Optional[str] = None,
    ) -> None:
        """Store one message in the single-user log."""
        logger.info(f"Appending message for user_id: {user_id}, role: {role}")
        data = self._load_log()
        data.setdefault(user_id, []).append(
            {
                "role": role,
                "content": content,
                "timestamp": ts or datetime.now(UTC).isoformat(),
            }
        )
        # keep everything; we'll slice later
        self._save_log(data)
        logger.debug(f"Message appended successfully for user_id: {user_id}")

    def fetch_recent(
        self, 
        user_id: str, 
        k: int = WINDOW_MESSAGES, 
        use_time_filtering: bool = True,
        offset: int = 0,
        limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Return the most recent messages, optionally filtered by time gaps.

        Args:
            user_id: The user identifier
            k: Maximum number of messages to return (when not using pagination)
            use_time_filtering: Whether to apply smart time-based filtering
            offset: Number of messages to skip from the end (for pagination)
            limit: Maximum number of messages to return (overrides k when provided)
        """
        # Use limit if provided, otherwise fall back to k
        actual_limit = limit if limit is not None else k
        
        logger.info(
            f"Fetching recent messages for user_id: {user_id}, k={k}, offset={offset}, "
            f"limit={actual_limit}, time_filtering={use_time_filtering}"
        )
        data = self._load_log()
        messages = data.get(user_id, [])

        if not messages:
            logger.info(f"No messages found for user_id: {user_id}")
            return []

        # When using pagination (offset > 0), we want to get older messages
        # Calculate the slice indices for pagination
        total_messages = len(messages)
        
        if offset >= total_messages:
            logger.info(f"Offset {offset} >= total messages {total_messages}, returning empty")
            return []
        
        # For pagination, we slice from the end backwards
        start_index = max(0, total_messages - offset - actual_limit)
        end_index = total_messages - offset
        
        # Get the requested slice
        raw_messages = messages[start_index:end_index]

        # Apply time-based filtering if enabled and not using pagination
        # When using pagination, we typically want all messages in the range
        if use_time_filtering and offset == 0:
            filtered_messages = filter_messages_by_time_gaps(raw_messages)
            logger.info(
                f"Time filtering: {len(raw_messages)} -> {len(filtered_messages)} messages"
            )
        else:
            filtered_messages = raw_messages
            logger.info(
                f"No time filtering applied, using {len(filtered_messages)} messages"
            )

        result = [
            {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg.get("timestamp", datetime.now(UTC).isoformat()),
            }
            for msg in filtered_messages
        ]
        return result

    def format_recent_messages(self, user_id: str, k: int = WINDOW_MESSAGES) -> str:
        """
        Format recent messages for inclusion in the system prompt.

        Note: This method is deprecated as we now pass recent messages directly in the thread parameter.
        Kept for backward compatibility.

        Args:
            user_id (str): The user identifier.
            k (int, optional): Number of messages to include. Defaults to WINDOW_MESSAGES.

        Returns:
            str: Formatted string of recent messages.
        """
        logger.warning("format_recent_messages is deprecated, use fetch_recent instead")
        messages = self._load_log().get(user_id, [])[-k:]
        if not messages:
            return "[none]"

        formatted_messages = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Ted"
            formatted_messages.append(f"{role}: {msg['content']}")

        return "\n".join(formatted_messages)
