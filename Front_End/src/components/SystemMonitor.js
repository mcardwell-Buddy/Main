import React, { useState, useEffect } from 'react';
import './SystemMonitor.css';

function SystemMonitor({ skipRefreshButton = false }) {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    // Load health status on mount only
    loadHealthStatus();
  }, []);

  const loadHealthStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/system/health');
      if (!response.ok) throw new Error(`Failed to fetch health: ${response.status}`);
      const data = await response.json();
      setHealthData(data);
      setLastUpdated(new Date().toLocaleTimeString());
      setLoading(false);
    } catch (error) {
      console.error('Error loading health status:', error);
      setLoading(false);
    }
  };


  const getStatusColor = (status) => {
    switch (status) {
      case 'green':
        return '#10b981'; // emerald
      case 'red':
        return '#ef4444'; // red
      case 'yellow':
        return '#f59e0b'; // amber
      case 'gray':
      default:
        return '#9ca3af'; // gray
    }
  };

  const categorizeHealth = () => {
    const categories = {
      'Core Infrastructure': ['Firebase', 'OpenAI', 'LLM Client', 'Mission Store'],
      'Agent Intelligence': ['Orchestrator', 'Action Readiness Engine', 'Goal Decomposer', 'Reflection Engine'],
      'Learning & Memory': ['Memory Manager', 'Knowledge Graph', 'Learning Signals', 'Success Tracker', 'Autonomy Manager'],
      'Tools & Execution': ['Tool Registry', 'Web Scraper', 'SerpAPI', 'Execution Stream', 'Screenshot Capture'],
      'External Integrations': ['Email System', 'GHL CRM', 'Build Signals', 'Budget Tracker']
    };

    const allSystems = {
      ...healthData.primary_systems,
      ...healthData.additional_systems
    };

    const categorized = {};
    Object.keys(categories).forEach(categoryName => {
      categorized[categoryName] = {};
      categories[categoryName].forEach(systemName => {
        if (allSystems[systemName]) {
          categorized[categoryName][systemName] = allSystems[systemName];
        }
      });
    });

    return categorized;
  };

  if (!healthData) {
    return (
      <section className="monitor-container">
        <div className="monitor-loading">Loading system monitor...</div>
      </section>
    );
  }

  const categorized = categorizeHealth();

  return (
    <section className="monitor-panel">
      <div className="monitor-header">
        <h2>System Health Monitor</h2>
        <div className="monitor-controls">
          {!skipRefreshButton && (
            <button
              className="monitor-btn refresh-btn"
              onClick={loadHealthStatus}
              disabled={loading}
            >
              {loading ? '⟳ Updating...' : '⟳ Refresh'}
            </button>
          )}
        </div>
      </div>

      {/* Overall Health Status */}
      <div className="overall-health">
        <div className="health-indicator">
          <div
            className="health-light"
            style={{
              backgroundColor:
                healthData.overall_health === 'healthy'
                  ? '#10b981'
                  : healthData.overall_health === 'degraded'
                  ? '#f59e0b'
                  : '#ef4444',
            }}
          ></div>
          <div className="health-text">
            <div className="health-status">
              {healthData.overall_health.toUpperCase()}
            </div>
            <div className="health-summary">
              {healthData.summary?.total?.green ?? 0}/{Object.keys(healthData.primary_systems || {}).length + Object.keys(healthData.additional_systems || {}).length} Systems Operational
            </div>
          </div>
        </div>

        {/* Status Decoder */}
        <div className="status-decoder">
          <div className="decoder-item">
            <span className="decoder-circle" style={{ backgroundColor: '#10b981' }}></span>
            <span className="decoder-label">Healthy</span>
            <span className="decoder-count">{healthData.summary?.total?.green ?? 0}</span>
          </div>
          <div className="decoder-item">
            <span className="decoder-circle" style={{ backgroundColor: '#9ca3af' }}></span>
            <span className="decoder-label">Not Found</span>
            <span className="decoder-count">{healthData.summary?.total?.gray ?? 0}</span>
          </div>
          <div className="decoder-item">
            <span className="decoder-circle" style={{ backgroundColor: '#ef4444' }}></span>
            <span className="decoder-label">Malfunction</span>
            <span className="decoder-count">{healthData.summary?.total?.red ?? 0}</span>
          </div>
        </div>
      </div>

      {/* Categorized Systems */}
      <div className="systems-accordion">
        {Object.entries(categorized).map(([categoryName, systems]) => (
          <div key={categoryName}>
            <h3 className="category-header">
              <span className="category-name">{categoryName}</span>
            </h3>
            <div className="systems-list">
              {Object.entries(systems).map(([systemName, info]) => (
                <div key={systemName} className="system-item">
                  <div className="system-status" style={{ backgroundColor: getStatusColor(info.status) }}></div>
                  <div className="system-info">
                    <div className="system-name">{systemName}</div>
                    <div className="system-detail">{info.message}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Metadata */}
      <div className="monitor-metadata">
        {lastUpdated && (
          <small>Last updated: {lastUpdated}</small>
        )}
      </div>
    </section>
  );
}

export default SystemMonitor;
