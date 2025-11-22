from pydantic import BaseModel


class QueueBasicStatsResponse(BaseModel):
    """Базовая статистика очереди"""

    queue_id: int
    queue_name: str
    current_position: int
    next_ticket_position: int | None
    tickets_by_status: dict[str, int]
    total_tickets: int
    waiting_count: int
    processing_count: int
    completed_count: int


class QueuePerformanceResponse(BaseModel):
    """Метрики производительности очереди"""

    queue_id: int
    avg_service_time_seconds: float | None
    avg_wait_time_seconds: float | None
    today_tickets: int
    today_completed: int
    today_completion_rate: float


class QueuesOverviewResponse(BaseModel):
    """Обзор всех очередей мероприятия"""

    queues: list[QueueBasicStatsResponse]