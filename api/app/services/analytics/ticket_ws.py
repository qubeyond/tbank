from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Ticket, Queue
from app.schemas.websocket import TicketWebSocketMessage


async def get_ticket_websocket_data(db: AsyncSession, ticket_id: int) -> TicketWebSocketMessage:
    """Получить данные для WebSocket о талоне"""
    
    # Получаем талон с информацией об очереди
    stmt = select(Ticket, Queue).join(Queue).where(Ticket.id == ticket_id)
    result = await db.execute(stmt)
    ticket_data = result.first()
    
    if not ticket_data:
        # Если талон не найден, возвращаем пустые данные
        return TicketWebSocketMessage(
            type="ticket_info",
            ticket_id=ticket_id,
            position=0,
            people_ahead=0,
            queue_name="Не найдено",
            queue_letter="X",
            estimated_wait_time=None,
            status="not_found"
        )
    
    ticket, queue = ticket_data
    
    # Считаем сколько людей перед талоном (ожидающих и обслуживаемых)
    people_ahead_stmt = select(func.count(Ticket.id)).where(
        Ticket.queue_id == queue.id,
        Ticket.position < ticket.position,
        Ticket.status.in_(['waiting', 'processing']),
        Ticket.is_deleted == False
    )
    people_ahead_result = await db.execute(people_ahead_stmt)
    people_ahead = people_ahead_result.scalar() or 0
    
    # Рассчитываем примерное время ожидания (2 минуты на человека)
    estimated_wait_time = people_ahead * 2
    
    # Буква очереди (первый символ названия очереди)
    queue_letter = queue.name[0] if queue.name else "A"
    
    # Форматируем название очереди
    queue_name = f"Очередь {queue.name}" if queue.name else "Очередь"
    
    return TicketWebSocketMessage(
        type="ticket_info",
        ticket_id=ticket_id,
        position=ticket.position,
        people_ahead=people_ahead,
        queue_name=queue_name,
        queue_letter=queue_letter,
        estimated_wait_time=estimated_wait_time,
        status=ticket.status
    )


async def get_ticket_display_data(db: AsyncSession, ticket_id: int) -> dict[str, str]:
    """Получить данные для отображения талона (буква + номер)"""
    stmt = select(Ticket, Queue).join(Queue).where(Ticket.id == ticket_id)
    result = await db.execute(stmt)
    ticket_data = result.first()
    
    if not ticket_data:
        return {"ticket_number": "X-000", "queue_name": "Не найдено"}
    
    ticket, queue = ticket_data
    queue_letter = queue.name[0] if queue.name else "A"
    ticket_number = f"{queue_letter}-{ticket.position:03d}"
    
    return {
        "ticket_number": ticket_number,
        "queue_name": queue.name or "Очередь"
    }