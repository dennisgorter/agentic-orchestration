import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const EXAMPLE_QUERIES = [
  {
    category: "Single Car Eligibility",
    queries: [
      "Is my car AB-123-CD allowed to enter Amsterdam city center?",
      "Can I drive my electric car IJ-789-KL into Amsterdam city center?",
      "Is EF-456-GH allowed in Rotterdam?"
    ]
  },
  {
    category: "Fleet Queries",
    queries: [
      "Which of my cars can enter Amsterdam city center?",
      "Can any of my cars access the Amsterdam logistics zone?"
    ]
  },
  {
    category: "Policy Information",
    queries: [
      "What are the pollution rules in Amsterdam?",
      "What are the pollution rules in Rotterdam?",
      "Tell me about the Amsterdam LEZ zone"
    ]
  }
];

const AVAILABLE_CARS = [
  { plate: "AB-123-CD", type: "Diesel Euro 4", status: "❌ Banned in Amsterdam LEZ" },
  { plate: "EF-456-GH", type: "Diesel Euro 5", status: "✅ Allowed in Amsterdam LEZ" },
  { plate: "IJ-789-KL", type: "Electric", status: "✅ Allowed everywhere" },
  { plate: "MN-321-OP", type: "Petrol Euro 6", status: "✅ Allowed in Amsterdam LEZ" }
];

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `user_${Date.now()}`);
  const [showExamples, setShowExamples] = useState(true);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    const userMessage = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setShowExamples(false);

    try {
      const response = await axios.post('/api/chat', {
        session_id: sessionId,
        message: messageText
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.reply,
        timestamp: new Date().toLocaleTimeString(),
        trace_id: response.data.trace_id,
        pending_question: response.data.pending_question,
        options: response.data.options
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        role: 'error',
        content: `Error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisambiguationChoice = async (optionIndex) => {
    setIsLoading(true);

    try {
      const response = await axios.post('/api/chat/answer', {
        session_id: sessionId,
        selection_index: optionIndex
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.reply,
        timestamp: new Date().toLocaleTimeString(),
        trace_id: response.data.trace_id,
        pending_question: response.data.pending_question,
        options: response.data.options
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        role: 'error',
        content: `Error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleExampleClick = (query) => {
    sendMessage(query);
  };

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>🚗 Agent Orchestrator</h1>
          <p className="subtitle">Car Pollution Zone Eligibility - POC</p>
        </header>

        {showExamples && messages.length === 0 && (
          <div className="welcome-section">
            <div className="info-card">
              <h2>Welcome! 👋</h2>
              <p>This POC helps you check if your car can enter pollution zones in Amsterdam and Rotterdam.</p>
              
              <div className="available-cars">
                <h3>Available Test Cars:</h3>
                <ul>
                  {AVAILABLE_CARS.map(car => (
                    <li key={car.plate}>
                      <strong>{car.plate}</strong> - {car.type} <span className="status">{car.status}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="example-queries">
                <h3>Try asking:</h3>
                {EXAMPLE_QUERIES.map((category, idx) => (
                  <div key={idx} className="query-category">
                    <h4>{category.category}</h4>
                    <div className="query-buttons">
                      {category.queries.map((query, qIdx) => (
                        <button
                          key={qIdx}
                          onClick={() => handleExampleClick(query)}
                          className="example-button"
                        >
                          {query}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <div className="chat-container">
          <div className="messages">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-header">
                  <span className="role">
                    {message.role === 'user' ? '👤 You' : message.role === 'assistant' ? '🤖 Assistant' : '⚠️ Error'}
                  </span>
                  <span className="timestamp">{message.timestamp}</span>
                </div>
                <div className="message-content">
                  {message.content}
                </div>
                {message.trace_id && (
                  <div className="trace-id">
                    🔍 Trace ID: <code>{message.trace_id}</code>
                  </div>
                )}
                {message.options && message.options.length > 0 && (
                  <div className="disambiguation-options">
                    <p className="options-prompt">Please select an option:</p>
                    {message.options.map((option) => (
                      <button
                        key={option.index}
                        onClick={() => handleDisambiguationChoice(option.index)}
                        className="option-button"
                        disabled={isLoading}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="message assistant loading">
                <div className="message-header">
                  <span className="role">🤖 Assistant</span>
                </div>
                <div className="message-content">
                  <div className="loading-dots">
                    <span>.</span><span>.</span><span>.</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="input-form">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about car eligibility or pollution rules..."
              disabled={isLoading}
              className="message-input"
            />
            <button type="submit" disabled={isLoading || !inputValue.trim()} className="send-button">
              Send
            </button>
          </form>
        </div>

        <footer className="footer">
          <p>💡 <strong>POC Features:</strong> Single car checks, fleet queries, policy information, smart disambiguation</p>
          <p className="session-info">Session ID: <code>{sessionId}</code></p>
        </footer>
      </div>
    </div>
  );
}

export default App;
