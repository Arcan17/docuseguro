import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


async def _send(text: str) -> None:
    if not settings.telegram_enabled:
        return
    url = TELEGRAM_API.format(token=settings.telegram_bot_token)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={"chat_id": settings.telegram_chat_id, "text": text})
    except Exception as exc:
        logger.warning("telegram_send_failed", error=str(exc))


async def notify_ingest(filename: str, chunk_count: int) -> None:
    msg = f"📄 PrivRAG: Document ingested\nFile: {filename}\nChunks: {chunk_count}"
    await _send(msg)


async def notify_query(
    clean_query: str,
    latency_ms: int,
    cache_hit: bool,
    pii_found: bool,
    pii_types: list[str],
) -> None:
    status = "CACHE HIT" if cache_hit else "LLM"
    pii_note = f" [PII: {', '.join(pii_types)}]" if pii_found else ""
    msg = (
        f"PrivRAG Query [{status}]{pii_note}\n"
        f"Q: {clean_query[:120]}\n"
        f"Latency: {latency_ms}ms"
    )
    await _send(msg)
