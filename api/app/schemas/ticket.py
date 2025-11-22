from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class TicketBase(BaseModel):
    """Базовая схема талона."""
    
    user_identity: str = Field(..., max_length=100)
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TicketCreate(BaseModel):
    """Схема для создания талона."""
    
    event_code: str
    user_identity: str = Field(..., max_length=100)
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TicketUpdate(BaseModel):
    """Схема для обновления талона."""
    
    status: Literal["waiting", "called", "completed", "cancelled"] | None = None
    notes: str | None = None
    user_identity: str | None = Field(None, max_length=100)

    model_config = ConfigDict(from_attributes=True)


class TicketResponse(TicketBase):
    """Схема ответа с талоном."""
    
    id: int
    queue_id: int
    position: int
    status: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    called_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class TicketCallRequest(BaseModel):
    """Схема для вызова талона."""
    
    notes: str | None = None


class TicketCompleteRequest(BaseModel):
    """Схема для завершения талона."""
    
    notes: str | None = None


class TicketMoveRequest(BaseModel):
    """Схема для перемещения талона."""
    
    target_queue_id: int


class TicketDeleteRequest(BaseModel):
    """Схема для удаления талона."""
    
    hard_delete: bool = False