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
    event_analytics_router,
    queue_analytics_router,
    ticket_analytics_router,
    ticket_ws_router,
    websocket_management_router
)

app = FastAPI(
    title="TBank Queue API",
    description="Queue management system for TBank",
    version="0.1",
    debug=settings.DEBUG,
)

app.add_middleware(CORSMiddleware, **CORS_SETTINGS)

# Health endpoints
app.include_router(private_health_router, prefix="/health")

# Authentication & Management
app.include_router(private_auth_router, prefix="/auth")
app.include_router(private_management_router, prefix="/management")

# Core entities
app.include_router(private_event_router, prefix="/event")
app.include_router(private_queue_router, prefix="/queue")
app.include_router(private_ticket_router, prefix="/ticket")

# Public API
app.include_router(public_ticket_router, prefix="/ticket")

# Analytics
app.include_router(event_analytics_router, prefix="/analytics")
app.include_router(queue_analytics_router, prefix="/analytics")
app.include_router(ticket_analytics_router, prefix="/analytics")

# WebSocket
app.include_router(ticket_ws_router, prefix="/ws")
app.include_router(websocket_management_router, prefix="/ws/management")