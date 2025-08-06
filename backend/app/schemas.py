import json
from pydantic import BaseModel, field_validator
import datetime
from typing import List, Dict, Any, Optional

class TicketBase(BaseModel):
    title: str
    conversation_history: List[Dict[str, Any]]
    summary: Optional[str] = None
    user_contact: Optional[str] = None

class TicketCreate(TicketBase):
    pass

class Ticket(TicketBase):
    id: int
    created_at: datetime.datetime

    @field_validator('conversation_history', mode='before')
    @classmethod
    def parse_conversation_history(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    question: str
    chat_history: List[Dict[str, Any]] = []