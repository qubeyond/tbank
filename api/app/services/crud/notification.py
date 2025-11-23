from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse
from datetime import datetime

async def create_notification(db: AsyncSession, notification_data: NotificationCreate) -> NotificationResponse:
    notification = Notification(**notification_data.model_dump())
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return NotificationResponse.model_validate(notification)

async def get_unsent_notifications(db: AsyncSession, session_id: str) -> list[NotificationResponse]:
    query = select(Notification).where(
        Notification.session_id == session_id,
        Notification.is_sent == False
    ).order_by(Notification.created_at)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    return [NotificationResponse.model_validate(notification) for notification in notifications]

async def mark_notification_sent(db: AsyncSession, notification_id: int) -> bool:
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    if notification:
        notification.is_sent = True
        notification.sent_at = datetime.now()
        await db.commit()
        return True
    return False