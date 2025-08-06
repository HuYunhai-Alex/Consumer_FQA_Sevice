# Customer FAQ System

This project is a customer FAQ system that uses an AI-powered chat interface to answer user questions. If the AI cannot answer a question, a ticket is automatically generated.

## Project Structure

- `backend/`: Contains the FastAPI backend application.
- `frontend/`: Contains the React frontend application.

## Getting Started

### Prerequisites

- Python 3.7+
- Node.js and npm

### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the FastAPI server:**
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

The frontend application will be accessible at `http://localhost:3001`.

## How to Use

1.  Open your web browser and go to `http://localhost:3001`.
2.  Use the chat interface to ask a question.
3.  If the AI can find an answer in the knowledge base, it will be displayed.
4.  If not, a ticket will be created. You can view the tickets by clicking the "View Tickets" button.
