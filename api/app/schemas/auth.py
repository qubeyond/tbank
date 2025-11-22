from pydantic import BaseModel

from typing import Optional
from datetime import datetime


class TokenResponse(BaseModel):
    """Схема ответа с JWT токеном."""
    
    access_token: str
    token_type: str

    class Config:
        from_attributes = True


class AdminInfo(BaseModel):
    """Информация об администраторе."""
    
    id: int
    username: str
    email: str
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminLoginResponse(BaseModel):
    """Схема ответа при успешном логине."""
    
    access_token: str
    token_type: str
    admin: AdminInfo

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Схема запроса для входа через JSON"""
    
    username: str
    password: str

    class Config:
        from_attributes = True


class LogoutResponse(BaseModel):
    """Схема ответа для выхода из системы"""
    
    message: str

    class Config:
        from_attributes = True