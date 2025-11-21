from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import health_router, event_router, queue_router, ticket_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="TBank Queue API",
        description="Queue management system for TBank",
        version="0.1",
        debug=settings.DEBUG,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  
            "http://127.0.0.1:3000",  
            "http://frontend:80"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(health_router, prefix="/health")
    app.include_router(event_router, prefix="/event")
    app.include_router(queue_router, prefix="/queue")
    app.include_router(ticket_router, prefix="/ticket")
    
    return app


app = create_app()