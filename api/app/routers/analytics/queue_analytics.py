from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.core.dependencies import get_current_admin
from app.schemas.analytics.queue_analytics import *
from app.services.analytics.queue_analytics import *


router = APIRouter(tags=["analytics"])


@router.get("/{queue_id}/basic", response_model=QueueBasicStatsResponse)
async def get_queue_basic_stats_route(
    queue_id: int, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Получить базовую статистику очереди"""
    
    return await get_queue_basic_stats(db, queue_id)


@router.get("/{queue_id}/performance", response_model=QueuePerformanceResponse)
async def get_queue_performance_stats_route(
    queue_id: int, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Получить метрики производительности очереди"""

    return await get_queue_performance_stats(db, queue_id)


@router.get("/event/{event_id}/overview", response_model=QueuesOverviewResponse)
async def get_event_queues_overview_route(
    event_id: int, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Получить обзор всех очередей мероприятия"""

    return await get_event_queues_overview(db, event_id)