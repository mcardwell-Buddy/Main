import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';

/**
 * ChatInterface Component
 * 
 * Conversational AI interface with:
 * - Message history (user and agent)
 * - Real-time reasoning steps (todos)
 * - Thinking states and streaming responses
 * - Natural conversation flow
 */

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'agent',
      content: "Hello! I'm Buddy, your autonomous reasoning agent. I can help you with code analysis, data processing, learning, and much more. What would you like me to help with?",
      timestamp: new Date().toISOString(),
      todos: []
    }
  ]);
  
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [todos, setTodos] = useState([]);
  const [expandedTodos, setExpandedTodos] = useState(false);
  const [confidence, setConfidence] = useState(0);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const messageIdRef = useRef(2);
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);
  
  const addMessage = (content, type = 'user', todos = []) => {
    const newMessage = {
      id: messageIdRef.current++,
      type,
      content,
      timestamp: new Date().toISOString(),
      todos
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  };
  
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    const userMessage = input.trim();
    setInput('');
    
    // Add user message
    addMessage(userMessage, 'user');
    
    // Show thinking state
    setIsThinking(true);
    setTodos([]);
    
    try {
      // Call reasoning endpoint
      const response = await fetch('http://localhost:8000/reasoning/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: userMessage })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const result = data.result;
        
        // Update todos from reasoning steps
        if (result.reasoning_steps) {
          setTodos(result.reasoning_steps);
        }
        
        // Update confidence
        if (result.confidence !== undefined) {
          setConfidence(result.confidence);
        }
        
        // Add agent response message
        addMessage(result.message, 'agent', result.reasoning_steps || []);
        
        // Add key findings if available
        if (result.key_findings && result.key_findings.length > 0) {
          const findingsContent = (
            <div className="findings-list">
              <strong>Key Findings:</strong>
              <ul>
                {result.key_findings.map((finding, idx) => (
                  <li key={idx}>{typeof finding === 'string' ? finding : JSON.stringify(finding)}</li>
                ))}
              </ul>
            </div>
          );
          addMessage(findingsContent, 'agent', []);
        }
        
        // Add recommendations if available
        if (result.recommendations && result.recommendations.length > 0) {
          const recsContent = (
            <div className="recommendations-list">
              <strong>Recommendations:</strong>
              <ul>
                {result.recommendations.map((rec, idx) => (
                  <li key={idx}>{typeof rec === 'string' ? rec : JSON.stringify(rec)}</li>
                ))}
              </ul>
            </div>
          );
          addMessage(recsContent, 'agent', []);
        }
      } else {
        addMessage(`Error: ${data.error || 'Unknown error'}`, 'agent');
      }
    } catch (error) {
      console.error('Error:', error);
      addMessage(`I encountered an error: ${error.message}`, 'agent');
    } finally {
      setIsThinking(false);
      inputRef.current?.focus();
    }
  };
  
  const handleKeyDown = (e) => {
    // Allow Enter to send, Shift+Enter for newline
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };
  
  const toggleTodos = () => {
    setExpandedTodos(!expandedTodos);
  };
  
  const getTodoStatusIcon = (status) => {
    switch (status) {
      case 'complete':
        return '✓';
      case 'in-progress':
        return '⟳';
      case 'failed':
        return '✗';
      default:
        return '○';
    }
  };
  
  const getTodoStatusColor = (status) => {
    switch (status) {
      case 'complete':
        return 'success';
      case 'in-progress':
        return 'loading';
      case 'failed':
        return 'error';
      default:
        return 'pending';
    }
  };
  
  return (
    <div className="chat-interface">
      {/* Header */}
      <div className="chat-header">
        <div className="header-content">
          <h1>🤖 Buddy - Autonomous Reasoning Agent</h1>
          <p>Ask me anything. I'll reason through it step by step.</p>
        </div>
        
        {/* Reasoning Stats */}
        {todos.length > 0 && (
          <div className="reasoning-stats">
            <div className="stat">
              <span className="stat-label">Steps</span>
              <span className="stat-value">{todos.length}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Confidence</span>
              <span className="stat-value">{(confidence * 100).toFixed(0)}%</span>
            </div>
            <button 
              className={`todos-toggle ${expandedTodos ? 'active' : ''}`}
              onClick={toggleTodos}
            >
              {expandedTodos ? '▼' : '▶'} Reasoning
            </button>
          </div>
        )}
      </div>
      
      {/* Todos Panel */}
      {expandedTodos && todos.length > 0 && (
        <div className="todos-panel">
          <div className="todos-header">Reasoning Steps</div>
          <div className="todos-list">
            {todos.map((todo, idx) => (
              <div 
                key={idx}
                className={`todo-item todo-${getTodoStatusColor(todo.status)}`}
              >
                <span className="todo-icon">
                  {getTodoStatusIcon(todo.status)}
                </span>
                <span className="todo-step">Step {todo.step}</span>
                <span className="todo-task">{todo.task}</span>
                {todo.result && (
                  <span className="todo-result">
                    {typeof todo.result === 'string' 
                      ? todo.result.substring(0, 50) + '...'
                      : JSON.stringify(todo.result).substring(0, 50) + '...'}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Messages */}
      <div className="messages-container">
        {messages.map((message) => (
          <div 
            key={message.id} 
            className={`message message-${message.type}`}
          >
            <div className="message-avatar">
              {message.type === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              {typeof message.content === 'string' ? (
                <p>{message.content}</p>
              ) : (
                message.content
              )}
              <span className="message-time">
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}
        
        {/* Thinking indicator */}
        {isThinking && (
          <div className="message message-agent thinking">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <p>Thinking...</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="chat-input-container">
        <form onSubmit={handleSendMessage}>
          <textarea
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything... (Shift+Enter for newline)"
            disabled={isThinking}
            rows="3"
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={isThinking || !input.trim()}
          >
            {isThinking ? '⟳ Thinking...' : '→ Send'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
