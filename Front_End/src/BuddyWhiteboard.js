import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './BuddyWhiteboard.css';
import SystemMonitor from './components/SystemMonitor';

function BuddyWhiteboard() {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState('health-monitor'); // Default section
  const [days, setDays] = useState(90);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [metricsData, setMetricsData] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [testResults, setTestResults] = useState(null);
  const [testLoading, setTestLoading] = useState(false);
  const [expandedCompanies, setExpandedCompanies] = useState({});

  const toggleCompany = (company) => {
    setExpandedCompanies(prev => ({
      ...prev,
      [company]: !prev[company]
    }));
  };

  useEffect(() => {
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
    
    fetchMetrics();
  }, [days]);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch('/api/analytics/all');
        if (!response.ok) {
          throw new Error(`Failed to fetch analytics: ${response.status}`);
        }
        const data = await response.json();
        setAnalyticsData(data);
      } catch (err) {
        console.error('Error fetching analytics:', err);
      }
    };
    
    fetchAnalytics();
    
    // Auto-refresh analytics every 5 seconds for Live Agents section
    const interval = setInterval(fetchAnalytics, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleBackToChat = () => {
    navigate('/');
  };

  const runTest = async () => {
    try {
      setTestLoading(true);
      setTestResults(null);
      const response = await fetch('/system/test-flow');
      if (!response.ok) throw new Error('Test failed');
      const data = await response.json();
      setTestResults(data);
      setTestLoading(false);
    } catch (error) {
      console.error('Error running test:', error);
      setTestResults({ error: error.message });
      setTestLoading(false);
    }
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
      {/* Top Bar */}
      <header className="whiteboard-header">
        <h1 className="whiteboard-title">System Monitor</h1>
        <button className="back-button" onClick={handleBackToChat}>
          ← Back to Chat
        </button>
      </header>

      {/* Main Layout: Sidebar + Content */}
      <div className="whiteboard-layout">
        {/* Left Sidebar */}
        <aside className="whiteboard-sidebar">
          <img 
            src="/Buddy.png" 
            alt="System Monitor" 
            className="buddy-avatar-image"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextElementSibling.style.display = 'flex';
            }}
          />
          <div className="avatar-circle-fallback" style={{display: 'none'}}>
            <span className="avatar-text">B</span>
          </div>

          {/* Navigation Menu */}
          <nav className="whiteboard-nav">
            <button 
              className={`nav-item ${activeSection === 'health-monitor' ? 'active' : ''}`}
              onClick={() => setActiveSection('health-monitor')}
            >
              Health Monitor
            </button>
            <button 
              className={`nav-item ${activeSection === 'live-agents' ? 'active' : ''}`}
              onClick={() => setActiveSection('live-agents')}
            >
              Live Agents
            </button>
            <button 
              className={`nav-item ${activeSection === 'api-usage' ? 'active' : ''}`}
              onClick={() => setActiveSection('api-usage')}
            >
              API Usage & Costing
            </button>
            <button 
              className={`nav-item ${activeSection === 'system-learning' ? 'active' : ''}`}
              onClick={() => setActiveSection('system-learning')}
            >
              System Learning
            </button>
            <button 
              className={`nav-item ${activeSection === 'artifacts' ? 'active' : ''}`}
              onClick={() => setActiveSection('artifacts')}
            >
              Artifacts
            </button>
            <button 
              className={`nav-item ${activeSection === 'function-test' ? 'active' : ''}`}
              onClick={() => setActiveSection('function-test')}
            >
              Function Test
            </button>
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="whiteboard-main">
          {error && (
            <div className="error-banner">
              Error: {error}
            </div>
          )}

          {loading && !metricsData ? (
            <div className="content-loading">Loading...</div>
          ) : (
            <>
              {/* Health Monitor Section */}
              {activeSection === 'health-monitor' && (
                <SystemMonitor skipRefreshButton={true} />
              )}

              {/* Live Agents Section */}
              {activeSection === 'live-agents' && analyticsData && (
                <section className="panel live-agents-panel">
                  <h2>Live Agents</h2>
                  <p className="section-description">Real-time agent status, predictive capacity, and task execution pipeline</p>
                  
                  <div className="agents-grid">
                    {/* Agents Card */}
                    <div className="analytics-card">
                      <h3>👤 Agents</h3>
                      {analyticsData.agents && analyticsData.agents.agents && analyticsData.agents.agents.length > 0 ? (
                        <div className="agents-list">
                          {analyticsData.agents.agents.map((agent) => (
                            <div key={agent.agent_id} className="agent-item">
                              <div className="agent-info">
                                <div className="agent-name">{agent.agent_id}</div>
                                <div className="agent-stats">
                                  <span>Tasks: {agent.tasks_completed_today}</span>
                                  <span>Response: {agent.avg_response_time.toFixed(2)}s</span>
                                  <span>Rate: {(agent.success_rate * 100).toFixed(1)}%</span>
                                </div>
                              </div>
                              <div className={`agent-status ${agent.status.toLowerCase()}`}>
                                {agent.status}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="empty-state">No agents connected</div>
                      )}
                    </div>

                    {/* Predictive Capacity Card */}
                    <div className="analytics-card">
                      <h3>📊 Predictive Capacity</h3>
                      {analyticsData.capacity && analyticsData.capacity.forecasts && analyticsData.capacity.forecasts.length > 0 ? (
                        <div className="capacity-list">
                          {analyticsData.capacity.forecasts.map((forecast) => (
                            <div key={forecast.agent_id} className="capacity-item">
                              <div className="capacity-label">
                                <span>{forecast.agent_id}</span>
                                <span>{forecast.estimated_available_capacity}%</span>
                              </div>
                              <div className="capacity-bar">
                                <div 
                                  className="capacity-fill" 
                                  style={{width: `${forecast.estimated_available_capacity}%`}}
                                >
                                  {forecast.estimated_available_capacity}%
                                </div>
                              </div>
                              {forecast.bottleneck_tools && forecast.bottleneck_tools.length > 0 && (
                                <div className="bottleneck-warning">
                                  ⚠️ Bottlenecks: {forecast.bottleneck_tools.join(', ')}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="empty-state">No capacity data</div>
                      )}
                    </div>

                    {/* Task Pipeline Card */}
                    <div className="analytics-card">
                      <h3>📈 Task Pipeline (24h)</h3>
                      {analyticsData.pipeline && analyticsData.pipeline.last_24_hours ? (
                        <div className="pipeline-stats">
                          <div className="stat-row">
                            <div className="stat-box">
                              <div className="stat-value">{analyticsData.pipeline.last_24_hours.total_tasks}</div>
                              <div className="stat-label">Total Tasks</div>
                            </div>
                            <div className="stat-box">
                              <div className="stat-value">{(analyticsData.pipeline.last_24_hours.success_rate * 100).toFixed(1)}%</div>
                              <div className="stat-label">Success Rate</div>
                            </div>
                          </div>
                          <div className="pipeline-breakdown">
                            <div className="breakdown-item success">
                              <span className="breakdown-label">Successful</span>
                              <span className="breakdown-value">{analyticsData.pipeline.last_24_hours.successful_tasks}</span>
                            </div>
                            <div className="breakdown-item failed">
                              <span className="breakdown-label">Failed</span>
                              <span className="breakdown-value">{analyticsData.pipeline.last_24_hours.failed_tasks}</span>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="empty-state">No pipeline data</div>
                      )}
                    </div>
                  </div>
                </section>
              )}

              {/* API Usage & Costing & Costing Section */}
              {activeSection === 'api-usage' && (
                <section className="panel api-usage-panel">
                  <div className="section-header">
                    <h2>API Usage & Costing</h2>
                    <div className="date-range-selector-inline">
                      <label htmlFor="days-select">Time Range:</label>
                      <select 
                        id="days-select"
                        value={days} 
                        onChange={(e) => setDays(parseInt(e.target.value))}
                        className="days-dropdown-inline"
                      >
                        <option value={7}>Last 7 Days</option>
                        <option value={30}>Last 30 Days</option>
                        <option value={90}>Last 90 Days</option>
                        <option value={180}>Last 6 Months</option>
                        <option value={365}>Last 12 Months</option>
                      </select>
                    </div>
                  </div>
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
                      {metricsData.api_usage.by_endpoint && metricsData.api_usage.by_endpoint.length > 0 ? (
                        <div className="endpoint-breakdown">
                          <h3>Internal Endpoint Traffic Breakdown</h3>
                          <table className="data-table">
                            <thead>
                              <tr>
                                <th>Endpoint</th>
                                <th>Requests</th>
                                <th>Avg Latency</th>
                                <th>Methods</th>
                              </tr>
                            </thead>
                            <tbody>
                              {metricsData.api_usage.by_endpoint
                                .slice(0, 20)
                                .map((endpoint) => (
                                  <tr key={endpoint.path} className={endpoint.count > 100 ? 'high-traffic' : ''}>
                                    <td className="endpoint-path">{endpoint.path}</td>
                                    <td className="request-count">{endpoint.count}</td>
                                    <td>{parseFloat(endpoint.avg_latency_ms || 0).toFixed(2)}ms</td>
                                    <td className="methods-list">{Object.keys(endpoint.methods).join(', ')}</td>
                                  </tr>
                                ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="no-data">No endpoint data available</p>
                      )}

                      {/* API Usage Summary */}
                      {analyticsData && analyticsData.costs && analyticsData.costs.api_usage && (
                        <div className="api-usage-summary">
                          <h3 style={{marginTop: '2rem'}}>Internal & External Usage Summary</h3>
                          <div className="stats-row">
                            <div className="stat-box">
                              <div className="stat-value">{analyticsData.costs.api_usage.total_tasks_24h}</div>
                              <div className="stat-label">Total Tasks (24h)</div>
                            </div>
                            <div className="stat-box">
                              <div className="stat-value">{analyticsData.costs.api_usage.total_tokens_24h.toLocaleString()}</div>
                              <div className="stat-label">Total Tokens (24h)</div>
                            </div>
                            <div className="stat-box">
                              <div className="stat-value">{analyticsData.costs.api_usage.api_calls_24h}</div>
                              <div className="stat-label">API Calls (24h)</div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Cost Summary */}
                      {analyticsData && analyticsData.costs && analyticsData.costs.costing && (
                        <div className="cost-summary">
                          <h3 style={{marginTop: '2rem'}}>Cost Summary</h3>
                          <div className="stats-row">
                            <div className="stat-box">
                              <div className="stat-value">${analyticsData.costs.costing.execution_costs_24h.toFixed(4)}</div>
                              <div className="stat-label">Execution Costs (24h)</div>
                            </div>
                            <div className="stat-box">
                              <div className="stat-value">${analyticsData.costs.costing.storage_costs_daily.toFixed(6)}</div>
                              <div className="stat-label">Storage/Day</div>
                            </div>
                            <div className="stat-box">
                              <div className="stat-value">${analyticsData.costs.costing.total_daily_cost.toFixed(4)}</div>
                              <div className="stat-label">Total Daily Cost</div>
                            </div>
                          </div>
                        </div>
                      )}

                      {metricsData && metricsData.external_api_usage && metricsData.external_api_usage.by_company && metricsData.external_api_usage.by_company.length > 0 ? (
                        <>
                          <h3 style={{marginTop: '2rem'}}>External API Usage by Company</h3>
                          <div className="stats-row">
                            <div className="stat-box">
                              <div className="stat-value">{metricsData.external_api_usage.total_calls || 0}</div>
                              <div className="stat-label">Total External Calls</div>
                            </div>
                            <div className="stat-box">
                              <div className="stat-value">{parseFloat(metricsData.external_api_usage.avg_latency_ms || 0).toFixed(0)}ms</div>
                              <div className="stat-label">Avg Latency</div>
                            </div>
                          </div>
                          <div className="companies-accordion">
                            {metricsData.external_api_usage.by_company.map((company) => (
                              <div key={company.company} className="company-card">
                                <div 
                                  className="company-header"
                                  onClick={() => toggleCompany(company.company)}
                                >
                                  <div className="company-name">
                                    <span className="toggle-icon">{expandedCompanies[company.company] ? '▼' : '▶'}</span>
                                    <strong>{company.company}</strong>
                                  </div>
                                  <div className="company-stats">
                                    <span className="stat">{company.total_calls} calls</span>
                                    <span className="stat">{parseFloat(company.avg_latency_ms).toFixed(2)}ms</span>
                                    {company.total_cost > 0 && <span className="stat cost">${parseFloat(company.total_cost).toFixed(4)}</span>}
                                  </div>
                                </div>
                                {expandedCompanies[company.company] && (
                                  <div className="request-types-container">
                                    <table className="request-types-table">
                                      <thead>
                                        <tr>
                                          <th>Request Type</th>
                                          <th>Count</th>
                                          <th>Avg Latency</th>
                                          <th>Cost</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {company.request_types.map((req) => (
                                          <tr key={req.type}>
                                            <td className="req-type">{req.type}</td>
                                            <td className="req-count">{req.count}</td>
                                            <td className="req-latency">{parseFloat(req.avg_latency_ms).toFixed(2)}ms</td>
                                            <td className="req-cost">{req.cost > 0 ? `$${parseFloat(req.cost).toFixed(4)}` : '—'}</td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </>
                      ) : null}
                    </>
                  ) : (
                    <p className="no-data">No API usage data</p>
                  )}
                </section>
              )}

              {/* System Learning Section */}
              {activeSection === 'system-learning' && (
                <section className="panel system-learning-panel">
                  <h2>System Learning</h2>
                  <p className="section-description">Tool confidence distribution and learning profiles</p>

                  {/* Tool Confidence Distribution */}
                  {analyticsData && analyticsData.learning && analyticsData.learning.confidence_distribution && (
                    <div className="confidence-distribution">
                      <h3>Tool Confidence Distribution</h3>
                      <div className="stats-row">
                        <div className="stat-box">
                          <div className="stat-value">{analyticsData.learning.confidence_distribution.high_confidence}</div>
                          <div className="stat-label">High Confidence</div>
                        </div>
                        <div className="stat-box">
                          <div className="stat-value">{analyticsData.learning.confidence_distribution.medium_confidence}</div>
                          <div className="stat-label">Medium Confidence</div>
                        </div>
                        <div className="stat-box warning">
                          <div className="stat-value">{analyticsData.learning.confidence_distribution.low_confidence}</div>
                          <div className="stat-label">Low Confidence ⚠️</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tool Profiles */}
                  {analyticsData && analyticsData.learning && analyticsData.learning.tool_profiles && analyticsData.learning.tool_profiles.length > 0 && (
                    <div className="tool-profiles">
                      <h3>Tool Profiles</h3>
                      <div className="tools-grid">
                        {analyticsData.learning.tool_profiles.slice(0, 12).map((tool) => (
                          <div key={tool.tool_name} className="tool-profile-item">
                            <div className="tool-name">{tool.tool_name}</div>
                            <div className="tool-stats">
                              <span>{tool.total_executions} exec</span>
                              <span>{(tool.success_rate * 100).toFixed(0)}%</span>
                            </div>
                            <div className={`confidence-badge confidence-${tool.confidence_level.toLowerCase()}`}>
                              {tool.confidence_level}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {(!analyticsData || !analyticsData.learning) && (
                    <div className="empty-state">Loading learning data...</div>
                  )}

                  <p className="section-description" style={{marginTop: '2rem'}}>
                    Tool confidence is calculated based on execution success rates and selection frequency.
                  </p>

                  <div className="tools-grid">
                    {/* Web Tools - Vision & Arms */}
                    <div className="tool-category">
                      <h3 className="category-title">🌐 Web Tools (Vision & Arms)</h3>
                      <p className="category-desc">Browse, inspect, and interact with websites</p>
                      <div className="tools-list">
                        <div className="tool-item low-risk">
                          <span className="tool-name">web_inspect</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">Inspect DOM structure</span>
                        </div>
                        <div className="tool-item low-risk">
                          <span className="tool-name">web_screenshot</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">Capture page screenshot</span>
                        </div>
                        <div className="tool-item low-risk">
                          <span className="tool-name">web_extract</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">Extract page content</span>
                        </div>
                        <div className="tool-item low-risk">
                          <span className="tool-name">web_navigate</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">Navigate to URL</span>
                        </div>
                        <div className="tool-item medium-risk">
                          <span className="tool-name">web_click</span>
                          <span className="tool-risk">MEDIUM</span>
                          <span className="tool-desc">Click element</span>
                        </div>
                        <div className="tool-item medium-risk">
                          <span className="tool-name">web_fill</span>
                          <span className="tool-risk">MEDIUM</span>
                          <span className="tool-desc">Fill form field</span>
                        </div>
                        <div className="tool-item high-risk">
                          <span className="tool-name">web_submit_form</span>
                          <span className="tool-risk">HIGH</span>
                          <span className="tool-desc">Submit form</span>
                        </div>
                        <div className="tool-item neutral">
                          <span className="tool-name">web_browser_start</span>
                          <span className="tool-risk">—</span>
                          <span className="tool-desc">Start session</span>
                        </div>
                        <div className="tool-item neutral">
                          <span className="tool-name">web_browser_stop</span>
                          <span className="tool-risk">—</span>
                          <span className="tool-desc">Stop session</span>
                        </div>
                      </div>
                    </div>

                    {/* Research & Analysis Tools */}
                    <div className="tool-category">
                      <h3 className="category-title">🔍 Research & Analysis</h3>
                      <p className="category-desc">Search, analyze, and reflect on information</p>
                      <div className="tools-list">
                        <div className="tool-item low-risk">
                          <span className="tool-name">web_search</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">Search the web</span>
                        </div>
                        <div className="tool-item low-risk">
                          <span className="tool-name">web_research</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">Multi-step research</span>
                        </div>
                        <div className="tool-item low-risk">
                          <span className="tool-name">reflect</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">Reflect & improve</span>
                        </div>
                      </div>
                    </div>

                    {/* Code & Repository Tools */}
                    <div className="tool-category">
                      <h3 className="category-title">📝 Code Tools</h3>
                      <p className="category-desc">Analyze and understand codebases</p>
                      <div className="tools-list">
                        <div className="tool-item low-risk">
                          <span className="tool-name">repo_index</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">Repository structure</span>
                        </div>
                        <div className="tool-item low-risk">
                          <span className="tool-name">file_summary</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">File analysis</span>
                        </div>
                        <div className="tool-item low-risk">
                          <span className="tool-name">dependency_map</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">Module dependencies</span>
                        </div>
                      </div>
                    </div>

                    {/* System & Utility Tools */}
                    <div className="tool-category">
                      <h3 className="category-title">⚙️ Utilities</h3>
                      <p className="category-desc">System and general utilities</p>
                      <div className="tools-list">
                        <div className="tool-item neutral">
                          <span className="tool-name">calculate</span>
                          <span className="tool-risk">—</span>
                          <span className="tool-desc">Math expressions</span>
                        </div>
                        <div className="tool-item neutral">
                          <span className="tool-name">read_file</span>
                          <span className="tool-risk">—</span>
                          <span className="tool-desc">Read files</span>
                        </div>
                        <div className="tool-item neutral">
                          <span className="tool-name">list_directory</span>
                          <span className="tool-risk">—</span>
                          <span className="tool-desc">List folders</span>
                        </div>
                        <div className="tool-item neutral">
                          <span className="tool-name">get_time</span>
                          <span className="tool-risk">—</span>
                          <span className="tool-desc">Current time</span>
                        </div>
                      </div>
                    </div>

                    {/* Self-Knowledge Tools */}
                    <div className="tool-category">
                      <h3 className="category-title">🧠 Self-Knowledge</h3>
                      <p className="category-desc">Introspection and learning</p>
                      <div className="tools-list">
                        <div className="tool-item low-risk">
                          <span className="tool-name">learning_query</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">Check knowledge</span>
                        </div>
                        <div className="tool-item low-risk">
                          <span className="tool-name">understanding_metrics</span>
                          <span className="tool-risk">LOW</span>
                          <span className="tool-desc">Confidence metrics</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="tools-legend">
                    <div className="legend-item">
                      <span className="risk-badge low-risk">LOW</span> Read-only, safe operations
                    </div>
                    <div className="legend-item">
                      <span className="risk-badge medium-risk">MEDIUM</span> Modifies state, reversible
                    </div>
                    <div className="legend-item">
                      <span className="risk-badge high-risk">HIGH</span> Permanent actions, dry-run by default
                    </div>
                  </div>
                </section>
              )}

              {/* Artifacts Section */}
              {activeSection === 'artifacts' && metricsData && (
                <section className="panel artifacts-panel">
                  <h2>Artifacts</h2>
                  <p className="section-description">Tracks saved outputs: documents, code, files, and creative works generated by Buddy</p>
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
              )}

              {/* Function Test Section */}
              {activeSection === 'function-test' && (
                <section className="panel function-test-panel">
                  <h2>Function Test</h2>
                  <div className="test-info">
                    <p className="info-description">
                      The Function Test runs a complete end-to-end integration test of Buddy's core systems. 
                      This includes testing workflows, API integrations, and system interactions.
                    </p>
                    <p className="info-description">
                      <strong>Note:</strong> Tests consume API resources and compute cycles, so they are run on-demand only. 
                      Click the button below to execute a test and see the results.
                    </p>
                  </div>
                  
                  <button 
                    className="test-action-button"
                    onClick={runTest}
                    disabled={testLoading}
                  >
                    {testLoading ? '⏱ Running test...' : '▶ Run Test Now'}
                  </button>
                  
                  <div className="test-results-area">
                    {testResults && (
                      <div className="test-results">
                        {testResults.error ? (
                          <div className="test-error">
                            <p>Error: {testResults.error}</p>
                          </div>
                        ) : (
                          <>
                            <div className="test-header">
                              <h3>{testResults.test_message || 'Test Results'}</h3>
                              <p className="test-timestamp">{testResults.timestamp ? new Date(testResults.timestamp).toLocaleString() : ''}</p>
                            </div>
                            
                            {testResults.summary && (
                              <div className="test-summary">
                                <div className="summary-item passed">
                                  <span className="summary-label">Passed:</span>
                                  <span className="summary-value">{testResults.summary.passed || 0}</span>
                                </div>
                                <div className="summary-item failed">
                                  <span className="summary-label">Failed:</span>
                                  <span className="summary-value">{testResults.summary.failed || 0}</span>
                                </div>
                                <div className="summary-item rate">
                                  <span className="summary-label">Success Rate:</span>
                                  <span className="summary-value">{testResults.summary.success_rate || '0'}%</span>
                                </div>
                              </div>
                            )}
                            
                            {testResults.steps && testResults.steps.length > 0 && (
                              <div className="test-steps">
                                <h4>Test Steps</h4>
                                <ul className="steps-list">
                                  {testResults.steps.map((step, index) => (
                                    <li key={index} className={`step ${step.status || 'unknown'}`}>
                                      <span className="step-icon">
                                        {step.status === 'passed' ? '✓' : step.status === 'failed' ? '✗' : '○'}
                                      </span>
                                      <div className="step-content">
                                        <span className="step-name">{step.name || `Step ${index + 1}`}</span>
                                        {step.detail && <span className="step-detail">{step.detail}</span>}
                                      </div>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </section>
              )}
            </>
          )}
        </main>
      </div>

      <footer className="whiteboard-footer">
        <small>Data from Buddy's core systems</small>
      </footer>
    </div>
  );
}

export default BuddyWhiteboard;

