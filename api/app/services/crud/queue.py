from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Ticket, Queue
from app.schemas.queue import *


def generate_queue_name(existing_queues: list[Queue]) -> str:
    if not existing_queues:
        return "A"
    
    used_names = {q.name for q in existing_queues}
    
    name = "A"
    
    while name in used_names:
        if name[-1] == 'Z':
            if len(name) == 1:
                name = "AA"
            else:
                prefix = name[:-1]
                last_char = name[-1]
                if last_char == 'Z':
                    name = prefix + 'AA'
                else:
                    name = prefix + chr(ord(last_char) + 1)
        else:
            name = name[:-1] + chr(ord(name[-1]) + 1)
    
    return name


async def create_queue(db: AsyncSession, queue_data: QueueCreate) -> QueueResponse:
    existing_queues = await get_queues_by_event(db, queue_data.event_id)
    
    name = generate_queue_name(existing_queues)
    
    queue = Queue(
        event_id=queue_data.event_id,
        name=name,
        is_active=queue_data.is_active
    )
    
    db.add(queue)
    await db.commit()
    await db.refresh(queue)
    return QueueResponse.model_validate(queue)


async def get_queue(db: AsyncSession, queue_id: int, include_deleted: bool = False) -> QueueResponse | None:
    query = select(Queue).where(Queue.id == queue_id)
    if not include_deleted:
        query = query.where(Queue.is_deleted == False)
    
    result = await db.execute(query)
    queue = result.scalar_one_or_none()
    return QueueResponse.model_validate(queue) if queue else None


async def get_queues_by_event(
    db: AsyncSession, 
    event_id: int,
    include_deleted: bool = False
) -> list[QueueResponse]:
    query = select(Queue).where(Queue.event_id == event_id)
    if not include_deleted:
        query = query.where(Queue.is_deleted == False)
    
    query = query.order_by(Queue.name)
    
    result = await db.execute(query)
    queues = result.scalars().all()
    return [QueueResponse.model_validate(queue) for queue in queues]


async def update_queue(db: AsyncSession, queue_id: int, queue_data: QueueUpdate) -> QueueResponse | None:
    query = select(Queue).where(Queue.id == queue_id, Queue.is_deleted == False)
    result = await db.execute(query)
    queue = result.scalar_one_or_none()
    
    if not queue:
        return None
    
    if queue_data.name and queue_data.name != queue.name:
        result = await db.execute(
            select(Queue).where(
                Queue.event_id == queue.event_id,
                Queue.name == queue_data.name,
                Queue.is_deleted == False,
                Queue.id != queue_id
            )
        )
        if result.scalar_one_or_none():
            raise ValueError(f"Очередь с именем '{queue_data.name}' уже существует")
    
    update_data = queue_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(queue, field, value)
    
    await db.commit()
    await db.refresh(queue)
    return QueueResponse.model_validate(queue)


async def delete_queue(
    db: AsyncSession, 
    queue_id: int, 
    hard_delete: bool = False,
    move_tickets_to: int | None = None
) -> bool:
    query = select(Queue).where(Queue.id == queue_id)
    result = await db.execute(query)
    queue = result.scalar_one_or_none()
    
    if not queue:
        return False
    
    if move_tickets_to:
        target_queue = await get_queue(db, move_tickets_to)
        if not target_queue:
            raise ValueError("Целевая очередь для перемещения талонов не найдена")
        
        if target_queue.id == queue_id:
            raise ValueError("Нельзя переместить талоны в ту же очередь")
        
        tickets_to_move = await db.execute(
            select(Ticket).where(
                Ticket.queue_id == queue_id,
                Ticket.is_deleted == False
            ).order_by(Ticket.created_at.asc())
        )
        tickets = tickets_to_move.scalars().all()
        
        existing_tickets = await db.execute(
            select(Ticket).where(
                Ticket.queue_id == move_tickets_to,
                Ticket.is_deleted == False
            ).order_by(Ticket.created_at.asc())
        )
        existing_tickets_list = existing_tickets.scalars().all()
        
        all_tickets = list(existing_tickets_list) + list(tickets)
        all_tickets_sorted = sorted(all_tickets, key=lambda x: x.created_at)
        
        for position, ticket in enumerate(all_tickets_sorted, 1):
            ticket.position = position
            if ticket.queue_id == queue_id:
                ticket.queue_id = move_tickets_to
                ticket.status = "waiting"
    
    if hard_delete:
        await db.delete(queue)
    else:
        queue.is_deleted = True
        queue.is_active = False
    
    await db.commit()
    return True


async def get_queue_status(db: AsyncSession, queue_id: int) -> QueueStatus | None:
    query = select(Queue).where(Queue.id == queue_id, Queue.is_deleted == False)
    result = await db.execute(query)
    queue = result.scalar_one_or_none()
    
    if not queue:
        return None
    
    counts_result = await db.execute(
        select(
            func.count(Ticket.id).filter(
                Ticket.queue_id == queue_id,
                Ticket.is_deleted == False,
                Ticket.status == "waiting"
            ).label("waiting"),
            func.count(Ticket.id).filter(
                Ticket.queue_id == queue_id,
                Ticket.is_deleted == False,
                Ticket.status == "called"
            ).label("processing"),
            func.count(Ticket.id).filter(
                Ticket.queue_id == queue_id,
                Ticket.is_deleted == False,
                Ticket.status == "completed"
            ).label("completed"),
            func.count(Ticket.id).filter(
                Ticket.queue_id == queue_id,
                Ticket.is_deleted == False
            ).label("total")
        )
    )
    
    counts = counts_result.first()
    
    return QueueStatus(
        queue_id=queue.id,
        name=queue.name,
        current_position=queue.current_position,
        waiting_count=counts.waiting or 0,
        processing_count=counts.processing or 0,
        completed_count=counts.completed or 0,
        is_active=queue.is_active,
        total_tickets=counts.total or 0
    )


async def call_next(db: AsyncSession, queue_id: int) -> QueueResponse | None:
    query = select(Queue).where(Queue.id == queue_id, Queue.is_deleted == False)
    result = await db.execute(query)
    queue = result.scalar_one_or_none()
    
    if not queue:
        return None
    
    queue.current_position += 1
    await db.commit()
    await db.refresh(queue)
    return QueueResponse.model_validate(queue)


async def reset_queue(db: AsyncSession, queue_id: int) -> QueueResponse | None:
    query = select(Queue).where(Queue.id == queue_id, Queue.is_deleted == False)
    result = await db.execute(query)
    queue = result.scalar_one_or_none()
    
    if not queue:
        return None
    
    queue.current_position = 0
    await db.commit()
    await db.refresh(queue)
    return QueueResponse.model_validate(queue)