import React, { useState } from 'react';

const WorkflowSnapshotPanel = ({ snapshots, activeSnapshotId, onSave, onLoad, onImport }) => {
  const [label, setLabel] = useState('');

  const handleExport = () => {
    const payload = JSON.stringify({ snapshots }, null, 2);
    const blob = new Blob([payload], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'workflow_snapshots.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        if (data.snapshots) {
          onImport(data.snapshots);
        }
      } catch (err) {
        // ignore
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="panel snapshot-panel">
      <div>
        <h2>Workflow Snapshots</h2>
        <div className="panel-subtitle">Versioned, local-only storage.</div>
      </div>

      <div className="panel-grid">
        <input
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="Snapshot label"
        />
        <button
          className="simulation-button"
          onClick={() => {
            if (label.trim()) {
              onSave(label.trim());
              setLabel('');
            }
          }}
        >
          Save Snapshot
        </button>
        <button className="simulation-button" onClick={handleExport}>Export JSON</button>
        <input type="file" accept=".json" onChange={handleImport} />
      </div>

      <div className="snapshot-list">
        {snapshots.map(snapshot => (
          <div key={snapshot.id} className="snapshot-item">
            <div><strong>{snapshot.label}</strong></div>
            <div className="small-text">{snapshot.createdAt}</div>
            <button
              className="simulation-button"
              onClick={() => onLoad(snapshot.id)}
              title="Load snapshot (read-only)"
            >
              {snapshot.id === activeSnapshotId ? 'Active' : 'Load'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WorkflowSnapshotPanel;
