"""Persiste el mapa de PII de los documentos de ejemplo.

Los documentos demo se enmascaran al sembrarlos (RUT/correo/teléfono → [RUT_1]…),
pero su mapa marcador→valor no se guardaba, así que esos identificadores no se
restauraban en las respuestas. Este script recorre los mismos documentos, calcula
el mismo mapa (el scrubber es determinístico → mismos marcadores) y lo guarda en
la base relacional.

Seguro de correr varias veces (borra e inserta por documento). NO toca el índice
vectorial ni requiere reiniciar la app: la restauración lee este mapa desde
PostgreSQL en cada consulta.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def main() -> None:
    from sqlalchemy import delete

    from app.models.database import AsyncSessionLocal, create_tables
    from app.models.doc_pii_token import DocPIIToken
    from app.services.ingestion.extractor import extract_text
    from app.services.privacy.doc_pii import persist_doc_map
    from app.services.privacy.scrubber import PIIScrubber

    await create_tables()

    sample_dir = Path(__file__).parent.parent / "data" / "sample_docs"
    docs = sorted(sample_dir.glob("*.txt"))
    if not docs:
        print("[pii-map] No hay documentos de ejemplo en data/sample_docs/ — nada que hacer.")
        return

    scrubber = PIIScrubber(spacy_enabled=False)
    async with AsyncSessionLocal() as db:
        for doc_path in docs:
            text = extract_text(doc_path.read_bytes(), doc_path.name)
            _clean, token_map, _types = scrubber.scrub(text)
            # Idempotente: limpia lo anterior de este documento antes de insertar.
            await db.execute(
                delete(DocPIIToken).where(DocPIIToken.doc_id == doc_path.stem)
            )
            await db.commit()
            await persist_doc_map(db, doc_path.stem, token_map, None)
            print(f"[pii-map] {doc_path.name}: {len(token_map)} identificador(es) guardado(s)")

    print("[pii-map] Listo — los documentos de ejemplo ya restauran sus datos reales.")


if __name__ == "__main__":
    asyncio.run(main())
