from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.models import Account
from app.core.dependencies import get_current_admin
from app.schemas.queue import (
    QueueCreate, QueueResponse, QueueStatus, QueueUpdate, QueueDeleteRequest
)
from app.utils.crud.queue import (
    create_queue, get_queue, get_queues_by_event, update_queue, 
    delete_queue, call_next, get_queue_status, reset_queue
)


router = APIRouter(tags=["private-queues"])


# POST
@router.post(
    "/", 
    response_model=QueueResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Создать очередь",
    description="Создание новой очереди для мероприятия. Имя очереди генерируется автоматически (A, B, C...)."
)
async def create_queue_route(
    queue_data: QueueCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> QueueResponse:
    """
    Args:
        queue_data: Данные для создания очереди
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        QueueResponse: Созданная очередь
        
    Raises:
        HTTPException: 400 при ошибке валидации данных
    """
    
    try:
        return await create_queue(db, queue_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# GET
@router.get(
    "/", 
    response_model=list[QueueResponse],
    summary="Получить очереди мероприятия",
    description="Получение списка всех очередей мероприятия. Поддерживает фильтрацию по удаленным очередям."
)
async def get_event_queues(
    event_id: int = Query(...),
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> list[QueueResponse]:
    """
    Args:
        event_id: ID мероприятия
        include_deleted: Включать удаленные очереди
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        list[QueueResponse]: Список очередей мероприятия
    """
    
    queues = await get_queues_by_event(db, event_id, include_deleted)
    return queues


@router.get(
    "/{queue_id}", 
    response_model=QueueResponse,
    summary="Получить очередь по ID", 
    description="Получение полной информации об очереди по ее идентификатору."
)
async def get_queue_route(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> QueueResponse:
    """
    Args:
        queue_id: ID очереди
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        QueueResponse: Найденная очередь
        
    Raises:
        HTTPException: 404 если очередь не найдена
    """
    
    queue = await get_queue(db, queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Очередь не найдена"
        )
    return queue


@router.get(
    "/{queue_id}/status", 
    response_model=QueueStatus,
    summary="Получить статус очереди",
    description="Получение текущего статуса очереди: количество ожидающих, обслуживаемых и завершенных талонов."
)
async def get_queue_status_route(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> QueueStatus:
    """
    Args:
        queue_id: ID очереди
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        QueueStatus: Статус очереди
        
    Raises:
        HTTPException: 404 если очередь не найдена
    """
    
    status_data = await get_queue_status(db, queue_id)
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Очередь не найдена"
        )
    return QueueStatus(**status_data)


# PUT
@router.put(
    "/{queue_id}", 
    response_model=QueueResponse,
    summary="Обновить очередь",
    description="Обновление информации об очереди. Позволяет изменить имя, активность или текущую позицию."
)
async def update_queue_route(
    queue_id: int,
    queue_data: QueueUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> QueueResponse:
    """
    Args:
        queue_id: ID очереди для обновления
        queue_data: Новые данные очереди
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        QueueResponse: Обновленная очередь
        
    Raises:
        HTTPException: 404 если очередь не найдена
        HTTPException: 400 при ошибке валидации данных
    """
    
    try:
        queue = await update_queue(db, queue_id, queue_data)
        if not queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Очередь не найдена"
            )
        return queue
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# DELETE
@router.delete(
    "/{queue_id}",
    summary="Удалить очередь",
    description="Удаление очереди из системы. Поддерживает soft delete и hard delete. Возможность перемещения талонов в другую очередь."
)
async def delete_queue_route(
    queue_id: int,
    delete_request: QueueDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> dict:
    """
    Args:
        queue_id: ID очереди для удаления
        delete_request: Параметры удаления
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        dict: Результат удаления
        
    Raises:
        HTTPException: 404 если очередь не найдена
        HTTPException: 400 при ошибке валидации данных
    """
    
    try:
        success = await delete_queue(
            db, 
            queue_id, 
            delete_request.hard_delete,
            delete_request.move_tickets_to
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Очередь не найдена"
            )
        
        delete_type = "hard delete" if delete_request.hard_delete else "soft delete"
        response = {
            "message": f"Очередь удалена ({delete_type})",
            "queue_id": queue_id,
            "hard_delete": delete_request.hard_delete
        }
        
        if delete_request.move_tickets_to:
            response["tickets_moved_to"] = delete_request.move_tickets_to
            
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# POST actions
@router.post(
    "/{queue_id}/next", 
    response_model=QueueResponse,
    summary="Вызвать следующего",
    description="Вызов следующего талона в очереди. Увеличивает текущую позицию очереди на 1."
)
async def call_next_route(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> QueueResponse:
    """
    Args:
        queue_id: ID очереди
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        QueueResponse: Обновленная очередь
        
    Raises:
        HTTPException: 404 если очередь не найдена
    """
    
    queue = await call_next(db, queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Очередь не найдена"
        )
    return queue


@router.post(
    "/{queue_id}/reset", 
    response_model=QueueResponse,
    summary="Сбросить очередь",
    description="Сброс текущей позиции очереди на 0. Не влияет на талоны, только на счетчик текущей позиции."
)
async def reset_queue_route(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> QueueResponse:
    """
    Args:
        queue_id: ID очереди
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        QueueResponse: Обновленная очередь
        
    Raises:
        HTTPException: 404 если очередь не найдена
    """
    
    queue = await reset_queue(db, queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Очередь не найдена"
        )
    return queue