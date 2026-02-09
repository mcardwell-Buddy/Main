import React, { useMemo } from 'react';

const RecoveryView = ({ queueState, metrics }) => {
  const recovery = useMemo(() => {
    if (!queueState) return null;
    const snapshotTime = queueState.timestamp ? new Date(queueState.timestamp) : null;
    const metricsByTask = new Map();
    metrics.forEach(item => {
      if (item.task_id) {
        metricsByTask.set(item.task_id, item);
      }
    });

    const pending = queueState.tasks.filter(task => ['pending', 'deferred', 'blocked'].includes(task.status));
    const recovered = pending.filter(task => {
      const metric = metricsByTask.get(task.id);
      if (!metric) return false;
      if (!snapshotTime) return true;
      return new Date(metric.timestamp) >= snapshotTime && metric.execution_result === 'completed';
    });

    return {
      snapshotTime: queueState.timestamp,
      pending,
      recovered
    };
  }, [queueState, metrics]);

  return (
    <div className="panel">
      <div>
        <h2>Recovery & Persistence</h2>
        <div className="panel-subtitle">Queue snapshots and restored tasks.</div>
        <div className="read-only-label">READ-ONLY</div>
      </div>

      {!recovery ? (
        <div className="small-text">No queue snapshot loaded.</div>
      ) : (
        <>
          <div className="small-text">Snapshot: {recovery.snapshotTime || 'n/a'}</div>
          <div className="panel-grid two-col">
            <div>
              <div className="small-text">Pending at snapshot</div>
              <div>{recovery.pending.length}</div>
            </div>
            <div>
              <div className="small-text">Recovered (completed later)</div>
              <div>{recovery.recovered.length}</div>
            </div>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Task</th>
                <th>Status</th>
                <th>Recovered</th>
              </tr>
            </thead>
            <tbody>
              {recovery.pending.map(task => (
                <tr key={task.id}>
                  <td>{task.id}</td>
                  <td><span className={`tag status-${task.status}`}>{task.status}</span></td>
                  <td>{recovery.recovered.find(t => t.id === task.id) ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
};

export default RecoveryView;
