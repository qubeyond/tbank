import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Event
from app.schemas.event import *


async def create_event(db: AsyncSession, event_data: EventCreate) -> EventResponse:
    code = str(uuid.uuid4())[:8].upper()
    
    event = Event(
        name=event_data.name,
        code=code,
        is_active=event_data.is_active
    )
    
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return EventResponse.model_validate(event)


async def get_event(db: AsyncSession, event_id: int, include_deleted: bool = False) -> EventResponse | None:
    query = select(Event).where(Event.id == event_id)
    if not include_deleted:
        query = query.where(Event.is_deleted == False)
    
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    return EventResponse.model_validate(event) if event else None


async def get_events(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    include_deleted: bool = False
) -> list[EventResponse]:
    query = select(Event)
    if not include_deleted:
        query = query.where(Event.is_deleted == False)
    
    query = query.offset(skip).limit(limit).order_by(Event.created_at.desc())
    
    result = await db.execute(query)
    events = result.scalars().all()
    return [EventResponse.model_validate(event) for event in events]


async def update_event(db: AsyncSession, event_id: int, event_data: EventUpdate) -> EventResponse | None:
    query = select(Event).where(Event.id == event_id, Event.is_deleted == False)
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        return None
    
    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    await db.commit()
    await db.refresh(event)
    return EventResponse.model_validate(event)


async def delete_event(db: AsyncSession, event_id: int, hard_delete: bool = False) -> bool:
    query = select(Event).where(Event.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        return False
    
    if hard_delete:
        await db.delete(event)
    else:
        event.is_deleted = True
        event.is_active = False
    
    await db.commit()
    return True


async def get_event_by_code(db: AsyncSession, code: str) -> EventResponse | None:
    result = await db.execute(
        select(Event).where(
            Event.code == code,
            Event.is_deleted == False
        )
    )
    event = result.scalar_one_or_none()
    return EventResponse.model_validate(event) if event else None