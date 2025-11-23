from sqlalchemy.ext.asyncio import AsyncSession
from app.services.crud.ticket import get_ticket_position, get_ticket
from app.services.crud.notification import create_notification
from app.schemas.notification import NotificationCreate
from app.services.websockets.notifications import notification_manager

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_ticket_position(self, ticket_id: int) -> bool:
        """Проверяет позицию талона и создает нотификации при необходимости"""
        position_info = await get_ticket_position(self.db, ticket_id)
        if not position_info:
            return False
        
        ahead_count = position_info.ahead_count
        notifications_created = False
        
        if ahead_count <= 1:
            await self._create_notification(
                ticket_id, 
                "Следующий! Подготовьтесь к вызову.",
                "position_alert"
            )
            notifications_created = True
        elif ahead_count <= 3:
            await self._create_notification(
                ticket_id, 
                f"Ваша очередь приближается! Перед вами {ahead_count} человек(а).",
                "position_alert"
            )
            notifications_created = True
        elif ahead_count <= 10:
            await self._create_notification(
                ticket_id, 
                f"Вы в очереди! Перед вами {ahead_count} человек.",
                "position_alert"
            )
            notifications_created = True
        
        return notifications_created
    
    async def _create_notification(self, ticket_id: int, message: str, notification_type: str):
        ticket = await get_ticket(self.db, ticket_id)
        if ticket:
            notification_data = NotificationCreate(
                ticket_id=ticket_id,
                session_id=ticket.session_id,
                message=message,
                notification_type=notification_type
            )
            await create_notification(self.db, notification_data)
    
    async def create_call_notification(self, ticket_id: int):
        """Создает нотификацию о вызове талона"""
        ticket = await get_ticket(self.db, ticket_id)
        if ticket:
            notification_data = NotificationCreate(
                ticket_id=ticket_id,
                session_id=ticket.session_id,
                message="Ваш талон вызван! Подойдите к стойке.",
                notification_type="called"
            )
            notification = await create_notification(self.db, notification_data)
            
            await notification_manager.send_notification(
                ticket.session_id,
                {
                    "type": "notification",
                    "data": notification.model_dump(),
                    "timestamp": notification.created_at.isoformat()
                }
            )

    async def create_completion_notification(self, ticket_id: int):
        """Создает нотификацию о завершении обслуживания"""
        ticket = await get_ticket(self.db, ticket_id)
        if ticket:
            notification_data = NotificationCreate(
                ticket_id=ticket_id,
                session_id=ticket.session_id,
                message="Обслуживание завершено. Спасибо!",
                notification_type="completed"
            )
            notification = await create_notification(self.db, notification_data)
            
            await notification_manager.send_notification(
                ticket.session_id,
                {
                    "type": "notification", 
                    "data": notification.model_dump(),
                    "timestamp": notification.created_at.isoformat()
                }
            )