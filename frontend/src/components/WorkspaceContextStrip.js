import React from 'react';
import './WorkspaceContextStrip.css';

const WorkspaceContextStrip = ({ items = [], onSelectMission }) => {
  return (
    <div className="workspace-strip">
      <div className="workspace-strip-title">Workspace Context</div>
      {items.length === 0 ? (
        <div className="workspace-strip-empty">No recent work yet</div>
      ) : (
        <div className="workspace-strip-cards">
          {items.map((item) => (
            <div key={item.mission_id} className="workspace-strip-card">
              <div className="workspace-strip-objective">
                {item.objective_description || 'Mission'}
              </div>
              <div className="workspace-strip-meta">
                <span className={`workspace-strip-status status-${item.status || 'unknown'}`}>
                  {item.status || 'unknown'}
                </span>
                <span className="workspace-strip-artifacts">
                  {(item.artifacts || []).length} artifacts
                </span>
              </div>
              <button
                className="workspace-strip-action"
                type="button"
                onClick={() => onSelectMission && onSelectMission(item.mission_id)}
              >
                Watch Mission
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default WorkspaceContextStrip;
