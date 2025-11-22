from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.db.models import Account
from app.core.security import security_service
from app.schemas import AdminLoginResponse


router = APIRouter(tags=["private-auth"])


@router.post(
    "/login", 
    response_model=AdminLoginResponse,
    summary="Аутентификация администратора",
    description="Аутентификация администратора с использованием Basic Auth и выдача JWT токена для доступа к защищенным эндпоинтам."
)
async def admin_login( 
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
    db: AsyncSession = Depends(get_db)
):
    """
    Args:
        credentials: Учетные данные Basic Auth (username и password)
        db: Сессия базы данных
        
    Returns:
        AdminLoginResponse: JWT токен и информация об администраторе
        
    Raises:
        HTTPException: 401 если учетные данные неверны или администратор неактивен
    """

    admin = await db.scalar(
        select(Account).where(Account.username == credentials.username)
    )
    
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    if not security_service.verify_password(credentials.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    access_token = security_service.create_access_token(
        data={"sub": admin.username}
    )
    
    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        admin={
            "id": admin.id,
            "username": admin.username,
            "email": admin.email
        }
    )