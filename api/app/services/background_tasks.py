import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models.queue import Queue
from app.db.models.ticket import Ticket
from app.services.notification_service import NotificationService

async def get_all_active_queues(db: AsyncSession):
    result = await db.execute(
        select(Queue).where(
            Queue.is_active == True,
            Queue.is_deleted == False
        )
    )
    return result.scalars().all()

async def get_waiting_tickets_for_queue(db: AsyncSession, queue_id: int):
    result = await db.execute(
        select(Ticket).where(
            Ticket.queue_id == queue_id,
            Ticket.status == "waiting",
            Ticket.is_deleted == False
        ).order_by(Ticket.position)
    )
    return result.scalars().all()

async def check_queue_positions():
    while True:
        try:
            db_gen = get_db()
            db = await anext(db_gen)
            
            try:
                notification_service = NotificationService(db)
                active_queues = await get_all_active_queues(db)
                
                for queue in active_queues:
                    try:
                        waiting_tickets = await get_waiting_tickets_for_queue(db, queue_id=queue.id)
                        
                        for ticket in waiting_tickets:
                            try:
                                await notification_service.check_ticket_position(ticket.id)
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                
                await asyncio.sleep(30)
                
            finally:
                try:
                    await anext(db_gen)
                except StopAsyncIteration:
                    pass
                    
        except Exception:
            await asyncio.sleep(60)