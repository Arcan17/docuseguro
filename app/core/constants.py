# Retrieval recall: the local embedding model (bge-small-en) compresses Spanish
# similarity scores into a narrow band (~0.64-0.74 for relevant matches), so the
# old 0.75 cutoff rejected most valid Spanish queries. 0.60 restores recall; the
# system prompt instructs the LLM to decline when context lacks the answer, which
# backstops the occasional marginally-relevant chunk that now passes.
COSINE_THRESHOLD = 0.60
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
MAX_CONTEXT_TOKENS = 1500
CACHE_TTL_SECONDS = 3600
PII_TOKEN_TTL_SECONDS = 7200

EMBEDDING_MODEL = "text-embedding-3-small"  # kept for reference (not used in demo)
EMBEDDING_MODEL_LOCAL = "BAAI/bge-small-en-v1.5"  # fastembed local model, 384-dim, ~24MB
EMBEDDING_BATCH_SIZE = 100

ANTHROPIC_MODEL = "claude-haiku-3-5-20241022"
OPENAI_MODEL = "gpt-4o-mini"
GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based strictly on the provided context. "
    "If the context does not contain enough information to answer, say so clearly. "
    "When you reference named entities from the context, reproduce them exactly as they appear, "
    "including any bracket-enclosed identifiers like [abc123-...]."
)
