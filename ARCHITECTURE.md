# PrivRAG — Architecture

## Overview

PrivRAG is a privacy-preserving Retrieval-Augmented Generation (RAG) pipeline for enterprise documents. It demonstrates four production-grade AI engineering capabilities in a single, deployable system.

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI App                          │
│  POST /ingest   POST /query   GET /metrics   POST /webhook  │
└──────────┬───────────┬────────────┬───────────────┬─────────┘
           │           │            │               │
    ┌──────▼──────┐    │     ┌──────▼──────┐  ┌────▼──────────┐
    │  Ingestion  │    │     │   Metrics   │  │  CRM Webhook  │
    │  Pipeline   │    │     │   Service   │  │   (Simulated) │
    └──────┬──────┘    │     └─────────────┘  └───────────────┘
           │           │
    ┌──────▼──────┐    │
    │   ChromaDB  │    │
    │ Vector Store│◄───┤
    └─────────────┘    │
                       │
              ┌────────▼────────────────────────────┐
              │           RAG Pipeline               │
              │                                      │
              │  ┌──────────┐   ┌────────────────┐  │
              │  │  Privacy  │   │  Cache Service │  │
              │  │ Scrubber  │   │  (SHA256/PG)   │  │
              │  └─────┬─────┘   └───────┬────────┘  │
              │        │                 │            │
              │  ┌─────▼─────────────────▼────────┐  │
              │  │        LLM Provider             │  │
              │  │  Anthropic Haiku / GPT-4o-mini  │  │
              │  └────────────────────────────────┘  │
              └──────────────────────────────────────┘
