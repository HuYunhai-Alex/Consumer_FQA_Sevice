import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app  # Assuming your FastAPI app instance is in app/main.py

# Create a TestClient instance
client = TestClient(app)

# --- Mocks ---

# This mock will simulate the behavior of the Gemini API call
@patch('app.api.ask_gemini')
def test_intent_classification_frustrated(mock_ask_gemini: MagicMock):
    """
    Tests if the system correctly identifies a FRUSTRATED user
    and creates a ticket.
    """
    # 1. First, the intent model is called. We make it return "FRUSTRATED".
    # 2. Then, the summarizer model is called. We give it a sample summary.
    mock_ask_gemini.side_effect = [
        "FRUSTRATED", 
        "The user is unhappy with the previous answers about the return policy."
    ]

    # Simulate a frustrated user message
    response = client.post("/chat", json={
        "question": "This is wrong, I'm very angry.",
        "chat_history": [
            {"user": "You", "message": "How do I return an item?"},
            {"user": "AI", "message": "You can return items within 30 days."}
        ]
    })

    # Assertions
    assert response.status_code == 200
    json_response = response.json()
    assert "I've created a support ticket" in json_response['response']
    
    # Check that ask_gemini was called twice (once for intent, once for summary)
    assert mock_ask_gemini.call_count == 2

@patch('app.api.ask_gemini')
def test_intent_classification_question(mock_ask_gemini: MagicMock):
    """
    Tests if the system correctly identifies a normal QUESTION
    and proceeds with the ReAct loop.
    """
    # 1. The intent model is called. We make it return "QUESTION".
    # 2. The ReAct model is called. We simulate a ReAct response.
    mock_ask_gemini.side_effect = [
        "QUESTION",
        "Thought: The user is asking a question. I will finish. Action: finish(This is a test answer.)"
    ]

    # Simulate a normal user question
    response = client.post("/chat", json={
        "question": "What is your return policy?",
        "chat_history": []
    })

    # Assertions
    assert response.status_code == 200
    json_response = response.json()
    # The frontend will parse this, so we check the raw response
    assert "finish(This is a test answer.)" in json_response['response']
    
    # Check that ask_gemini was called twice (once for intent, once for ReAct)
    assert mock_ask_gemini.call_count == 2
