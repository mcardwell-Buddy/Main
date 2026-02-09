import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';
import UnifiedChat from './UnifiedChat';
import BuddyWhiteboard from './BuddyWhiteboard';

function App() {
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
