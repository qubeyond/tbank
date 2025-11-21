from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db import get_db


router = APIRouter(tags=["health"])

@router.get("/")
async def root():
    return {
        "message": "TBank Queue System API",
        "version": "0.1", 
        "docs": "/docs"
    }

@router.get("/status")
async def health_check():
    return {
        "status": "healthy",
        "service": "TBank Queue API", 
        "version": "0.1"
    }

@router.get("/db")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "message": str(e)}