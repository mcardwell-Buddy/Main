import React from 'react';

const readFile = (file, onLoad) => {
  const reader = new FileReader();
  reader.onload = (event) => onLoad(event.target.result);
  reader.readAsText(file);
};

const DataSourcePanel = ({
  loadStatus,
  onMetricsLoaded,
  onWorkflowSummariesLoaded,
  onSchedulerHealthLoaded,
  onQueueStateLoaded
}) => {
  const handleFile = (event, type) => {
    const file = event.target.files?.[0];
    if (!file) return;

    readFile(file, (text) => {
      try {
        if (type === 'metrics') {
          const records = text
            .split('\n')
            .map(line => line.trim())
            .filter(Boolean)
            .map(line => JSON.parse(line));
          onMetricsLoaded(records);
        } else if (type === 'workflowSummaries') {
          onWorkflowSummariesLoaded(JSON.parse(text));
        } else if (type === 'schedulerHealth') {
          onSchedulerHealthLoaded(JSON.parse(text));
        } else if (type === 'queueState') {
          onQueueStateLoaded(JSON.parse(text));
        }
      } catch (err) {
        // ignore parsing errors
      }
    });
  };

  return (
    <div className="panel">
      <div>
        <h2>Data Sources</h2>
        <div className="panel-subtitle">Read-only inputs from logs and snapshots.</div>
      </div>

      <div className="panel-grid two-col">
        <div className="data-source">
          <div><strong>Metrics JSONL</strong></div>
          <div className="small-text">Status: {loadStatus.metrics || 'not loaded'}</div>
          <input type="file" accept=".jsonl,.txt" onChange={(e) => handleFile(e, 'metrics')} />
        </div>
        <div className="data-source">
          <div><strong>Workflow Summaries</strong></div>
          <div className="small-text">Status: {loadStatus.workflowSummaries || 'not loaded'}</div>
          <input type="file" accept=".json" onChange={(e) => handleFile(e, 'workflowSummaries')} />
        </div>
        <div className="data-source">
          <div><strong>Scheduler Health</strong></div>
          <div className="small-text">Status: {loadStatus.schedulerHealth || 'not loaded'}</div>
          <input type="file" accept=".json" onChange={(e) => handleFile(e, 'schedulerHealth')} />
        </div>
        <div className="data-source">
          <div><strong>Queue State Snapshot</strong></div>
          <div className="small-text">Status: {loadStatus.queueState || 'not loaded'}</div>
          <input type="file" accept=".json" onChange={(e) => handleFile(e, 'queueState')} />
        </div>
      </div>
    </div>
  );
};

export default DataSourcePanel;
