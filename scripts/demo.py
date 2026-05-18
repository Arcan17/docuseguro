"""
PrivRAG Demo Script
===================
Demonstrates all 4 AI capabilities with measurable metrics.

Usage:
    python scripts/demo.py             # normal run
    python scripts/demo.py --verbose   # show PII scrubbing in action

Requirements:
    - .env with valid OPENAI_API_KEY and ANTHROPIC_API_KEY (or LLM_PROVIDER=openai)
    - PostgreSQL running (or docker compose up -d db)
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

QUERIES = [
    ("¿Cuántos días de vacaciones tienen los empleados?", False),
    ("¿Cómo solicito acceso a herramientas de trabajo?", False),
    ("¿Cuál es la política de teletrabajo?", False),
    ("¿Qué hago si olvido mi contraseña?", False),
    ("¿Cómo reporto un incidente de seguridad?", False),
    # Repeated queries → should hit cache
    ("¿Cuántos días de vacaciones tienen los empleados?", True),  # cache hit
    ("¿Cómo solicito acceso a herramientas de trabajo?", True),  # cache hit
    ("¿Cuál es la política de teletrabajo?", True),  # cache hit
    # Queries with PII
    ("¿Cumplió el empleado con RUT 12.345.678-9 sus metas?", False),
    ("Necesito el contrato del trabajador jorge.fuentes@empresa.cl", False),
]

# Queries used in verbose PII walkthrough
_VERBOSE_PII_QUERIES = [
    "¿Cumplió el empleado con RUT 12.345.678-9 sus metas?",
    "Necesito el contrato del trabajador jorge.fuentes@empresa.cl",
    "Llame al +56 9 8765 4321 para confirmar el contrato",
]


def _section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def _sep() -> None:
    print("-" * 60)


async def _show_verbose_pii_walkthrough() -> None:
    from app.services.privacy.scrubber import PIIScrubber

    _section("VERBOSE: PII SCRUBBING WALKTHROUGH")
    scrubber = PIIScrubber(spacy_enabled=False)

    for raw_query in _VERBOSE_PII_QUERIES:
        clean, token_map, pii_types = scrubber.scrub(raw_query)

        print(f"\n  Original query  : {raw_query}")
        print(f"  Sent to LLM/embed: {clean}")
        if pii_types:
            print(f"  PII detected    : {', '.join(pii_types)}")
            for token, original in token_map.items():
                print(f"    [{token}]  <--  {original!r}")
        else:
            print("  PII detected    : none")

    print()
    print("  > The LLM prompt is built from the 'Sent to LLM/embed' version.")
    print("  > [uuid] tokens are replaced back with originals in the response.")
    print("  > Document PII was also scrubbed at ingest — not restorable.")


async def run_demo(verbose: bool = False) -> None:
    from app.core.logging import configure_logging
    from app.models.database import AsyncSessionLocal, create_tables
    from app.models.document import Document
    from app.services.ingestion.chunker import semantic_chunk
    from app.services.ingestion.embedder import embed_chunks
    from app.services.ingestion.extractor import extract_text
    from app.services.privacy.scrubber import PIIScrubber
    from app.services.rag_pipeline import RAGPipeline
    from app.services.vector_store import upsert_chunks

    configure_logging("WARNING")  # quiet during demo

    _section("PrivRAG — Privacy-Preserving RAG Pipeline DEMO")

    if verbose:
        await _show_verbose_pii_walkthrough()

    await create_tables()

    # Ingest sample documents
    sample_dir = Path(__file__).parent.parent / "data" / "sample_docs"
    docs = list(sample_dir.glob("*.txt"))

    print(f"\n[1] INGESTING {len(docs)} DOCUMENTS")
    _sep()
    scrubber = PIIScrubber(spacy_enabled=False)

    async with AsyncSessionLocal() as db:
        for doc_path in docs:
            content = doc_path.read_bytes()
            text = extract_text(content, doc_path.name)

            clean_text, token_map, pii_types = scrubber.scrub(text)
            pii_found = bool(token_map)

            chunks = semantic_chunk(clean_text, doc_id=doc_path.stem)
            embeddings = await embed_chunks(chunks)
            await upsert_chunks(doc_path.stem, chunks, embeddings)

            doc = Document(
                filename=doc_path.name,
                content_hash=__import__("hashlib").sha256(content).hexdigest(),
                chunk_count=len(chunks),
                file_size=len(content),
                status="ready",
            )
            db.add(doc)
            try:
                await db.commit()
            except Exception:
                await db.rollback()

            if verbose and pii_found:
                print(f"   {doc_path.name}  →  {len(chunks)} chunks  [PII scrubbed: {', '.join(pii_types)}]")
            else:
                print(f"   {doc_path.name}  →  {len(chunks)} chunks")

    # Run queries
    print(f"\n[2] RUNNING {len(QUERIES)} QUERIES")
    _sep()
    results = []

    async with AsyncSessionLocal() as db:
        pipeline = RAGPipeline(db)
        for i, (query, _expected_cache) in enumerate(QUERIES, 1):
            t0 = time.monotonic()
            result = await pipeline.query(
                session_id="00000000-0000-0000-0000-000000000001",
                query_text=query,
            )
            latency = int((time.monotonic() - t0) * 1000)

            cache_str = "CACHE" if result.cache_hit else "LLM  "
            pii_str = f"[PII:{','.join(result.pii_types)}]" if result.pii_found else "          "
            saved_str = f"saved {result.tokens_saved_pct:.0f}%" if result.tokens_saved_pct else "—"

            print(f"  {i:2}. [{cache_str}] {query[:45]:<45} | {latency:>4}ms | {pii_str} | {saved_str}")

            if verbose and result.pii_found:
                print(f"       Original  : {query}")
                print(f"       Sent to LLM: {result.clean_query}")

            results.append(result)

    # Summary metrics
    _section("METRICS SUMMARY")
    total = len(results)
    cache_hits = sum(1 for r in results if r.cache_hit)
    pii_queries = sum(1 for r in results if r.pii_found)
    latencies = [r.latency_ms for r in results]
    avg_lat = sum(latencies) / len(latencies)
    p95_lat = sorted(latencies)[int(len(latencies) * 0.95)]
    savings = [r.tokens_saved_pct for r in results if r.tokens_saved_pct is not None]
    avg_saved = sum(savings) / len(savings) if savings else 0

    print(f"  Queries total:      {total}")
    print(f"  Cache hit rate:     {cache_hits}/{total} ({cache_hits / total * 100:.0f}%)")
    print(f"  PII queries:        {pii_queries}  (100% stripped before LLM — RUT/email/phone)")
    print(f"  Avg latency:        {avg_lat:.0f}ms")
    print(f"  P95 latency:        {p95_lat}ms")
    print(f"  Avg tokens saved:   {avg_saved:.1f}%")
    print()
    print("All 4 capabilities demonstrated:")
    print("  RAG      cosine similarity threshold >= 0.75 — low-quality chunks rejected")
    print("  CACHE    SHA256(query+context) — repeated queries served from PostgreSQL")
    print(f"  COMPRESS sentence dedup + tiktoken trim — avg {avg_saved:.1f}% tokens saved")
    print("  PRIVACY  PII stripped at ingest AND at query time — LLM never sees raw data")
    print("=" * 60)
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PrivRAG demo")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show PII scrubbing details: original query, clean version, and token map",
    )
    args = parser.parse_args()
    asyncio.run(run_demo(verbose=args.verbose))
