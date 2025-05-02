# export_schema.py  – build a schema dict for Mem0’s /v1/exports endpoint
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MentorMemory(BaseModel):
    """Shape of a single memory record we want in the CSV/JSON export."""

    id: str
    user_id: str
    memory: str = Field(..., description="Canonical fact or statement")
    created_at: datetime
    updated_at: datetime
    categories: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    score: Optional[float] = Field(
        None, description="Similarity/retrieval score if returned by Mem0 search"
    )


# 👉 the dict you pass to `create_memory_export(schema=...)`
json_schema: Dict[str, Any] = MentorMemory.model_json_schema()
