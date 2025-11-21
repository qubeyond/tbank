from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Схема ответа с JWT токеном."""
    
    access_token: str
    token_type: str


class AdminInfo(BaseModel):
    """Информация об администраторе."""
    
    id: int
    username: str
    email: str


class AdminLoginResponse(BaseModel):
    """Схема ответа при успешном логине."""
    
    access_token: str
    token_type: str
    admin: AdminInfo