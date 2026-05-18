from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class QueryCache(Base):
    __tablename__ = "query_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cache_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_cache_key", "cache_key"),
        Index("idx_cache_expires", "expires_at"),
    )
