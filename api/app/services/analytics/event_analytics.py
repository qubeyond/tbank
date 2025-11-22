from datetime import datetime, timedelta

from sqlalchemy import func, and_, case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Event, Queue, Ticket
from app.schemas.analytics.event_analytics import (
    EventBasicStatsResponse, 
    EventDetailedStatsResponse,
    EventsOverviewResponse,
    QueueDetailedStats
)


async def get_event_basic_stats(db: AsyncSession, event_id: int) -> EventBasicStatsResponse:
    """Базовая статистика мероприятия"""

    stmt = select(Event).where(Event.id == event_id)
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()
    
    if not event:
        return EventBasicStatsResponse(
            event_id=0,
            event_name="",
            queues_count=0,
            total_tickets=0,
            active_tickets=0,
            completed_tickets=0,
            completion_rate=0.0
        )
    
    queues_count_stmt = select(func.count(Queue.id)).where(
        Queue.event_id == event_id,
        Queue.is_deleted == False
    )
    queues_count_result = await db.execute(queues_count_stmt)
    queues_count = queues_count_result.scalar() or 0
    
    total_tickets_stmt = select(func.count(Ticket.id)).select_from(Ticket).join(Queue).where(
        Queue.event_id == event_id,
        Ticket.is_deleted == False
    )
    total_tickets_result = await db.execute(total_tickets_stmt)
    total_tickets = total_tickets_result.scalar() or 0
    
    active_tickets_stmt = select(func.count(Ticket.id)).select_from(Ticket).join(Queue).where(
        Queue.event_id == event_id,
        Ticket.is_deleted == False,
        Ticket.status.in_(['waiting', 'processing'])
    )
    active_tickets_result = await db.execute(active_tickets_stmt)
    active_tickets = active_tickets_result.scalar() or 0
    
    completed_tickets_stmt = select(func.count(Ticket.id)).select_from(Ticket).join(Queue).where(
        Queue.event_id == event_id,
        Ticket.is_deleted == False,
        Ticket.status == 'completed'
    )
    completed_tickets_result = await db.execute(completed_tickets_stmt)
    completed_tickets = completed_tickets_result.scalar() or 0
    
    completion_rate = round(completed_tickets / total_tickets * 100, 2) if total_tickets > 0 else 0.0
    
    return EventBasicStatsResponse(
        event_id=event_id,
        event_name=event.name,
        queues_count=queues_count,
        total_tickets=total_tickets,
        active_tickets=active_tickets,
        completed_tickets=completed_tickets,
        completion_rate=completion_rate
    )


async def get_event_detailed_stats(db: AsyncSession, event_id: int) -> EventDetailedStatsResponse:
    """Детальная статистика мероприятия"""

    basic_stats = await get_event_basic_stats(db, event_id)
    
    queues_stats_stmt = select(
        Queue.id,
        Queue.name,
        func.count(Ticket.id).label('total_tickets'),
        func.sum(case((Ticket.status == 'completed', 1), else_=0)).label('completed_tickets'),
        func.sum(case((Ticket.status.in_(['waiting', 'processing']), 1), else_=0)).label('active_tickets')
    ).outerjoin(Ticket, and_(
        Ticket.queue_id == Queue.id,
        Ticket.is_deleted == False
    )).where(
        Queue.event_id == event_id,
        Queue.is_deleted == False
    ).group_by(Queue.id, Queue.name)
    
    queues_stats_result = await db.execute(queues_stats_stmt)
    queues_stats = queues_stats_result.all()
    
    time_threshold = datetime.now() - timedelta(hours=24)
    
    recent_tickets_stmt = select(func.count(Ticket.id)).select_from(Ticket).join(Queue).where(
        Queue.event_id == event_id,
        Ticket.created_at >= time_threshold,
        Ticket.is_deleted == False
    )
    recent_tickets_result = await db.execute(recent_tickets_stmt)
    recent_tickets = recent_tickets_result.scalar() or 0
    
    recent_completed_stmt = select(func.count(Ticket.id)).select_from(Ticket).join(Queue).where(
        Queue.event_id == event_id,
        Ticket.status == 'completed',
        Ticket.completed_at >= time_threshold,
        Ticket.is_deleted == False
    )
    recent_completed_result = await db.execute(recent_completed_stmt)
    recent_completed = recent_completed_result.scalar() or 0
    
    queues_detailed = [
        QueueDetailedStats(
            queue_id=queue.id,
            queue_name=queue.name,
            total_tickets=queue.total_tickets or 0,
            completed_tickets=queue.completed_tickets or 0,
            active_tickets=queue.active_tickets or 0
        ) for queue in queues_stats
    ]
    
    recent_activity = {
        'last_24h_tickets': recent_tickets,
        'last_24h_completed': recent_completed
    }
    
    return EventDetailedStatsResponse(
        **basic_stats.dict(),
        queues_detailed=queues_detailed,
        recent_activity=recent_activity,
        timestamp=datetime.now().isoformat()
    )


async def get_events_overview(db: AsyncSession) -> EventsOverviewResponse:
    """Обзор всех активных мероприятий"""

    active_events_stmt = select(Event).where(
        Event.is_active == True,
        Event.is_deleted == False
    )
    result = await db.execute(active_events_stmt)
    active_events = result.scalars().all()
    
    events = []
    for event in active_events:
        stats = await get_event_basic_stats(db, event.id)
        events.append(stats)
    
    return EventsOverviewResponse(events=events)