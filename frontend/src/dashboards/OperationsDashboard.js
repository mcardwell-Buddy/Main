import React, { useState, useEffect } from 'react';
import './DashboardStyles.css';

function OperationsDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [executionMode, setExecutionMode] = useState('LIVE');

  useEffect(() => {
    fetchOperationsData();
    const interval = setInterval(fetchOperationsData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchOperationsData = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/dashboards/operations');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const dashboardData = await response.json();
      setData(dashboardData);
      setExecutionMode(dashboardData.execution_mode || 'LIVE');
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="dashboard-view"><div className="loading-spinner">Loading Operations...</div></div>;
  }

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Operations Dashboard</h1>
          <span className={`execution-mode-badge ${executionMode.toLowerCase()}`}>
            {executionMode}
          </span>
        </div>
        <button className="refresh-btn" onClick={fetchOperationsData}>⟳ Refresh</button>
      </div>

      {error && <div className="error-alert">{error}</div>}

      {data && (
        <div className="dashboard-grid">
          {/* Real-time Metrics */}
          <div className="card metrics-card">
            <h2>Real-Time Metrics</h2>
            <div className="metrics-display">
              <div className="metric-item">
                <span className="metric-label">Active Goals</span>
                <span className="metric-value">{data.active_goals || 0}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Active Tasks</span>
                <span className="metric-value">{data.active_tasks || 0}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">System Health</span>
                <span className={`metric-value health-${(data.system_health?.status || 'unknown').toLowerCase()}`}>
                  {data.system_health?.health_assessment || 'Unknown'}
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Health Score</span>
                <span className="metric-value">{data.system_health?.health_score || 0}/100</span>
              </div>
            </div>
          </div>

          {/* System Health Details */}
          {data.system_health && (
            <div className="card health-card">
              <h2>System Health Details</h2>
              <div className="health-metrics">
                <div className="health-row">
                  <span>Tool Success Rate</span>
                  <span className="metric-badge">{(data.system_health.metrics?.tool_success_rate || 0).toFixed(1)}%</span>
                </div>
                <div className="health-row">
                  <span>Execution Latency</span>
                  <span className="metric-badge">{(data.system_health.metrics?.execution_latency_ms || 0).toFixed(0)}ms</span>
                </div>
                <div className="health-row">
                  <span>Rollback Frequency</span>
                  <span className="metric-badge">{(data.system_health.metrics?.rollback_frequency || 0).toFixed(2)}</span>
                </div>
                <div className="health-row">
                  <span>Conflict Rate</span>
                  <span className="metric-badge">{(data.system_health.metrics?.conflict_rate || 0).toFixed(2)}</span>
                </div>
              </div>
            </div>
          )}

          {/* Recent Executions */}
          {data.recent_executions && data.recent_executions.length > 0 && (
            <div className="card executions-card">
              <h2>Recent Executions</h2>
              <div className="execution-list">
                {data.recent_executions.slice(0, 8).map((exec, idx) => (
                  <div key={idx} className={`execution-row status-${(exec.status || 'pending').toLowerCase()}`}>
                    <span className="exec-tool">{exec.tool_name || 'Unknown'}</span>
                    <span className="exec-status">{exec.status}</span>
                    <span className="exec-time">{new Date(exec.timestamp).toLocaleTimeString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Unresolved Conflicts */}
          {data.unresolved_conflicts && data.unresolved_conflicts.length > 0 && (
            <div className="card conflicts-card alert">
              <h2>⚠️ Unresolved Conflicts</h2>
              <div className="conflicts-list">
                {data.unresolved_conflicts.map((conflict, idx) => (
                  <div key={idx} className="conflict-item">
                    <span className="conflict-type">{conflict.conflict_type}</span>
                    <span className="conflict-details">{conflict.details}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Rollbacks */}
          {data.recent_rollbacks && data.recent_rollbacks.length > 0 && (
            <div className="card rollbacks-card">
              <h2>📊 Recent Rollbacks</h2>
              <div className="rollbacks-list">
                {data.recent_rollbacks.slice(0, 5).map((rollback, idx) => (
                  <div key={idx} className="rollback-item">
                    <span className="rollback-note">{rollback.note || rollback.reason || 'Rollback event'}</span>
                    <span className="rollback-time">{new Date(rollback.timestamp).toLocaleTimeString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Task Distribution */}
          {data.task_distribution && Object.keys(data.task_distribution).length > 0 && (
            <div className="card distribution-card">
              <h2>Task Distribution</h2>
              <div className="distribution-grid">
                {Object.entries(data.task_distribution).map(([type, count]) => (
                  <div key={type} className="dist-item">
                    <span className="dist-label">{type}</span>
                    <span className="dist-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default OperationsDashboard;
