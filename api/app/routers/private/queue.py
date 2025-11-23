from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Account
from app.core.dependencies import get_current_admin
from app.schemas.queue import *
from app.services.crud.queue import *


router = APIRouter(tags=["private-queues"])


@router.post(
    "/", 
    response_model=QueueResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_queue_route(queue_data: QueueCreate, db: AsyncSession = Depends(get_db),
                             current_admin: Account = Depends(get_current_admin)) -> QueueResponse:
    try:
        return await create_queue(db, queue_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/", 
    response_model=list[QueueResponse]
)
async def get_event_queues(event_id: int = Query(...), include_deleted: bool = Query(False), db: AsyncSession = Depends(get_db),
                           current_admin: Account = Depends(get_current_admin)) -> list[QueueResponse]:
    queues = await get_queues_by_event(db, event_id, include_deleted)
    return queues


@router.get(
    "/{queue_id}", 
    response_model=QueueResponse
)
async def get_queue_route(queue_id: int, db: AsyncSession = Depends(get_db),
                          current_admin: Account = Depends(get_current_admin)) -> QueueResponse:
    queue = await get_queue(db, queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Очередь не найдена"
        )
    return queue


@router.get(
    "/{queue_id}/status", 
    response_model=QueueStatus
)
async def get_queue_status_route(queue_id: int, db: AsyncSession = Depends(get_db),
                                 current_admin: Account = Depends(get_current_admin)) -> QueueStatus:
    status_data = await get_queue_status(db, queue_id)
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Очередь не найдена"
        )
    return status_data


@router.put(
    "/{queue_id}", 
    response_model=QueueResponse
)
async def update_queue_route(queue_id: int, queue_data: QueueUpdate, db: AsyncSession = Depends(get_db),
                             current_admin: Account = Depends(get_current_admin)) -> QueueResponse: 
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


@router.delete(
    "/{queue_id}"
)
async def delete_queue_route(queue_id: int, delete_request: QueueDeleteRequest, db: AsyncSession = Depends(get_db),
                             current_admin: Account = Depends(get_current_admin)) -> dict:
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


@router.post(
    "/{queue_id}/next", 
    response_model=QueueResponse
)
async def call_next_route(queue_id: int, db: AsyncSession = Depends(get_db),
                          current_admin: Account = Depends(get_current_admin)) -> QueueResponse:
    queue = await call_next(db, queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Очередь не найдена"
        )
    return queue


@router.post(
    "/{queue_id}/reset", 
    response_model=QueueResponse
)
async def reset_queue_route(queue_id: int, db: AsyncSession = Depends(get_db),
                            current_admin: Account = Depends(get_current_admin)) -> QueueResponse:
    queue = await reset_queue(db, queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Очередь не найдена"
        )
    return queue