from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Account
from app.core.security import security_service
from app.schemas.admin import *


router = APIRouter(tags=["private-management"])
security = HTTPBearer()


async def get_current_admin(token: str = Depends(security), db: AsyncSession = Depends(get_db)) -> Account:
    payload = security_service.verify_access_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    admin = await db.scalar(select(Account).where(Account.username == username))
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found or inactive",
        )
    
    return admin


@router.get(
    "/test", 
    response_model=AdminTestResponse,
    summary="Тест аутентификации администратора",
    description="Тестовый эндпоинт для проверки корректности JWT аутентификации и получения информации о текущем администраторе."
)
async def admin_test_route(current_admin: Account = Depends(get_current_admin)):
    return AdminTestResponse(
        message="Admin authentication successful",
        admin=AdminResponse(
            id=current_admin.id,
            username=current_admin.username,
            email=current_admin.email,
            is_active=current_admin.is_active,
            created_at=current_admin.created_at
        )
    )


@router.get(
    "/me", 
    response_model=AdminResponse,
    summary="Получить информацию о текущем администраторе",
    description="Возвращает полную информацию о текущем аутентифицированном администраторе."
)
async def get_current_admin_info(current_admin: Account = Depends(get_current_admin)):
    return AdminResponse(
        id=current_admin.id,
        username=current_admin.username,
        email=current_admin.email,
        is_active=current_admin.is_active,
        created_at=current_admin.created_at
    )