import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './BuddyWhiteboard.css';

function BuddyWhiteboard() {
  const navigate = useNavigate();
  const [days, setDays] = useState(90);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [metricsData, setMetricsData] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, [days]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/whiteboard/metrics?days=${days}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.status}`);
      }

      const data = await response.json();
      setMetricsData(data);
      setLastUpdated(new Date().toLocaleTimeString());
      setLoading(false);
    } catch (err) {
      console.error('Error fetching metrics:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchMetrics();
  };

  const handleBackToChat = () => {
    navigate('/');
  };

  if (loading && !metricsData) {
    return (
      <div className="whiteboard-container">
        <div className="loading-screen">
          <div className="spinner"></div>
          <p>Loading whiteboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="whiteboard-container">
      <header className="whiteboard-header">
        <div className="header-left">
          <button className="back-button" onClick={handleBackToChat}>
            ← Back to Chat
          </button>
          <h1>📊 Buddy Whiteboard</h1>
        </div>
        <div className="header-controls">
          <select 
            className="days-select" 
            value={days} 
            onChange={(e) => setDays(parseInt(e.target.value))}
          >
            <option value={7}>7 Days</option>
            <option value={30}>30 Days</option>
            <option value={90}>90 Days</option>
            <option value={180}>180 Days</option>
            <option value={365}>1 Year</option>
          </select>
          <button 
            className="refresh-btn" 
            onClick={handleRefresh} 
            disabled={loading}
          >
            {loading ? '⟳ Refreshing...' : '⟳ Refresh'}
          </button>
          {lastUpdated && (
            <span className="last-updated">
              Updated: {lastUpdated}
            </span>
          )}
        </div>
      </header>

      {error && (
        <div className="error-banner">
          ⚠️ Error: {error}
          <button onClick={handleRefresh}>Retry</button>
        </div>
      )}

      {metricsData && (
        <main className="whiteboard-grid">
          <section className="panel api-usage-panel">
            <h2>📡 API Usage</h2>
            {metricsData.api_usage ? (
              <>
                <div className="stats-row">
                  <div className="stat-box">
                    <div className="stat-value">{metricsData.api_usage.total_requests || 0}</div>
                    <div className="stat-label">Total Requests</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-value">{parseFloat(metricsData.api_usage.avg_latency_ms || 0).toFixed(0)}ms</div>
                    <div className="stat-label">Avg Latency</div>
                  </div>
                </div>
                {metricsData.api_usage.summary && Object.keys(metricsData.api_usage.summary).length > 0 ? (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Endpoint</th>
                        <th>Count</th>
                        <th>Avg Latency</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(metricsData.api_usage.summary)
                        .sort(([,a], [,b]) => b.count - a.count)
                        .slice(0, 10)
                        .map(([path, stats]) => (
                          <tr key={path}>
                            <td className="endpoint-path">{path}</td>
                            <td>{stats.count}</td>
                            <td>{parseFloat(stats.avg_latency_ms || 0).toFixed(2)}ms</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="no-data">No API usage data available</p>
                )}
              </>
            ) : (
              <p className="no-data">No API usage data</p>
            )}
          </section>

          <section className="panel costing-panel">
            <h2>💰 Costing</h2>
            {metricsData.costing ? (
              <>
                <div className="cost-summary">
                  <div className="cost-total">
                    ${ (parseFloat(metricsData.costing.openai_cost || 0) + 
                        parseFloat(metricsData.costing.firestore_cost || 0)).toFixed(2) }
                    <span className="cost-label">Total USD</span>
                  </div>
                </div>
                <div className="cost-breakdown">
                  <div className="cost-item">
                    <span className="cost-service">🔍 SerpAPI</span>
                    <span className="cost-value">{metricsData.costing.serpapi_searches_used || 0} searches</span>
                  </div>
                  <div className="cost-item">
                    <span className="cost-service">🤖 OpenAI</span>
                    <span className="cost-value">${parseFloat(metricsData.costing.openai_cost || 0).toFixed(2)}</span>
                  </div>
                  <div className="cost-item">
                    <span className="cost-service">🔥 Firestore</span>
                    <span className="cost-value">${parseFloat(metricsData.costing.firestore_cost || 0).toFixed(2)}</span>
                  </div>
                </div>
              </>
            ) : (
              <p className="no-data">No costing data</p>
            )}
          </section>

          <section className="panel income-panel">
            <h2>💵 Income</h2>
            {metricsData.income ? (
              <div className="income-grid">
                <div className="income-card">
                  <div className="income-value">{metricsData.income.gigs_recommended || 0}</div>
                  <div className="income-label">Gigs Recommended</div>
                </div>
                <div className="income-card">
                  <div className="income-value">{metricsData.income.gigs_hired || 0}</div>
                  <div className="income-label">Gigs Hired</div>
                </div>
                <div className="income-card">
                  <div className="income-value">{metricsData.income.invoices_received || 0}</div>
                  <div className="income-label">Invoices Received</div>
                </div>
              </div>
            ) : (
              <p className="no-data">No income data</p>
            )}
          </section>

          <section className="panel tool-confidence-panel">
            <h2>🎯 Tool Confidence</h2>
            {metricsData.tool_confidence && metricsData.tool_confidence.tools && metricsData.tool_confidence.tools.length > 0 ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Tool</th>
                    <th>Confidence %</th>
                    <th>Selection %</th>
                    <th>Variation</th>
                  </tr>
                </thead>
                <tbody>
                  {metricsData.tool_confidence.tools
                    .sort((a, b) => b.confidence_pct - a.confidence_pct)
                    .slice(0, 10)
                    .map((tool, idx) => (
                      <tr key={idx}>
                        <td>{tool.tool_name}</td>
                        <td>{tool.confidence_pct.toFixed(1)}%</td>
                        <td>{tool.selection_pct.toFixed(1)}%</td>
                        <td>{tool.variation.toFixed(2)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            ) : (
              <p className="no-data">No tool confidence data</p>
            )}
          </section>

          <section className="panel response-times-panel">
            <h2>⚡ Response Times</h2>
            {metricsData.response_times ? (
              <div className="latency-stats">
                <div className="latency-card">
                  <div className="latency-value">{parseFloat(metricsData.response_times.avg_ms || 0).toFixed(0)}ms</div>
                  <div className="latency-label">Average</div>
                </div>
                <div className="latency-card">
                  <div className="latency-value">{parseFloat(metricsData.response_times.p50_ms || 0).toFixed(0)}ms</div>
                  <div className="latency-label">P50 (Median)</div>
                </div>
                <div className="latency-card">
                  <div className="latency-value">{parseFloat(metricsData.response_times.p95_ms || 0).toFixed(0)}ms</div>
                  <div className="latency-label">P95</div>
                </div>
              </div>
            ) : (
              <p className="no-data">No response time data</p>
            )}
          </section>

          <section className="panel session-stats-panel">
            <h2>💬 Session Stats</h2>
            {metricsData.session_stats ? (
              <>
                <div className="stats-row">
                  <div className="stat-box">
                    <div className="stat-value">{metricsData.session_stats.total_sessions || 0}</div>
                    <div className="stat-label">Total Sessions</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-value">{metricsData.session_stats.total_messages || 0}</div>
                    <div className="stat-label">Total Messages</div>
                  </div>
                </div>
                {metricsData.session_stats.sessions && metricsData.session_stats.sessions.length > 0 ? (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Session</th>
                        <th>Source</th>
                        <th>Sent</th>
                        <th>Received</th>
                      </tr>
                    </thead>
                    <tbody>
                      {metricsData.session_stats.sessions.slice(0, 5).map((session, idx) => (
                        <tr key={idx}>
                          <td>{session.session_id.substring(0, 8)}...</td>
                          <td>{session.source || 'web'}</td>
                          <td>{session.messages_sent}</td>
                          <td>{session.messages_received}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : null}
              </>
            ) : (
              <p className="no-data">No session data</p>
            )}
          </section>

          <section className="panel artifacts-panel">
            <h2>🎨 Artifacts</h2>
            {metricsData.artifacts && metricsData.artifacts.by_type ? (
              <>
                <div className="stat-box">
                  <div className="stat-value">{metricsData.artifacts.total || 0}</div>
                  <div className="stat-label">Total Artifacts</div>
                </div>
                <div className="artifacts-list">
                  {Object.entries(metricsData.artifacts.by_type)
                    .sort(([,a], [,b]) => b - a)
                    .map(([type, count]) => (
                      <div key={type} className="artifact-item">
                        <span className="artifact-type">{type.replace(/_/g, ' ')}</span>
                        <span className="artifact-count">{count}</span>
                      </div>
                    ))}
                </div>
              </>
            ) : (
              <p className="no-data">No artifacts data</p>
            )}
          </section>
        </main>
      )}

      <footer className="whiteboard-footer">
        <small>Data from Buddy's core systems • Auto-refreshes every 30s</small>
      </footer>
    </div>
  );
}

export default BuddyWhiteboard;

