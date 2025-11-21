from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from app.db.base import Base


class Ticket(Base):
    """Модель талона участника в очереди.
    
    Атрибуты:
        id: Уникальный идентификатор талона в БД
        queue_id: Ссылка на очередь
        position: Позиция в очереди (1, 2, 3...)
        user_identity: Идентификатор пользователя (фингерпринт, TG ID, etc.)
        status: Статус талона
        notes: Дополнительные заметки
        is_deleted: Удален ли талон (soft delete)
        created_at: Время создания талона
        updated_at: Время последнего обновления
        called_at: Время когда талон был вызван
        completed_at: Время завершения обслуживания
        queue: Связь с очередью
    """

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    queue_id: Mapped[int] = mapped_column(
        ForeignKey("queues.id", ondelete="CASCADE"),
        nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    user_identity: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), 
        default="waiting",  # waiting, called, completed, cancelled
        nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    called_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Связи
    queue: Mapped["Queue"] = relationship("Queue", back_populates="tickets")