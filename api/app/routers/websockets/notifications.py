from fastapi import APIRouter, WebSocket, Depends
from app.db.session import get_db, AsyncSession
from app.services.websockets.notifications import websocket_endpoint, notification_manager

router = APIRouter(tags=["notifications"])

@router.websocket("/ws/{session_id}")
async def websocket_notifications(websocket: WebSocket, session_id: str):
    await websocket_endpoint(websocket, session_id)

@router.get("/{session_id}")
async def get_notifications(session_id: str, db: AsyncSession = Depends(get_db)):
    from app.services.crud.notification import get_unsent_notifications
    notifications = await get_unsent_notifications(db, session_id)
    return notifications