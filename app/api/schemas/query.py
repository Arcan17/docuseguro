from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1)


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
