"""CRUD операции для талонов."""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ticket import Ticket
from app.db.models.queue import Queue
from app.db.models.event import Event
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.utils.crud.queue import get_queues_by_event

async def create_ticket(db: AsyncSession, ticket_data: TicketCreate) -> Ticket:
    """Создать новый талон с автоматическим распределением в наименее загруженную очередь."""
    
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
        raise ValueError("No suitable queue found")
    
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
        user_identity=ticket_data.user_identity,  
        position=next_position,
        notes=ticket_data.notes
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def find_least_loaded_queue(db: AsyncSession, queues: list[Queue]) -> Queue | None:
    """Найти наименее загруженную очередь.
    
    Args:
        db: Асинхронная сессия базы данных
        queues: Список очередей для выбора
        
    Returns:
        Наименее загруженная очередь
    """
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


async def get_ticket(db: AsyncSession, ticket_id: int, include_deleted: bool = False) -> Ticket | None:
    """Получить талон по ID.
    
    Args:
        db: Асинхронная сессия базы данных
        ticket_id: ID талона
        include_deleted: Включать удаленные талоны
        
    Returns:
        Талон или None если не найден
    """
    query = select(Ticket).where(Ticket.id == ticket_id)
    if not include_deleted:
        query = query.where(Ticket.is_deleted == False)
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_tickets_by_queue(
    db: AsyncSession, 
    queue_id: int, 
    include_deleted: bool = False
) -> list[Ticket]:
    """Получить все талоны в очереди.
    
    Args:
        db: Асинхронная сессия базы данных
        queue_id: ID очереди
        include_deleted: Включать удаленные талоны
        
    Returns:
        Список талонов в очереди
    """
    query = select(Ticket).where(Ticket.queue_id == queue_id)
    if not include_deleted:
        query = query.where(Ticket.is_deleted == False)
    
    query = query.order_by(Ticket.position)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_tickets_by_user(
    db: AsyncSession, 
    user_identity: str,
    include_deleted: bool = False
) -> list[Ticket]:
    """Получить все талоны пользователя.
    
    Args:
        db: Асинхронная сессия базы данных
        user_identity: Идентификатор пользователя
        include_deleted: Включать удаленные талоны
        
    Returns:
        Список талонов пользователя
    """
    query = select(Ticket).where(Ticket.user_identity == user_identity)
    if not include_deleted:
        query = query.where(Ticket.is_deleted == False)
    
    query = query.order_by(Ticket.created_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_ticket(db: AsyncSession, ticket_id: int, ticket_data: TicketUpdate) -> Ticket | None:
    """Обновить талон.
    
    Args:
        db: Асинхронная сессия базы данных
        ticket_id: ID талона
        ticket_data: Данные для обновления
        
    Returns:
        Обновленный талон или None если не найден
    """
    ticket = await get_ticket(db, ticket_id)
    if not ticket:
        return None
    
    update_data = ticket_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)
    
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def call_ticket(db: AsyncSession, ticket_id: int, notes: str | None = None) -> Ticket | None:
    """Вызвать талон.
    
    Args:
        db: Асинхронная сессия базы данных
        ticket_id: ID талона
        notes: Дополнительные заметки
        
    Returns:
        Обновленный талон или None если не найден
    """
    ticket = await get_ticket(db, ticket_id)
    if not ticket:
        return None
    
    ticket.status = "called"
    ticket.called_at = datetime.now()
    if notes:
        ticket.notes = notes
    
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def complete_ticket(db: AsyncSession, ticket_id: int, notes: str | None = None) -> Ticket | None:
    """Завершить талон.
    
    Args:
        db: Асинхронная сессия базы данных
        ticket_id: ID талона
        notes: Дополнительные заметки
        
    Returns:
        Обновленный талон или None если не найден
    """
    ticket = await get_ticket(db, ticket_id)
    if not ticket:
        return None
    
    ticket.status = "completed"
    ticket.completed_at = datetime.now()
    if notes:
        ticket.notes = notes
    
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def cancel_ticket(db: AsyncSession, ticket_id: int, notes: str | None = None) -> Ticket | None:
    """Отменить талон.
    
    Args:
        db: Асинхронная сессия базы данных
        ticket_id: ID талона
        notes: Дополнительные заметки
        
    Returns:
        Обновленный талон или None если не найден
    """
    ticket = await get_ticket(db, ticket_id)
    if not ticket:
        return None
    
    ticket.status = "cancelled"
    if notes:
        ticket.notes = notes
    
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def move_ticket(db: AsyncSession, ticket_id: int, target_queue_id: int) -> Ticket | None:
    """Переместить талон в другую очередь с учетом времени создания.
    
    Args:
        db: Асинхронная сессия базы данных
        ticket_id: ID талона
        target_queue_id: ID целевой очереди
        
    Returns:
        Обновленный талон или None если не найден
    """
    ticket = await get_ticket(db, ticket_id)
    if not ticket:
        return None
    
    # Проверяем, что целевая очередь существует и не удалена
    queue_result = await db.execute(
        select(Queue).where(
            Queue.id == target_queue_id,
            Queue.is_deleted == False
        )
    )
    target_queue = queue_result.scalar_one_or_none()
    if not target_queue:
        raise ValueError("Целевая очередь не найдена или удалена")
    
    # Получаем все талоны в целевой очереди (включая перемещаемый)
    all_tickets_result = await db.execute(
        select(Ticket).where(
            Ticket.queue_id == target_queue_id,
            Ticket.is_deleted == False
        ).order_by(Ticket.created_at.asc())
    )
    existing_tickets = all_tickets_result.scalars().all()
    
    # Добавляем перемещаемый талон в список
    ticket.queue_id = target_queue_id
    ticket.status = "waiting"
    all_tickets = list(existing_tickets) + [ticket]
    
    # Сортируем все талоны по времени создания
    all_tickets_sorted = sorted(all_tickets, key=lambda x: x.created_at)
    
    # Пересчитываем позиции
    for position, t in enumerate(all_tickets_sorted, 1):
        t.position = position
    
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def delete_ticket(db: AsyncSession, ticket_id: int, hard_delete: bool = False) -> bool:
    """Удалить талон.
    
    Args:
        db: Асинхронная сессия базы данных
        ticket_id: ID талона
        hard_delete: Полное удаление из базы
        
    Returns:
        True если удалено, False если не найдено
    """
    ticket = await get_ticket(db, ticket_id, include_deleted=True)
    if not ticket:
        return False
    
    if hard_delete:
        await db.delete(ticket)
    else:
        ticket.is_deleted = True
    
    await db.commit()
    return True


async def get_ticket_position(db: AsyncSession, ticket_id: int) -> dict | None:
    """Получить позицию талона в очереди.
    
    Args:
        db: Асинхронная сессия базы данных
        ticket_id: ID талона
        
    Returns:
        Информация о позиции или None если не найден
    """
    ticket = await get_ticket(db, ticket_id)
    if not ticket:
        return None
    
    # Считаем количество талонов перед текущим в той же очереди
    result = await db.execute(
        select(func.count(Ticket.id))
        .where(
            Ticket.queue_id == ticket.queue_id,
            Ticket.position < ticket.position,
            Ticket.is_deleted == False,
            Ticket.status == "waiting"  # Считаем только ожидающие
        )
    )
    ahead_count = result.scalar() or 0
    
    return {
        "ticket_id": ticket.id,
        "queue_id": ticket.queue_id,
        "position": ticket.position,
        "ahead_count": ahead_count,
        "estimated_wait_time": ahead_count * 5  # 5 минут на каждого
    }