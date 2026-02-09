import React, { useState, useEffect, useRef } from 'react';
import './DashboardStyles.css';

function InteractionDashboard() {
  const [messages, setMessages] = useState([
    { id: 1, type: 'system', text: 'Welcome to Interaction Dashboard', timestamp: new Date() }
  ]);
  const [input, setInput] = useState('');
  const [notifications, setNotifications] = useState([
    { id: 1, type: 'info', message: 'System initialized', time: new Date().toLocaleTimeString() }
  ]);
  const [searchTerm, setSearchTerm] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = () => {
    if (input.trim()) {
      const newMessage = {
        id: messages.length + 1,
        type: 'user',
        text: input,
        timestamp: new Date()
      };
      setMessages([...messages, newMessage]);

      // Simulate bot response
      setTimeout(() => {
        const response = {
          id: messages.length + 2,
          type: 'bot',
          text: `Processing: "${input}"... This is a read-only interaction view. Actual task execution occurs through the Operations dashboard.`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, response]);
      }, 500);

      setInput('');
    }
  };

  const handleAddNotification = (type, message) => {
    const newNotification = {
      id: notifications.length + 1,
      type,
      message,
      time: new Date().toLocaleTimeString()
    };
    setNotifications([newNotification, ...notifications].slice(0, 20));
  };

  const filteredMessages = messages.filter(msg =>
    msg.text.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="dashboard-view interaction-dashboard">
      <div className="dashboard-header">
        <h1>Interaction Dashboard</h1>
        <span className="subtitle">Chat with Buddy • View notifications & alerts</span>
      </div>

      <div className="interaction-grid">
        {/* Chat Section */}
        <div className="chat-section">
          <div className="chat-container">
            <div className="chat-header">
              <h2>💬 Chat with Buddy</h2>
              <span className="status-indicator online">Online</span>
            </div>
            <div className="messages-container">
              {filteredMessages.map((msg) => (
                <div key={msg.id} className={`message message-${msg.type}`}>
                  <div className="message-avatar">
                    {msg.type === 'user' ? '👤' : msg.type === 'system' ? '⚙️' : '🤖'}
                  </div>
                  <div className="message-content">
                    <p>{msg.text}</p>
                    <span className="message-time">{msg.timestamp.toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            <div className="chat-input-area">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask a question or describe a task..."
                className="chat-input"
              />
              <button onClick={handleSendMessage} className="send-btn">Send</button>
            </div>
          </div>
        </div>

        {/* Notifications Section */}
        <div className="notifications-section">
          <div className="card">
            <div className="notifications-header">
              <h2>🔔 Notifications & Alerts</h2>
              <button
                className="clear-btn"
                onClick={() => setNotifications([])}
              >
                Clear All
              </button>
            </div>

            <div className="search-box">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search messages..."
                className="search-input"
              />
            </div>

            <div className="notifications-list">
              {notifications.length === 0 ? (
                <div className="empty-state">No notifications</div>
              ) : (
                notifications.map((notif) => (
                  <div key={notif.id} className={`notification notification-${notif.type}`}>
                    <span className="notif-icon">
                      {notif.type === 'error' ? '❌' : notif.type === 'success' ? '✅' : 'ℹ️'}
                    </span>
                    <div className="notif-content">
                      <p>{notif.message}</p>
                      <span className="notif-time">{notif.time}</span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="quick-actions">
              <button
                className="action-btn"
                onClick={() => handleAddNotification('success', 'Goal approved and queued for execution')}
              >
                ✅ Simulate Approval
              </button>
              <button
                className="action-btn"
                onClick={() => handleAddNotification('error', 'Task failed: Connection timeout')}
              >
                ❌ Simulate Alert
              </button>
            </div>
          </div>

          {/* Active Tasks Summary */}
          <div className="card">
            <h2>📋 Active Interactions</h2>
            <div className="interactions-summary">
              <div className="interaction-item">
                <span className="label">Messages Exchanged</span>
                <span className="value">{messages.length}</span>
              </div>
              <div className="interaction-item">
                <span className="label">Active Notifications</span>
                <span className="value">{notifications.length}</span>
              </div>
              <div className="interaction-item">
                <span className="label">Session Duration</span>
                <span className="value">Active</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default InteractionDashboard;
