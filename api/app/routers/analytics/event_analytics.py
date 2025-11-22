from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.core.dependencies import get_current_admin
from app.schemas.analytics.event_analytics import *
from app.services.analytics.event_analytics import *


router = APIRouter(tags=["analytics"])


@router.get("/{event_id}/basic", response_model=EventBasicStatsResponse)
async def get_event_basic_stats_route(
    event_id: int, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Получить базовую статистику мероприятия"""

    return await get_event_basic_stats(db, event_id)


@router.get("/{event_id}/detailed", response_model=EventDetailedStatsResponse)
async def get_event_detailed_stats_route(
    event_id: int, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Получить детальную статистику мероприятия"""

    return await get_event_detailed_stats(db, event_id)


@router.get("/overview", response_model=EventsOverviewResponse)
async def get_events_overview_route(
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Получить обзор всех мероприятий"""
    
    return await get_events_overview(db)