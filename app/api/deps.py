
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.services.cache.query_cache import CacheService
from app.services.rag_pipeline import RAGPipeline


async def get_cache_service(
    db: AsyncSession = Depends(get_db),
) -> CacheService:
    return CacheService(db)


async def get_rag_pipeline(
    db: AsyncSession = Depends(get_db),
) -> RAGPipeline:
    return RAGPipeline(db)
