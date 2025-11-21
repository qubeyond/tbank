"""Роуты для работы с мероприятиями."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.event import EventCreate, EventResponse, EventUpdate, EventDeleteRequest
from app.utils.crud.event import (
    create_event, 
    get_event, 
    get_events, 
    update_event, 
    delete_event,
)

router = APIRouter()


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event_route(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db)
) -> EventResponse:
    """Создать новое мероприятие."""
    return await create_event(db, event_data)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event_route(
    event_id: int,
    db: AsyncSession = Depends(get_db)
) -> EventResponse:
    """Получить мероприятие по ID."""
    event = await get_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event


@router.get("/", response_model=list[EventResponse])
async def get_events_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db)
) -> list[EventResponse]:
    """Получить список мероприятий."""
    events = await get_events(db, skip=skip, limit=limit, include_deleted=include_deleted)
    return events


@router.put("/{event_id}", response_model=EventResponse)
async def update_event_route(
    event_id: int,
    event_data: EventUpdate,
    db: AsyncSession = Depends(get_db)
) -> EventResponse:
    """Обновить мероприятие."""
    event = await update_event(db, event_id, event_data)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event


@router.delete("/{event_id}")
async def delete_event_route(
    event_id: int,
    delete_request: EventDeleteRequest,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Удалить мероприятие."""
    success = await delete_event(db, event_id, delete_request.hard_delete)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    delete_type = "hard" if delete_request.hard_delete else "soft"
    return {
        "message": f"Event {delete_type} deleted successfully",
        "event_id": event_id,
        "hard_delete": delete_request.hard_delete
    }