COSINE_THRESHOLD = 0.75
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
MAX_CONTEXT_TOKENS = 1500
CACHE_TTL_SECONDS = 3600
PII_TOKEN_TTL_SECONDS = 7200

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 100

ANTHROPIC_MODEL = "claude-haiku-3-5-20241022"
OPENAI_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based strictly on the provided context. "
    "If the context does not contain enough information to answer, say so clearly. "
    "When you reference named entities from the context, reproduce them exactly as they appear, "
    "including any bracket-enclosed identifiers like [abc123-...]."
)
