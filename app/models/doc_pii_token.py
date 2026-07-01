from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DocPIIToken(Base):
    """Mapa de datos personales de un DOCUMENTO: marcador → valor original.

    En la ingesta el documento se enmascara (RUT/correo/teléfono → [RUT_1] …) antes
    de guardarse en el vector store. Este mapa se guarda aquí, en la base relacional
    (nunca en el vector store), para poder restaurar los valores reales en la
    respuesta al usuario. La IA nunca ve estos valores: solo marcadores.
    """

    __tablename__ = "doc_pii_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # Marcador legible dentro del documento, p.ej. "RUT_1". Único por (doc_id, token).
    token: Mapped[str] = mapped_column(String(40), nullable=False)
    original_value: Mapped[str] = mapped_column(Text, nullable=False)
    pii_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Null = sin expiración (documentos de cuentas). Para subidas anónimas se fija
    # un TTL igual al de los chunks del documento.
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_docpii_doc", "doc_id"),
        Index("idx_docpii_doc_token", "doc_id", "token", unique=True),
    )
