from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.ticket import *
from app.services.crud.ticket import *


router = APIRouter(tags=["public-tickets"])


@router.post("/", response_model=TicketCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket_route(
    ticket_data: TicketCreate,  
    db: AsyncSession = Depends(get_db)
) -> TicketCreateResponse:
    try:
        ticket, is_existing = await create_ticket(db, ticket_data)
        
        if is_existing:
            message = "У вас уже есть активный талон на это мероприятие"
        else:
            message = "Талон успешно создан"
            
        return TicketCreateResponse(
            ticket=ticket,
            is_existing_ticket=is_existing,
            message=message
        )
            
    except ValueError as e:
        error_msg = str(e)
        status_code = status.HTTP_404_NOT_FOUND if "не найдено" in error_msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=error_msg)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании талона: {str(e)}"
        )


@router.get("/my-tickets", response_model=list[TicketResponse])
async def get_my_tickets(
    x_session_id: str = Header(..., alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db)
) -> list[TicketResponse]:
    return await get_tickets_by_session(db, x_session_id)


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket_public_route(
    ticket_id: int,
    ticket_update: TicketUpdatePublic,
    x_session_id: str = Header(..., alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    if not await verify_ticket_ownership(db, ticket_id, x_session_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )
    
    ticket = await update_ticket_public(db, ticket_id, ticket_update, x_session_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    
    if ticket.status in ["called", "completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно обновить обработанный талон"
        )
    
    return ticket


@router.post("/{ticket_id}/cancel", response_model=TicketResponse)
async def cancel_ticket_route(
    ticket_id: int,
    x_session_id: str = Header(..., alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    ticket = await cancel_ticket(db, ticket_id, x_session_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден или доступ запрещен"
        )
    
    return ticket