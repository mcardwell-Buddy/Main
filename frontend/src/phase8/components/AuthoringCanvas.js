import React, { useRef } from 'react';

const AuthoringCanvas = ({ workflow, selectedTaskId, onSelectTask, onNodeMove, overlay }) => {
  const containerRef = useRef(null);

  const handlePointerDown = (event, node) => {
    event.preventDefault();
    const startX = event.clientX;
    const startY = event.clientY;
    const initial = node.position;

    const handleMove = (moveEvent) => {
      const dx = moveEvent.clientX - startX;
      const dy = moveEvent.clientY - startY;
      onNodeMove(node.id, { x: Math.max(0, initial.x + dx), y: Math.max(0, initial.y + dy) });
    };

    const handleUp = () => {
      window.removeEventListener('pointermove', handleMove);
      window.removeEventListener('pointerup', handleUp);
    };

    window.addEventListener('pointermove', handleMove);
    window.addEventListener('pointerup', handleUp);
  };

  return (
    <div className="authoring-canvas" ref={containerRef}>
      {workflow.nodes.map((node) => {
        const isSelected = node.id === selectedTaskId;
        const overlayInfo = overlay[node.id];
        return (
          <div
            key={node.id}
            className={`authoring-node ${isSelected ? 'selected' : ''}`}
            style={{ left: node.position.x, top: node.position.y }}
            onClick={() => onSelectTask(node.id)}
            onPointerDown={(event) => handlePointerDown(event, node)}
          >
            <div className="node-title">{node.title}</div>
            <div className="node-tags">
              <span className={`tag ${node.risk.toLowerCase()}`}>{node.risk}</span>
              <span className="tag">{node.priority}</span>
              <span className={`tag status-${overlayInfo?.status || 'pending'}`}>{overlayInfo?.status || 'pending'}</span>
            </div>
            <div className="small-text">Tool: {node.tool}</div>
            <div className="small-text">Retries: {node.retries}</div>
            <div className="small-text">Confidence: {node.confidence.toFixed(2)}</div>
            {overlayInfo?.warning && <div className="small-text">⚠ {overlayInfo.warning}</div>}
          </div>
        );
      })}
    </div>
  );
};

export default AuthoringCanvas;
