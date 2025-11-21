"""Схемы для мероприятий."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventBase(BaseModel):
    """Базовая схема мероприятия."""
    name: str
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class EventCreate(EventBase):
    """Схема для создания мероприятия."""
    pass


class EventUpdate(BaseModel):
    """Схема для обновления мероприятия."""
    name: str | None = None
    is_active: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class EventResponse(EventBase):
    """Схема ответа с мероприятием."""
    id: int
    code: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventDeleteRequest(BaseModel):
    """Схема для удаления мероприятия."""
    hard_delete: bool = False