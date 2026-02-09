import React, { useState, useEffect } from 'react';
import './Phase25Dashboards.css';

function Phase25LearningDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchLearningData();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchLearningData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchLearningData = async () => {
    try {
      setRefreshing(true);
      const response = await fetch('http://127.0.0.1:8000/dashboards/learning');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const dashboardData = await response.json();
      setData(dashboardData);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching learning dashboard:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  if (loading) {
    return <div className="dashboard-container"><div className="loading">Loading Learning Dashboard...</div></div>;
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Learning Dashboard</h1>
        <button 
          className={`refresh-btn ${refreshing ? 'refreshing' : ''}`}
          onClick={fetchLearningData}
          disabled={refreshing}
        >
          {refreshing ? '⟳ Refreshing...' : '⟳ Refresh'}
        </button>
      </div>

      {error && <div className="error-banner">Error: {error}</div>}

      {data && (
        <div className="dashboard-grid">
          {/* Competitor Insights */}
          {data.competitor_insights && data.competitor_insights.length > 0 && (
            <div className="dashboard-card insights">
              <h2>🔍 Competitor Insights</h2>
              <div className="insights-list">
                {data.competitor_insights.slice(0, 5).map((insight, idx) => (
                  <div key={idx} className="insight-item">
                    <span className="company">{insight.company}</span>
                    <span className="finding">{insight.finding}</span>
                    <span className="confidence">{(insight.confidence * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* GHL Campaign Trends */}
          {data.ghl_campaign_trends && (
            <div className="dashboard-card trends">
              <h2>📈 GHL Campaign Trends</h2>
              <div className="trends-grid">
                {Object.entries(data.ghl_campaign_trends).map(([metric, value]) => (
                  <div key={metric} className="trend-item">
                    <span className="label">{metric}</span>
                    <span className="value">{typeof value === 'number' ? value.toFixed(2) : value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Lead Enrichment Status */}
          {data.lead_enrichment_status && (
            <div className="dashboard-card enrichment">
              <h2>👥 Lead Enrichment</h2>
              <div className="enrichment-grid">
                <div className="stat">
                  <span className="label">Total Processed</span>
                  <span className="value">{data.lead_enrichment_status.total_processed || 0}</span>
                </div>
                <div className="stat">
                  <span className="label">Success Rate</span>
                  <span className="value">{((data.lead_enrichment_status.success_rate || 0) * 100).toFixed(1)}%</span>
                </div>
                <div className="stat">
                  <span className="label">Fields Enhanced</span>
                  <span className="value">{data.lead_enrichment_status.fields_enhanced || 0}</span>
                </div>
              </div>
            </div>
          )}

          {/* Market Opportunities */}
          {data.market_opportunities && data.market_opportunities.length > 0 && (
            <div className="dashboard-card opportunities">
              <h2>💡 Market Opportunities</h2>
              <div className="opportunity-list">
                {data.market_opportunities.slice(0, 5).map((opp, idx) => (
                  <div key={idx} className="opportunity-item">
                    <span className="title">{opp.title}</span>
                    <span className="potential">${opp.potential_revenue || 0}</span>
                    <span className="confidence">{(opp.confidence * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* High Confidence Learning Signals */}
          {data.learning_signals && data.learning_signals.length > 0 && (
            <div className="dashboard-card signals">
              <h2>⭐ Learning Signals (80%+ Confidence)</h2>
              <div className="signal-list">
                {data.learning_signals.slice(0, 5).map((signal, idx) => (
                  <div key={idx} className="signal-item">
                    <span className="type">{signal.signal_type}</span>
                    <span className="insight">{signal.insight}</span>
                    <span className="confidence">{(signal.confidence * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Success Metrics */}
          {data.success_metrics && (
            <div className="dashboard-card metrics">
              <h2>📊 Success Metrics</h2>
              <div className="metrics-grid">
                {Object.entries(data.success_metrics).map(([metric, value]) => (
                  <div key={metric} className="metric">
                    <span className="label">{metric}</span>
                    <span className="value">{typeof value === 'number' ? value.toFixed(2) : value}</span>
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

export default Phase25LearningDashboard;
