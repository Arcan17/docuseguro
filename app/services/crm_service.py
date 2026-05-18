import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def log_crm_event(
    query_hash: str,
    latency_ms: int,
    cache_hit: bool,
    chunk_count: int,
) -> None:
    """Fire audit event to the simulated CRM webhook."""
    payload = {
        "query_hash": query_hash,
        "latency_ms": latency_ms,
        "cache_hit": cache_hit,
        "chunk_count": chunk_count,
        "source": "privrag",
    }
    headers: dict[str, str] = {}
    if settings.auth_enabled:
        headers["X-API-Key"] = settings.api_key

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(settings.crm_webhook_url, json=payload, headers=headers)
            resp.raise_for_status()
    except Exception as exc:
        logger.warning("crm_webhook_failed", error=str(exc))
