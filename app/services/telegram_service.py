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


async def notify_query(query: str, answer: str, latency_ms: int, cache_hit: bool) -> None:
    status = "⚡ CACHE HIT" if cache_hit else "🤖 LLM"
    preview = answer[:100] + "..." if len(answer) > 100 else answer
    msg = (
        f"🔍 PrivRAG Query [{status}]\n"
        f"Q: {query[:80]}\n"
        f"A: {preview}\n"
        f"Latency: {latency_ms}ms"
    )
    await _send(msg)
