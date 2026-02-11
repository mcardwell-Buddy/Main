import React, { useState, useEffect } from 'react';
import './BrowserView.css';

/**
 * BrowserView Component
 * Displays live browser view during web learning with screenshot and interactive overlay
 * Used when agent is navigating/learning from websites
 */
export const BrowserView = ({ 
  screenshot, 
  pageState, 
  clickables = [], 
  onInteract,
  loading = false 
}) => {
  const [hoveredElement, setHoveredElement] = useState(null);
  const [showElementOverlay, setShowElementOverlay] = useState(true);

  if (!screenshot || !screenshot.base64) {
    return (
      <div className="browser-view-empty">
        <div className="empty-state">
          <p>Waiting for browser view...</p>
        </div>
      </div>
    );
  }

  const handleElementClick = (element, e) => {
    e.stopPropagation();
    
    if (onInteract) {
      onInteract({
        action_type: 'click',
        selector: element.text,
        element: element
      });
    }
  };

  const calculateElementPosition = (element, imgWidth, imgHeight) => {
    // Calculate position relative to rendered image
    const ratio = imgWidth / screenshot.width;
    return {
      left: element.x * ratio,
      top: element.y * ratio,
      width: element.width * ratio,
      height: element.height * ratio
    };
  };

  return (
    <div className="browser-view">
      <div className="browser-header">
        <div className="browser-controls">
          <div className="browser-url-bar">
            {pageState?.url && (
              <>
                <span className="browser-icon">ðŸŒ</span>
                <input 
                  type="text" 
                  value={pageState.url} 
                  readOnly 
                  className="url-input"
                />
              </>
            )}
          </div>
          <div className="browser-buttons">
            <button 
              className="toggle-overlay-btn"
              onClick={() => setShowElementOverlay(!showElementOverlay)}
              title={showElementOverlay ? "Hide element overlay" : "Show element overlay"}
            >
              {showElementOverlay ? 'ðŸ‘ï¸ Hide' : 'ðŸ‘ï¸ Show'} Elements
            </button>
            {loading && <span className="loading-indicator">â³ Loading...</span>}
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
            src={`data:image/png;base64,${screenshot.base64}`}
            alt="Current browser view"
            className="screenshot"
          />
          
          {/* Interactive element overlay */}
          {showElementOverlay && clickables.length > 0 && (
            <svg className="element-overlay">
              {clickables.map((element, idx) => {
                const isHovered = hoveredElement === idx;
                const pos = calculateElementPosition(
                  element, 
                  screenshot.width, 
                  screenshot.height
                );
                
                return (
                  <g key={`element-${idx}`}>
                    {/* Clickable rectangle */}
                    <rect
                      x={pos.left}
                      y={pos.top}
                      width={pos.width}
                      height={pos.height}
                      className={`element-rect ${isHovered ? 'hovered' : ''}`}
                      onMouseEnter={() => setHoveredElement(idx)}
                      onMouseLeave={() => setHoveredElement(null)}
                      onClick={(e) => handleElementClick(element, e)}
                    />
                    
                    {/* Label on hover */}
                    {isHovered && (
                      <>
                        <rect
                          x={pos.left}
                          y={Math.max(pos.top - 25, 0)}
                          width={Math.min(200, pos.width + 20)}
                          height="22"
                          className="label-background"
                        />
                        <text
                          x={pos.left + 5}
                          y={Math.max(pos.top - 7, 15)}
                          className="element-label"
                        >
                          {element.text.substring(0, 25)}
                        </text>
                      </>
                    )}
                  </g>
                );
              })}
            </svg>
          )}
        </div>
      </div>

      <div className="browser-footer">
        <div className="footer-info">
          {clickables.length > 0 && (
            <span className="info-badge">
              {clickables.length} interactive elements
            </span>
          )}
          {pageState?.viewport && (
            <span className="info-badge">
              {pageState.viewport.width}Ã—{pageState.viewport.height}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default BrowserView;
