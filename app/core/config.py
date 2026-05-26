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
    cosine_similarity_threshold: float = 0.75
    chunk_size: int = 800
    chunk_overlap: int = 150
    max_context_tokens: int = 1500
    cache_ttl_seconds: int = 3600

    # Privacy
    spacy_enabled: bool = False
    pii_token_ttl_seconds: int = 7200

    # Auth
    api_key: str = ""
    max_upload_size_mb: int = 10

    # Audit
    audit_hash_secret: str = ""  # HMAC secret for query_hash in audit logs

    @property
    def auth_enabled(self) -> bool:
        return bool(self.api_key)

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def effective_context_token_limit(self) -> int:
        return int(self.max_context_tokens * 0.85)


settings = Settings()
