from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.metrics import MetricsReport
from app.models.query_log import QueryLog


async def get_metrics(db: AsyncSession, period_hours: int = 24) -> MetricsReport:
    since = datetime.now(UTC) - timedelta(hours=period_hours)

    rows = (
        await db.execute(
            select(QueryLog).where(QueryLog.created_at >= since)
        )
    ).scalars().all()

    if not rows:
        return MetricsReport(
            queries_total=0,
            cache_hit_rate_pct=0.0,
            avg_latency_ms=0.0,
            p95_latency_ms=0.0,
            pii_detected_count=0,
            tokens_saved_avg_pct=None,
        )

    latencies = sorted(r.latency_ms for r in rows)
    cache_hits = sum(1 for r in rows if r.cache_hit)
    pii_count = sum(1 for r in rows if r.pii_found)

    # p95 latency
    p95_idx = int(len(latencies) * 0.95)
    p95 = float(latencies[min(p95_idx, len(latencies) - 1)])

    # Average tokens saved
    savings: list[float] = []
    for r in rows:
        if r.original_tokens and r.compressed_tokens and r.original_tokens > 0:
            savings.append((1 - r.compressed_tokens / r.original_tokens) * 100)
    avg_saved = round(sum(savings) / len(savings), 1) if savings else None

    return MetricsReport(
        queries_total=len(rows),
        cache_hit_rate_pct=round(cache_hits / len(rows) * 100, 1),
        avg_latency_ms=round(sum(latencies) / len(latencies), 1),
        p95_latency_ms=p95,
        pii_detected_count=pii_count,
        tokens_saved_avg_pct=avg_saved,
        period_hours=period_hours,
    )
