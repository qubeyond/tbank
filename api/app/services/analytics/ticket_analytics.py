from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Ticket
from app.schemas.analytics.ticket_analytics import (
    TicketStatsResponse,
    TicketsTimelineResponse,
    TicketTimelineResponse,
    QueueTicketsStatsResponse
)


async def get_ticket_stats(db: AsyncSession, ticket_id: int) -> TicketStatsResponse:
    """Статистика по конкретному талону"""

    stmt = select(Ticket).where(Ticket.id == ticket_id)
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return TicketStatsResponse(
            ticket_id=0,
            position=0,
            status="",
            wait_time_seconds=None,
            service_time_seconds=None,
            created_at="",
            called_at=None,
            completed_at=None
        )
    
    wait_time = None
    service_time = None
    
    if ticket.called_at:
        wait_time = (ticket.called_at - ticket.created_at).total_seconds()
        
    if ticket.called_at and ticket.completed_at:
        service_time = (ticket.completed_at - ticket.called_at).total_seconds()
    
    return TicketStatsResponse(
        ticket_id=ticket_id,
        position=ticket.position,
        status=ticket.status,
        wait_time_seconds=wait_time,
        service_time_seconds=service_time,
        created_at=ticket.created_at.isoformat(),
        called_at=ticket.called_at.isoformat() if ticket.called_at else None,
        completed_at=ticket.completed_at.isoformat() if ticket.completed_at else None
    )


async def get_tickets_timeline(db: AsyncSession, queue_id: int, hours: int = 24) -> TicketsTimelineResponse:
    """Таймлайн талонов за указанный период"""

    time_threshold = datetime.now() - timedelta(hours=hours)
    
    tickets_stmt = select(Ticket).where(
        Ticket.queue_id == queue_id,
        Ticket.created_at >= time_threshold,
        Ticket.is_deleted == False
    ).order_by(Ticket.created_at.asc())
    
    tickets_result = await db.execute(tickets_stmt)
    tickets = tickets_result.scalars().all()
    
    timeline_tickets = [
        TicketTimelineResponse(
            ticket_id=ticket.id,
            position=ticket.position,
            status=ticket.status,
            created_at=ticket.created_at.isoformat(),
            called_at=ticket.called_at.isoformat() if ticket.called_at else None,
            completed_at=ticket.completed_at.isoformat() if ticket.completed_at else None
        )
        for ticket in tickets
    ]
    
    return TicketsTimelineResponse(tickets=timeline_tickets)


async def get_queue_tickets_stats(db: AsyncSession, queue_id: int) -> QueueTicketsStatsResponse:
    """Статистика по всем талонам очереди"""
    
    status_stats_stmt = select(
        Ticket.status,
        func.count(Ticket.id).label('count')
    ).where(
        Ticket.queue_id == queue_id,
        Ticket.is_deleted == False
    ).group_by(Ticket.status)
    
    status_stats_result = await db.execute(status_stats_stmt)
    status_stats = status_stats_result.all()
    
    avg_wait_time_stmt = select(
        func.avg(func.extract('epoch', Ticket.called_at - Ticket.created_at))
    ).where(
        Ticket.queue_id == queue_id,
        Ticket.status == 'completed',
        Ticket.called_at.isnot(None)
    )
    avg_wait_time_result = await db.execute(avg_wait_time_stmt)
    avg_wait_time = avg_wait_time_result.scalar()
    
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
    
    status_distribution = {status: count for status, count in status_stats}
    total_tickets = sum(count for _, count in status_stats)
    
    return QueueTicketsStatsResponse(
        queue_id=queue_id,
        total_tickets=total_tickets,
        avg_wait_time=round(avg_wait_time, 2) if avg_wait_time else None,
        avg_service_time=round(avg_service_time, 2) if avg_service_time else None,
        status_distribution=status_distribution
    )