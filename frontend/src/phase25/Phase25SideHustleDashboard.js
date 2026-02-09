import React, { useState, useEffect } from 'react';
import './Phase25Dashboards.css';

function Phase25SideHustleDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchSideHustleData();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchSideHustleData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchSideHustleData = async () => {
    try {
      setRefreshing(true);
      const response = await fetch('http://127.0.0.1:8000/dashboards/side_hustle');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const dashboardData = await response.json();
      setData(dashboardData);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching side hustle dashboard:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  if (loading) {
    return <div className="dashboard-container"><div className="loading">Loading Side Hustle Dashboard...</div></div>;
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>💰 Side Hustle Dashboard</h1>
        <button 
          className={`refresh-btn ${refreshing ? 'refreshing' : ''}`}
          onClick={fetchSideHustleData}
          disabled={refreshing}
        >
          {refreshing ? '⟳ Refreshing...' : '⟳ Refresh'}
        </button>
      </div>

      {error && <div className="error-banner">Error: {error}</div>}

      {data && (
        <div className="dashboard-grid">
          {/* Daily Revenue Summary */}
          {data.daily_summary && (
            <div className="dashboard-card summary highlight">
              <h2>Today's Income</h2>
              <div className="summary-grid">
                <div className="summary-item">
                  <span className="label">Daily Earnings</span>
                  <span className="value large">${(data.daily_summary.daily_earnings || 0).toFixed(2)}</span>
                </div>
                <div className="summary-item">
                  <span className="label">Active Tasks</span>
                  <span className="value">{data.daily_summary.active_tasks || 0}</span>
                </div>
                <div className="summary-item">
                  <span className="label">Completed Today</span>
                  <span className="value">{data.daily_summary.completed_today || 0}</span>
                </div>
              </div>
            </div>
          )}

          {/* Revenue Potential */}
          {data.revenue_potential && (
            <div className="dashboard-card potential">
              <h2>🎯 Revenue Potential</h2>
              <div className="potential-grid">
                <div className="potential-item">
                  <span className="label">Daily Potential</span>
                  <span className="value">${(data.revenue_potential.daily || 0).toFixed(2)}</span>
                </div>
                <div className="potential-item">
                  <span className="label">Weekly Potential</span>
                  <span className="value">${(data.revenue_potential.weekly || 0).toFixed(2)}</span>
                </div>
                <div className="potential-item">
                  <span className="label">Monthly Potential</span>
                  <span className="value">${(data.revenue_potential.monthly || 0).toFixed(2)}</span>
                </div>
              </div>
            </div>
          )}

          {/* Active Opportunities */}
          {data.active_opportunities && data.active_opportunities.length > 0 && (
            <div className="dashboard-card opportunities full-width">
              <h2>🚀 Active Opportunities</h2>
              <div className="opportunity-table">
                <div className="table-header">
                  <span className="col-title">Opportunity</span>
                  <span className="col-status">Status</span>
                  <span className="col-revenue">Revenue</span>
                  <span className="col-roi">ROI</span>
                </div>
                {data.active_opportunities.slice(0, 10).map((opp, idx) => (
                  <div key={idx} className="table-row">
                    <span className="col-title">{opp.title}</span>
                    <span className={`col-status status-${opp.status}`}>{opp.status}</span>
                    <span className="col-revenue">${(opp.daily_revenue || 0).toFixed(2)}</span>
                    <span className="col-roi">{((opp.roi || 0) * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Income Streams */}
          {data.income_streams && data.income_streams.length > 0 && (
            <div className="dashboard-card streams">
              <h2>💳 Income Streams</h2>
              <div className="streams-list">
                {data.income_streams.map((stream, idx) => (
                  <div key={idx} className="stream-item">
                    <span className="name">{stream.name}</span>
                    <span className="earnings">${(stream.daily_earnings || 0).toFixed(2)}</span>
                    <span className="progress" style={{width: `${Math.min((stream.daily_earnings || 0) / 100 * 100, 100)}%`}}></span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ROI Analysis */}
          {data.opportunity_roi && (
            <div className="dashboard-card roi">
              <h2>📊 ROI Analysis</h2>
              <div className="roi-grid">
                {Object.entries(data.opportunity_roi).map(([stream, roi]) => (
                  <div key={stream} className="roi-item">
                    <span className="stream">{stream}</span>
                    <span className={`roi-value ${roi > 100 ? 'positive' : 'neutral'}`}>
                      {(roi * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Automated Tasks */}
          {data.automated_tasks && (
            <div className="dashboard-card tasks">
              <h2>⚙️ Automated Tasks</h2>
              <div className="tasks-grid">
                <div className="task-stat">
                  <span className="label">Running</span>
                  <span className="value">{data.automated_tasks.running || 0}</span>
                </div>
                <div className="task-stat">
                  <span className="label">Scheduled</span>
                  <span className="value">{data.automated_tasks.scheduled || 0}</span>
                </div>
                <div className="task-stat">
                  <span className="label">Paused</span>
                  <span className="value">{data.automated_tasks.paused || 0}</span>
                </div>
                <div className="task-stat">
                  <span className="label">Total</span>
                  <span className="value">{data.automated_tasks.total || 0}</span>
                </div>
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

export default Phase25SideHustleDashboard;
