"""
Seed demo documents on startup (Railway / production).
Skips if documents are already in the database.
"""
import asyncio
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def seed_if_empty() -> None:
    from app.models.database import AsyncSessionLocal, create_tables
    from app.models.document import Document
    from app.services.ingestion.chunker import semantic_chunk
    from app.services.ingestion.embedder import embed_chunks
    from app.services.ingestion.extractor import extract_text
    from app.services.privacy.scrubber import PIIScrubber
    from app.services.vector_store import upsert_chunks, vector_count

    await create_tables()

    # Gate on the vector store, not the Document table: ChromaDB is ephemeral on
    # Railway while PostgreSQL persists, so after a redeploy we can have Document
    # rows but an empty vector store. Re-seeding restores searchable chunks;
    # duplicate Document rows are skipped gracefully below.
    vcount = await vector_count()
    if vcount > 0:
        print(f"[seed] vector store already has {vcount} chunk(s) — skipping.")
        return

    print("[seed] Vector store empty — ingesting demo data...")

    sample_dir = Path(__file__).parent.parent / "data" / "sample_docs"
    docs = sorted(sample_dir.glob("*.txt"))

    if not docs:
        print("[seed] No sample docs found in data/sample_docs/ — skipping.")
        return

    scrubber = PIIScrubber(spacy_enabled=False)

    async with AsyncSessionLocal() as db:
        for doc_path in docs:
            content = doc_path.read_bytes()
            text = extract_text(content, doc_path.name)
            clean_text, _token_map, pii_types = scrubber.scrub(text)
            chunks = semantic_chunk(clean_text, doc_id=doc_path.stem)
            embeddings = await embed_chunks(chunks)
            # Demo docs are shared and never expired (visible to every visitor).
            await upsert_chunks(
                doc_path.stem, chunks, embeddings, metadata_extra={"source": "demo"}
            )

            doc = Document(
                filename=doc_path.name,
                content_hash=hashlib.sha256(content).hexdigest(),
                chunk_count=len(chunks),
                file_size=len(content),
                status="ready",
            )
            db.add(doc)
            try:
                await db.commit()
                pii_note = f" [PII scrubbed: {', '.join(pii_types)}]" if pii_types else ""
                print(f"[seed]   {doc_path.name} → {len(chunks)} chunks{pii_note}")
            except Exception:
                await db.rollback()
                print(f"[seed]   {doc_path.name} already exists — skipped")

    print("[seed] Demo data ready.")


if __name__ == "__main__":
    asyncio.run(seed_if_empty())
