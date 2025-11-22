from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from app.db.base import Base


class Ticket(Base):
    """Модель талона участника в очереди.
    
    Attributes:
        id: Уникальный идентификатор талона
        queue_id: ID очереди
        session_id: Идентификатор сессии пользователя
        position: Позиция в очереди
        status: Статус талона
        notes: Дополнительные заметки
        is_deleted: Флаг удаления
        created_at: Время создания
        updated_at: Время обновления
        called_at: Время вызова
        completed_at: Время завершения
        queue: Связь с очередью
    """

    __tablename__ = "tickets"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    queue_id: Mapped[int] = mapped_column(
        ForeignKey("queues.id", ondelete="CASCADE"),
        nullable=False
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), 
        default="waiting",
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