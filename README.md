# Customer FAQ System

This project is a customer FAQ system that uses an AI-powered chat interface to answer user questions. It is built with a FastAPI backend and a React frontend.

## Product Preview

![Product Preview](./assets/preview.gif)

## Key Features

- **Proactive Ticket Creation**: The AI automatically detects user frustration or unresolved issues and creates a support ticket, ensuring no query is lost.
- **ReAct-Based RAG**: Utilizes an advanced ReAct (Reason + Act) model, allowing the AI to perform targeted searches against a vector database to find the most relevant information before answering.
- **Full Conversation Context**: Both user-initiated and AI-initiated tickets automatically capture the complete chat history, providing support agents with the full context needed for resolution.
- **Dynamic AI-Generated Greetings**: The chat experience is enhanced with unique, AI-generated welcome messages for each new session.
- **Markdown Support**: The frontend correctly renders Markdown, allowing for richly formatted AI responses including lists, bolding, and more.

## Project Structure

- `backend/`: Contains the FastAPI backend application, including the ReAct logic, vector database, and ticket management system.
- `frontend/`: Contains the React frontend application.

## Getting Started

### Prerequisites

- Python 3.7+
- Node.js and npm
- A Gemini API Key

### Backend Setup

1.  **Set API Key**: Set your Gemini API key as an environment variable:
    ```bash
    export GEMINI_API_KEY="YOUR_API_KEY"
    ```

2.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```
    
4.  **Build the Vector Database**:
    ```bash
    python3 build_vector_db.py
    ```

5.  **Run the FastAPI server:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```

The backend server will be running at `http://localhost:8000`.

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install the required npm packages:**
    ```bash
    npm install
    ```

3.  **Run the React development server:**
    ```bash
    npm start
    ```

The frontend application will be accessible at `http://localhost:3000`.

## How to Use

1.  Open your web browser and go to `http://localhost:3000`.
2.  Use the chat interface to ask a question. The AI will use its ReAct logic to find an answer.
3.  If you are unsatisfied, you can either click the "👎" button or express frustration directly. The system will create a ticket.
4.  You can view all created tickets by clicking the "View Tickets" link.
