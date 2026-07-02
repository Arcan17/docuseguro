# Retrieval: the multilingual model understands Spanish, so relevant matches
# (~0.46-0.69) separate cleanly from off-topic queries (~0.23-0.42). The cut lives
# in config (cosine_similarity_threshold ~0.40); the system prompt is the final
# relevance judge and declines when the context lacks the answer.
COSINE_THRESHOLD = 0.40
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
MAX_CONTEXT_TOKENS = 1500
CACHE_TTL_SECONDS = 3600
PII_TOKEN_TTL_SECONDS = 7200

EMBEDDING_MODEL = "text-embedding-3-small"  # kept for reference (not used in demo)
# Multilingual (entiende español), 384-dim — reemplazo directo del bge-small-en.
EMBEDDING_MODEL_LOCAL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_BATCH_SIZE = 100

ANTHROPIC_MODEL = "claude-haiku-3-5-20241022"
OPENAI_MODEL = "gpt-4o-mini"
# Groq discontinued llama-3.1-8b-instant (2026-06; removed 2026-08-16);
# migrated to their recommended replacement.
GROQ_MODEL = "openai/gpt-oss-20b"

# Mensaje canónico cuando la respuesta no está en los documentos. Se usa tanto en
# el corto-circuito por recuperación como en la instrucción al modelo, para que la
# negativa sea consistente y detectable.
NO_INFO_MESSAGE = "Esa información no está en tus documentos."

SYSTEM_PROMPT = (
    "Eres un asistente que responde ÚNICAMENTE con la información contenida en el "
    "CONTEXTO entregado. Reglas estrictas:\n"
    "1. Si el contexto no contiene la información para responder, responde EXACTAMENTE: "
    f"«{NO_INFO_MESSAGE}» y nada más.\n"
    "2. NUNCA uses conocimiento general ni externo: no respondas operaciones matemáticas, "
    "datos históricos, definiciones ni cultura general si no están en el contexto, aunque "
    "sepas la respuesta.\n"
    "3. No inventes ni completes datos que no aparezcan en el contexto.\n"
    "4. Cuando cites datos del contexto, reprodúcelos EXACTAMENTE como aparecen, incluidos "
    "los identificadores entre corchetes como [RUT_1], [CORREO_1] o [TELEFONO_1].\n"
    "Responde siempre en español."
)
