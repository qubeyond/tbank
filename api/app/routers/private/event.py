from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.models import Account
from app.core.dependencies import get_current_admin

from app.schemas import (
    EventCreate, EventResponse, 
    EventUpdate, EventDeleteRequest,
)
from app.utils.crud import (
    create_event, get_event, get_events, 
    update_event, delete_event,
)


router = APIRouter(tags=["private-events"])


# POST
@router.post(
    "/", 
    response_model=EventResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Создать мероприятие",
    description="Создание нового мероприятия в системе. Автоматически генерирует уникальный код мероприятия."
)
async def create_event_route(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> EventResponse:
    """
    Args:
        event_data: Данные для создания мероприятия
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        EventResponse: Созданное мероприятие
    """
    
    return await create_event(db, event_data)


# GET
@router.get(
    "/", 
    response_model=list[EventResponse],
    summary="Получить список мероприятий",
    description="Получение списка мероприятий с поддержкой пагинации и фильтрации по удаленным записям."
)
async def get_events_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> list[EventResponse]:
    """
    Args:
        skip: Количество записей для пропуска
        limit: Лимит записей на странице (1-1000)
        include_deleted: Включать удаленные мероприятия
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        list[EventResponse]: Список мероприятий
    """

    events = await get_events(
        db,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted
    )
    return events


@router.get(
    "/{event_id}", 
    response_model=EventResponse,
    summary="Получить мероприятие по ID",
    description="Получение полной информации о мероприятии по его идентификатору."
)
async def get_event_route(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> EventResponse:
    """
    Args:
        event_id: ID мероприятия
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        EventResponse: Найденное мероприятие
        
    Raises:
        HTTPException: 404 если мероприятие не найдено
    """

    event = await get_event(db, event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено"
        )
    
    return event


# PUT 
@router.put(
    "/{event_id}", 
    response_model=EventResponse,
    summary="Обновить мероприятие",
    description="Обновление информации о мероприятии. Позволяет изменить название и статус активности."
)
async def update_event_route(
    event_id: int,
    event_data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> EventResponse:
    """
    Args:
        event_id: ID мероприятия для обновления
        event_data: Новые данные мероприятия
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        EventResponse: Обновленное мероприятие
        
    Raises:
        HTTPException: 404 если мероприятие не найдено
    """

    event = await update_event(db, event_id, event_data)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено"
        )
    
    return event


# DELETE
@router.delete(
    "/{event_id}",
    summary="Удалить мероприятие",
    description="Удаление мероприятия из системы. Поддерживает soft delete и hard delete."
)
async def delete_event_route(
    event_id: int,
    delete_request: EventDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> dict:
    """
    Args:
        event_id: ID мероприятия для удаления
        delete_request: Параметры удаления (hard_delete: bool)
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        dict: Результат удаления
        
    Raises:
        HTTPException: 404 если мероприятие не найдено
    """

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