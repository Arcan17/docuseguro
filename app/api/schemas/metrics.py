from pydantic import BaseModel


class MetricsReport(BaseModel):
    queries_total: int
    cache_hit_rate_pct: float
    avg_latency_ms: float
    p95_latency_ms: float
    pii_detected_count: int
    tokens_saved_avg_pct: float | None
    period_hours: int = 24
