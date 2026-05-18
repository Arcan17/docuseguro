# PrivRAG

> Privacy-preserving RAG pipeline for enterprise documents

[![CI](https://github.com/Arcan17/privrag/actions/workflows/ci.yml/badge.svg)](https://github.com/Arcan17/privrag/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-oriented FastAPI backend that lets companies query their internal documents in natural language — **without ever sending sensitive data to an external LLM**.

Built to demonstrate four enterprise AI engineering capabilities:

| Capability | Implementation | Key Metric |
|-----------|---------------|------------|
| **RAG + semantic chunking** | ChromaDB + cosine threshold 0.75 | Rejects low-quality context before LLM call |
| **Token optimization** | SHA256 cache (PostgreSQL) + sentence compression | 30-45% cache hit rate, ~15% tokens saved |
| **PII stripping** | Regex (Chilean RUT / email / phone) + optional spaCy | 100% RUT & email detection |
| **Workflow automation** | Telegram Bot + simulated CRM webhook + `/metrics` | Non-blocking async notifications |

---

## Business use cases

This system is especially relevant for Chilean companies or any business that handles regulated data:

- **Legal & compliance**: Query contracts and regulatory documents without exposing client RUTs to third-party APIs
- **HR portals**: Let employees ask about vacation policies, payroll, and benefits — PII-safe
- **Healthcare**: Search clinical guidelines or internal protocols without sending patient data externally
- **Insurance**: Query internal policy documents with automatic masking of policyholder identifiers
- **Tech support**: Internal FAQ bot that strips ticket reporter contacts before hitting the LLM

---

## Architecture

```
POST /query {"query": "¿Cumplió el empleado 12.345.678-9?", "session_id": "..."}
     │
     ├─ [1] PII Scrubber  →  "12.345.678-9" replaced with [uuid]  (DB-persisted, TTL 2h)
     ├─ [2] Embedding     →  OpenAI text-embedding-3-small  (clean text, no PII)
     ├─ [3] Vector search →  ChromaDB cosine ≥ 0.75  (low-quality chunks rejected)
     ├─ [4] Cache lookup  →  SHA256(query + context) → PostgreSQL  (HIT: return <20ms)
     ├─ [5] Compression   →  sentence dedup + tiktoken trim  (MISS path only)
     ├─ [6] LLM call      →  Anthropic Haiku or GPT-4o-mini  (never sees raw PII)
     ├─ [7] PII restore   →  [uuid] → "12.345.678-9" in response
     └─ [8] Async tasks   →  Telegram (PII-free summary only) + CRM webhook (non-blocking)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full diagrams and design decisions.

### Privacy guarantees

| Boundary | What leaves the system |
|----------|----------------------|
| OpenAI Embeddings | Clean query text — PII replaced with `[uuid]` tokens |
| Anthropic / OpenAI LLM | Compressed context + clean query — no raw PII |
| PostgreSQL `pii_tokens` | UUID ↔ original value mapping, TTL 2h, for audit only |
| Telegram notification | PII-type summary (`[PII: rut, email]`) and anonymized query — never the original value or the full response |
| CRM webhook | Query hash, latency, cache status — no query text at all |

---

## Quick start

```bash
git clone https://github.com/Arcan17/privrag.git && cd privrag
cp .env.example .env
```

Edit `.env` and set at minimum:
```bash
OPENAI_API_KEY=sk-...        # Required for embeddings (always)
ANTHROPIC_API_KEY=sk-ant-... # Required if LLM_PROVIDER=anthropic
API_KEY=your-secret-key      # Leave empty to disable auth in local dev
```

> **Note:** OpenAI is always required for embeddings (`text-embedding-3-small`), even when using Claude as the LLM. Set `LLM_PROVIDER=openai` to use only one API key.

```bash
# Production (no hot-reload, DB not exposed externally)
docker compose up -d

# Development (hot-reload enabled, DB on localhost:5432)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Check it's running:
```bash
curl http://localhost:8000/health
# {"status":"ok","provider":"anthropic"}
```

---

## API reference

All endpoints except `/health` require the `X-API-Key` header when `API_KEY` is set in `.env`.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Health check |
| `POST` | `/ingest` | Yes | Upload PDF or .txt (max 10MB) |
| `POST` | `/query` | Yes | Query documents with RAG |
| `GET` | `/metrics` | Yes | Performance metrics (last N hours) |
| `POST` | `/webhook/crm` | Yes | Simulated CRM event receiver |

### Ingest a document

```bash
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: your-secret-key" \
  -F "file=@data/sample_docs/sample_policy.txt"
```

```json
{"doc_id": 1, "filename": "sample_policy.txt", "chunk_count": 8, "status": "ready"}
```

### Query (no PII)

```bash
curl -X POST http://localhost:8000/query \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Cuántos días de vacaciones hay?", "session_id": "abc-123"}'
```

```json
{
  "answer": "Los empleados con contrato indefinido tienen 15 días hábiles...",
  "cache_hit": false,
  "latency_ms": 1203,
  "pii_found": false,
  "llm_provider": "anthropic",
  "tokens_saved_pct": 12.3,
  "chunk_count": 3,
  "source_chunks": [...]
}
```

### Query with PII — automatically masked

```bash
curl -X POST http://localhost:8000/query \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "El empleado 12.345.678-9 con correo ana@empresa.cl cumplió?", "session_id": "abc-123"}'
```

The RUT and email are replaced with UUID tokens **before** the embedding call and the LLM call. The response has the original values restored within the same request using the in-memory token map. The token mapping is also persisted to PostgreSQL with a 2-hour TTL for audit purposes.

```json
{
  "answer": "El empleado 12.345.678-9 cumplió con los requisitos...",
  "pii_found": true,
  "pii_types": ["rut", "email"]
}
```

### Metrics

```bash
curl -H "X-API-Key: your-secret-key" "http://localhost:8000/metrics?hours=24"
```

```json
{
  "queries_total": 50,
  "cache_hit_rate_pct": 44.0,
  "avg_latency_ms": 438.2,
  "p95_latency_ms": 1102.0,
  "pii_detected_count": 8,
  "tokens_saved_avg_pct": 17.3
}
```

---

## Running tests

```bash
pip install -r requirements.txt aiosqlite
pytest -v --tb=short
# 44 passed
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `anthropic` | `anthropic` or `openai` |
| `OPENAI_API_KEY` | — | **Always required** for embeddings |
| `ANTHROPIC_API_KEY` | — | Required when `LLM_PROVIDER=anthropic` |
| `API_KEY` | *(empty)* | Auth key for all endpoints. Leave empty to disable in local dev |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum file size for `/ingest` |
| `COSINE_SIMILARITY_THRESHOLD` | `0.75` | Min similarity to include a chunk |
| `CHUNK_SIZE` | `800` | Max chars per chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between consecutive chunks |
| `MAX_CONTEXT_TOKENS` | `1500` | Max tokens sent to LLM (compressed to 85%) |
| `CACHE_TTL_SECONDS` | `3600` | Response cache TTL |
| `TELEGRAM_BOT_TOKEN` | *(empty)* | Leave empty to disable Telegram |
| `SPACY_ENABLED` | `false` | Enable spaCy NER for person/org PII detection |

---

## Stack

- **Python 3.11** — FastAPI, SQLAlchemy async, Pydantic v2
- **PostgreSQL 16** — query cache, audit log, PII token store (TTL-governed)
- **ChromaDB 0.5** — vector store (cosine similarity, persistent volume, no LangChain)
- **OpenAI** — `text-embedding-3-small` embeddings
- **Anthropic / OpenAI** — Claude Haiku or GPT-4o-mini (configurable)
- **structlog** — structured JSON logging
- **Docker Compose** — production + dev override configs
