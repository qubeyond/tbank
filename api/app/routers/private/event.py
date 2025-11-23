from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Account
from app.core.dependencies import get_current_admin

from app.schemas.event import *
from app.services.crud.event import *


router = APIRouter(tags=["private-events"])


@router.post(
    "/", 
    response_model=EventResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_event_route(event_data: EventCreate, db: AsyncSession = Depends(get_db),
                             current_admin: Account = Depends(get_current_admin)) -> EventResponse:
    return await create_event(db, event_data)


@router.get(
    "/", 
    response_model=list[EventResponse]
)
async def get_events_route(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000),
                           include_deleted: bool = Query(False), db: AsyncSession = Depends(get_db),
                           current_admin: Account = Depends(get_current_admin)) -> list[EventResponse]:
    events = await get_events(
        db,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted
    )
    return events


@router.get(
    "/{event_id}", 
    response_model=EventResponse
)
async def get_event_route(event_id: int, db: AsyncSession = Depends(get_db),
                          current_admin: Account = Depends(get_current_admin)) -> EventResponse:
    event = await get_event(db, event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено"
        )
    
    return event


@router.put(
    "/{event_id}", 
    response_model=EventResponse
)
async def update_event_route(event_id: int, event_data: EventUpdate, db: AsyncSession = Depends(get_db),
                             current_admin: Account = Depends(get_current_admin)) -> EventResponse:
    event = await update_event(db, event_id, event_data)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено"
        )
    
    return event


@router.delete(
    "/{event_id}"
)
async def delete_event_route(event_id: int, delete_request: EventDeleteRequest, db: AsyncSession = Depends(get_db),
                             current_admin: Account = Depends(get_current_admin)) -> dict:
    success = await delete_event(db, event_id, delete_request.hard_delete)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено"
        )
    
    delete_type = "hard delete" if delete_request.hard_delete else "soft delete"
    
    return {
        "message": f"Мероприятие удалено ({delete_type})",
        "event_id": event_id,
        "hard_delete": delete_request.hard_delete
    }