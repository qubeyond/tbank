from pydantic import BaseModel


class EventBasicStatsResponse(BaseModel):
    """Базовая статистика мероприятия"""

    event_id: int
    event_name: str
    queues_count: int
    total_tickets: int
    active_tickets: int
    completed_tickets: int
    completion_rate: float


class QueueDetailedStats(BaseModel):
    """Детальная статистика очереди в мероприятии"""
    queue_id: int
    queue_name: str
    total_tickets: int
    completed_tickets: int
    active_tickets: int


class EventDetailedStatsResponse(EventBasicStatsResponse):
    """Детальная статистика мероприятия"""

    queues_detailed: list[QueueDetailedStats]
    recent_activity: dict[str, int]
    timestamp: str


class EventsOverviewResponse(BaseModel):
    """Обзор всех активных мероприятий"""

    events: list[EventBasicStatsResponse]