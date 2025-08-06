import json
from sqlalchemy.orm import Session
from . import models, schemas

def get_ticket(db: Session, ticket_id: int):
    return db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

def get_tickets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Ticket).offset(skip).limit(limit).all()

def create_ticket(db: Session, ticket: schemas.TicketCreate):
    conversation_history_str = json.dumps(ticket.conversation_history)
    
    db_ticket = models.Ticket(
        title=ticket.title,
        summary=ticket.summary,
        conversation_history=conversation_history_str,
        user_contact=ticket.user_contact
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket