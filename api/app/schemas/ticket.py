from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class TicketBase(BaseModel):
    """Базовая схема талона."""
    
    session_id: str = Field(..., max_length=100, description="Идентификатор сессии пользователя")
    notes: Optional[str] = Field(None, description="Дополнительные заметки")

    model_config = ConfigDict(from_attributes=True)


class TicketCreate(BaseModel):
    """Схема для создания талона."""
    
    event_code: str = Field(..., description="Код мероприятия")
    session_id: str = Field(..., max_length=100, description="Идентификатор сессии пользователя")
    notes: Optional[str] = Field(None, description="Дополнительные заметки")

    model_config = ConfigDict(from_attributes=True)


class TicketUpdate(BaseModel):
    """Схема для обновления талона (админ)."""
    
    status: Optional[Literal["waiting", "called", "completed", "cancelled"]] = Field(None, description="Статус талона")
    notes: Optional[str] = Field(None, description="Дополнительные заметки")
    session_id: Optional[str] = Field(None, max_length=100, description="Идентификатор сессии пользователя")

    model_config = ConfigDict(from_attributes=True)


class TicketUpdatePublic(BaseModel):
    """Схема для обновления талона (публичный)."""
    
    notes: Optional[str] = Field(None, description="Дополнительные заметки")

    model_config = ConfigDict(from_attributes=True)


class TicketResponse(BaseModel):
    """Схема ответа с талоном."""
    
    id: int = Field(..., description="ID талона")
    queue_id: int = Field(..., description="ID очереди")
    session_id: str = Field(..., description="Идентификатор сессии пользователя")
    position: int = Field(..., description="Позиция в очереди")
    status: str = Field(..., description="Статус талона")
    notes: Optional[str] = Field(None, description="Дополнительные заметки")
    is_deleted: bool = Field(..., description="Удален ли талон")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime = Field(..., description="Время обновления")
    called_at: Optional[datetime] = Field(None, description="Время вызова")
    completed_at: Optional[datetime] = Field(None, description="Время завершения")

    model_config = ConfigDict(from_attributes=True)


class TicketCallRequest(BaseModel):
    """Схема для вызова талона."""
    
    notes: Optional[str] = Field(None, description="Дополнительные заметки")


class TicketCompleteRequest(BaseModel):
    """Схема для завершения талона."""
    
    notes: Optional[str] = Field(None, description="Дополнительные заметки")


class TicketMoveRequest(BaseModel):
    """Схема для перемещения талона."""
    
    target_queue_id: int = Field(..., description="ID целевой очереди")


class TicketDeleteRequest(BaseModel):
    """Схема для удаления талона."""
    
    hard_delete: bool = Field(False, description="Полное удаление из базы данных")