# app/api.py
import json
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

from . import crud, models, schemas
from .database import SessionLocal, engine

# Initialize database metadata
models.Base.metadata.create_all(bind=engine)

# Router
router = APIRouter()

# --- Vector DB ---
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "/home/asperger/genspark_fqa/backend/faiss_index.bin")
KNOWLEDGE_CHUNKS_PATH = os.getenv("KNOWLEDGE_CHUNKS_PATH", "/home/asperger/genspark_fqa/backend/knowledge_chunks.pkl")

# Load Sentence Transformer Model
print("Loading sentence transformer model...")
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model loaded.")

def search_vector_db(query: str, k: int = 3) -> Optional[str]:
    """Searches the vector DB for the top k most relevant knowledge chunks."""
    try:
        index = faiss.read_index(FAISS_INDEX_PATH)
        with open(KNOWLEDGE_CHUNKS_PATH, "rb") as f:
            chunks = pickle.load(f)
        question_embedding = sbert_model.encode([query])
        distances, indices = index.search(question_embedding, k)
        if len(indices) > 0:
            relevant_chunks = [chunks[i] for i in indices[0]]
            return "\n---\n".join(relevant_chunks)
        return "No relevant information found."
    except FileNotFoundError:
        return "Vector DB files not found."
    except Exception as e:
        return f"An error occurred during vector search: {e}"

# --- DB Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Gemini API and Models (Initialized Once) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = None
GREETING_MODEL = None
INTENT_MODEL = None
SUMMARIZER_MODEL = None

if GEMINI_API_KEY:
    print("Configuring Gemini API...")
    genai.configure(api_key=GEMINI_API_KEY)
    
    REACT_SYSTEM_PROMPT = """You are a professional customer support assistant using the ReAct model. Your tools: `search(query)` and `finish(answer)`. Your task is to answer the user's question. If you cannot find an answer, use `finish(I could not find an answer.)`."""
    GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=REACT_SYSTEM_PROMPT)
    
    GREETING_MODEL = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction="You are a friendly customer support assistant. Generate a short, one-sentence greeting.")
    
    INTENT_SYSTEM_PROMPT = "Analyze the user's message. Is the user expressing frustration, anger, or saying a previous answer was wrong? Respond with only one word: FRUSTRATED or QUESTION."
    INTENT_MODEL = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=INTENT_SYSTEM_PROMPT)
    
    SUMMARIZER_SYSTEM_PROMPT = "You are a helpful assistant. Based on the provided conversation history, write a concise, one-paragraph summary of the user's problem for a support ticket."
    SUMMARIZER_MODEL = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=SUMMARIZER_SYSTEM_PROMPT)

    print("Gemini models initialized.")
else:
    print("GEMINI_API_KEY not found. AI chat functionality will be disabled.")

def ask_gemini(model, history: List[dict]) -> Optional[str]:
    if not model: return "The AI model is not configured."
    try:
        # This function now expects a clean history with 'role' and 'parts'
        resp = model.generate_content(history, generation_config=genai.types.GenerationConfig(temperature=0.0))
        return resp.text.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def format_history_for_gemini(history: List[dict]) -> List[dict]:
    """Converts the frontend chat history format to the Gemini API format."""
    gemini_history = []
    for msg in history:
        sender = msg.get('user') or msg.get('role')
        role = 'model' if sender in ['AI', 'assistant'] else 'user'
        content = msg.get('message') or msg.get('content')
        gemini_history.append({'role': role, 'parts': [content]})
    return gemini_history

@router.get("/greeting")
def get_greeting():
    if not GREETING_MODEL: return {"greeting": "Hello! How can I help you today?"}
    greeting_history = format_history_for_gemini([{"role": "user", "content": "Generate a greeting."}])
    return {"greeting": ask_gemini(GREETING_MODEL, greeting_history)}

@router.post("/chat")
def chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    question = request.question.strip()
    if not question: raise HTTPException(status_code=400, detail="Question is required.")

    # --- Intent Analysis Step ---
    intent_history = format_history_for_gemini([{"role": "user", "content": question}])
    intent = ask_gemini(INTENT_MODEL, intent_history)

    if intent == "FRUSTRATED":
        # --- Ticket Creation Flow ---
        full_history_for_db = request.chat_history
        
        # Prepare a clean history for the summarizer model
        history_for_summarizer = format_history_for_gemini(full_history_for_db)
        summary = ask_gemini(SUMMARIZER_MODEL, history_for_summarizer)
        
        initial_question = next((msg.get('message') for msg in request.chat_history if msg.get('user') == 'You'), question)
        
        ticket_data = schemas.TicketCreate(
            title=initial_question, 
            summary=summary, 
            conversation_history=full_history_for_db # Save the original history
        )
        crud.create_ticket(db=db, ticket=ticket_data)
        
        return {"response": "I'm sorry you're having trouble. I've created a support ticket with a summary of our conversation, and our team will be in touch shortly."}

    # --- ReAct Loop (If intent is QUESTION) ---
    messages_for_react = request.chat_history + [{"user": "You", "message": f"User: {question}"}]
    max_iterations = 5
    for i in range(max_iterations):
        gemini_history = format_history_for_gemini(messages_for_react)
        llm_response = ask_gemini(GEMINI_MODEL, gemini_history)
        
        if not llm_response: return {"response": "I'm sorry, I encountered an issue."}

        messages_for_react.append({"role": "assistant", "content": llm_response})
        action_match = re.search(r"Action:\s*(search|finish)\(.*\)", llm_response, re.DOTALL)

        if not action_match or len(action_match.groups()) < 2: return {"response": llm_response}

        action_type, action_arg = action_match.group(1).strip(), action_match.group(2).strip()

        if action_type == "finish":
            return {"response": llm_response}

        if action_type == "search":
            observation = search_vector_db(action_arg)
            messages_for_react.append({"role": "user", "content": f"Observation: {observation}"})
            continue

    return {"response": "I am having trouble finding a definitive answer."}

@router.post("/tickets/", response_model=schemas.Ticket)
def create_ticket_endpoint(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    return crud.create_ticket(db=db, ticket=ticket)

@router.get("/tickets/", response_model=List[schemas.Ticket])
def read_tickets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_tickets(db, skip=skip, limit=limit)

@router.get("/tickets/{ticket_id}", response_model=schemas.Ticket)
def read_ticket(ticket_id: int, db: Session = Depends(get_db)):
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if not db_ticket: raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket
