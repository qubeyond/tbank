from .ticket import TicketConnectionManager
from .base import BaseConnectionManager

class WebSocketManagerFactory:
    def __init__(self):
        self._managers: dict[str, BaseConnectionManager] = {
            "tickets": TicketConnectionManager(),
        }

    def get_manager(self, entity_type: str) -> BaseConnectionManager:
        """Получить менеджер для типа сущности"""
        if entity_type not in self._managers:
            raise ValueError(f"Unknown entity type: {entity_type}")
        return self._managers[entity_type]

    async def notify_all_managers(self, message: dict[str, object]) -> None:
        """Отправить сообщение во все каналы всех менеджеров"""
        for manager in self._managers.values():
            for channel in manager.active_connections:
                await manager.broadcast_to_channel(message, channel)


manager_factory = WebSocketManagerFactory()