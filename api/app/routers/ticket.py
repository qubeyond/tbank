"""Роуты для работы с талонами."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.ticket import (
    TicketCreate, TicketResponse, TicketUpdate, 
    TicketCallRequest, TicketCompleteRequest,
    TicketMoveRequest, TicketDeleteRequest
)
from app.utils.crud.ticket import (
    create_ticket, get_ticket, get_tickets_by_queue,
    get_tickets_by_user, update_ticket, call_ticket,
    complete_ticket, cancel_ticket, move_ticket,
    delete_ticket, get_ticket_position
)

router = APIRouter()


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket_route(
    ticket_data: TicketCreate,  
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Создать новый талон (автоматически распределяется в наименее загруженную очередь мероприятия)."""
    try:
        return await create_ticket(db, ticket_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket_route(
    ticket_id: int,
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Получить талон по ID."""
    ticket = await get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return ticket


@router.get("/queue/{queue_id}", response_model=list[TicketResponse])
async def get_queue_tickets(
    queue_id: int,
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db)
) -> list[TicketResponse]:
    """Получить талоны очереди."""
    tickets = await get_tickets_by_queue(db, queue_id, include_deleted)
    return tickets


@router.get("/user/{user_identity}", response_model=list[TicketResponse])
async def get_user_tickets(
    user_identity: str,
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db)
) -> list[TicketResponse]:
    """Получить талоны пользователя."""
    tickets = await get_tickets_by_user(db, user_identity, include_deleted)
    return tickets


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket_route(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Обновить талон."""
    ticket = await update_ticket(db, ticket_id, ticket_data)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return ticket


@router.post("/{ticket_id}/call", response_model=TicketResponse)
async def call_ticket_route(
    ticket_id: int,
    call_data: TicketCallRequest,
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Вызвать талон."""
    ticket = await call_ticket(db, ticket_id, call_data.notes)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return ticket


@router.post("/{ticket_id}/complete", response_model=TicketResponse)
async def complete_ticket_route(
    ticket_id: int,
    complete_data: TicketCompleteRequest,
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Завершить обслуживание по талону."""
    ticket = await complete_ticket(db, ticket_id, complete_data.notes)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return ticket


@router.post("/{ticket_id}/cancel", response_model=TicketResponse)
async def cancel_ticket_route(
    ticket_id: int,
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Отменить талон."""
    ticket = await cancel_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return ticket


@router.post("/{ticket_id}/move", response_model=TicketResponse)
async def move_ticket_route(
    ticket_id: int,
    move_data: TicketMoveRequest,
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Переместить талон в другую очередь."""
    try:
        ticket = await move_ticket(db, ticket_id, move_data.target_queue_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        return ticket
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{ticket_id}")
async def delete_ticket_route(
    ticket_id: int,
    delete_request: TicketDeleteRequest,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Удалить талон."""
    success = await delete_ticket(db, ticket_id, delete_request.hard_delete)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    delete_type = "hard" if delete_request.hard_delete else "soft"
    return {
        "message": f"Ticket {delete_type} deleted successfully",
        "ticket_id": ticket_id,
        "hard_delete": delete_request.hard_delete
    }


@router.get("/{ticket_id}/position")
async def get_ticket_position_route(
    ticket_id: int,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Получить позицию талона в очереди."""
    position_info = await get_ticket_position(db, ticket_id)
    if not position_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return position_info