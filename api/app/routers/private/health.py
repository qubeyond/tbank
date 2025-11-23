from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.db.models import Account
from app.core.dependencies import get_current_admin


router = APIRouter(tags=["private-health"])


@router.get(
    "/",
    summary="Основная информация о API",
    description="Возвращает основную информацию о системе управления очередями TBank."
)
async def root(current_admin: Account = Depends(get_current_admin)) -> dict:
    return {
        "message": "TBank Queue System API",
        "version": "0.1", 
        "docs": "/docs"
    }


@router.get(
    "/status",
    summary="Проверить статус службы", 
    description="Проверка общего статуса работы сервиса управления очередями."
)
async def health_check(current_admin: Account = Depends(get_current_admin)) -> dict:
    return {
        "status": "healthy",
        "service": "TBank Queue API", 
        "version": "0.1"
    }


@router.get(
    "/db",
    summary="Проверить подключение к БД",
    description="Проверка подключения и работоспособности базы данных системы."
)
async def db_health_check(db: AsyncSession = Depends(get_db),
                          current_admin: Account = Depends(get_current_admin)) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "message": str(e)}