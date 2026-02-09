import React, { useState, useEffect } from 'react';
import './DashboardStyles.css';

function HustleDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('opportunities');

  useEffect(() => {
    fetchHustleData();
    const interval = setInterval(fetchHustleData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchHustleData = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/dashboards/side_hustle');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const dashboardData = await response.json();
      setData(dashboardData);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="dashboard-view"><div className="loading-spinner">Loading Hustle...</div></div>;
  }

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <div className="header-left">
          <h1>💰 Hustle Dashboard</h1>
          <span className="subtitle">Revenue opportunities, marketing campaigns & lead generation</span>
        </div>
        <button className="refresh-btn" onClick={fetchHustleData}>⟳ Refresh</button>
      </div>

      {error && <div className="error-alert">{error}</div>}

      {data && (
        <div className="dashboard-grid">
          {/* Today's Income Summary */}
          {data.daily_summary && (
            <div className="card daily-summary-card highlight">
              <h2>Today's Income</h2>
              <div className="income-display">
                <div className="income-main">
                  <span className="income-label">Daily Earnings</span>
                  <span className="income-value">${(data.daily_summary.daily_earnings || 0).toFixed(2)}</span>
                </div>
                <div className="income-stats">
                  <div className="income-stat">
                    <span className="stat-label">Active Tasks</span>
                    <span className="stat-value">{data.daily_summary.active_tasks || 0}</span>
                  </div>
                  <div className="income-stat">
                    <span className="stat-label">Completed</span>
                    <span className="stat-value">{data.daily_summary.completed_today || 0}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Revenue Potential */}
          {data.revenue_potential && (
            <div className="card potential-card">
              <h2>🎯 Revenue Potential</h2>
              <div className="potential-display">
                <div className="potential-item">
                  <span className="pot-label">Daily</span>
                  <span className="pot-value">${(data.revenue_potential.daily || 0).toFixed(2)}</span>
                </div>
                <div className="potential-item">
                  <span className="pot-label">Weekly</span>
                  <span className="pot-value">${(data.revenue_potential.weekly || 0).toFixed(2)}</span>
                </div>
                <div className="potential-item">
                  <span className="pot-label">Monthly</span>
                  <span className="pot-value">${(data.revenue_potential.monthly || 0).toFixed(2)}</span>
                </div>
              </div>
            </div>
          )}

          {/* Active Opportunities */}
          {data.active_opportunities && data.active_opportunities.length > 0 && (
            <div className="card opportunities-card full-width">
              <h2>🚀 Active Opportunities</h2>
              <div className="opportunities-table">
                <div className="table-header">
                  <span className="col-title">Opportunity</span>
                  <span className="col-status">Status</span>
                  <span className="col-revenue">Daily Revenue</span>
                  <span className="col-roi">ROI</span>
                </div>
                {data.active_opportunities.slice(0, 10).map((opp, idx) => (
                  <div key={idx} className={`table-row status-${(opp.status || 'pending').toLowerCase()}`}>
                    <span className="col-title">{opp.title}</span>
                    <span className="col-status">{opp.status}</span>
                    <span className="col-revenue">${(opp.daily_revenue || 0).toFixed(2)}</span>
                    <span className="col-roi">{((opp.roi || 0) * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Income Streams */}
          {data.income_streams && data.income_streams.length > 0 && (
            <div className="card streams-card">
              <h2>💳 Income Streams</h2>
              <div className="streams-list">
                {data.income_streams.map((stream, idx) => (
                  <div key={idx} className="stream-item">
                    <span className="stream-name">{stream.name}</span>
                    <span className="stream-earnings">${(stream.daily_earnings || 0).toFixed(2)}</span>
                    <div className="stream-bar">
                      <div 
                        className="stream-progress" 
                        style={{width: `${Math.min((stream.daily_earnings || 0) / 100 * 100, 100)}%`}}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ROI Analysis */}
          {data.opportunity_roi && Object.keys(data.opportunity_roi).length > 0 && (
            <div className="card roi-card">
              <h2>📊 ROI Analysis</h2>
              <div className="roi-grid">
                {Object.entries(data.opportunity_roi).map(([stream, roi]) => (
                  <div key={stream} className="roi-item">
                    <span className="roi-stream">{stream}</span>
                    <span className={`roi-value ${roi > 1 ? 'positive' : 'neutral'}`}>
                      {(roi * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Automated Tasks */}
          {data.automated_tasks && (
            <div className="card tasks-card">
              <h2>⚙️ Automated Tasks</h2>
              <div className="tasks-grid">
                <div className="task-stat">
                  <span className="task-label">Running</span>
                  <span className="task-value">{data.automated_tasks.running || 0}</span>
                </div>
                <div className="task-stat">
                  <span className="task-label">Scheduled</span>
                  <span className="task-value">{data.automated_tasks.scheduled || 0}</span>
                </div>
                <div className="task-stat">
                  <span className="task-label">Paused</span>
                  <span className="task-value">{data.automated_tasks.paused || 0}</span>
                </div>
                <div className="task-stat">
                  <span className="task-label">Total</span>
                  <span className="task-value">{data.automated_tasks.total || 0}</span>
                </div>
              </div>
            </div>
          )}

          {/* GHL Campaigns Section */}
          <div className="card ghl-campaigns-card full-width">
            <h2>📧 GHL Marketing Campaigns</h2>
            <div className="campaigns-info">
              <p>Marketing campaign management and automation appears here.</p>
              <p className="subtitle-text">Campaigns are managed through the Operations interface with approvals.</p>
            </div>
          </div>

          {/* Lead Generation Summary */}
          <div className="card lead-gen-card">
            <h2>📍 Lead Generation</h2>
            <div className="lead-gen-stats">
              <div className="stat-box">
                <span className="stat-icon">👥</span>
                <span className="stat-label">Leads This Week</span>
                <span className="stat-number">--</span>
              </div>
              <div className="stat-box">
                <span className="stat-icon">✅</span>
                <span className="stat-label">Qualified</span>
                <span className="stat-number">--</span>
              </div>
              <div className="stat-box">
                <span className="stat-icon">📞</span>
                <span className="stat-label">Follow-ups</span>
                <span className="stat-number">--</span>
              </div>
            </div>
          </div>

          {/* Competitor Research */}
          <div className="card research-card">
            <h2>🔍 Competitor Research</h2>
            <div className="research-info">
              <p>Recent competitor insights from web scraping:</p>
              <p className="subtitle-text">Detailed competitor analysis available in the Learning dashboard.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default HustleDashboard;
