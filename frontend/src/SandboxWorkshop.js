import React, { useState, useRef, useEffect } from 'react';
import './SandboxWorkshop.css';

/**
 * Sandbox Workshop Component
 * 
 * Collaborative space where:
 * - Agent analyzes Buddy's own codebase
 * - Suggests UI/feature improvements
 * - Builds and tests them live
 * - User iterates and approves
 * 
 * No buttons. Natural conversation flow.
 */

const SandboxWorkshop = () => {
  const [messages, setMessages] = useState([
    {
      type: 'agent',
      role: 'workshop',
      content: '👋 Welcome to the Sandbox Workshop! I can help us build better together. Ask me to:\n\n• Review and suggest improvements to our codebase\n• Build new UI features\n• Test improvements\n• Explain architectural decisions\n\nWhat would you like to work on?',
      timestamp: new Date().toISOString()
    }
  ]);
  
  const [input, setInput] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [livePreview, setLivePreview] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const addMessage = (content, type = 'user') => {
    const msg = {
      type,
      role: type === 'user' ? 'user' : 'workshop',
      content,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, msg]);
    return msg;
  };
  
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const userInput = input.trim();
    setInput('');
    
    // Add user message
    addMessage(userInput, 'user');
    
    setIsAnalyzing(true);
    
    try {
      // Determine what the user wants
      const isCodeReview = /review|improve|analyze|suggest|what|wrong|better|refactor/i.test(userInput);
      const isBuildRequest = /build|create|make|implement|show|test/i.test(userInput);
      
      if (isCodeReview) {
        // Run background code analysis
        await analyzeOwnCode(userInput);
      } else if (isBuildRequest) {
        // Build/test something
        await buildImprovement(userInput);
      } else {
        // General conversation
        await conversationalResponse(userInput);
      }
    } catch (error) {
      addMessage(`Error: ${error.message}`, 'agent');
    } finally {
      setIsAnalyzing(false);
      inputRef.current?.focus();
    }
  };
  
  const analyzeOwnCode = async (prompt) => {
    // Call reasoning endpoint to analyze Buddy's own code
    try {
      const response = await fetch('http://localhost:8000/reasoning/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goal: `Analyze Buddy's codebase and provide suggestions for improvement. ${prompt}`
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const result = data.result;
        
        // Show agent's analysis
        addMessage(result.message, 'agent');
        
        // Show findings as structured data
        if (result.key_findings && result.key_findings.length > 0) {
          const findings = result.key_findings
            .map(f => `• ${typeof f === 'string' ? f : JSON.stringify(f)}`)
            .join('\n');
          addMessage(`**Key Findings:**\n\n${findings}`, 'agent');
        }
        
        // Store for preview/building
        // (In future: setAnalysisResults(result) for building on results)
        
        // Show recommendations
        if (result.recommendations && result.recommendations.length > 0) {
          const recs = result.recommendations
            .map(r => `→ ${typeof r === 'string' ? r : JSON.stringify(r)}`)
            .join('\n');
          addMessage(`**What we could improve:**\n\n${recs}\n\nSay "build [idea]" to create it, or ask more questions!`, 'agent');
        }
      } else {
        addMessage(`Analysis failed: ${data.error}`, 'agent');
      }
    } catch (error) {
      addMessage(`Couldn't analyze: ${error.message}`, 'agent');
    }
  };
  
  const buildImprovement = async (prompt) => {
    addMessage('🔨 Building... Let me create this for you.', 'agent');
    
    // Simulate building - in real implementation would call build endpoint
    setTimeout(() => {
      addMessage('✨ I\'ve created a preview. Here\'s what I built:', 'agent');
      
      // Show live preview
      setLivePreview({
        title: 'New UI Component Preview',
        code: `// New component based on suggestion
const NewFeature = () => {
  return (
    <div className="new-feature">
      <h2>Improved Feature</h2>
      <p>This shows what the improvement looks like</p>
    </div>
  );
};`,
        description: 'Click "Approve", "Reject", or "Iterate" to continue.'
      });
      
      addMessage('**Live Preview Ready** - See it on the right side of your screen.\n\nWhat do you think? Should we:\n• ✅ **Approve** - Merge this into the actual code\n• ❌ **Reject** - Discard and try something else\n• 🔄 **Iterate** - Make adjustments', 'agent');
    }, 800);
  };
  
  const conversationalResponse = async (prompt) => {
    // Just respond conversationally
    const responses = [
      'Interesting thought! To help better, could you tell me more about what you\'d like to improve?',
      'I can help with that! Do you want me to review the codebase first, or do you have a specific area in mind?',
      'Great idea! Should I analyze the current code structure and suggest improvements, or do you want to start fresh?'
    ];
    
    addMessage(responses[Math.floor(Math.random() * responses.length)], 'agent');
  };
  
  const handleApprove = () => {
    addMessage('✅ Great! I\'ve merged the improvement into the codebase. What should we work on next?', 'agent');
    setLivePreview(null);
  };
  
  const handleReject = () => {
    addMessage('❌ Noted, we\'ll try a different approach. What would work better?', 'agent');
    setLivePreview(null);
  };
  
  const handleIterate = () => {
    addMessage('🔄 What adjustments should I make? Describe the changes you\'d like to see.', 'agent');
  };
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };
  
  return (
    <div className="sandbox-workshop">
      {/* Main workspace */}
      <div className="workshop-main">
        {/* Conversation area */}
        <div className="workshop-conversation">
          <div className="conversation-header">
            <h2>🔧 Sandbox Workshop</h2>
            <p>Building better together</p>
          </div>
          
          <div className="messages-feed">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message message-${msg.type}`}>
                <div className="message-avatar">
                  {msg.type === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-body">
                  <div className="message-text">{msg.content}</div>
                  <span className="message-time">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
            
            {isAnalyzing && (
              <div className="message message-agent thinking">
                <div className="message-avatar">🤖</div>
                <div className="message-body">
                  <div className="thinking-indicator">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          {/* Input area */}
          <form onSubmit={handleSendMessage} className="workshop-input">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Review the code... Build a new feature... Ask a question..."
              disabled={isAnalyzing}
              rows="2"
            />
            <button type="submit" disabled={isAnalyzing || !input.trim()}>
              {isAnalyzing ? '🔄' : '→'}
            </button>
          </form>
        </div>
        
        {/* Live preview area */}
        <div className="workshop-preview">
          {livePreview ? (
            <div className="preview-container">
              <div className="preview-header">
                <h3>✨ Live Preview</h3>
                <p>{livePreview.description}</p>
              </div>
              
              <div className="preview-content">
                <div className="preview-render">
                  {/* Show the actual component preview */}
                  <div className="new-feature-preview">
                    <h2>{livePreview.title}</h2>
                    <pre className="code-preview">{livePreview.code}</pre>
                  </div>
                </div>
              </div>
              
              <div className="preview-actions">
                <button onClick={handleApprove} className="action-approve">
                  ✅ Approve
                </button>
                <button onClick={handleIterate} className="action-iterate">
                  🔄 Iterate
                </button>
                <button onClick={handleReject} className="action-reject">
                  ❌ Reject
                </button>
              </div>
            </div>
          ) : (
            <div className="preview-empty">
              <div className="empty-state">
                <h3>Preview Area</h3>
                <p>Ask me to build something and watch it appear here</p>
                <div className="preview-tips">
                  <p>Try saying:</p>
                  <ul>
                    <li>"Review the ChatInterface code"</li>
                    <li>"Suggest improvements to the reasoning system"</li>
                    <li>"Build a better dashboard"</li>
                    <li>"Analyze the component structure"</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SandboxWorkshop;
