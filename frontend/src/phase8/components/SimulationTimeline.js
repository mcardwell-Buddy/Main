import React from 'react';

const SimulationTimeline = ({ simulation, onRunSimulation, validation }) => {
  const hasErrors = validation.errors.length > 0;

  return (
    <div className="panel simulation-panel">
      <div>
        <h2>Simulation Timeline (Dry-Run)</h2>
        <div className="panel-subtitle">No execution. Timeline is simulated only.</div>
        <div className="read-only-label">DRY-RUN ONLY</div>
      </div>

      {hasErrors && (
        <div className="validation-banner error">Resolve validation errors before simulation.</div>
      )}

      <div className="simulation-controls">
        <button
          className="simulation-button"
          onClick={onRunSimulation}
          disabled={hasErrors}
          title="Dry-run simulation only. No tasks will execute."
        >
          Run Simulation
        </button>
        {simulation && (
          <span className="small-text">{simulation.summary}</span>
        )}
      </div>

      {simulation && (
        <table className="table">
          <thead>
            <tr>
              <th>Task</th>
              <th>Status</th>
              <th>Retries</th>
              <th>Branch</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {simulation.timeline.map((item, idx) => (
              <tr key={`${item.task_id}-${idx}`}>
                <td>{item.task_id}</td>
                <td><span className={`tag status-${item.execution_result}`}>{item.execution_result}</span></td>
                <td>{item.retries}</td>
                <td>{item.branch || 'n/a'}</td>
                <td>{item.confidence_score?.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default SimulationTimeline;
