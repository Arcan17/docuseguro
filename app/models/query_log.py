from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Index, Integer, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class QueryLog(Base):
    __tablename__ = "query_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    query_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    chunk_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    original_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    compressed_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    llm_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pii_found: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pii_types: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (Index("idx_log_created", "created_at"),)
