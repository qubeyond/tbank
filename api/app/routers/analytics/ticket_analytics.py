from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.core.dependencies import get_current_admin
from app.schemas.analytics.ticket_analytics import *
from app.services.analytics.ticket_analytics import *


router = APIRouter(tags=["analytics"])


@router.get("/{ticket_id}/stats", response_model=TicketStatsResponse)
async def get_ticket_stats_route(
    ticket_id: int, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Получить статистику по талону"""
    
    return await get_ticket_stats(db, ticket_id)


@router.get("/queue/{queue_id}/timeline", response_model=TicketsTimelineResponse)
async def get_tickets_timeline_route(
    queue_id: int, 
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Получить таймлайн талонов очереди"""

    return await get_tickets_timeline(db, queue_id, hours)


@router.get("/queue/{queue_id}/stats", response_model=QueueTicketsStatsResponse)
async def get_queue_tickets_stats_route(
    queue_id: int, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Получить статистику по всем талонам очереди"""

    return await get_queue_tickets_stats(db, queue_id)