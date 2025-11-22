from fastapi import HTTPException, status
from sqlalchemy import select

from app.db import get_db
from app.db.models import Account
from app.core.security import security_service
from app.schemas import AdminLoginResponse, LogoutResponse


async def login_user(login_data) -> AdminLoginResponse:
    """Логика логина"""
    
    async for db in get_db():
        admin = await db.scalar(
            select(Account)
            .where(Account.username == login_data.username)
            .where(Account.is_active == True)
        )
        
        if not admin or not security_service.verify_password(login_data.password, admin.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        
        token = security_service.create_access_token({"sub": admin.username})
        
        return AdminLoginResponse(
            access_token=token,
            token_type="bearer",
            admin={
                "id": admin.id,
                "username": admin.username,
                "email": admin.email
            }
        )


async def logout_user(current_admin) -> LogoutResponse:
    """Логика логаута"""
   
    return LogoutResponse(message="Logout successful")