"""Роуты для работы с очередями."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.queue import (
    QueueCreate, 
    QueueResponse, 
    QueueStatus, 
    QueueUpdate,
    QueueDeleteRequest
)
from app.utils.crud.queue import (
    create_queue, 
    get_queue, 
    get_queues_by_event, 
    update_queue,
    delete_queue,
    call_next,
    get_queue_status,
    reset_queue
)

router = APIRouter()


@router.post("/", response_model=QueueResponse, status_code=status.HTTP_201_CREATED)
async def create_queue_route(
    queue_data: QueueCreate,
    db: AsyncSession = Depends(get_db)
) -> QueueResponse:
    """Создать новую очередь для мероприятия."""
    try:
        return await create_queue(db, queue_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/event/{event_id}", response_model=list[QueueResponse])
async def get_event_queues(
    event_id: int,
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db)
) -> list[QueueResponse]:
    """Получить очереди мероприятия."""
    queues = await get_queues_by_event(db, event_id, include_deleted)
    return queues


@router.get("/{queue_id}", response_model=QueueResponse)
async def get_queue_route(
    queue_id: int,
    db: AsyncSession = Depends(get_db)
) -> QueueResponse:
    """Получить очередь по ID."""
    queue = await get_queue(db, queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )
    return queue


@router.put("/{queue_id}", response_model=QueueResponse)
async def update_queue_route(
    queue_id: int,
    queue_data: QueueUpdate,
    db: AsyncSession = Depends(get_db)
) -> QueueResponse:
    """Обновить очередь."""
    try:
        queue = await update_queue(db, queue_id, queue_data)
        if not queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Queue not found"
            )
        return queue
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{queue_id}")
async def delete_queue_route(
    queue_id: int,
    delete_request: QueueDeleteRequest,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Удалить очередь."""
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
                detail="Queue not found"
            )
        
        delete_type = "hard" if delete_request.hard_delete else "soft"
        response = {
            "message": f"Queue {delete_type} deleted successfully",
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


@router.get("/{queue_id}/status", response_model=QueueStatus)
async def get_queue_status_route(
    queue_id: int,
    db: AsyncSession = Depends(get_db)
) -> QueueStatus:
    """Получить статус очереди."""
    status_data = await get_queue_status(db, queue_id)
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )
    return QueueStatus(**status_data)


@router.post("/{queue_id}/next", response_model=QueueResponse)
async def call_next_route(
    queue_id: int,
    db: AsyncSession = Depends(get_db)
) -> QueueResponse:
    """Вызвать следующего в очереди."""
    queue = await call_next(db, queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )
    return queue


@router.post("/{queue_id}/reset", response_model=QueueResponse)
async def reset_queue_route(
    queue_id: int,
    db: AsyncSession = Depends(get_db)
) -> QueueResponse:
    """Сбросить очередь (обнулить текущую позицию)."""
    queue = await reset_queue(db, queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )
    return queue