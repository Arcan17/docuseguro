"""PII a nivel de documento (spec 006, P1b).

Conserva el mapa de datos personales de cada documento (que hoy se descartaba en la
ingesta) y, en la consulta, re-etiqueta la PII del documento y de la pregunta a un
único espacio de marcadores de presentación (`[RUT_1]`, `[CORREO_1]`, …) limpio,
legible y sin colisiones entre documentos. La IA solo ve marcadores; los valores
reales se restauran únicamente en la respuesta final.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.doc_pii_token import DocPIIToken
from app.services.privacy.scrubber import TokenMap

logger = get_logger(__name__)

# Marcadores tienen la forma [LABEL_N], p.ej. [RUT_1], [CORREO_2], [TELEFONO_1].
_MARKER_RE = re.compile(r"\[([A-ZÑ]+)_(\d+)\]")


def pii_type_from_marker(marker: str) -> str:
    """Deriva el tipo de PII desde la etiqueta del marcador ("RUT_1" → "rut")."""
    label = marker.split("_", 1)[0]
    return {"RUT": "rut", "CORREO": "email", "TELEFONO": "phone"}.get(label, "ner")


async def persist_doc_map(
    db: AsyncSession,
    doc_id: str,
    token_map: TokenMap,
    expires_at: datetime | None,
) -> None:
    """Guarda el mapa marcador→valor del documento en la base relacional."""
    if not token_map:
        return
    for token, original in token_map.items():
        db.add(
            DocPIIToken(
                doc_id=doc_id,
                token=token,
                original_value=original,
                pii_type=pii_type_from_marker(token),
                expires_at=expires_at,
            )
        )
    try:
        await db.commit()
    except Exception as e:  # pragma: no cover - defensivo
        await db.rollback()
        logger.warning("doc_pii_persist_failed", doc_id=doc_id, error=str(e))


async def load_doc_maps(
    db: AsyncSession, doc_ids: set[str]
) -> dict[str, TokenMap]:
    """Carga los mapas (marcador→original) de los documentos indicados, sin
    incluir los expirados."""
    if not doc_ids:
        return {}
    now = datetime.now(UTC)
    rows = (
        await db.execute(
            select(DocPIIToken).where(DocPIIToken.doc_id.in_(doc_ids))
        )
    ).scalars().all()
    maps: dict[str, TokenMap] = {}
    for r in rows:
        if r.expires_at is not None and r.expires_at <= now:
            continue
        maps.setdefault(r.doc_id, {})[r.token] = r.original_value
    return maps


@dataclass
class Presentation:
    """Resultado del re-etiquetado para una consulta."""

    chunk_texts: list[str]  # textos de chunk con marcadores de presentación
    query_text: str  # consulta con marcadores de presentación
    display_map: TokenMap  # marcador de presentación → valor original (para restaurar)


def build_presentation(
    chunk_texts_with_doc: list[tuple[str, str]],
    doc_maps: dict[str, TokenMap],
    clean_query: str,
    query_map: TokenMap,
) -> Presentation:
    """Re-etiqueta la PII del contexto y la consulta a un espacio único de
    marcadores de presentación, deduplicando por valor original.

    - `chunk_texts_with_doc`: lista de (texto_del_chunk, doc_id).
    - `doc_maps`: por doc_id, el mapa marcador_almacenado→original.
    - `query_map`: mapa marcador→original de la consulta (del scrub de la pregunta).

    Garantiza que el mismo valor real reciba siempre el mismo marcador de
    presentación (aunque venga de la consulta y de un documento a la vez) y que no
    haya dos marcadores iguales con significados distintos.
    """
    display_map: TokenMap = {}
    original_to_pres: dict[str, str] = {}
    counters: dict[str, int] = {}

    def pres_for(original: str, label: str) -> str:
        if original not in original_to_pres:
            counters[label] = counters.get(label, 0) + 1
            marker = f"{label}_{counters[label]}"
            original_to_pres[original] = marker
            display_map[marker] = original
        return original_to_pres[original]

    def relabel(text: str, local_map: TokenMap) -> str:
        def repl(m: re.Match[str]) -> str:
            marker = m.group(0)[1:-1]  # "RUT_1"
            label = m.group(1)  # "RUT"
            original = local_map.get(marker)
            if original is None:
                return m.group(0)  # marcador sin valor conocido: se deja igual
            return f"[{pres_for(original, label)}]"

        return _MARKER_RE.sub(repl, text)

    chunk_texts = [
        relabel(text, doc_maps.get(doc_id, {})) for text, doc_id in chunk_texts_with_doc
    ]
    query_text = relabel(clean_query, query_map)
    return Presentation(
        chunk_texts=chunk_texts, query_text=query_text, display_map=display_map
    )
