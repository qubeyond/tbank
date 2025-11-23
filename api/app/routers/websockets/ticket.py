from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websockets.managers import manager_factory
from app.services.analytics.ticket_ws import get_ticket_websocket_data
from app.db import get_db
import asyncio

router = APIRouter()

@router.websocket("/ticket/{ticket_id}")
async def websocket_ticket_info(websocket: WebSocket, ticket_id: int):
    ticket_manager = manager_factory.get_manager("tickets")
    
    await ticket_manager.subscribe_to_entity(websocket, ticket_id)
    
    try:
        # Отправляем начальные данные
        async for db in get_db():
            ticket_data = await get_ticket_websocket_data(db, ticket_id)
            await ticket_manager.notify_entity_subscribers(ticket_id, ticket_data.model_dump())
        
        # Основной цикл соединения
        while True:
            try:
                # Ожидаем сообщения от клиента с таймаутом
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "refresh":
                    async for db in get_db():
                        ticket_data = await get_ticket_websocket_data(db, ticket_id)
                        await websocket.send_json(ticket_data.model_dump())
                        
            except asyncio.TimeoutError:
                # Таймаут - отправляем обновление и heartbeat
                async for db in get_db():
                    ticket_data = await get_ticket_websocket_data(db, ticket_id)
                    await ticket_manager.notify_entity_subscribers(ticket_id, ticket_data.model_dump())
                await websocket.send_text("ping")
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error for ticket {ticket_id}: {e}")
    finally:
        ticket_manager.unsubscribe_from_entity(websocket, ticket_id)