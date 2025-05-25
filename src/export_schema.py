"""
Defines the schema for exporting Ted memory records to Mem0's /v1/exports endpoint.
Provides a TedMemory Pydantic model and a JSON schema for export.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TedMemory(BaseModel):
    """
    Pydantic model representing the shape of a single memory record for export.

    Attributes:
        id (str): Unique identifier for the memory record.
        user_id (str): Identifier for the user who owns the memory.
        memory (str): Canonical fact or statement.
        created_at (datetime): Timestamp when the memory was created.
        updated_at (datetime): Timestamp when the memory was last updated.
        categories (Optional[List[str]]): Optional list of categories for the memory.
        metadata (Optional[Dict[str, Any]]): Optional metadata dictionary.
        score (Optional[float]): Optional similarity/retrieval score if returned by Mem0 search.
    """

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
json_schema: Dict[str, Any] = TedMemory.model_json_schema()
