from pydantic import BaseModel

from typing import Any, Optional


class WebSocketMessage(BaseModel):
    type: str  
    channel: str  
    payload: dict[str, Any]
    timestamp: str


class TicketWebSocketMessage(BaseModel):
    type: str  
    ticket_id: int
    position: int
    people_ahead: int
    queue_name: str
    queue_letter: str
    estimated_wait_time: Optional[int] = None  
    status: str


class EventStatsUpdate(BaseModel):
    event_id: int
    stats: dict[str, Any]


class QueueStatsUpdate(BaseModel):
    queue_id: int
    stats: dict[str, Any]


class TicketUpdate(BaseModel):
    ticket_id: int
    action: str  
    data: dict[str, Any]