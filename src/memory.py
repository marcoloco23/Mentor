"""
Encapsulates memory retrieval, storage, and thread management logic for the Mentor agent.
Provides a MemoryManager class for handling user memories and conversation threads.
"""

from mem0 import MemoryClient
from collections import OrderedDict
from datetime import UTC, datetime, timezone
from zoneinfo import ZoneInfo
import re
import logging
from typing import Any, Optional, List, Dict
import json
import os
from threading import Lock

USER_TZ = ZoneInfo("Europe/Berlin")
RECENCY_HALFLIFE_DAYS = 30
_MIN_SIMILARITY = 0.45
_DUPLICATE_REGEX = re.compile(r"\W+")
WINDOW_MESSAGES = 20  # static tail you feed to the LLM
LOG_FILE = "data/chatlog.json"
_log_lock = Lock()

logger = logging.getLogger("MentorMemory")


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

        logger.info(f"Retrieving memories for query: {query!r}")
        raw_hits = self.memory.search(
            query,
            version=version,
            user_id=user_id,
            keyword_search=True,
            rerank=True,
            filter_memories=False,
            top_k=k * 3,
        )
        now_utc = datetime.now(timezone.utc)

        def score(hit: dict) -> float:
            sim = hit["score"]
            if sim < _MIN_SIMILARITY:
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
        logger.info("Storing conversation to memory")
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

    def fetch_recent(
        self, user_id: str, k: int = WINDOW_MESSAGES
    ) -> List[Dict[str, str]]:
        """Return the *k* most-recent messages (oldest first)."""
        data = self._load_log()
        tail = data.get(user_id, [])[-k:]
        return tail
