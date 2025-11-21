from pydantic import BaseModel
from datetime import datetime


class AdminResponse(BaseModel):
    """Схема ответа с информацией об администраторе."""
    
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime


class AdminTestResponse(BaseModel):
    """Схема ответа тестового рута."""
    
    message: str
    admin: AdminResponse