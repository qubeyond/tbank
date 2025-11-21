"""CRUD операции для очередей."""
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.queue import Queue
from app.db.models.ticket import Ticket
from app.schemas.queue import QueueCreate, QueueUpdate


def generate_queue_name(existing_queues: list[Queue]) -> str:
    """Автоматически генерирует имя для новой очереди.
    
    Генерирует имена в порядке: A, B, C, ..., Z, AA, AB, ...
    """
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


async def create_queue(db: AsyncSession, queue_data: QueueCreate) -> Queue:
    """Создать новую очередь.
    
    Args:
        db: Асинхронная сессия базы данных
        queue_data: Данные для создания очереди
        
    Returns:
        Созданная очередь
    """
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
    return queue


async def get_queue(db: AsyncSession, queue_id: int, include_deleted: bool = False) -> Queue | None:
    """Получить очередь по ID.
    
    Args:
        db: Асинхронная сессия базы данных
        queue_id: ID очереди
        include_deleted: Включать удаленные очереди
        
    Returns:
        Очередь или None если не найдена
    """
    query = select(Queue).where(Queue.id == queue_id)
    if not include_deleted:
        query = query.where(Queue.is_deleted == False)
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_queues_by_event(
    db: AsyncSession, 
    event_id: int,
    include_deleted: bool = False
) -> list[Queue]:
    """Получить все очереди мероприятия.
    
    Args:
        db: Асинхронная сессия базы данных
        event_id: ID мероприятия
        include_deleted: Включать удаленные очереди
        
    Returns:
        Список очередей мероприятия
    """
    query = select(Queue).where(Queue.event_id == event_id)
    if not include_deleted:
        query = query.where(Queue.is_deleted == False)
    
    query = query.order_by(Queue.name)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_queue(db: AsyncSession, queue_id: int, queue_data: QueueUpdate) -> Queue | None:
    """Обновить очередь.
    
    Args:
        db: Асинхронная сессия базы данных
        queue_id: ID очереди
        queue_data: Данные для обновления
        
    Returns:
        Обновленная очередь или None если не найдена
    """
    queue = await get_queue(db, queue_id)
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
    return queue


async def delete_queue(
    db: AsyncSession, 
    queue_id: int, 
    hard_delete: bool = False,
    move_tickets_to: int | None = None
) -> bool:
    """Удалить очередь.
    
    Args:
        db: Асинхронная сессия базы данных
        queue_id: ID очереди
        hard_delete: Полное удаление из базы
        move_tickets_to: ID очереди для перемещения талонов
        
    Returns:
        True если удалено, False если не найдено
    """
    queue = await get_queue(db, queue_id, include_deleted=True)
    if not queue:
        return False
    
    if move_tickets_to:
        target_queue = await get_queue(db, move_tickets_to)
        if not target_queue:
            raise ValueError("Целевая очередь для перемещения талонов не найдена")
        
        await db.execute(
            Ticket.__table__.update()
            .where(Ticket.queue_id == queue_id)
            .values(queue_id=move_tickets_to)
        )
    
    if hard_delete:
        await db.delete(queue)
    else:
        queue.is_deleted = True
        queue.is_active = False
    
    await db.commit()
    return True


async def call_next(db: AsyncSession, queue_id: int) -> Queue | None:
    """Вызвать следующего в очереди.
    
    Args:
        db: Асинхронная сессия базы данных
        queue_id: ID очереди
        
    Returns:
        Обновленная очередь или None если не найдена
    """
    queue = await get_queue(db, queue_id)
    if not queue:
        return None
    
    queue.current_position += 1
    await db.commit()
    await db.refresh(queue)
    return queue


async def get_queue_status(db: AsyncSession, queue_id: int) -> dict:
    """Получить статус очереди.
    
    Args:
        db: Асинхронная сессия базы данных
        queue_id: ID очереди
        
    Returns:
        Словарь со статусом очереди
    """
    queue = await get_queue(db, queue_id)
    if not queue:
        return {}
    
    result = await db.execute(
        select(
            func.count(Ticket.id).filter(Ticket.status == "waiting").label("waiting"),
            func.count(Ticket.id).filter(Ticket.status == "processing").label("processing"),
            func.count(Ticket.id).filter(Ticket.status == "completed").label("completed"),
            func.count(Ticket.id).label("total")
        ).where(Ticket.queue_id == queue_id)
    )
    
    counts = result.first()
    
    return {
        "queue_id": queue.id,
        "name": queue.name,
        "current_position": queue.current_position,
        "waiting_count": counts.waiting or 0,
        "processing_count": counts.processing or 0,
        "completed_count": counts.completed or 0,
        "is_active": queue.is_active,
        "total_tickets": counts.total or 0
    }


async def reset_queue(db: AsyncSession, queue_id: int) -> Queue | None:
    """Сбросить очередь (обнулить текущую позицию).
    
    Args:
        db: Асинхронная сессия базы данных
        queue_id: ID очереди
        
    Returns:
        Обновленная очередь или None если не найдена
    """
    queue = await get_queue(db, queue_id)
    if not queue:
        return None
    
    queue.current_position = 0
    await db.commit()
    await db.refresh(queue)
    return queue