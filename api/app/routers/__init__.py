"""Роутеры API."""
from .health import router as health_router
from .event import router as event_router
from .queue import router as queue_router
from .ticket import router as ticket_router


__all__ = ["health_router", "event_router", "queue_router", "ticket_router"]