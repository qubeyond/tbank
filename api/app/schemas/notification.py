from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class NotificationBase(BaseModel):
    ticket_id: int
    session_id: str
    message: str
    notification_type: str

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: int
    is_sent: bool
    created_at: datetime
    sent_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)