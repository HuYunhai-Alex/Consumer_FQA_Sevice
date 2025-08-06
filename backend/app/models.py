import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from .database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    summary = Column(Text, nullable=True)
    conversation_history = Column(Text) # Storing conversation as a JSON string
    user_contact = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)