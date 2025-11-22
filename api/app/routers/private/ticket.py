# app/api/endpoints/private/tickets.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.models import Account
from app.core.dependencies import get_current_admin
from app.schemas.ticket import (
    TicketResponse, TicketUpdate, 
    TicketCallRequest, TicketCompleteRequest,
    TicketMoveRequest, TicketDeleteRequest
)
from app.utils.crud.ticket import (
    get_ticket, get_tickets_by_queue,
    get_tickets_by_session, update_ticket, call_ticket,
    complete_ticket, cancel_ticket, move_ticket,
    delete_ticket, get_ticket_position
)


router = APIRouter(tags=["private-tickets"])


@router.get(
    "/{ticket_id}", 
    response_model=TicketResponse,
    summary="Получить талон по ID",
    description="Получение полной информации о талоне по его идентификатору."
)
async def get_ticket_route(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin),
) -> TicketResponse:
    """
    Получение талона по ID.
    
    Args:
        ticket_id: ID талона
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        TicketResponse: Найденный талон
        
    Raises:
        HTTPException: 404 - Талон не найден
    """
    ticket = await get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return ticket


@router.get(
    "/queue/{queue_id}", 
    response_model=list[TicketResponse],
    summary="Получить талоны очереди",
    description="Получение списка всех талонов в указанной очереди."
)
async def get_queue_tickets(
    queue_id: int,
    include_deleted: bool = Query(False, description="Включать удаленные талоны"),
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> list[TicketResponse]:
    """
    Получение талонов очереди.
    
    Args:
        queue_id: ID очереди
        include_deleted: Включать удаленные талоны
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        list[TicketResponse]: Список талонов очереди
    """
    tickets = await get_tickets_by_queue(db, queue_id, include_deleted)
    return tickets


@router.get(
    "/user/{session_id}", 
    response_model=list[TicketResponse],
    summary="Получить талоны пользователя", 
    description="Получение всех талонов конкретного пользователя по session_id."
)
async def get_user_tickets(
    session_id: str,
    include_deleted: bool = Query(False, description="Включать удаленные талоны"),
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> list[TicketResponse]:
    """
    Получение талонов пользователя.
    
    Args:
        session_id: Идентификатор сессии пользователя
        include_deleted: Включать удаленные талоны
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        list[TicketResponse]: Список талонов пользователя
    """
    tickets = await get_tickets_by_session(db, session_id, include_deleted)
    return tickets


@router.get(
    "/{ticket_id}/position",
    summary="Получить позицию талона",
    description="Получение информации о текущей позиции талона в очереди."
)
async def get_ticket_position_route(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> dict:
    """
    Получение позиции талона.
    
    Args:
        ticket_id: ID талона
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        dict: Информация о позиции талона
        
    Raises:
        HTTPException: 404 - Талон не найден
    """
    position_info = await get_ticket_position(db, ticket_id)
    if not position_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return position_info


@router.put(
    "/{ticket_id}", 
    response_model=TicketResponse,
    summary="Обновить талон",
    description="Обновление информации о талоне."
)
async def update_ticket_route(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> TicketResponse:
    """
    Обновление талона.
    
    Args:
        ticket_id: ID талона для обновления
        ticket_data: Новые данные талона
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        TicketResponse: Обновленный талон
        
    Raises:
        HTTPException: 404 - Талон не найден
    """
    ticket = await update_ticket(db, ticket_id, ticket_data)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return ticket


@router.post(
    "/{ticket_id}/call", 
    response_model=TicketResponse,
    summary="Вызвать талон",
    description="Вызов талона для обслуживания."
)
async def call_ticket_route(
    ticket_id: int,
    call_data: TicketCallRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> TicketResponse:
    """
    Вызов талона.
    
    Args:
        ticket_id: ID талона
        call_data: Данные для вызова
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        TicketResponse: Обновленный талон
        
    Raises:
        HTTPException: 404 - Талон не найден
    """
    ticket = await call_ticket(db, ticket_id, call_data.notes)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return ticket


@router.post(
    "/{ticket_id}/complete", 
    response_model=TicketResponse,
    summary="Завершить обслуживание",
    description="Завершение обслуживания по талону."
)
async def complete_ticket_route(
    ticket_id: int,
    complete_data: TicketCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> TicketResponse:
    """
    Завершение обслуживания талона.
    
    Args:
        ticket_id: ID талона
        complete_data: Данные для завершения
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        TicketResponse: Обновленный талон
        
    Raises:
        HTTPException: 404 - Талон не найден
    """
    ticket = await complete_ticket(db, ticket_id, complete_data.notes)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return ticket


@router.post(
    "/{ticket_id}/cancel", 
    response_model=TicketResponse,
    summary="Отменить талон",
    description="Отмена талона администратором."
)
async def cancel_ticket_route(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> TicketResponse:
    """
    Отмена талона администратором.
    
    Args:
        ticket_id: ID талона
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        TicketResponse: Отмененный талон
        
    Raises:
        HTTPException: 404 - Талон не найден
    """
    ticket = await cancel_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return ticket


@router.post(
    "/{ticket_id}/move", 
    response_model=TicketResponse,
    summary="Переместить талон",
    description="Перемещение талона в другую очередь."
)
async def move_ticket_route(
    ticket_id: int,
    move_data: TicketMoveRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> TicketResponse:
    """
    Перемещение талона.
    
    Args:
        ticket_id: ID талона
        move_data: Данные для перемещения
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        TicketResponse: Обновленный талон
        
    Raises:
        HTTPException: 404 - Талон не найден
        HTTPException: 400 - Ошибка валидации данных
    """
    try:
        ticket = await move_ticket(db, ticket_id, move_data.target_queue_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Талон не найден"
            )
        return ticket
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{ticket_id}",
    summary="Удалить талон",
    description="Удаление талона из системы."
)
async def delete_ticket_route(
    ticket_id: int,
    delete_request: TicketDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Account = Depends(get_current_admin)
) -> dict:
    """
    Удаление талона.
    
    Args:
        ticket_id: ID талона для удаления
        delete_request: Параметры удаления
        db: Сессия базы данных
        current_admin: Текущий администратор
        
    Returns:
        dict: Результат удаления
        
    Raises:
        HTTPException: 404 - Талон не найден
    """
    success = await delete_ticket(db, ticket_id, delete_request.hard_delete)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    
    delete_type = "hard" if delete_request.hard_delete else "soft"
    return {
        "message": f"Талон удален ({delete_type} delete)",
        "ticket_id": ticket_id,
        "hard_delete": delete_request.hard_delete
    }