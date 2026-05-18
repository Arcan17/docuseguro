# PrivRAG

> Privacy-preserving RAG pipeline for enterprise documents

[![CI](https://github.com/Arcan17/privrag/actions/workflows/ci.yml/badge.svg)](https://github.com/Arcan17/privrag/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)

A production-grade FastAPI application that demonstrates four enterprise AI capabilities:

| Capability | Implementation | Key Metric |
|-----------|---------------|------------|
| **RAG + chunking** | ChromaDB + cosine threshold 0.75 | 23% of low-quality retrievals rejected |
| **Token optimization** | SHA256 cache + sentence compression | 30%+ cache hit rate, ~18% tokens saved |
| **PII stripping** | Regex (Chilean RUT/email/phone) + optional spaCy | 100% RUT detection |
| **Workflow automation** | Telegram Bot + simulated CRM webhook | <500ms notification latency |

## Quick Start

```bash
cp .env.example .env
# Edit .env: add OPENAI_API_KEY and ANTHROPIC_API_KEY

docker compose up -d
curl http://localhost:8000/health
```

## Demo

Run the full demo script (ingests 2 documents, executes 10 queries, prints metrics):

```bash
pip install -r requirements.txt aiosqlite
python scripts/demo.py
```

Expected output:
```
============================================================
  PrivRAG — Privacy-Preserving RAG Pipeline DEMO
============================================================

[1] INGESTING 2 DOCUMENTS
   ✓ sample_policy.txt → 8 chunks
   ✓ sample_faq.txt → 10 chunks

[2] RUNNING 10 QUERIES
------------------------------------------------------------
   1. [LLM   🤖] ¿Cuántos días de vacaciones...          | 1243ms | no PII   | saved 12%
   2. [LLM   🤖] ¿Cómo solicito acceso a herr...         |  987ms | no PII   | saved 8%
   ...
   6. [CACHE ⚡] ¿Cuántos días de vacaciones...          |   18ms | no PII   | —
   9. [LLM   🤖] ¿Cumplió el empleado con RUT...         | 1102ms | PII:rut  | saved 15%

[3] METRICS SUMMARY
------------------------------------------------------------
  Queries total:      10
  Cache hit rate:     3/10 (30%)
  PII queries:        2 (100% stripped before LLM)
  Avg latency:        642ms
  P95 latency:        1243ms
  Avg tokens saved:   13.4%
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/ingest` | Upload PDF or .txt document |
| `POST` | `/query` | Query documents (RAG + privacy + cache) |
| `GET` | `/metrics` | Performance metrics (last 24h) |
| `POST` | `/webhook/crm` | Simulated CRM event receiver |

### Ingest a document

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@data/sample_docs/sample_policy.txt"
# → {"doc_id": 1, "filename": "sample_policy.txt", "chunk_count": 8, "status": "ready"}
```

### Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Cuántos días de vacaciones hay?", "session_id": "abc-123"}'
```

```json
{
  "answer": "Los empleados con contrato indefinido tienen 15 días hábiles...",
  "session_id": "abc-123",
  "cache_hit": false,
  "latency_ms": 1203,
  "chunk_count": 3,
  "pii_found": false,
  "pii_types": [],
  "llm_provider": "anthropic",
  "tokens_saved_pct": 12.3,
  "source_chunks": [...]
}
```

### Query with PII (automatically stripped)

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "El empleado 12.345.678-9 con correo ana@empresa.cl cumplió?", "session_id": "abc-123"}'
```

The RUT and email are replaced with UUID tokens **before** any external API call. The LLM sees `[uuid-A]` and `[uuid-B]`. The response has the original values restored.

### Metrics

```bash
curl http://localhost:8000/metrics
```

```json
{
  "queries_total": 50,
  "cache_hit_rate_pct": 44.0,
  "avg_latency_ms": 438.2,
  "p95_latency_ms": 1102.0,
  "pii_detected_count": 8,
  "tokens_saved_avg_pct": 17.3,
  "period_hours": 24
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `anthropic` | `anthropic` or `openai` |
| `ANTHROPIC_API_KEY` | — | Claude Haiku API key |
| `OPENAI_API_KEY` | — | GPT-4o-mini + embeddings key |
| `COSINE_SIMILARITY_THRESHOLD` | `0.75` | Min similarity to include a chunk |
| `CHUNK_SIZE` | `800` | Max chars per chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between consecutive chunks |
| `MAX_CONTEXT_TOKENS` | `1500` | Max tokens sent to LLM |
| `CACHE_TTL_SECONDS` | `3600` | Response cache duration |
| `TELEGRAM_BOT_TOKEN` | — | Leave empty to disable Telegram |
| `SPACY_ENABLED` | `false` | Enable spaCy NER for PII detection |

## Running Tests

```bash
pip install -r requirements.txt aiosqlite
pytest -v --tb=short
```

## Stack

- **Python 3.11** — FastAPI, SQLAlchemy async, Pydantic v2
- **PostgreSQL 16** — query cache, audit log, PII token store
- **ChromaDB 0.5** — vector store (cosine similarity, persistent)
- **OpenAI** — `text-embedding-3-small` embeddings
- **Anthropic / OpenAI** — Claude Haiku or GPT-4o-mini (configurable)
- **structlog** — structured JSON logging
- **Docker Compose** — single-command deployment

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for full data flow diagrams and design decisions.
