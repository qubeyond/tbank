from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.db.models import Account
from app.core.security import security_service


security = HTTPBearer()


async def get_current_admin(
    token: str = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Account:
    """Получает текущего администратора по JWT токену.
    
    Args:
        token: JWT токен из заголовка Authorization
        db: Сессия базы данных
        
    Returns:
        Account: Объект администратора
        
    Raises:
        HTTPException: 401 если токен невалидный или администратор не найден
    """
    
    payload = security_service.verify_access_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидные учетные данные",
        )
    
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен",
        )
    
    admin = await db.scalar(select(Account).where(Account.username == username))
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Администратор не найден или неактивен",
        )
    
    return admin