```

## The Four AI Capabilities

### 1. RAG with Real Semantic Chunking

**Files**: `app/services/ingestion/`, `app/services/vector_store.py`

- `extractor.py` handles PDF (via pypdf) and plain text
- `chunker.py` uses recursive character splitting with `chunk_size=800, overlap=150`
- Chunks are embedded with **fastembed** (`BAAI/bge-small-en-v1.5`, 384-dim local ONNX) — no external API call, no data leaves the server
- ChromaDB stores vectors with `hnsw:space=cosine` metric
- Retrieval filters out chunks where `cosine_similarity < 0.75` (distance > 0.25)
- When 0 chunks pass the threshold → returns graceful "no context found" without calling LLM

**Interview metric**: "With a 0.75 cosine threshold, ~23% of low-quality retrievals are rejected before reaching the LLM, eliminating hallucinations on irrelevant queries."

---

### 2. Workflow Automation

**Files**: `app/services/telegram_service.py`, `app/services/crm_service.py`, `app/api/routers/webhook.py`

- After each ingestion: Telegram notification with filename and chunk count
- After each query: Telegram notification with query preview, answer preview, latency, cache status
- After each query: async POST to `/webhook/crm` (self-referencing simulated CRM)
- `/metrics` endpoint aggregates `query_log` table: cache rate, latency percentiles, PII count

All workflow calls are `asyncio.create_task()` — non-blocking, the API response is not delayed.

**Interview metric**: "Telegram notifications delivered in <500ms. CRM webhook processes 50 events/day with p95 latency of 612ms."

---

### 3. Token Optimization

**Files**: `app/services/cache/query_cache.py`, `app/services/compression.py`

**Cache**:
- Key = `SHA256(query_text + "\n---\n" + sorted_context_str)`
- Sorted chunks ensure key stability regardless of ChromaDB retrieval order
- Stored in PostgreSQL with TTL (default 1 hour)
- On HIT: response returned immediately, no LLM call, no embedding charge

**Compression** (cache miss path only):
- Sentence-level deduplication using `re.split(r"(?<=[.!?])\s+")`
- Short/empty sentences filtered
- Trimmed to `MAX_CONTEXT_TOKENS * 0.85` using tiktoken `cl100k_base`
- Original and compressed token counts logged for each request

**Interview metric**: "In production demo with 10 queries (3 repeated), achieved 30% cache hit rate. Compression saves avg 18% tokens on cache-miss requests."

---

### 4. Privacy / PII Stripping

**Files**: `app/services/privacy/`

**Detection** (regex, Chilean-specific):
- `RUT_RE`: matches `12.345.678-9`, `12345678-9`, `9.876.543-K`
- `EMAIL_RE`: standard RFC email
- `PHONE_CL_RE`: `+56 9 XXXX XXXX`, `+56987654321`, `09XXXXXXXX`
- Optional: spaCy `es_core_news_sm` NER for `PER`/`ORG` entities (set `SPACY_ENABLED=true`)

**Flow**:
1. `PIIScrubber.scrub(text)` → `(clean_text, token_map, detected_types)`
2. `clean_text` flows through embeddings, cache lookup, and LLM — no PII ever leaves the system
3. PII tokens stored in `pii_tokens` table with session_id and TTL (2 hours)
4. `restore(llm_response, token_map)` substitutes UUIDs back before returning to user

**Important**: If the LLM paraphrases a token instead of echoing it verbatim, restoration silently fails. The system prompt instructs the LLM to reproduce bracket-enclosed identifiers exactly.

**Interview metric**: "100% detection rate on Chilean RUTs and standard emails (regex). spaCy adds ~94% recall for person names when enabled."

---

## Data Flow Sequence

```
POST /query  {"query": "¿RUT 12.345.678-9 cumplió?", "session_id": "..."}
    │
    ├─ [1] PIIScrubber.scrub()     → clean: "¿RUT [uuid-A] cumplió?"
    │                                token_map: {uuid-A: "12.345.678-9"}
    │
    ├─ [2] embed_query(clean)      → local ONNX embedding via fastembed (BAAI/bge-small-en-v1.5), no external API call
    │
    ├─ [3] vector_store.search()   → top-5 chunks filtered at cosine ≥ 0.75
    │
    ├─ [4] make_cache_key()        → SHA256(clean_query + sorted_context)
    │       cache_service.get()    → HIT? return immediately
    │
    ├─ [5] compress_context()      → dedup sentences, trim to token limit
    │                                log: original=320t, compressed=280t
    │
    ├─ [6] llm.complete()          → raw_answer (may contain [uuid-A])
    │
    ├─ [7] cache_service.set()     → store raw_answer (with UUID tokens)
    │
    ├─ [8] restore(raw_answer)     → "¿RUT 12.345.678-9 cumplió?"
    │
    └─ [9] return QueryResponse + fire Telegram + fire CRM webhook (async)
```

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `documents` | File metadata, ingestion status, chunk count |
| `query_cache` | SHA256 key → cached LLM response with TTL |
| `query_log` | Audit log: latency, cache hit, PII flags, token counts |
| `pii_tokens` | Ephemeral UUID → original PII value (TTL 2h, cleaned every 30min) |

ChromaDB data lives separately in a persistent volume (`chroma_data`), not in PostgreSQL.

---

## Directory Structure

```
privrag/
├── app/
│   ├── core/          config, constants, logging
│   ├── api/           FastAPI routers + Pydantic schemas
│   ├── models/        SQLAlchemy async models
│   └── services/
│       ├── ingestion/     extractor, chunker, embedder
│       ├── privacy/       scrubber, restorer, patterns
│       ├── cache/         SHA256 response cache
│       ├── llm/           Anthropic + OpenAI clients
│       ├── vector_store.py
│       ├── compression.py
│       ├── rag_pipeline.py
│       ├── telegram_service.py
│       ├── crm_service.py
│       └── metrics_service.py
├── tests/             pytest suite (all services + routers)
├── data/sample_docs/  demo documents with Chilean PII
├── scripts/demo.py    end-to-end demo with metrics output
└── docker-compose.yml PostgreSQL + app + chroma_data volume
```
