from typing import Any
from fastapi import WebSocket
from .base import BaseConnectionManager


class TicketConnectionManager(BaseConnectionManager):
    def __init__(self):
        super().__init__()
        self.ticket_subscriptions: dict[int, set[WebSocket]] = {}

    async def subscribe_to_entity(self, websocket: WebSocket, ticket_id: int) -> None:
        await websocket.accept()
        if ticket_id not in self.ticket_subscriptions:
            self.ticket_subscriptions[ticket_id] = set()
        self.ticket_subscriptions[ticket_id].add(websocket)

    def unsubscribe_from_entity(self, websocket: WebSocket, ticket_id: int) -> None:
        if ticket_id in self.ticket_subscriptions:
            self.ticket_subscriptions[ticket_id].discard(websocket)
            if not self.ticket_subscriptions[ticket_id]:
                del self.ticket_subscriptions[ticket_id]

    async def notify_entity_subscribers(self, ticket_id: int, message: dict[str, Any]) -> None:
        if ticket_id not in self.ticket_subscriptions:
            return

        disconnected: set[WebSocket] = set()
        for connection in self.ticket_subscriptions[ticket_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
      
        for connection in disconnected:
            self.unsubscribe_from_entity(connection, ticket_id)

    async def get_subscribed_tickets(self) -> list[int]:
        """Получить список талонов с активными подписками"""
        return list(self.ticket_subscriptions.keys())

    async def get_ticket_subscribers_count(self, ticket_id: int) -> int:
        """Получить количество подписчиков талона"""
        return len(self.ticket_subscriptions.get(ticket_id, set()))