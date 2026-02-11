import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './UnifiedChat.css';
import SuccessFeedback from './SuccessFeedback';
import BrowserView from './components/BrowserView';
import LiveBrowserView from './components/LiveBrowserView';
import MissionVisualizer from './components/MissionVisualizer';
import { generateBuddyResponse } from './whiteboardContextGenerator';

/* global firebase */

/**
 * Unified Chat with Integrated Sandbox
 * 
 * One conversation where:
 * - You talk to Buddy
 * - Buddy suggests improvements
 * - Interactive previews appear inline in chat
 * - You interact with UI, not code
 * - Agent explains what was built
 * 
 * No tabs. No separation. Just natural collaboration.
 */

const createWelcomeMessages = () => ([]);

const createSession = (id, title, topic = '') => ({
  id: String(id),
  title: title || `Session ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`,
  topic: topic || 'General conversation',
  archived: false,
  createdAt: new Date().toISOString(),
  messages: createWelcomeMessages(),
  messageCount: createWelcomeMessages().length,
  source: 'chat_ui',
  externalUserId: null,
  linkedGoals: []
});

const loadSessions = () => {
  // Sessions will be loaded from backend API in useEffect
  // Return empty array initially
  return [];
};

const getAuthHeaders = async () => {
  if (typeof firebase === 'undefined' || !firebase.auth) {
    return {};
  }

  const user = firebase.auth().currentUser;
  if (!user) {
    return {};
  }

  try {
    const token = await user.getIdToken();
    return { Authorization: `Bearer ${token}` };
  } catch (error) {
    console.warn('Failed to get auth token:', error);
    return {};
  }
};

const authorizedFetch = async (url, options = {}) => {
  const authHeaders = await getAuthHeaders();
  const mergedHeaders = { ...(options.headers || {}), ...authHeaders };
  return fetch(url, { ...options, headers: mergedHeaders });
};

const mapBackendMessage = (message) => ({
  id: message.message_id,
  type: message.role === 'user' ? 'user' : 'agent',
  content: message.text,
  timestamp: message.timestamp,
  source: message.source
});

const mapBackendSession = (session, sessionNumber) => ({
  id: String(session.session_id),
  title: session.source === 'telegram'
    ? `Telegram ${session.external_user_id || ''}`.trim()
    : (session.title || `Session ${new Date(session.messages?.[0]?.timestamp || new Date()).toLocaleDateString()} ${new Date(session.messages?.[0]?.timestamp || new Date()).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`),
  topic: session.source === 'telegram' ? 'Telegram conversation' : 'General conversation',
  archived: session.archived || false,
  createdAt: session.messages?.[0]?.timestamp || new Date().toISOString(),
  messages: (session.messages || []).map(mapBackendMessage),
  messageCount: session.message_count ?? (session.messages || []).length,
  source: session.source,
  externalUserId: session.external_user_id || null,
  linkedGoals: session.linked_goals || []
});

const mergeSessions = (localSessions, remoteSessions) => {
  const merged = [...localSessions];
  const localMap = new Map(localSessions.map(s => [String(s.id), s]));

  remoteSessions.forEach(remote => {
    const existing = localMap.get(String(remote.id));
    if (existing) {
      const updated = {
        ...existing,
        ...remote,
        messages: remote.messages.length > 0 ? remote.messages : existing.messages,
        messageCount: remote.messageCount ?? existing.messageCount
      };
      const idx = merged.findIndex(s => String(s.id) === String(remote.id));
      if (idx >= 0) merged[idx] = updated;
    } else {
      merged.unshift(remote);
    }
  });

  return merged;
};

