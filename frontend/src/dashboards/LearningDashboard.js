import React, { useState, useEffect } from 'react';
import './DashboardStyles.css';

function LearningDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLearningData();
    const interval = setInterval(fetchLearningData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchLearningData = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/dashboards/learning');
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
    return <div className="dashboard-view"><div className="loading-spinner">Loading Learning...</div></div>;
  }

  return (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h1>Learning Dashboard</h1>
        <button className="refresh-btn" onClick={fetchLearningData}>⟳ Refresh</button>
      </div>

      {error && <div className="error-alert">{error}</div>}

      {data && (
        <div className="dashboard-grid">
          {/* Learning Signals */}
          {data.learning_signals && data.learning_signals.length > 0 && (
            <div className="card learning-signals-card">
              <h2>⭐ High-Confidence Learning Signals</h2>
              <div className="signals-list">
                {data.learning_signals.slice(0, 6).map((signal, idx) => (
                  <div key={idx} className="signal-item">
                    <div className="signal-header">
                      <span className="signal-type">{signal.signal_type}</span>
                      <span className="confidence-badge">{(signal.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="signal-insight">{signal.insight}</p>
                    {signal.recommended_action && (
                      <p className="signal-action">→ {signal.recommended_action}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* GHL Campaign Trends */}
          {data.ghl_campaign_trends && (
            <div className="card trends-card">
              <h2>📈 GHL Campaign Trends</h2>
              <div className="trends-display">
                {Object.entries(data.ghl_campaign_trends).map(([metric, value]) => (
                  <div key={metric} className="trend-item">
                    <span className="trend-label">{metric}</span>
                    <span className="trend-value">
                      {typeof value === 'number' ? value.toFixed(2) : value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Competitor Insights */}
          {data.competitor_insights && data.competitor_insights.length > 0 && (
            <div className="card insights-card">
              <h2>🔍 Competitor Insights</h2>
              <div className="insights-list">
                {data.competitor_insights.slice(0, 5).map((insight, idx) => (
                  <div key={idx} className="insight-item">
                    <div className="insight-header">
                      <span className="company">{insight.company}</span>
                      <span className="confidence">{(insight.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="finding">{insight.finding}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Lead Enrichment Status */}
          {data.lead_enrichment_status && (
            <div className="card enrichment-card">
              <h2>👥 Lead Enrichment Status</h2>
              <div className="enrichment-metrics">
                <div className="enrichment-item">
                  <span className="label">Total Processed</span>
                  <span className="value">{data.lead_enrichment_status.total_processed || 0}</span>
                </div>
                <div className="enrichment-item">
                  <span className="label">Success Rate</span>
                  <span className="value">
                    {((data.lead_enrichment_status.success_rate || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="enrichment-item">
                  <span className="label">Fields Enhanced</span>
                  <span className="value">{data.lead_enrichment_status.fields_enhanced || 0}</span>
                </div>
              </div>
            </div>
          )}

          {/* Market Opportunities */}
          {data.market_opportunities && data.market_opportunities.length > 0 && (
            <div className="card opportunities-card">
              <h2>💡 Market Opportunities</h2>
              <div className="opportunities-list">
                {data.market_opportunities.slice(0, 5).map((opp, idx) => (
                  <div key={idx} className="opportunity-item">
                    <div className="opp-header">
                      <span className="opp-title">{opp.title}</span>
                      <span className="conf">{(opp.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <span className="opp-revenue">${(opp.potential_revenue || 0).toFixed(0)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Success Metrics */}
          {data.success_metrics && (
            <div className="card metrics-card">
              <h2>📊 Success Metrics</h2>
              <div className="metrics-display">
                {Object.entries(data.success_metrics).map(([metric, value]) => (
                  <div key={metric} className="metric-item">
                    <span className="metric-label">{metric}</span>
                    <span className="metric-value">
                      {typeof value === 'number' ? value.toFixed(2) : value}
                    </span>
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

export default LearningDashboard;
