from typing import Any
from fastapi import WebSocket
from abc import ABC, abstractmethod


class BaseConnectionManager(ABC):
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Базовый метод подключения к каналу"""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Базовый метод отключения от канала"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """Отправить сообщение конкретному соединению"""
        await websocket.send_text(message)

    async def broadcast_to_channel(self, message: dict[str, Any], channel: str) -> None:
        """Отправить сообщение всем в канале"""
        if channel not in self.active_connections:
            return

        disconnected: set[WebSocket] = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        for connection in disconnected:
            self.disconnect(connection, channel)

    @abstractmethod
    async def subscribe_to_entity(self, websocket: WebSocket, entity_id: int) -> None:
        """Абстрактный метод для подписки на сущность"""
        pass

    @abstractmethod
    def unsubscribe_from_entity(self, websocket: WebSocket, entity_id: int) -> None:
        """Абстрактный метод для отписки от сущности"""
        pass

    @abstractmethod
    async def notify_entity_subscribers(self, entity_id: int, message: dict[str, Any]) -> None:
        """Абстрактный метод для уведомления подписчиков сущности"""
        pass
