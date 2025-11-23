from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ticket import Ticket
from app.db.models.queue import Queue
from app.db.models.event import Event
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketUpdatePublic, TicketResponse, TicketPositionInfo
from app.services.crud.queue import get_queues_by_event
from app.services.websockets.notifications import notification_manager

async def create_ticket(db: AsyncSession, ticket_data: TicketCreate) -> tuple[TicketResponse, bool]:
    existing_ticket_result = await db.execute(
        select(Ticket)
        .join(Queue)
        .join(Event)
        .where(
            Event.code == ticket_data.event_code,
            Ticket.session_id == ticket_data.session_id,
            Ticket.is_deleted == False,
            Ticket.status.in_(["waiting", "called"])
        )
    )
    
    existing_ticket = existing_ticket_result.scalar_one_or_none()
    if existing_ticket:
        return TicketResponse.model_validate(existing_ticket), True
    
    event_result = await db.execute(  
        select(Event).where(
            Event.code == ticket_data.event_code,
            Event.is_deleted == False,
            Event.is_active == True
        )
    )
    event = event_result.scalar_one_or_none()
    if not event:
        raise ValueError("Мероприятие не найдено, удалено или неактивно")
    
    queues = await get_queues_by_event(db, event.id)  
    if not queues:
        raise ValueError("Нет активных очередей для этого мероприятия")
    
    least_loaded_queue = await find_least_loaded_queue(db, queues)
    if not least_loaded_queue:
        raise ValueError("Не найдена подходящая очередь")
    
    result = await db.execute(
        select(Ticket.position)
        .where(
            Ticket.queue_id == least_loaded_queue.id,
            Ticket.is_deleted == False
        )
        .order_by(Ticket.position.desc())
    )
    last_position = result.scalar()
    next_position = (last_position or 0) + 1
    
    ticket = Ticket(
        queue_id=least_loaded_queue.id,
        session_id=ticket_data.session_id,
        position=next_position,
        notes=ticket_data.notes
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    
    return TicketResponse.model_validate(ticket), False


async def find_least_loaded_queue(db: AsyncSession, queues: list[Queue]) -> Queue | None:
    if not queues:
        return None
    
    queue_loads = []
    for queue in queues:
        if not queue.is_active or queue.is_deleted:
            continue
            
        result = await db.execute(
            select(func.count(Ticket.id))
            .where(
                Ticket.queue_id == queue.id,
                Ticket.is_deleted == False,
                Ticket.status == "waiting"
            )
        )
        waiting_count = result.scalar() or 0
        
        queue_loads.append({
            "queue": queue,
            "load": waiting_count,
            "current_position": queue.current_position
        })
    
    if not queue_loads:
        return None
    
    queue_loads.sort(key=lambda x: x["load"])
    
    min_load = queue_loads[0]["load"]
    min_load_queues = [q for q in queue_loads if q["load"] == min_load]
    
    if len(min_load_queues) > 1:
        min_load_queues.sort(key=lambda x: x["current_position"])
    
    return min_load_queues[0]["queue"]


async def get_ticket(db: AsyncSession, ticket_id: int, include_deleted: bool = False) -> TicketResponse | None:
    query = select(Ticket).where(Ticket.id == ticket_id)
    if not include_deleted:
        query = query.where(Ticket.is_deleted == False)
    
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    return TicketResponse.model_validate(ticket) if ticket else None


async def get_tickets_by_queue(
    db: AsyncSession, 
    queue_id: int, 
    include_deleted: bool = False
) -> list[TicketResponse]:
    query = select(Ticket).where(Ticket.queue_id == queue_id)
    if not include_deleted:
        query = query.where(Ticket.is_deleted == False)
    
    query = query.order_by(Ticket.position)
    
    result = await db.execute(query)
    tickets = result.scalars().all()
    return [TicketResponse.model_validate(ticket) for ticket in tickets]


async def get_tickets_by_session(
    db: AsyncSession, 
    session_id: str,
    include_deleted: bool = False
) -> list[TicketResponse]:
    query = select(Ticket).where(Ticket.session_id == session_id)
    if not include_deleted:
        query = query.where(Ticket.is_deleted == False)
    
    query = query.order_by(Ticket.created_at.desc())
    
    result = await db.execute(query)
    tickets = result.scalars().all()
    return [TicketResponse.model_validate(ticket) for ticket in tickets]


async def update_ticket(db: AsyncSession, ticket_id: int, ticket_data: TicketUpdate) -> TicketResponse | None:
    query = select(Ticket).where(Ticket.id == ticket_id, Ticket.is_deleted == False)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return None
    
    update_data = ticket_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)
    
    await db.commit()
    await db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


