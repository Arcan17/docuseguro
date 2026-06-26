from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "PrivRAG"
    log_level: str = "INFO"
    llm_provider: Literal["anthropic", "openai", "groq"] = "groq"

    # Database
    database_url: str = "postgresql+asyncpg://privrag:privrag@localhost:5432/privrag"

    # ChromaDB
    chroma_path: str = ".chroma"
    chroma_collection: str = "documents"

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # CRM Webhook
    crm_webhook_url: str = "http://localhost:8000/webhook/crm"

    # RAG tuning
    cosine_similarity_threshold: float = 0.50
    chunk_size: int = 800
    chunk_overlap: int = 150
    max_context_tokens: int = 1500
    cache_ttl_seconds: int = 3600

    # Privacy
    spacy_enabled: bool = False
    pii_token_ttl_seconds: int = 7200
    # User-uploaded documents are auto-deleted from the vector store after this
    # window, so nothing a user uploads is stored permanently.
    upload_ttl_seconds: int = 3600

    # Auth
    api_key: str = ""
    max_upload_size_mb: int = 10

    # Rate limiting — max requests per minute per client IP (0 disables)
    rate_limit_per_minute: int = 30

    # CORS — comma-separated allowed frontend origins. Locked to the production
    # site + local dev by default; override with CORS_ORIGINS (or "*" for any).
    cors_origins: str = (
        "https://privrag.vercel.app,http://localhost:3000,http://localhost:3100"
    )

    # Audit
    audit_hash_secret: str = ""  # HMAC secret for query_hash in audit logs

    # Auth (Fase 1 — cuentas)
    jwt_secret: str = ""  # signing key for JWT; random per-process if empty
    # Shorter expiry limits the window if a token is stolen (no revocation yet).
    jwt_expire_minutes: int = 1440  # 1 day
    password_min_length: int = 8
    # Per-account login lockout (brute force): max failures before a cooldown.
    login_max_failures: int = 5
    login_lockout_seconds: int = 300

    # Trial (Fase 2): free days from registration before upload/query is blocked.
    trial_days: int = 14
    trial_contact_email: str = "bast-1996@hotmail.com"

    @property
    def auth_enabled(self) -> bool:
        return bool(self.api_key)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def effective_context_token_limit(self) -> int:
        return int(self.max_context_tokens * 0.85)

    @property
    def effective_audit_secret(self) -> str:
        # Never fall back to a known constant. If unset, use a per-process random
        # secret so audit query hashes can't be reversed with a dictionary.
        if self.audit_hash_secret:
            return self.audit_hash_secret
        return _RUNTIME_AUDIT_SECRET

    @property
    def effective_jwt_secret(self) -> str:
        # Same pattern: never a known default. Set JWT_SECRET in production so
        # tokens survive restarts; otherwise a per-process random key is used.
        if self.jwt_secret:
            return self.jwt_secret
        return _RUNTIME_JWT_SECRET


import secrets as _secrets  # noqa: E402

_RUNTIME_AUDIT_SECRET = _secrets.token_hex(32)
_RUNTIME_JWT_SECRET = _secrets.token_hex(32)

settings = Settings()
