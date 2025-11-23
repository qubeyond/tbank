from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.websockets.managers import manager_factory
from app.services.analytics.ticket_ws import get_ticket_websocket_data
from app.schemas.websocket import WebSocketMessage


class WebSocketNotifier:
    """Централизованная система уведомлений для WebSocket"""
    
    @staticmethod
    async def notify_ticket_update(ticket_id: int, db: AsyncSession) -> None:
        """Уведомить всех подписчиков талона об обновлении"""
        ticket_manager = manager_factory.get_manager("tickets")
        
        # Получаем актуальные данные талона
        ticket_data = await get_ticket_websocket_data(db, ticket_id)
        
        # Создаем сообщение
        message = WebSocketMessage(
            type="ticket_updated",
            channel="tickets",
            payload=ticket_data.model_dump(),
            timestamp=datetime.now().isoformat()
        )
        
        # Отправляем подписчикам талона
        await ticket_manager.notify_entity_subscribers(ticket_id, message.model_dump())

    @staticmethod
    async def notify_queue_update(queue_id: int, db: AsyncSession) -> None:
        """Уведомить всех подписчиков очереди и всех талонов в очереди"""
        queue_manager = manager_factory.get_manager("queues")
        ticket_manager = manager_factory.get_manager("tickets")
        
        from sqlalchemy import select
        from app.db.models import Ticket
        
        # Получаем все талоны в очереди
        stmt = select(Ticket).where(
            Ticket.queue_id == queue_id,
            Ticket.is_deleted == False
        )
        result = await db.execute(stmt)
        tickets = result.scalars().all()
        
        # Уведомляем каждый талон в очереди
        for ticket in tickets:
            await WebSocketNotifier.notify_ticket_update(ticket.id, db)
        
        # Уведомляем подписчиков очереди (если нужна общая статистика)
        queue_message = WebSocketMessage(
            type="queue_updated",
            channel="queues", 
            payload={"queue_id": queue_id, "ticket_count": len(tickets)},
            timestamp=datetime.now().isoformat()
        )
        await queue_manager.notify_entity_subscribers(queue_id, queue_message.model_dump())

    @staticmethod
    async def notify_ticket_created(ticket_id: int, db: AsyncSession) -> None:
        """Уведомить о создании нового талона"""
        await WebSocketNotifier.notify_ticket_update(ticket_id, db)

    @staticmethod
    async def notify_ticket_called(ticket_id: int, db: AsyncSession) -> None:
        """Уведомить о вызове талона"""
        ticket_manager = manager_factory.get_manager("tickets")
        
        ticket_data = await get_ticket_websocket_data(db, ticket_id)
        
        message = WebSocketMessage(
            type="ticket_called",
            channel="tickets",
            payload={
                **ticket_data.model_dump(),
                "called_at": datetime.now().isoformat()
            },
            timestamp=datetime.now().isoformat()
        )
        
        await ticket_manager.notify_entity_subscribers(ticket_id, message.model_dump())

    @staticmethod
    async def notify_ticket_completed(ticket_id: int, db: AsyncSession) -> None:
        """Уведомить о завершении талона"""
        ticket_manager = manager_factory.get_manager("tickets")
        
        ticket_data = await get_ticket_websocket_data(db, ticket_id)
        
        message = WebSocketMessage(
            type="ticket_completed",
            channel="tickets", 
            payload={
                **ticket_data.model_dump(),
                "completed_at": datetime.now().isoformat()
            },
            timestamp=datetime.now().isoformat()
        )
        
        await ticket_manager.notify_entity_subscribers(ticket_id, message.model_dump())


# Глобальный экземпляр нотификатора
notifier = WebSocketNotifier()