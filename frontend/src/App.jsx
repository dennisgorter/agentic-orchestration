import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import WorkflowDiagram from './WorkflowDiagram';

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
  const [sessionId] = useState(() => `user_${Date.now()}`); // Keep for display/reference only
  const [showExamples, setShowExamples] = useState(true);
  const [showWorkflow, setShowWorkflow] = useState(false);
  const [showTraceModal, setShowTraceModal] = useState(false);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const messagesEndRef = useRef(null);
  
  // V2 API uses stateless design - client manages conversation history
  const API_VERSION = "v2";  // Switch between v1 and v2

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

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputValue('');
    setIsLoading(true);
    setShowExamples(false);

    try {
      // Build conversation history for v2 API (stateless)
      const conversationHistory = newMessages.slice(-10).map(msg => ({
        role: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));
      
      const response = await axios.post(`/api/${API_VERSION}/chat`, {
        message: messageText,
        conversation_history: conversationHistory
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.reply,
        timestamp: new Date().toLocaleTimeString(),
        trace_id: response.data.trace_id,
        pending_question: response.data.pending_question,
        options: response.data.options
      };

      setMessages([...newMessages, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        role: 'error',
        content: `Error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages([...newMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisambiguationChoice = async (optionLabel) => {
    // In v2 (stateless), we just send the selection as a new message
    await sendMessage(optionLabel);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleExampleClick = (query) => {
    sendMessage(query);
  };

  const handleNewChat = () => {
    setMessages([]);
    setSessionId(`user_${Date.now()}`);
    setInputValue('');
    setShowExamples(true);
  };

  const handleTraceClick = async (traceId, message) => {
    setSelectedTrace({ traceId, message, loading: true });
    setShowTraceModal(true);
    
    try {
      const response = await axios.get(`/api/trace/${traceId}`);
      setSelectedTrace({ traceId, message, traceData: response.data, loading: false });
    } catch (error) {
      console.error('Error fetching trace:', error);
      setSelectedTrace({ traceId, message, error: error.message, loading: false });
    }
  };

  const closeTraceModal = () => {
    setSelectedTrace(null);
  };

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>🚗 Agent Orchestrator</h1>
          <p className="subtitle">Car Pollution Zone Eligibility - POC</p>
          <div className="header-buttons">
            <button 
              className="workflow-toggle"
              onClick={() => setShowWorkflow(!showWorkflow)}
            >
              {showWorkflow ? '💬 Hide Workflow' : '🔄 Show Workflow'}
            </button>
            <button 
              className="new-chat-button"
              onClick={handleNewChat}
              title="Start a new conversation"
            >
              ✨ New Chat
            </button>
          </div>
        </header>

        {showWorkflow && (
          <div className="workflow-diagram-wrapper">
            <WorkflowDiagram />
          </div>
        )}

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
                    🔍 Trace ID: <code 
                      className="trace-id-link" 
                      onClick={() => handleTraceClick(message.trace_id, message)}
                      title="Click to view trace details"
                    >{message.trace_id}</code>
                  </div>
                )}
                {message.options && message.options.length > 0 && (
                  <div className="disambiguation-options">
                    <p className="options-prompt">Please select an option:</p>
                    {message.options.map((option, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleDisambiguationChoice(option.label)}
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

      {showTraceModal && selectedTrace && (
        <div className="modal-overlay" onClick={closeTraceModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🔍 Trace Details</h2>
              <button className="modal-close" onClick={closeTraceModal}>✕</button>
            </div>
            <div className="modal-body">
              {selectedTrace.loading && (
                <div className="trace-loading">
                  <div className="loading-dots">
                    <span>.</span><span>.</span><span>.</span>
                  </div>
                  <p>Loading trace details...</p>
                </div>
              )}

              {selectedTrace.error && (
                <div className="trace-error">
                  <p>❌ Error loading trace: {selectedTrace.error}</p>
                </div>
              )}

              {selectedTrace.traceData && (
                <>
                  <div className="trace-section">
                    <h3>Execution Summary</h3>
                    <div className="trace-field">
                      <span className="field-label">Trace ID:</span>
                      <code className="field-value">{selectedTrace.traceData.trace_id}</code>
                    </div>
                    <div className="trace-field">
                      <span className="field-label">Session ID:</span>
                      <code className="field-value">{selectedTrace.traceData.session_id}</code>
                    </div>
                    <div className="trace-field">
                      <span className="field-label">Status:</span>
                      <span className={`field-value status-badge ${selectedTrace.traceData.success ? 'success' : 'error'}`}>
                        {selectedTrace.traceData.success ? '✓ Success' : '✗ Failed'}
                      </span>
                    </div>
                    <div className="trace-field">
                      <span className="field-label">Duration:</span>
                      <span className="field-value">{selectedTrace.traceData.total_duration_ms?.toFixed(2) || '—'} ms</span>
                    </div>
                    <div className="trace-field">
                      <span className="field-label">Steps:</span>
                      <span className="field-value">{selectedTrace.traceData.steps?.length || 0}</span>
                    </div>
                  </div>

                  {selectedTrace.traceData.error && (
                    <div className="trace-section">
                      <h3>Error</h3>
                      <pre className="trace-error-detail">{selectedTrace.traceData.error}</pre>
                    </div>
                  )}

                  {selectedTrace.traceData.steps && selectedTrace.traceData.steps.length > 0 && (
                    <div className="trace-section">
                      <h3>Workflow Execution Steps</h3>
                      <div className="workflow-steps">
                        {selectedTrace.traceData.steps.map((step, idx) => (
                          <details key={idx} className="workflow-step" open={idx === 0}>
                            <summary className="step-summary">
                              <span className="step-number">Step {step.step_number}</span>
                              <span className="step-name">{step.node_name}</span>
                              <span className="step-duration">{step.duration_ms.toFixed(2)}ms</span>
                            </summary>
                            <div className="step-content">
                              <div className="step-subsection">
                                <h4>Input State</h4>
                                <pre className="json-preview">{JSON.stringify(step.input_state, null, 2)}</pre>
                              </div>
                              <div className="step-subsection">
                                <h4>Output State</h4>
                                <pre className="json-preview">{JSON.stringify(step.output_state, null, 2)}</pre>
                              </div>
                            </div>
                          </details>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedTrace.traceData.final_reply && (
                    <div className="trace-section">
                      <h3>Final Reply</h3>
                      <div className="final-reply">{selectedTrace.traceData.final_reply}</div>
                    </div>
                  )}
                </>
              )}

              {!selectedTrace.loading && !selectedTrace.traceData && !selectedTrace.error && (
                <div className="trace-section">
                  <h3>Basic Message Info</h3>
                  <div className="trace-field">
                    <span className="field-label">Trace ID:</span>
                    <code className="field-value">{selectedTrace.traceId}</code>
                  </div>
                  <div className="trace-field">
                    <span className="field-label">Role:</span>
                    <span className="field-value">{selectedTrace.message.role}</span>
                  </div>
                  <div className="trace-field">
                    <span className="field-label">Timestamp:</span>
                    <span className="field-value">{selectedTrace.message.timestamp}</span>
                  </div>
                </div>
              )}

              <div className="trace-section">
                <h3>Complete Message Data</h3>
                <details className="json-details">
                  <summary>View Full Message Object</summary>
                  <pre className="json-preview">{JSON.stringify(selectedTrace.message, null, 2)}</pre>
                </details>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
