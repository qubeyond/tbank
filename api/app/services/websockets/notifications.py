from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.services.crud.notification import get_unsent_notifications, mark_notification_sent

class NotificationManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"WebSocket disconnected: {session_id}")

    async def send_notification(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
                return True
            except Exception as e:
                print(f"Error sending notification: {e}")
                self.disconnect(session_id)
        return False

notification_manager = NotificationManager()

async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await notification_manager.connect(websocket, session_id)
    
    try:
        await websocket.send_json({
            "type": "connected", 
            "message": f"Connected to notifications for session {session_id}"
        })
        
        try:
            async with AsyncSessionLocal() as db:
                from app.services.crud.notification import get_unsent_notifications, mark_notification_sent
                unsent_notifications = await get_unsent_notifications(db, session_id)
                for notification in unsent_notifications:
                    try:
                        await websocket.send_json({
                            "type": "notification",
                            "data": notification.model_dump(),
                            "timestamp": notification.created_at.isoformat()
                        })
                        await mark_notification_sent(db, notification.id)
                    except Exception as e:
                        print(f"Error sending notification: {e}")
                        continue
        except Exception as e:
            print(f"Error loading notifications from DB: {e}")
          
        while True:
            data = await websocket.receive_text()
            print(f"Received from {session_id}: {data}")
            
            if data == "ping":
                await websocket.send_text("pong")
                print(f"Sent pong to {session_id}")
            else:
                await websocket.send_json({
                    "type": "echo",
                    "message": f"You said: {data}",
                    "session_id": session_id
                })
                
    except WebSocketDisconnect:
        notification_manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        notification_manager.disconnect(session_id)