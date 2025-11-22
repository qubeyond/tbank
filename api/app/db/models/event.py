from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Event(Base):
    """Модель мероприятия.
    
    Атрибуты:
        id: Уникальный идентификатор мероприятия
        name: Название мероприятия
        code: Уникальный код мероприятия (автогенерация)
        is_active: Активно ли мероприятие
        is_deleted: Удалено ли мероприятие (soft delete)
        created_at: Время создания
        updated_at: Время последнего обновления
        queues: Связь с очередями
    """

    __tablename__ = "events"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Связи
    queues: Mapped[list["Queue"]] = relationship("Queue", back_populates="event")