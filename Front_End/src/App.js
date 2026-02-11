import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';
import Login from './Login';
import UnifiedChat from './UnifiedChat';
import BuddyWhiteboard from './BuddyWhiteboard';

// eslint-disable-next-line no-undef
function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Listen to auth state changes
    // eslint-disable-next-line no-undef
    const unsubscribe = firebase.auth().onAuthStateChanged((currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        fontSize: '18px',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        Loading Buddy...
      </div>
    );
  }

  // Show login screen if not authenticated
  if (!user) {
    return <Login />;
  }

  // Show app if authenticated
  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/" element={<UnifiedChat />} />
          <Route path="/whiteboard" element={<BuddyWhiteboard />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
