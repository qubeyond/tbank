from pydantic import BaseModel


class TicketStatsResponse(BaseModel):
    """Статистика по талону"""

    ticket_id: int
    position: int
    status: str
    wait_time_seconds: float | None
    service_time_seconds: float | None
    created_at: str
    called_at: str | None
    completed_at: str | None


class TicketTimelineResponse(BaseModel):
    """Элемент таймлайна талона"""

    ticket_id: int
    position: int
    status: str
    created_at: str
    called_at: str | None
    completed_at: str | None


class TicketsTimelineResponse(BaseModel):
    """Таймлайн талонов"""

    tickets: list[TicketTimelineResponse]


class QueueTicketsStatsResponse(BaseModel):
    """Статистика по талонам очереди"""

    queue_id: int
    total_tickets: int
    avg_wait_time: float | None
    avg_service_time: float | None
    status_distribution: dict[str, int]