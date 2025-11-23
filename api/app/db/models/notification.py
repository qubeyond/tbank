from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from app.db.base import Base
from datetime import datetime

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, nullable=False)
    session_id = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    sent_at = Column(DateTime, nullable=True)