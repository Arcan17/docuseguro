from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.metrics import MetricsReport
from app.core.auth import require_api_key
from app.models.database import get_db
from app.services.metrics_service import get_metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=MetricsReport, dependencies=[Depends(require_api_key)])
async def metrics_report(
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
) -> MetricsReport:
    return await get_metrics(db, period_hours=hours)
