from typing import Literal

from pydantic import BaseModel, Field


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=4000)


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1)
    # Prior turns for follow-up questions (most recent last). Capped server-side.
    history: list[Turn] = Field(default_factory=list)


class SourceChunk(BaseModel):
    chunk_id: str
    doc_id: str
    similarity: float
    text_preview: str


class QueryResponse(BaseModel):
    answer: str
    session_id: str
    cache_hit: bool
    latency_ms: int
    chunk_count: int
    pii_found: bool
    pii_types: list[str]
    llm_provider: str
    source_chunks: list[SourceChunk]
    tokens_saved_pct: float | None = None
