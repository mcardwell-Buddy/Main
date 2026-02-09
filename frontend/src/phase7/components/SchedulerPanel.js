import React, { useMemo } from 'react';

const SchedulerPanel = ({ metrics, schedulerHealth, taskIndex }) => {
  const summary = useMemo(() => {
    const counts = { pending: 0, executing: 0, completed: 0, failed: 0, deferred: 0 };
    taskIndex.forEach(task => {
      const status = (task.status || 'unknown').toLowerCase();
      if (counts[status] !== undefined) {
        counts[status] += 1;
      }
    });
    return counts;
  }, [taskIndex]);

  const latestMetrics = metrics.slice(-10).reverse();

  return (
    <div className="panel">
      <div>
        <h2>Scheduler Observatory</h2>
        <div className="panel-subtitle">Read-only view of queue + task states.</div>
        <div className="read-only-label">READ-ONLY</div>
      </div>

      <div className="panel-grid two-col">
        {Object.entries(summary).map(([key, value]) => (
          <div key={key}>
            <div className="small-text">{key.toUpperCase()}</div>
            <div>{value}</div>
          </div>
        ))}
      </div>

      {schedulerHealth && (
        <div>
          <div className="small-text">Scheduler Health Snapshot</div>
          <table className="table">
            <thead>
              <tr>
                <th>Wave</th>
                <th>Success</th>
                <th>Failed</th>
                <th>Deferred</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(schedulerHealth).map(([wave, data]) => (
                <tr key={wave}>
                  <td>{wave}</td>
                  <td>{(data.success_rate * 100).toFixed(1)}%</td>
                  <td>{data.total_failed}</td>
                  <td>{data.total_deferred}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div>
        <div className="small-text">Recent Task Activity</div>
        <table className="table">
          <thead>
            <tr>
              <th>Task</th>
              <th>Status</th>
              <th>Risk</th>
              <th>Retries</th>
            </tr>
          </thead>
          <tbody>
            {latestMetrics.map((item, idx) => (
              <tr key={`${item.task_id}-${idx}`}>
                <td>{item.task_id || 'n/a'}</td>
                <td><span className={`tag status-${item.execution_result}`}>{item.execution_result}</span></td>
                <td><span className={`tag ${item.risk_level?.toLowerCase()}`}>{item.risk_level}</span></td>
                <td>{item.retries}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SchedulerPanel;
