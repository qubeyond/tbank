from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.security import CORS_SETTINGS
from app.routers import (
    private_health_router,
    private_event_router, 
    private_queue_router,
    private_ticket_router,
    private_auth_router,
    private_management_router,
    public_ticket_router,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="TBank Queue API",
        description="Queue management system for TBank",
        version="0.1",
        debug=settings.DEBUG,
    )
    
    app.add_middleware(CORSMiddleware, **CORS_SETTINGS)
    
    app.include_router(private_health_router, prefix="/health")
    app.include_router(private_event_router, prefix="/event")
    app.include_router(private_queue_router, prefix="/queue")
    app.include_router(private_ticket_router, prefix="/ticket")
    app.include_router(private_auth_router, prefix="/auth")
    app.include_router(private_management_router, prefix="/management")
    
    app.include_router(public_ticket_router, prefix="/ticket")
    
    return app


app = create_app()