async def update_ticket_public(db: AsyncSession, ticket_id: int, ticket_data: TicketUpdatePublic, session_id: str) -> TicketResponse | None:
    query = select(Ticket).where(Ticket.id == ticket_id, Ticket.is_deleted == False)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return None
    
    if ticket.session_id != session_id:
        return None
    
    if ticket_data.notes is not None:
        ticket.notes = ticket_data.notes
    
    await db.commit()
    await db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


async def call_ticket(db: AsyncSession, ticket_id: int, notes: str | None = None) -> TicketResponse | None:
    query = select(Ticket).where(Ticket.id == ticket_id, Ticket.is_deleted == False)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return None
    
    ticket.status = "called"
    ticket.called_at = datetime.now()
    if notes:
        ticket.notes = notes
    
    await db.commit()
    await db.refresh(ticket)
    
    try:
        await notification_manager.send_notification(
            ticket.session_id,
            {
                "type": "called",
                "message": "Ваш талон вызван! Подойдите к стойке.",
                "ticket_id": ticket.id,
                "position": ticket.position,
                "timestamp": datetime.now().isoformat()
            }
        )
        print(f"Call notification sent to {ticket.session_id}")
    except Exception as e:
        print(f"Error sending call notification: {e}")
    
    return TicketResponse.model_validate(ticket)

async def complete_ticket(db: AsyncSession, ticket_id: int, notes: str | None = None) -> TicketResponse | None:
    query = select(Ticket).where(Ticket.id == ticket_id, Ticket.is_deleted == False)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return None
    
    ticket.status = "completed"
    ticket.completed_at = datetime.now()
    if notes:
        ticket.notes = notes
    
    await db.commit()
    await db.refresh(ticket)
    
    try:
        await notification_manager.send_notification(
            ticket.session_id,
            {
                "type": "completed", 
                "message": "Обслуживание завершено. Спасибо!",
                "ticket_id": ticket.id,
                "timestamp": datetime.now().isoformat()
            }
        )
        print(f"Completion notification sent to {ticket.session_id}")
    except Exception as e:
        print(f"Error sending completion notification: {e}")
    
    return TicketResponse.model_validate(ticket)


async def cancel_ticket(db: AsyncSession, ticket_id: int, session_id: str | None = None, notes: str | None = None) -> TicketResponse | None:
    query = select(Ticket).where(Ticket.id == ticket_id, Ticket.is_deleted == False)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return None
    
    if session_id and ticket.session_id != session_id:
        return None
    
    ticket.status = "cancelled"
    if notes:
        ticket.notes = notes
    
    await db.commit()
    await db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


async def move_ticket(db: AsyncSession, ticket_id: int, target_queue_id: int) -> TicketResponse | None:
    query = select(Ticket).where(Ticket.id == ticket_id, Ticket.is_deleted == False)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return None
    
    queue_result = await db.execute(
        select(Queue).where(
            Queue.id == target_queue_id,
            Queue.is_deleted == False
        )
    )
    target_queue = queue_result.scalar_one_or_none()
    if not target_queue:
        raise ValueError("Целевая очередь не найдена или удалена")
    
    all_tickets_result = await db.execute(
        select(Ticket).where(
            Ticket.queue_id == target_queue_id,
            Ticket.is_deleted == False
        ).order_by(Ticket.created_at.asc())
    )
    existing_tickets = all_tickets_result.scalars().all()
    
    ticket.queue_id = target_queue_id
    ticket.status = "waiting"
    all_tickets = list(existing_tickets) + [ticket]
    
    all_tickets_sorted = sorted(all_tickets, key=lambda x: x.created_at)
    
    for position, t in enumerate(all_tickets_sorted, 1):
        t.position = position
    
    await db.commit()
    await db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


async def delete_ticket(db: AsyncSession, ticket_id: int, hard_delete: bool = False) -> bool:
    query = select(Ticket).where(Ticket.id == ticket_id)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return False
    
    if hard_delete:
        await db.delete(ticket)
    else:
        ticket.is_deleted = True
    
    await db.commit()
    return True


async def get_ticket_position(db: AsyncSession, ticket_id: int) -> TicketPositionInfo | None:
    query = select(Ticket).where(Ticket.id == ticket_id, Ticket.is_deleted == False)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return None
    
    result = await db.execute(
        select(func.count(Ticket.id))
        .where(
            Ticket.queue_id == ticket.queue_id,
            Ticket.position < ticket.position,
            Ticket.is_deleted == False,
            Ticket.status == "waiting"
        )
    )
    ahead_count = result.scalar() or 0
    
    return TicketPositionInfo(
        ticket_id=ticket.id,
        queue_id=ticket.queue_id,
        position=ticket.position,
        ahead_count=ahead_count,
        estimated_wait_time=ahead_count * 5
    )


async def verify_ticket_ownership(db: AsyncSession, ticket_id: int, session_id: str) -> bool:
    query = select(Ticket).where(Ticket.id == ticket_id, Ticket.is_deleted == False)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return False
    
    return ticket.session_id == session_id