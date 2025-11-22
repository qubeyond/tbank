from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.ticket import TicketCreate, TicketResponse
from app.utils.crud.ticket import create_ticket


router = APIRouter(tags=["public-tickets"])


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket_route(
    ticket_data: TicketCreate,  
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Создать новый талон (автоматически распределяется в наименее загруженную очередь мероприятия).
    
    Args:
        ticket_data: Данные для создания талона
        db: Сессия базы данных
        
    Returns:
        TicketResponse: Созданный талон
        
    Raises:
        HTTPException: 400 при ошибке валидации данных
    """
    
    try:
        return await create_ticket(db, ticket_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )