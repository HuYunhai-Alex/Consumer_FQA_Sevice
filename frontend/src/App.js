import React, { useState, useEffect, useRef } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Navbar, Nav, Form, Button, Card, ListGroup, Modal } from 'react-bootstrap';
import ReactMarkdown from 'react-markdown';

// --- Helper Functions ---
const parseFinalAnswer = (response) => {
  const match = /Action:\s*finish\((.*)\)/s.exec(response);
  return (match && match[1]) ? match[1].trim() : response;
};

// --- Components ---
const ChatMessage = ({ chat }) => (
  <div className={`mb-2 text-${chat.user === 'You' ? 'end' : 'start'}`}>
    <div><strong>{chat.user}:</strong></div>
    <div className="d-inline-block p-2 rounded" style={{ backgroundColor: chat.user === 'You' ? '#e0f7fa' : '#f1f1f1' }}>
      <ReactMarkdown>{chat.message}</ReactMarkdown>
    </div>
  </div>
);

const TicketHistoryModal = ({ show, handleClose, ticket }) => {
  if (!ticket) return null;
  return (
    <Modal show={show} onHide={handleClose} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Conversation History for Ticket #{ticket.id}</Modal.Title>
      </Modal.Header>
      <Modal.Body style={{ maxHeight: '60vh', overflowY: 'auto' }}>
        <h5>{ticket.title}</h5>
        <p><strong>AI's Reasoning Summary:</strong></p>
        <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: '0.9em' }}>{ticket.summary}</pre>
        <hr />
        <h6>Full Conversation:</h6>
        {ticket.conversation_history?.map((chat, index) => (
          <div key={index} className={`mb-2 text-${(chat.user || chat.role) === 'You' || (chat.user || chat.role) === 'user' ? 'end' : 'start'}`}>
            <strong>{(chat.user || chat.role) === 'assistant' ? 'AI' : (chat.user || chat.role)}:</strong>
            <p style={{ whiteSpace: 'pre-wrap' }}>{chat.message || chat.content}</p>
          </div>
        ))}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose}>Close</Button>
      </Modal.Footer>
    </Modal>
  );
};

// --- Main App ---
function App() {
  const [question, setQuestion] = useState('');
  const [tickets, setTickets] = useState([]);
  const [feedbackGiven, setFeedbackGiven] = useState({});
  const [chatHistory, setChatHistory] = useState([]);
  const [view, setView] = useState('chat');
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const chatEndRef = useRef(null); // Create a ref for the end of the chat

  // Auto-scroll to the bottom of the chat history
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  useEffect(() => {
    const fetchGreeting = async () => {
      try {
        const response = await fetch('http://localhost:8000/greeting');
        const data = await response.json();
        const initialChat = [{ user: 'AI', message: data.greeting || 'Hello!', id: Date.now(), fullResponse: data.greeting }];
        setChatHistory(sessionStorage.getItem('chatHistory') ? JSON.parse(sessionStorage.getItem('chatHistory')) : initialChat);
      } catch (error) {
        setChatHistory([{ user: 'AI', message: 'Hello! How can I help?', id: Date.now(), fullResponse: 'Hello!' }]);
      }
    };
    fetchGreeting();
  }, []);

  useEffect(() => {
    if (chatHistory.length > 0) sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));
  }, [chatHistory]);

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    const newChat = [...chatHistory, { user: 'You', message: question, id: Date.now() }];
    setChatHistory(newChat);
    setQuestion('');

    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, chat_history: newChat }),
    });
    const data = await response.json();
    const finalAnswer = parseFinalAnswer(data.response);
    setChatHistory([...newChat, { user: 'AI', message: finalAnswer, id: Date.now() + 1, fullResponse: data.response }]);
  };

  const handleFeedback = async (chat, isGood) => {
    setFeedbackGiven({ ...feedbackGiven, [chat.id]: true });
    if (!isGood) {
      const userQuestion = chatHistory.findLast(c => c.user === 'You')?.message || "Feedback Ticket";
      await fetch('http://localhost:8000/tickets/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: userQuestion, summary: chat.fullResponse, conversation_history: chatHistory }),
      });
      alert("Thank you! A ticket has been created for our team to review.");
    } else {
      alert("Thank you for your feedback!");
    }
  };

  const fetchTickets = async () => {
    const response = await fetch('http://localhost:8000/tickets/');
    const data = await response.json();
    setTickets(data);
  };

  const handleClearChat = async () => {
    try {
      const response = await fetch('http://localhost:8000/greeting');
      const data = await response.json();
      setChatHistory([{ user: 'AI', message: data.greeting || 'Hello!', id: Date.now(), fullResponse: data.greeting }]);
    } catch (error) {
      setChatHistory([{ user: 'AI', message: 'Hello! How can I help?', id: Date.now(), fullResponse: 'Hello!' }]);
    }
    setFeedbackGiven({});
  };

  const handleViewTicket = (ticket) => {
    setSelectedTicket(ticket);
    setShowModal(true);
  };

  useEffect(() => {
    if (view === 'tickets') fetchTickets();
  }, [view]);

  return (
    <>
      <Navbar bg="dark" variant="dark" expand="lg">
        <Container>
          <Navbar.Brand href="#home">Customer Support</Navbar.Brand>
          <Nav className="me-auto">
            <Nav.Link onClick={() => setView('chat')}>Chat</Nav.Link>
            <Nav.Link onClick={() => setView('tickets')}>View Tickets</Nav.Link>
          </Nav>
        </Container>
      </Navbar>
      <Container style={{ marginTop: '20px' }}>
        {view === 'chat' ? (
          <Card>
            <Card.Header>Chat</Card.Header>
            <Card.Body>
              <div className="chat-history" style={{ height: '400px', overflowY: 'scroll', marginBottom: '20px' }}>
                {chatHistory.map((chat, index) => (
                  <div key={chat.id || index}>
                    <ChatMessage chat={chat} />
                    {chat.user === 'AI' && !feedbackGiven[chat.id] && index === chatHistory.length - 1 && index > 0 && (
                      <div className="mt-1 text-start">
                        <small>Helpful? </small>
                        <Button variant="outline-success" size="sm" onClick={() => handleFeedback(chat, true)}>👍</Button>
                        <Button variant="outline-danger" size="sm" onClick={() => handleFeedback(chat, false)} style={{ marginLeft: '5px' }}>👎</Button>
                      </div>
                    )}
                  </div>
                ))}
                <div ref={chatEndRef} /> {/* Add the ref to an empty div at the end */}
              </div>
              <Form onSubmit={handleChatSubmit}>
                <Form.Group className="mb-3">
                  <Form.Control type="text" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a question..." />
                </Form.Group>
                <Button variant="primary" type="submit">Send</Button>
                <Button variant="secondary" onClick={handleClearChat} style={{ marginLeft: '10px' }}>Clear</Button>
              </Form>
            </Card.Body>
          </Card>
        ) : (
          <Card>
            <Card.Header>Generated Tickets</Card.Header>
            <Card.Body>
              <ListGroup>
                {tickets.map((ticket) => (
                  <ListGroup.Item key={ticket.id} className="d-flex justify-content-between align-items-center">
                    <div>
                      <h5>{ticket.title}</h5>
                      <p><small>Created: {new Date(ticket.created_at).toLocaleString()}</small></p>
                    </div>
                    <Button variant="outline-primary" size="sm" onClick={() => handleViewTicket(ticket)}>View History</Button>
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Card.Body>
          </Card>
        )}
      </Container>
      <TicketHistoryModal show={showModal} handleClose={() => setShowModal(false)} ticket={selectedTicket} />
    </>
  );
}

export default App;