from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Account
from app.core.dependencies import get_current_admin
from app.schemas.ticket import *
from app.services.crud.ticket import *


router = APIRouter(tags=["private-tickets"])


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket_route(ticket_id: int, db: AsyncSession = Depends(get_db),
                           current_admin: Account = Depends(get_current_admin)) -> TicketResponse:
    ticket = await get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return ticket


@router.get("/queue/{queue_id}", response_model=list[TicketResponse])
async def get_queue_tickets(queue_id: int, include_deleted: bool = Query(False), db: AsyncSession = Depends(get_db),
                            current_admin: Account = Depends(get_current_admin)) -> list[TicketResponse]:
    tickets = await get_tickets_by_queue(db, queue_id, include_deleted)
    return tickets


@router.get("/user/{session_id}", response_model=list[TicketResponse])
async def get_user_tickets(session_id: str, include_deleted: bool = Query(False), db: AsyncSession = Depends(get_db),
                           current_admin: Account = Depends(get_current_admin)) -> list[TicketResponse]:
    tickets = await get_tickets_by_session(db, session_id, include_deleted)
    return tickets


@router.get("/{ticket_id}/position", response_model=TicketPositionInfo)
async def get_ticket_position_route(ticket_id: int, db: AsyncSession = Depends(get_db), 
                                    current_admin: Account = Depends(get_current_admin)) -> TicketPositionInfo:
    position_info = await get_ticket_position(db, ticket_id)
    if not position_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return position_info


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket_route(ticket_id: int, ticket_data: TicketUpdate, db: AsyncSession = Depends(get_db),
                              current_admin: Account = Depends(get_current_admin)) -> TicketResponse:
    ticket = await update_ticket(db, ticket_id, ticket_data)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return ticket


@router.post("/{ticket_id}/call", response_model=TicketResponse)
async def call_ticket_route(ticket_id: int, call_data: TicketCallRequest, db: AsyncSession = Depends(get_db),
                            current_admin: Account = Depends(get_current_admin)) -> TicketResponse:
    ticket = await call_ticket(db, ticket_id, call_data.notes)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return ticket


@router.post("/{ticket_id}/complete", response_model=TicketResponse)
async def complete_ticket_route(ticket_id: int, complete_data: TicketCompleteRequest, db: AsyncSession = Depends(get_db),
                                current_admin: Account = Depends(get_current_admin)) -> TicketResponse:
    ticket = await complete_ticket(db, ticket_id, complete_data.notes)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return ticket


@router.post("/{ticket_id}/cancel", response_model=TicketResponse)
async def cancel_ticket_route(ticket_id: int, db: AsyncSession = Depends(get_db),
                              current_admin: Account = Depends(get_current_admin)) -> TicketResponse:
    ticket = await cancel_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    return ticket


@router.post("/{ticket_id}/move", response_model=TicketResponse)
async def move_ticket_route(ticket_id: int, move_data: TicketMoveRequest, db: AsyncSession = Depends(get_db),
                            current_admin: Account = Depends(get_current_admin)) -> TicketResponse:
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


@router.delete("/{ticket_id}")
async def delete_ticket_route(ticket_id: int, delete_request: TicketDeleteRequest, db: AsyncSession = Depends(get_db),
                              current_admin: Account = Depends(get_current_admin)) -> dict:
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