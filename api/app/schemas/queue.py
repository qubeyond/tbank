from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class QueueBase(BaseModel):
    """Базовая схема очереди."""
    
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class QueueCreate(QueueBase):
    """Схема для создания очереди."""
    
    event_id: int


class QueueUpdate(BaseModel):
    """Схема для обновления очереди."""
    
    name: str | None = Field(None, max_length=10)
    is_active: bool | None = None
    current_position: int | None = Field(None, ge=0)

    model_config = ConfigDict(from_attributes=True)


class QueueResponse(QueueBase):
    """Схема ответа с информацией об очереди."""
    
    id: int
    event_id: int
    name: str = Field(..., max_length=10)
    is_deleted: bool
    current_position: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueueStatus(BaseModel):
    """Схема со статусом очереди."""
    
    queue_id: int
    name: str
    current_position: int
    waiting_count: int
    processing_count: int
    completed_count: int
    is_active: bool
    total_tickets: int

    model_config = ConfigDict(from_attributes=True)


class QueueDeleteRequest(BaseModel):
    """Схема для удаления очереди."""
    
    hard_delete: bool = False
    move_tickets_to: int | None = None