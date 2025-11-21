"""CRUD операции для мероприятий."""
import secrets
import string
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.event import Event
from app.schemas.event import EventCreate, EventUpdate


def generate_event_code(length: int = 8) -> str:
    """Генерация уникального кода мероприятия."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def create_event(db: AsyncSession, event_data: EventCreate) -> Event:
    """Создать новое мероприятие.
    
    Args:
        db: Асинхронная сессия базы данных
        event_data: Данные для создания мероприятия
        
    Returns:
        Созданное мероприятие
    """
    code = generate_event_code()
    
    while True:
        result = await db.execute(select(Event).where(Event.code == code))
        if not result.scalar_one_or_none():
            break
        code = generate_event_code()
    
    event = Event(
        name=event_data.name,
        code=code,
        is_active=event_data.is_active
    )
    
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def get_event(db: AsyncSession, event_id: int, include_deleted: bool = False) -> Event | None:
    """Получить мероприятие по ID.
    
    Args:
        db: Асинхронная сессия базы данных
        event_id: ID мероприятия
        include_deleted: Включать удаленные мероприятия
        
    Returns:
        Мероприятие или None если не найдено
    """
    query = select(Event).where(Event.id == event_id)
    if not include_deleted:
        query = query.where(Event.is_deleted == False)
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_events(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    include_deleted: bool = False
) -> list[Event]:
    """Получить список мероприятий.
    
    Args:
        db: Асинхронная сессия базы данных
        skip: Количество пропущенных записей
        limit: Максимальное количество записей
        include_deleted: Включать удаленные мероприятия
        
    Returns:
        Список мероприятий
    """
    query = select(Event)
    if not include_deleted:
        query = query.where(Event.is_deleted == False)
    
    query = query.offset(skip).limit(limit).order_by(Event.created_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_event(db: AsyncSession, event_id: int, event_data: EventUpdate) -> Event | None:
    """Обновить мероприятие.
    
    Args:
        db: Асинхронная сессия базы данных
        event_id: ID мероприятия
        event_data: Данные для обновления
        
    Returns:
        Обновленное мероприятие или None если не найдено
    """
    event = await get_event(db, event_id)
    if not event:
        return None
    
    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    await db.commit()
    await db.refresh(event)
    return event


async def delete_event(db: AsyncSession, event_id: int, hard_delete: bool = False) -> bool:
    """Удалить мероприятие.
    
    Args:
        db: Асинхронная сессия базы данных
        event_id: ID мероприятия
        hard_delete: Полное удаление из базы
        
    Returns:
        True если удалено, False если не найдено
    """
    event = await get_event(db, event_id, include_deleted=True)
    if not event:
        return False
    
    if hard_delete:
        await db.delete(event)
    else:
        event.is_deleted = True
        event.is_active = False
    
    await db.commit()
    return True


async def get_event_by_code(db: AsyncSession, code: str) -> Event | None:
    """Получить мероприятие по коду.
    
    Args:
        db: Асинхронная сессия базы данных
        code: Код мероприятия
        
    Returns:
        Мероприятие или None если не найдено
    """
    result = await db.execute(
        select(Event).where(
            Event.code == code,
            Event.is_deleted == False
        )
    )
    return result.scalar_one_or_none()