const UnifiedChat = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [sessions, setSessions] = useState(loadSessions);
  const [activeSessionId, setActiveSessionId] = useState(() => {
    // Restore last active session from localStorage (UI state only)
    try {
      return localStorage.getItem('buddy_active_session_id') || null;
    } catch {
      return null;
    }
  });
  const [showArchived, setShowArchived] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [sessionNameDraft, setSessionNameDraft] = useState('');

  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [confidence, setConfidence] = useState(0);
  const [isListening, setIsListening] = useState(false);
  const [silenceTimer, setSilenceTimer] = useState(null);
  const [showKnowledgeGraph, setShowKnowledgeGraph] = useState(false);
  const [knowledgeData, setKnowledgeData] = useState(null);
  const [activeMissionStreamId, setActiveMissionStreamId] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const [messageIdCounter, setMessageIdCounter] = useState(2);
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);
  
  const activeSession = sessions.find(session => session.id === activeSessionId) || sessions[0];
  const messages = activeSession?.messages || [];

  useEffect(() => {
    if (!activeSessionId && sessions.length > 0) {
      setActiveSessionId(sessions[0].id);
    }
  }, [activeSessionId, sessions]);

  // Load sessions from backend on component mount
  useEffect(() => {
    const loadSessionsFromBackend = async () => {
      try {
        const response = await authorizedFetch('/conversation/sessions');
        if (response.ok) {
          const data = await response.json();
          const backendSessions = (data.sessions || []).map((session, index) => 
            mapBackendSession(session, (data.sessions || []).length - index)
          );
          setSessions(backendSessions);
          
          const savedSessionId = localStorage.getItem('buddy_active_session_id');
          if (savedSessionId) {
            const sessionExists = backendSessions.some(s => s.id === savedSessionId);
            setActiveSessionId(sessionExists ? savedSessionId : backendSessions[0]?.id || null);
          } else if (backendSessions.length > 0) {
            setActiveSessionId(backendSessions[0].id);
          }
        }
      } catch (error) {
        setSessions([]);
      }
    };
    
    loadSessionsFromBackend();
  }, []); // Run once on mount

  // Load messages when active session changes
  useEffect(() => {
    const loadSessionDetails = async () => {
      if (!activeSessionId) return;
      
      try {
        const response = await authorizedFetch(`/conversation/sessions/${activeSessionId}`);
        if (!response.ok) return;
        
        const fullSession = await response.json();
        const sessionWithMessages = mapBackendSession(fullSession);
        setSessions(prev => mergeSessions(prev, [sessionWithMessages]));
      } catch (error) {
        // Silently fail - session loading errors are not critical
      }
    };
    
    loadSessionDetails();
  }, [activeSessionId]);

  // Save active session ID to localStorage (UI state only)
  useEffect(() => {
    if (activeSessionId) {
      try {
        localStorage.setItem('buddy_active_session_id', activeSessionId);
      } catch {
        // Ignore localStorage errors
      }
    }
  }, [activeSessionId]);

  // Load sessions from backend on mount
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load sessions from backend on mount and when navigating back to chat
  useEffect(() => {
    const loadSessionsFromBackend = async () => {
      try {
        const response = await authorizedFetch('/conversation/sessions');
        if (response.ok) {
          const data = await response.json();
          const backendSessions = (data.sessions || []).map((session, index) => 
            mapBackendSession(session, (data.sessions || []).length - index)
          );
          setSessions(backendSessions);
          
          if (activeSessionId) {
            const sessionExists = backendSessions.some(s => s.id === activeSessionId);
            if (!sessionExists && backendSessions.length > 0) {
              try { localStorage.removeItem('buddy_active_session_id'); } catch {}
              setActiveSessionId(backendSessions[0].id);
            }
          } else if (backendSessions.length > 0) {
            setActiveSessionId(backendSessions[0].id);
          }
        }
      } catch (error) {
        setSessions([]);
      }
    };
    
    // Load on component mount and whenever location changes
    loadSessionsFromBackend();
    
    // Also reload when tab comes back into focus (returns from another tab/app)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadSessionsFromBackend();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [location.pathname, activeSessionId]); // Reload when navigating or session changes

  // Focus input when component mounts or active session changes
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [activeSessionId]);

  useEffect(() => {
    // Setup speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      
      recognitionRef.current.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        
        setInput(transcript);
        
        // Clear existing timer
        if (silenceTimer) {
          clearTimeout(silenceTimer);
        }
        
        // Set new timer for 3 seconds of silence
        const timer = setTimeout(() => {
          if (transcript.trim()) {
            handleSendMessage(new Event('submit'));
            setIsListening(false);
            if (recognitionRef.current) {
              recognitionRef.current.stop();
            }
          }
        }, 3000);
        
        setSilenceTimer(timer);
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };
      
      recognitionRef.current.onend = () => {
        if (isListening) {
          recognitionRef.current.start();
        }
      };
    }
    
    return () => {
      if (silenceTimer) {
        clearTimeout(silenceTimer);
      }
    };
  }, [activeSessionId, isListening, silenceTimer]);

  const updateActiveSession = (updater) => {
    setSessions(prev => {
      let targetId = activeSessionId;
      if (!targetId || !prev.some(session => session.id === targetId)) {
        targetId = prev[0]?.id || null;
      }
      if (!targetId) {
        return prev;
      }
      return prev.map(session => (
        session.id === targetId ? updater(session) : session
      ));
    });
  };

  const speakText = (text) => {
    // Cancel any ongoing speech
    synthRef.current.cancel();
    
    // Replace visual references
    const spokenText = text
      .replace(/\[.*?\]\(.*?\)/g, '') // Remove markdown links
      .replace(/preview/gi, 'on the screen')
      .replace(/above|below/gi, 'on the screen')
      .replace(/inline/gi, 'on the screen');
    
    const utterance = new SpeechSynthesisUtterance(spokenText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    synthRef.current.speak(utterance);
  };

  const toggleVoiceInput = () => {
    if (isListening) {
      setIsListening(false);
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (silenceTimer) {
        clearTimeout(silenceTimer);
      }
    } else {
      setIsListening(true);
      if (recognitionRef.current) {
        recognitionRef.current.start();
      }
    }
  };

  const handleKnowledgeClick = async () => {
    try {
      const response = await authorizedFetch('/knowledge/graph?domain=_global');
      const data = await response.json();
      setKnowledgeData(data);
      setShowKnowledgeGraph(true);
    } catch (error) {
      console.error('Failed to fetch knowledge graph:', error);
    }
  };

  // Removed: handleInteractiveAction - approval now comes through natural language chat messages

  const addMessage = (content, type = 'user', preview = null, todosList = [], goalId = null, toolResults = null, source = null, interactiveElements = []) => {
    const uniqueId = typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const msg = {
      id: uniqueId,
      type,
      content,
      timestamp: new Date().toISOString(),
      preview,
      todos: todosList,
      goalId,
      toolResults,  // Add tool results
      source: source || activeSession?.source || 'chat_ui',
      interactiveElements
    };
    updateActiveSession(session => ({
      ...session,
      messages: [...session.messages, msg],
      messageCount: (session.messageCount ?? session.messages.length) + 1
    }));
    setMessageIdCounter(prev => prev + 1);
    return msg;
  };

  const handleCreateSession = async () => {
    try {
      // Call backend to create session
      const response = await authorizedFetch('/conversation/sessions/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ external_user_id: 'anonymous' })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // Find next available session number
        const existingNumbers = sessions
          .map(s => s.title.match(/^Session (\d+)$/))
          .filter(Boolean)
          .map(m => parseInt(m[1]));
        const nextNumber = existingNumbers.length > 0 ? Math.max(...existingNumbers) + 1 : 1;
        const sessionTitle = `Session ${nextNumber}`;
        
        // Save title to backend
        await authorizedFetch(`/conversation/sessions/${data.session_id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: sessionTitle })
        }).catch(err => console.warn('Failed to save session title:', err));
        
        // Create session with backend's ID and numbered title
        const newSession = createSession(data.session_id, sessionTitle, '');
        setSessions(prev => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
      }
    } catch (error) {
      console.error('Failed to create session:', error);
      // Fallback to local creation
      const existingNumbers = sessions
        .map(s => s.title.match(/^Session (\d+)$/))
        .filter(Boolean)
        .map(m => parseInt(m[1]));
      const nextNumber = existingNumbers.length > 0 ? Math.max(...existingNumbers) + 1 : 1;
      const newSession = createSession(Date.now(), `Session ${nextNumber}`, '');
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
    }
  };

  const handleRenameSession = async (sessionId, newTitle) => {
    if (!newTitle.trim()) return;
    
    try {
      const response = await authorizedFetch(`/conversation/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle.trim() })
      });
      
      if (response.ok) {
        setSessions(prev => prev.map(session => (
          session.id === sessionId ? { ...session, title: newTitle.trim() } : session
        )));
      }
    } catch (error) {
      console.error('Failed to rename session:', error);
    }
    
    setEditingSessionId(null);
    setSessionNameDraft('');
  };

  const handleArchiveSession = async (sessionId) => {
    const session = sessions.find(s => s.id === sessionId);
    if (!session) return;
    
    try {
      const response = await authorizedFetch(`/conversation/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ archived: !session.archived })
      });
      
      if (response.ok) {
        setSessions(prev => prev.map(s => (
          s.id === sessionId ? { ...s, archived: !s.archived } : s
        )));
      }
    } catch (error) {
      console.error('Failed to archive session:', error);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!window.confirm('Delete this session? This cannot be undone.')) return;
    
    try {
      const response = await authorizedFetch(`/conversation/sessions/${sessionId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        setSessions(prev => {
          const remaining = prev.filter(session => session.id !== sessionId);
          if (activeSessionId === sessionId) {
            setActiveSessionId(remaining[0]?.id || null);
          }
          return remaining;
        });
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };
  
  const processMessage = async (userInput) => {
    if (!userInput.trim()) return;
    setIsThinking(true);
    inputRef.current?.focus();

    try {
      if (activeSession?.source === 'telegram') {
        addMessage(userInput, 'user', null, [], null, null, 'chat_ui');
        const response = await authorizedFetch('/conversation/message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: activeSession.id,
            source: 'telegram',
            external_user_id: activeSession.externalUserId,
            text: userInput
          })
        });
        const data = await response.json();
        const reply = data.response || 'Buddy received your message.';
        addMessage(reply, 'agent', null, [], null, null, 'buddy_core');
        if (Array.isArray(data.linked_goals)) {
          updateActiveSession(session => ({
            ...session,
            linkedGoals: data.linked_goals
          }));
        }
        setIsThinking(false);
        return;
      }

      // Add user message to chat
      addMessage(userInput.trim(), 'user');
      
      // Ensure we have an active session - create one if needed
      let currentSessionId = activeSession?.id;
      if (!currentSessionId) {
        console.warn('[SESSION] No active session, creating one automatically');
        try {
          // Create session synchronously
          const response = await authorizedFetch('/conversation/sessions/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ external_user_id: 'anonymous' })
          });
          const data = await response.json();
          if (data.status === 'success') {
            currentSessionId = data.session_id;
            
            // Find next number and save title
            const existingNumbers = sessions
              .map(s => s.title.match(/^Session (\d+)$/))
              .filter(Boolean)
              .map(m => parseInt(m[1]));
            const nextNumber = existingNumbers.length > 0 ? Math.max(...existingNumbers) + 1 : 1;
            const sessionTitle = `Session ${nextNumber}`;
            
            await authorizedFetch(`/conversation/sessions/${currentSessionId}`, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ title: sessionTitle })
            }).catch(err => console.warn('Failed to save session title:', err));
            
            // Add to sessions list
            const newSession = createSession(currentSessionId, sessionTitle, '');
            setSessions(prev => [newSession, ...prev]);
            setActiveSessionId(currentSessionId);
          } else {
            throw new Error('Failed to create session');
          }
        } catch (error) {
          console.error('[SESSION] Failed to create session:', error);
          addMessage('Error: Could not create chat session. Please try again.', 'agent');
          setIsThinking(false);
          return;
        }
      }
      
      // PHASE 3 INTEGRATION: Call unified chat endpoint
      // This is now the canonical path for all chat messages
      const response = await authorizedFetch('/chat/integrated', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSessionId,  // Always send a valid session_id
          source: 'chat_ui',
          external_user_id: null,
          text: userInput.trim()
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success' && data.envelope) {
        const env = data.envelope;
        const responseEngine = data.response_engine;
        const responseText = responseEngine?.primary_content || env.summary || 'Processing your request...';
        addMessage(responseText, 'agent', null, [], null, null, 'chat_ui', responseEngine?.interactive_elements || []);

        if (env.live_stream_id) {
          setActiveMissionStreamId(env.live_stream_id);
        }
        
        // Display any proposed missions
        if (env.missions_spawned && env.missions_spawned.length > 0) {
          const missionsText = env.missions_spawned.map((m, i) => 
            `**Mission ${i + 1}**: ${m.objective_description || m.objective_type || 'Unnamed'}\n(Status: ${m.status}, ID: ${m.mission_id})`
          ).join('\n\n');
          
          addMessage(`Proposed Missions:\n\n${missionsText}\n\nYou can view mission details by asking or check the whiteboard.`, 'agent');
        }
        
        // Display artifacts if any
        if (env.artifacts && env.artifacts.length > 0) {
          const artifactsText = env.artifacts.map((a, i) =>
            `**Artifact ${i + 1}**: ${a.artifact_type || 'Unknown'} - ${a.title || 'Untitled'}`
          ).join('\n');
          
          addMessage(`Artifacts Generated:\n\n${artifactsText}`, 'agent');
        }
        
        // Note if streaming
        if (env.live_stream_id) {
          addMessage(`Live Stream: Watch execution progress at stream ID ${env.live_stream_id}`, 'agent');
        }

      } else {
        addMessage(`Error: ${data.error || 'Unknown error'}`, 'agent');
      }
    } catch (error) {
      addMessage(`Couldn't connect: ${error.message}`, 'agent');
    } finally {
      setIsThinking(false);
    }
  };

  const submitMessage = (userInput) => {
    if (!userInput.trim()) return;
    // Message will be added in processMessage() to avoid duplicates
    processMessage(userInput.trim());
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userInput = input.trim();
    setInput('');
    submitMessage(userInput);
    
    // FIX: Restore focus to input after sending message
    // Use setTimeout to ensure DOM has updated and state is flushed
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }, 0);
  };

  useEffect(() => {
    try {
      const injectedContext = localStorage.getItem('whiteboard_context');
      if (injectedContext) {
        localStorage.removeItem('whiteboard_context');
        
        // Parse the context payload
        const context = JSON.parse(injectedContext);
        
        if (context.source === 'whiteboard') {
          // System intake: context is invisible to user
          // Buddy auto-generates a response based on the context
          const buddyResponse = generateBuddyResponse(context);
          
          // Add Buddy's contextual response as an agent message (not user)
          addMessage(buddyResponse, 'agent');
          
          console.log('Whiteboard context received:', context);
        }
      }
    } catch (error) {
      console.error('Failed to load whiteboard context:', error);
    }
  }, [activeSessionId]);
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };
  
  const extractComponentName = (input) => {
    const words = input.split(' ');
    return words.slice(1, 3).join(' ') || 'Feature';
  };
  
  const generatePreviewComponent = (input) => {
    // Return component based on request
    if (/toggle|dark|mode|theme/i.test(input)) {
      return 'DarkModeToggle';
    }
    if (/keyboard|shortcut/i.test(input)) {
      return 'KeyboardShortcuts';
    }
    if (/dashboard|stat|metric/i.test(input)) {
      return 'Dashboard';
    }
    return 'CustomComponent';
  };
  
  const generateFeatures = (input) => {
    if (/toggle|dark|mode|theme/i.test(input)) {
      return [
        '- Toggle between light and dark themes',
        '- Your preference is saved',
        '- Smooth transitions',
        '- Works with the existing design'
      ];
    }
    if (/keyboard|shortcut/i.test(input)) {
      return [
        '- View all keyboard shortcuts',
        '- Search shortcuts',
        '- Copy any shortcut',
        '- Learn helpful tips'
      ];
    }
    return [
      '- Fully interactive component',
      '- Try clicking around',
      '- See how it works',
      '- Let me know what you think'
    ];
  };
  
  const handlePreviewAction = (action, messageId) => {
    if (action === 'approve') {
      addMessage('Perfect! I merged it into the system. What would you like to do next?', 'agent');
      updateActiveSession(session => ({
        ...session,
        messages: session.messages.map((msg) => (
          msg.id === messageId ? { ...msg, preview: null } : msg
        ))
      }));
    } else if (action === 'reject') {
      addMessage('Got it, let\'s try something different. What changes would you like?', 'agent');
      updateActiveSession(session => ({
        ...session,
        messages: session.messages.map((msg) => (
          msg.id === messageId ? { ...msg, preview: null } : msg
        ))
      }));
    }
  };
  
  const getTodoStatusIcon = (status) => {
    switch(status) {
      case 'complete': return '[x]';
      case 'in_progress': return '[~]';
      case 'failed': return '[!]';
      default: return '[ ]';
    }
  };
  
  const visibleSessions = sessions.filter(session => showArchived || !session.archived);

  return (
    <div className="unified-chat-shell">
      {showKnowledgeGraph && (
        <div className="knowledge-modal-overlay" onClick={() => setShowKnowledgeGraph(false)}>
          <div className="knowledge-modal" onClick={(e) => e.stopPropagation()}>
            <div className="knowledge-modal-header">
              <h2>Buddy Knowledge and Performance</h2>
              <button onClick={() => setShowKnowledgeGraph(false)} className="close-btn">X</button>
            </div>
            <div className="knowledge-modal-content">
              {knowledgeData ? (
                <>
                  <div className="knowledge-stats">
                    <div className="stat-card">
                      <div className="stat-label">Total Skills</div>
                      <div className="stat-value">{knowledgeData.nodes?.length || 0}</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-label">Connections</div>
                      <div className="stat-value">{knowledgeData.edges?.length || 0}</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-label">Success Rate</div>
                      <div className="stat-value">{knowledgeData.metrics?.overall_success_rate ? `${(knowledgeData.metrics.overall_success_rate * 100).toFixed(0)}%` : 'N/A'}</div>
                    </div>
                  </div>
                  
                  <div className="knowledge-skills">
                    <h3>Skills & Expertise</h3>
                    <div className="skills-grid">
                      {knowledgeData.nodes?.map((node, idx) => (
                        <div key={idx} className="skill-item">
                          <div className="skill-name">{node.label || node.id}</div>
                          {node.confidence && (
                            <div className="skill-confidence">
                              <div className="skill-bar" style={{width: `${node.confidence * 100}%`}}></div>
                              <span>{(node.confidence * 100).toFixed(0)}%</span>
                            </div>
                          )}
                        </div>
                      )) || <p>No skills tracked yet.</p>}
                    </div>
                  </div>
                </>
              ) : (
                <div className="loading">Loading knowledge graph...</div>
              )}
            </div>
          </div>
        </div>
      )}

      <aside className="buddy-panel">
        <h1 className="buddy-name">Buddy</h1>
        <div className="buddy-container">
          <img 
            src="/Buddy.png" 
            alt="Buddy" 
            className="buddy-avatar-large"
            data-testid="open-whiteboard"
            onClick={() => navigate('/whiteboard')}
            title="Click to open Whiteboard"
          />
        </div>
        
        <div className="sessions-sidebar">
          <div className="sidebar-header">
            <h2>Sessions</h2>
            <button onClick={handleCreateSession} className="new-session-btn">+ New Session</button>
          </div>
          <div className="sidebar-toggle">
            <label>
              <input
                type="checkbox"
                checked={showArchived}
                onChange={(e) => setShowArchived(e.target.checked)}
              />
              Show archived
            </label>
          </div>
          <div className="sessions-list">
            {visibleSessions.map(session => (
              <div
                key={session.id}
                className={`session-item ${session.id === activeSessionId ? 'active' : ''} ${session.archived ? 'archived' : ''}`}
                onClick={() => setActiveSessionId(session.id)}
              >
                <div className="session-title">
                  {editingSessionId === session.id ? (
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        handleRenameSession(session.id, sessionNameDraft);
                      }}
                    >
                      <input
                        value={sessionNameDraft}
                        onChange={(e) => setSessionNameDraft(e.target.value)}
                        onBlur={() => handleRenameSession(session.id, sessionNameDraft)}
                        autoFocus
                      />
                    </form>
                  ) : (
                    <span>{session.title}</span>
                  )}
                  <span className="session-count">{session.messageCount ?? session.messages.length}</span>
                </div>
                <div className="session-actions">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingSessionId(session.id);
                      setSessionNameDraft(session.title);
                    }}
                    title="Rename"
                  >Edit</button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleArchiveSession(session.id);
                    }}
                    title={session.archived ? 'Unarchive' : 'Archive'}
                  >{session.archived ? 'Unarchive' : 'Archive'}</button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSession(session.id);
                    }}
                    title="Delete"
                  >Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>

      <div className="unified-chat">
        <div className="chat-header">
          <div className="header-content">
            <div className="header-actions">
              <button
                type="button"
                className="logout-btn"
                onClick={async () => {
                  try {
                    if (typeof firebase !== 'undefined' && firebase.auth) {
                      await firebase.auth().signOut();
                    }
                  } catch (error) {
                    console.error('Sign out error:', error);
                  }
                }}
              >
                Log out
              </button>
            </div>
          </div>
        </div>

        <div className="messages-container">
          {messages.map((msg, idx) => (
          <div key={msg.id}>
            {/* Message */}
            <div className={`message message-${msg.type}`}>
              <div className="message-avatar">
                {msg.type === 'user' ? <svg width="40" height="40" viewBox="0 0 40 40" style={{backgroundColor: '#e0e0e0', borderRadius: '50%'}}><circle cx="20" cy="12" r="6" fill="#666"/><path d="M20 20 Q5 30 5 40 L35 40 Q35 30 20 20" fill="#666"/></svg> : <img src="/Buddy.png" alt="Buddy" onError={(e) => {e.target.style.display='none'}} />}
              </div>
              <div className="message-body">
                <div className="message-text">{msg.content}</div>
                {msg.source && (
                  <div className="message-source">Source: {msg.source}</div>
                )}
                
                {/* Tool Results Display */}
                {msg.toolResults && msg.toolResults.length > 0 && (
                  <div className="tool-results">
                    <details>
                      <summary>Tool Execution Results ({msg.toolResults.filter(t => t.success).length}/{msg.toolResults.length} succeeded)</summary>
                      <div className="tool-results-list">
                        {msg.toolResults.map((result, i) => (
                          <div key={`${msg.id}-tool-${i}`} className={`tool-result tool-result-${result.success ? 'success' : 'failure'}`}>
                            <span className="tool-status">{result.status}</span>
                            <span className="tool-name">{result.tool_name}</span>
                            {!result.success && (
                              <div className="tool-error">Error: {result.message}</div>
                            )}
                            {result.success && result.message && (
                              <div className="tool-output">{result.message}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}
                
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
                
                {/* Todos if present */}
                {msg.todos && msg.todos.length > 0 && (
                  <details className="message-todos">
                    <summary>Show my reasoning ({msg.todos.filter(t => t.status === 'complete').length}/{msg.todos.length} steps)</summary>
                    <div className="todos-list">
                      {msg.todos.map((todo, i) => (
                        <div key={`${msg.id}-todo-${todo.step_num ?? todo.id ?? i}`} className={`todo-item todo-${todo.status}`}>
                          <span className="todo-icon">{getTodoStatusIcon(todo.status)}</span>
                          <span className="todo-task">{todo.task || `Step ${todo.step_num}`}</span>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
                
                {/* Feedback component for agent responses */}
                {msg.type === 'agent' && msg.goalId && (
                  <SuccessFeedback 
                    goalId={msg.goalId}
                    messageIndex={idx}
                    onFeedbackSubmitted={(score) => {
                      console.log(`Feedback submitted with score: ${score}`);
                    }}
                  />
                )}
              </div>
            </div>
            
            {/* Inline Preview */}
            {msg.preview && (
              <div className="inline-preview">
                {msg.preview.type === 'browser_live' ? (
                  <>
                    <div className="preview-header">
                      <h3>Live Browser View</h3>
                      <p>{msg.preview.description}</p>
                    </div>
                    <LiveBrowserView
                      streamUrl={msg.preview.streamUrl}
                      onInteract={async (action) => {
                        try {
                          await authorizedFetch('/vision/interact', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(action)
                          });
                        } catch (err) {
                          console.log('Live interaction error:', err);
                        }
                      }}
                    />
                  </>
                ) : msg.preview.type === 'browser' ? (
                  <>
                    <div className="preview-header">
                      <h3>Live Browser View</h3>
                      {msg.preview.pageState?.url && (
                        <p>{msg.preview.pageState.url}</p>
                      )}
                    </div>
                    <BrowserView 
                      screenshot={msg.preview.screenshot}
                      pageState={msg.preview.pageState}
                      clickables={msg.preview.clickables || []}
                      onInteract={(action) => {
                        console.log('User interacted with browser:', action);
                        // Could send back to agent for guidance
                      }}
                      loading={msg.preview.loading}
                    />
                  </>
                ) : (
                  <>
                    <div className="preview-header">
                      <h3>{msg.preview.title}</h3>
                      <p>{msg.preview.description}</p>
                    </div>
                    
                    <div className="preview-content">
                      {msg.preview.generatedCode ? (
                        <iframe
                          srcDoc={msg.preview.generatedCode}
                          title="Generated Preview"
                          sandbox="allow-scripts allow-forms allow-modals"
                          className="generated-preview-iframe"
                        />
                      ) : (
                        <PreviewComponent name={msg.preview.component} />
                      )}
                    </div>
                    
                    <div className="preview-actions">
                      <button 
                        onClick={() => handlePreviewAction('approve', msg.id)}
                        className="action-approve"
                      >
                        Looks good!
                      </button>
                      <button 
                        onClick={() => handlePreviewAction('reject', msg.id)}
                        className="action-reject"
                      >
                        Try something else
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        ))}
        
        {activeMissionStreamId && (
          <div className="message message-agent">
            <MissionVisualizer
              missionId={activeMissionStreamId}
              onAction={(text) => submitMessage(text)}
            />
          </div>
        )}
        
        {isThinking && (
          <div className="message message-agent thinking">
            <div className="message-avatar">
              <img src="/Buddy.png" alt="Buddy" />
            </div>
            <div className="message-body">
              <div className="thinking-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
        </div>
      
      {/* Input */}
      <form onSubmit={handleSendMessage} className="chat-input-form">
        <button 
          type="button" 
          onClick={toggleVoiceInput}
          className={`voice-btn ${isListening ? 'listening' : ''}`}
          title={isListening ? 'Stop listening' : 'Start voice input'}
        >
          {isListening ? 'REC' : 'MIC'}
        </button>
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="How can I help?"
          disabled={isThinking}
          rows="2"
          data-testid="chat-input"
        />
        <button type="submit" disabled={isThinking || !input.trim()} data-testid="chat-send">
          {isThinking ? '...' : 'Send'}
        </button>
      </form>
      </div>
    </div>
  );
};

/**
 * Preview Component Renderer
 * Shows actual interactive UI, not code
 */
const PreviewComponent = ({ name }) => {
  const [darkMode, setDarkMode] = useState(false);
  const [clicked, setClicked] = useState(false);
  
  if (name === 'DarkModeToggle') {
    return (
      <div className={`preview-component ${darkMode ? 'dark' : 'light'}`}>
        <div className="dark-mode-demo">
          <div className="demo-header">
            <h2>Your App</h2>
            <button 
              className="toggle-btn"
              onClick={() => setDarkMode(!darkMode)}
              title="Click to toggle dark mode"
            >
              {darkMode ? 'Light' : 'Dark'}
            </button>
          </div>
          <div className="demo-content">
            <p>This is how your interface looks in {darkMode ? 'dark' : 'light'} mode.</p>
            <div className="demo-card">
              <h3>Sample Card</h3>
              <p>Click the toggle in the top right to see the theme change instantly!</p>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  if (name === 'KeyboardShortcuts') {
    const shortcuts = [
      { key: 'Enter', action: 'Send message' },
      { key: 'Shift + Enter', action: 'New line' },
      { key: 'Ctrl + B', action: 'Build' },
      { key: 'Ctrl + R', action: 'Review' }
    ];
    
    return (
      <div className="preview-component">
        <div className="keyboard-shortcuts-demo">
          <h3>Keyboard Shortcuts</h3>
          <div className="shortcuts-grid">
            {shortcuts.map((s, i) => (
              <div key={i} className="shortcut-item">
                <kbd>{s.key}</kbd>
                <span>{s.action}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }
  
  // Default component
  return (
    <div className="preview-component">
      <div className="default-preview">
        <h3>Interactive Preview</h3>
        <p>Try interacting with this component!</p>
        <button 
          className="demo-button"
          onClick={() => {
            setClicked(!clicked);
            alert('Button clicked! This is running in the preview sandbox.');
          }}
        >
          {clicked ? 'Clicked!' : 'Click Me'}
        </button>
        <p className="demo-text">
          {clicked 
            ? 'Great! You just interacted with a live component.' 
            : 'This is a sample component. In a real build, you\'d see the actual UI here.'}
        </p>
      </div>
    </div>
  );
};

export default UnifiedChat;
