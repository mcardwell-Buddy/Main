import React, { useState, useEffect } from 'react';
import './Phase25Dashboards.css';

function Phase25OperationsDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchOperationsData();
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchOperationsData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchOperationsData = async () => {
    try {
      setRefreshing(true);
      const response = await fetch('http://127.0.0.1:8000/dashboards/operations');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const dashboardData = await response.json();
      setData(dashboardData);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching operations dashboard:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  if (loading) {
    return <div className="dashboard-container"><div className="loading">Loading Operations Dashboard...</div></div>;
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Operations Dashboard</h1>
        <button 
          className={`refresh-btn ${refreshing ? 'refreshing' : ''}`}
          onClick={fetchOperationsData}
          disabled={refreshing}
        >
          {refreshing ? '⟳ Refreshing...' : '⟳ Refresh'}
        </button>
      </div>

      {error && <div className="error-banner">Error: {error}</div>}

      {data && (
        <div className="dashboard-grid">
          {/* Key Metrics */}
          <div className="dashboard-card metrics">
            <h2>Real-Time Metrics</h2>
            <div className="metrics-grid">
              <div className="metric">
                <span className="label">Active Goals</span>
                <span className="value">{data.active_goals || 0}</span>
              </div>
              <div className="metric">
                <span className="label">Active Tasks</span>
                <span className="value">{data.active_tasks || 0}</span>
              </div>
              <div className="metric">
                <span className="label">Execution Mode</span>
                <span className="value mode">{data.execution_mode || 'MOCK'}</span>
              </div>
              <div className="metric">
                <span className="label">System Health</span>
                <span className={`value health-${data.system_health?.status || 'unknown'}`}>
                  {data.system_health?.status || 'Unknown'}
                </span>
              </div>
            </div>
          </div>

          {/* Recent Executions */}
          {data.recent_executions && data.recent_executions.length > 0 && (
            <div className="dashboard-card executions">
              <h2>Recent Executions</h2>
              <div className="execution-list">
                {data.recent_executions.slice(0, 5).map((exec, idx) => (
                  <div key={idx} className={`execution-item status-${exec.status}`}>
                    <span className="tool">{exec.tool_name}</span>
                    <span className="status">{exec.status}</span>
                    <span className="time">{new Date(exec.timestamp).toLocaleTimeString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Unresolved Conflicts */}
          {data.unresolved_conflicts && data.unresolved_conflicts.length > 0 && (
            <div className="dashboard-card conflicts">
              <h2>⚠️ Unresolved Conflicts</h2>
              <div className="conflict-list">
                {data.unresolved_conflicts.map((conflict, idx) => (
                  <div key={idx} className="conflict-item">
                    <span className="type">{conflict.conflict_type}</span>
                    <span className="details">{conflict.details}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Rollbacks */}
          {data.recent_rollbacks && data.recent_rollbacks.length > 0 && (
            <div className="dashboard-card rollbacks">
              <h2>📊 Recent Rollbacks</h2>
              <div className="rollback-list">
                {data.recent_rollbacks.map((rollback, idx) => (
                  <div key={idx} className="rollback-item">
                    <span className="reason">{rollback.reason}</span>
                    <span className="time">{new Date(rollback.timestamp).toLocaleTimeString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Task Distribution */}
          {data.task_distribution && (
            <div className="dashboard-card distribution">
              <h2>Task Distribution</h2>
              <div className="distribution-grid">
                {Object.entries(data.task_distribution).map(([type, count]) => (
                  <div key={type} className="dist-item">
                    <span className="label">{type}</span>
                    <span className="count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Last Updated */}
          <div className="dashboard-card timestamp">
            <p>Last updated: {new Date(data.timestamp).toLocaleString()}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Phase25OperationsDashboard;
