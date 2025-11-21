from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Account(Base):
    """Модель аккаунта для администраторов системы.
    
    Атрибуты:
        id: Уникальный идентификатор
        username: Уникальное имя пользователя
        email: Электронная почта
        hashed_password: Хэшированный пароль
        is_active: Активен ли аккаунт
        created_at: Время создания
        last_login: Время последнего входа
    """

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)