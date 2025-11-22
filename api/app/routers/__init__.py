from .public.auth import router as private_auth_router
from .private.management import router as private_management_router
from .private.health import router as private_health_router
from .private.event import router as private_event_router
from .private.queue import router as private_queue_router
from .private.ticket import router as private_ticket_router

from .public.ticket import router as public_ticket_router

from .analytics.event_analytics import router as event_analytics_router
from .analytics.queue_analytics import router as queue_analytics_router
from .analytics.ticket_analytics import router as ticket_analytics_router

__all__ = [
    "private_auth_router", 
    "private_management_router",
    "private_health_router", 
    "private_event_router", 
    "private_queue_router", 
    "private_ticket_router",
    "public_ticket_router",
    "event_analytics_router",
    "queue_analytics_router",
    "ticket_analytics_router"
]