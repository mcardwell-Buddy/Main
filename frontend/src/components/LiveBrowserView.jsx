import React, { useEffect, useRef, useState } from 'react';
import './BrowserView.css';

const LiveBrowserView = ({ streamUrl, onInteract, loading = false }) => {
  const [frame, setFrame] = useState(null);
  const [pageState, setPageState] = useState(null);
  const [clickables, setClickables] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const imgRef = useRef(null);

  useEffect(() => {
    if (!streamUrl) return;

    let reconnectTimer = null;
    let isActive = true;

    const connect = () => {
      if (!isActive) return;

      const ws = new WebSocket(streamUrl);
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (isActive) {
          reconnectTimer = setTimeout(connect, 1000);
        }
      };
      ws.onerror = () => {
        setConnected(false);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'frame') {
            setFrame(data.frame);
            setPageState(data.page_state || null);
            setClickables(data.clickables || []);
          }
        } catch (err) {
          // Ignore malformed frames
        }
      };
    };

    connect();

    return () => {
      isActive = false;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      try {
        wsRef.current?.close();
      } catch (e) {
        // ignore
      }
    };
  }, [streamUrl]);

  const handleClick = (e) => {
    if (!onInteract || !frame || !imgRef.current) return;

    const img = imgRef.current;
    const rect = img.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const scaleX = frame.width / rect.width;
    const scaleY = frame.height / rect.height;

    const clickX = Math.round(x * scaleX);
    const clickY = Math.round(y * scaleY);

    onInteract({
      action_type: 'click_at',
      x: clickX,
      y: clickY
    });
  };

  if (!frame || !frame.base64) {
    return (
      <div className="browser-view-empty">
        <div className="empty-state">
          <p>{connected ? 'Waiting for live view...' : 'Connecting to live view...'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="browser-view">
      <div className="browser-header">
        <div className="browser-controls">
          <div className="browser-url-bar">
            <span className="browser-icon">🟢</span>
            <input
              type="text"
              value={pageState?.url || 'Loading...'}
              readOnly
              className="url-input"
            />
          </div>
          <div className="browser-buttons">
            {loading && <span className="loading-indicator">⏳ Live</span>}
          </div>
        </div>
        {pageState?.title && (
          <div className="browser-title">
            <span>{pageState.title}</span>
          </div>
        )}
      </div>

      <div className="browser-viewport">
        <div className="screenshot-container">
          <img
            ref={imgRef}
            src={`data:image/png;base64,${frame.base64}`}
            alt="Live browser view"
            className="screenshot"
            onClick={handleClick}
          />
        </div>
      </div>

      <div className="browser-footer">
        <div className="footer-info">
          <span className="info-badge">Live</span>
          {pageState?.viewport && (
            <span className="info-badge">
              {pageState.viewport.width}×{pageState.viewport.height}
            </span>
          )}
          {clickables.length > 0 && (
            <span className="info-badge">
              {clickables.length} interactive elements
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default LiveBrowserView;
