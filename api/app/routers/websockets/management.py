from fastapi import APIRouter, Depends
from app.services.websockets.managers import manager_factory
from app.core.dependencies import get_current_admin

router = APIRouter()

@router.get("/stats")
async def get_websocket_stats(current_admin = Depends(get_current_admin)):
    """Получить статистику WebSocket соединений"""
    ticket_manager = manager_factory.get_manager("tickets")
    
    return {
        "active_ticket_subscriptions": await ticket_manager.get_subscribed_tickets(),
        "total_ticket_subscriptions": len(ticket_manager.ticket_subscriptions),
        "queues_manager_connections": len(ticket_manager.active_connections.get("queues", set())),
        "events_manager_connections": len(ticket_manager.active_connections.get("events", set()))
    }