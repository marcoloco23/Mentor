"""
Encapsulates memory retrieval and storage logic for the Mentor agent.
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
THREADS_FILE = "threads.json"
_threads_lock = Lock()

logger = logging.getLogger("MentorMemory")


class MemoryManager:
    """
    Handles retrieval and storage of user memories.
    """

    def __init__(self, memory_client: MemoryClient):
        self.memory = memory_client

    def retrieve(
        self, query: str, user_id: str, k: Optional[int] = 5, version: str = "v2"
    ) -> str:
        """
        Return memories grouped by local date with time-stamped bullets.
        If *query* is empty or only whitespace, no retrieval is attempted and an empty
        string is returned. This protects against Mem0 400-errors on blank queries.
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

    def _load_threads(self) -> dict:
        """
        Load all threads from the local JSON file.
        """
        if not os.path.exists(THREADS_FILE):
            return {}
        with _threads_lock, open(THREADS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}

    def _save_threads(self, threads: dict) -> None:
        """
        Save all threads to the local JSON file.
        """
        with _threads_lock, open(THREADS_FILE, "w", encoding="utf-8") as f:
            json.dump(threads, f, ensure_ascii=False, indent=2)

    def append_to_thread(
        self,
        thread_id: str,
        user_id: str,
        role: str,
        content: str,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Append a message to a thread, creating the thread if it does not exist.
        """
        threads = self._load_threads()
        if thread_id not in threads:
            # The first user message becomes the provisional title
            title = content.strip()[:60] if role == "user" else "Conversation"
            threads[thread_id] = {"user_id": user_id, "messages": [], "title": title}
        threads[thread_id]["messages"].append(
            {
                "role": role,
                "content": content,
                "timestamp": timestamp or datetime.now(UTC).isoformat(),
            }
        )
        self._save_threads(threads)

    def get_thread(self, thread_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve all messages in a thread by thread_id.
        """
        threads = self._load_threads()
        thread = threads.get(thread_id)
        if thread:
            return thread["messages"]
        return None

    def list_threads(self, user_id: str) -> List[Dict[str, str]]:
        """
        Return a list of dicts with ``id`` and ``title`` for all threads that
        belong to *user_id*.
        """
        threads = self._load_threads()
        out: list[dict[str, str]] = []
        for tid, t in threads.items():
            if t.get("user_id") == user_id:
                out.append({"id": tid, "title": t.get("title", tid[:8])})
        # show most-recent threads first (based on last message timestamp)
        out.sort(key=lambda x: self.get_thread(x["id"])[-1]["timestamp"], reverse=True)  # type: ignore[arg-type]
        return out

    def rename_thread(self, thread_id: str, user_id: str, new_title: str) -> bool:
        """
        Rename an existing thread. Returns *True* when successful.
        """
        new_title = new_title.strip()
        if not new_title:
            return False
        threads = self._load_threads()
        if thread_id in threads and threads[thread_id].get("user_id") == user_id:
            threads[thread_id]["title"] = new_title[:60]
            self._save_threads(threads)
            return True
        return False
