from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdatePublic
from app.utils.crud.ticket import (
    create_ticket, update_ticket_public, cancel_ticket, 
    get_tickets_by_session, verify_ticket_ownership
)


router = APIRouter(tags=["public-tickets"])


@router.post(
    "/", 
    response_model=TicketResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Создать талон",
    description="Создать новый талон в наименее загруженной очереди мероприятия"
)
async def create_ticket_route(
    ticket_data: TicketCreate,  
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """
    Создание нового талона.
    
    Args:
        ticket_data: Данные для создания талона
        db: Сессия базы данных
        
    Returns:
        TicketResponse: Созданный талон
        
    Raises:
        HTTPException: 400 - Неверные данные или мероприятие не найдено
        HTTPException: 404 - Мероприятие или очередь не найдены
    """
    try:
        return await create_ticket(db, ticket_data)
    except ValueError as e:
        error_msg = str(e)
        
        # Уточняем статус код в зависимости от текста ошибки
        if "не найдено" in error_msg.lower():
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        
        raise HTTPException(
            status_code=status_code,
            detail=error_msg
        )
    except Exception as e:
        # Ловим любые другие исключения чтобы не было 500
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании талона: {str(e)}"
        )


@router.get(
    "/my-tickets",
    response_model=list[TicketResponse],
    summary="Получить мои талоны",
    description="Получить все талоны текущего пользователя"
)
async def get_my_tickets(
    x_session_id: str = Header(..., alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db)
) -> list[TicketResponse]:
    """
    Получение всех талонов текущего пользователя.
    
    Args:
        x_session_id: Идентификатор сессии пользователя
        db: Сессия базы данных
        
    Returns:
        list[TicketResponse]: Список талонов пользователя
    """
    return await get_tickets_by_session(db, x_session_id)


@router.put(
    "/{ticket_id}", 
    response_model=TicketResponse,
    summary="Обновить заметку талона",
    description="Обновить заметку талона. Доступно только владельцу талона."
)
async def update_ticket_public(
    ticket_id: int,
    ticket_update: TicketUpdatePublic,
    x_session_id: str = Header(..., alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """
    Обновление заметки талона.
    
    Args:
        ticket_id: ID талона для обновления
        ticket_update: Данные для обновления
        x_session_id: Идентификатор сессии пользователя
        db: Сессия базы данных
        
    Returns:
        TicketResponse: Обновленный талон
        
    Raises:
        HTTPException: 404 - Талон не найден
        HTTPException: 403 - Доступ запрещен
        HTTPException: 400 - Невозможно обновить обработанный талон
    """
    # Проверяем права доступа
    if not await verify_ticket_ownership(db, ticket_id, x_session_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )
    
    # Обновляем талон
    ticket = await update_ticket_public(db, ticket_id, ticket_update, x_session_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден"
        )
    
    # Проверяем, что талон еще не обработан
    if ticket.status in ["called", "completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно обновить обработанный талон"
        )
    
    return ticket


@router.post(
    "/{ticket_id}/cancel", 
    response_model=TicketResponse,
    summary="Отменить талон", 
    description="Отмена талона. Доступно только владельцу талона."
)
async def cancel_ticket_route(
    ticket_id: int,
    x_session_id: str = Header(..., alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    """
    Отмена талона.
    
    Args:
        ticket_id: ID талона для отмены
        x_session_id: Идентификатор сессии пользователя
        db: Сессия базы данных
        
    Returns:
        TicketResponse: Отмененный талон
        
    Raises:
        HTTPException: 404 - Талон не найден
        HTTPException: 403 - Доступ запрещен
    """
    # Отменяем талон с проверкой прав
    ticket = await cancel_ticket(db, ticket_id, x_session_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Талон не найден или доступ запрещен"
        )
    
    return ticket