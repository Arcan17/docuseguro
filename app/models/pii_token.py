from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PIIToken(Base):
    __tablename__ = "pii_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    token: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    original_value: Mapped[str] = mapped_column(Text, nullable=False)
    pii_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_pii_session", "session_id"),
        Index("idx_pii_token", "token"),
    )
