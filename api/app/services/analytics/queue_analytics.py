from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Queue, Ticket
from app.schemas.analytics.queue_analytics import (
    QueueBasicStatsResponse,
    QueuePerformanceResponse,
    QueuesOverviewResponse
)


async def get_queue_basic_stats(db: AsyncSession, queue_id: int) -> QueueBasicStatsResponse:
    """Базовая статистика очереди"""

    stmt = select(Queue).where(Queue.id == queue_id)
    result = await db.execute(stmt)
    queue = result.scalar_one_or_none()
    
    if not queue:
        return QueueBasicStatsResponse(
            queue_id=0,
            queue_name="",
            current_position=0,
            next_ticket_position=None,
            tickets_by_status={},
            total_tickets=0,
            waiting_count=0,
            processing_count=0,
            completed_count=0
        )
    
    status_stats_stmt = select(
        Ticket.status, 
        func.count(Ticket.id).label('count')
    ).where(
        Ticket.queue_id == queue_id, 
        Ticket.is_deleted == False
    ).group_by(Ticket.status)
    
    status_stats_result = await db.execute(status_stats_stmt)
    status_stats = status_stats_result.all()
    
    status_counts = {status: count for status, count in status_stats}
    
    next_ticket_stmt = select(Ticket).where(
        Ticket.queue_id == queue_id,
        Ticket.position > queue.current_position,
        Ticket.status == 'waiting',
        Ticket.is_deleted == False
    ).order_by(Ticket.position.asc())
    
    next_ticket_result = await db.execute(next_ticket_stmt)
    next_ticket = next_ticket_result.first()
    
    return QueueBasicStatsResponse(
        queue_id=queue_id,
        queue_name=queue.name,
        current_position=queue.current_position,
        next_ticket_position=next_ticket[0].position if next_ticket else None,
        tickets_by_status=status_counts,
        total_tickets=sum(status_counts.values()),
        waiting_count=status_counts.get('waiting', 0),
        processing_count=status_counts.get('processing', 0),
        completed_count=status_counts.get('completed', 0)
    )


async def get_queue_performance_stats(db: AsyncSession, queue_id: int) -> QueuePerformanceResponse:
    """Метрики производительности очереди"""

    avg_service_time_stmt = select(
        func.avg(func.extract('epoch', Ticket.completed_at - Ticket.called_at))
    ).where(
        Ticket.queue_id == queue_id,
        Ticket.status == 'completed',
        Ticket.called_at.isnot(None),
        Ticket.completed_at.isnot(None)
    )
    avg_service_time_result = await db.execute(avg_service_time_stmt)
    avg_service_time = avg_service_time_result.scalar()
    
    avg_wait_time_stmt = select(
        func.avg(func.extract('epoch', Ticket.called_at - Ticket.created_at))
    ).where(
        Ticket.queue_id == queue_id,
        Ticket.status == 'completed',
        Ticket.called_at.isnot(None)
    )
    avg_wait_time_result = await db.execute(avg_wait_time_stmt)
    avg_wait_time = avg_wait_time_result.scalar()
    
    today = datetime.now().date()
    
    today_tickets_stmt = select(func.count(Ticket.id)).where(
        Ticket.queue_id == queue_id,
        func.date(Ticket.created_at) == today,
        Ticket.is_deleted == False
    )
    today_tickets_result = await db.execute(today_tickets_stmt)
    today_tickets = today_tickets_result.scalar() or 0
    
    today_completed_stmt = select(func.count(Ticket.id)).where(
        Ticket.queue_id == queue_id,
        Ticket.status == 'completed',
        func.date(Ticket.completed_at) == today,
        Ticket.is_deleted == False
    )
    today_completed_result = await db.execute(today_completed_stmt)
    today_completed = today_completed_result.scalar() or 0
    
    today_completion_rate = round(today_completed / today_tickets * 100, 2) if today_tickets > 0 else 0.0
    
    return QueuePerformanceResponse(
        queue_id=queue_id,
        avg_service_time_seconds=round(avg_service_time, 2) if avg_service_time else None,
        avg_wait_time_seconds=round(avg_wait_time, 2) if avg_wait_time else None,
        today_tickets=today_tickets,
        today_completed=today_completed,
        today_completion_rate=today_completion_rate
    )


async def get_event_queues_overview(db: AsyncSession, event_id: int) -> QueuesOverviewResponse:
    """Обзор всех очередей мероприятия"""
    
    queues_stmt = select(Queue).where(
        Queue.event_id == event_id,
        Queue.is_deleted == False
    )
    queues_result = await db.execute(queues_stmt)
    queues = queues_result.scalars().all()
    
    queues_stats = []
    for queue in queues:
        stats = await get_queue_basic_stats(db, queue.id)
        queues_stats.append(stats)
    
    return QueuesOverviewResponse(queues=queues_stats)