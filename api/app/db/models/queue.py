from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Queue(Base):
    """Модель очереди в рамках мероприятия.
    
    Атрибуты:
        id: Уникальный идентификатор очереди
        event_id: Ссылка на родительское мероприятие
        name: Название очереди (A, B, C...) - уникальное в рамках мероприятия
        is_active: Активна ли очередь
        is_deleted: Удалена ли очередь (soft delete)
        current_position: Текущая позиция (кого сейчас обслуживают)
        created_at: Время создания очереди
        updated_at: Время последнего обновления
        event: Связь с мероприятием
        tickets: Связь с талонами
    """

    __tablename__ = "queues"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(10), nullable=False)  
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    current_position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Связи
    event: Mapped["Event"] = relationship("Event", back_populates="queues")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="queue")