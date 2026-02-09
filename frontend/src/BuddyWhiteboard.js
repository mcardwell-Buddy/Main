import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './BuddyWhiteboard.css';
import {
  generateRollbackContext,
  generateApprovalContext,
  generateAlertContext,
  generateConfidenceContext,
  generateExecutionContext,
  generateOpportunityContext
} from './whiteboardContextGenerator';

function BuddyWhiteboard() {
  const navigate = useNavigate();
  
  // Load persisted UI state from localStorage
  const loadPersistedState = () => {
    try {
      const savedState = localStorage.getItem('whiteboard_ui_state');
      if (savedState) {
        return JSON.parse(savedState);
      }
    } catch (error) {
      console.error('Failed to load persisted UI state:', error);
    }
    return {
      collapsed: { operations: false, learning: false, hustle: false, interaction: false },
      timeFilter: '24h'
    };
  };

  const persistedState = loadPersistedState();

  // State for collapsible sections (with localStorage persistence)
  const [collapsed, setCollapsed] = useState(persistedState.collapsed);

  // State for dashboard data
  const [operationsData, setOperationsData] = useState(null);
  const [learningData, setLearningData] = useState(null);
  const [hustleData, setHustleData] = useState(null);
  
  // State for filters (with localStorage persistence)
  const [timeFilter, setTimeFilter] = useState(persistedState.timeFilter);
  
  // State for modals
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [selectedSignal, setSelectedSignal] = useState(null);
  const [detailModal, setDetailModal] = useState(null);

  const defaultSignalPriorities = ['CRITICAL', 'ECONOMIC'];
  const [signalPriorityFilter, setSignalPriorityFilter] = useState(defaultSignalPriorities);

  const getSignalPriority = (signal) => (signal?.signal_priority || 'INFO').toUpperCase();
  const totalLearningSignals = learningData?.learning_signals?.length || 0;
  const filteredLearningSignals = (learningData?.learning_signals || []).filter(
    (signal) => signalPriorityFilter.includes(getSignalPriority(signal))
  );
  const displayLearningSignals = filteredLearningSignals;

  const toggleSignalPriority = (priority) => {
    setSignalPriorityFilter((prev) => (
      prev.includes(priority)
        ? prev.filter((p) => p !== priority)
        : [...prev, priority]
    ));
  };

  // Persist UI state to localStorage whenever it changes
  useEffect(() => {
    try {
      const stateToSave = {
        collapsed,
        timeFilter
      };
      localStorage.setItem('whiteboard_ui_state', JSON.stringify(stateToSave));
    } catch (error) {
      console.error('Failed to persist UI state:', error);
    }
  }, [collapsed, timeFilter]);

  // Fetch all dashboard data
  const fetchAllData = async () => {
    try {
      const [opsRes, learnRes, hustleRes] = await Promise.all([
        fetch('http://127.0.0.1:8000/dashboards/operations'),
        fetch('http://127.0.0.1:8000/dashboards/learning'),
        fetch('http://127.0.0.1:8000/dashboards/side_hustle')
      ]);

      if (opsRes.ok) setOperationsData(await opsRes.json());
      if (learnRes.ok) setLearningData(await learnRes.json());
      if (hustleRes.ok) setHustleData(await hustleRes.json());
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  // Fetch on mount and set up auto-refresh every 3 seconds
  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 3000); // Real-time updates every 3 seconds
    return () => clearInterval(interval);
  }, []);

  // Toggle section collapse
  const toggleSection = (section) => {
    setCollapsed(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Scroll to section
  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Filter and sort executions
  const getFilteredExecutions = () => {
    if (!operationsData?.recent_executions) return [];
    
    let filtered = [...operationsData.recent_executions];
    
    // Apply time filter
    const now = Date.now();
    const timeRanges = {
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
      'all': Infinity
    };
    
    if (timeFilter !== 'all') {
      const cutoff = now - timeRanges[timeFilter];
      filtered = filtered.filter(exec => new Date(exec.timestamp).getTime() > cutoff);
    }
    
    // Sort by timestamp (newest first)
    filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    
    return filtered;
  };

  const filteredExecutions = getFilteredExecutions();

  // Get execution mode badge color
  const getModeBadgeColor = (mode) => {
    switch (mode) {
      case 'MOCK': return '#fbbf24'; // yellow
      case 'DRY_RUN': return '#3b82f6'; // blue
      case 'LIVE': return '#10b981'; // green
      default: return '#6b7280'; // gray
    }
  };

  const isApprovedOpportunity = (opportunity) => {
    if (!opportunity) return false;
    if (opportunity.approved === true) return true;
    const status = (opportunity.status || '').toLowerCase();
    return ['approved', 'active', 'live'].includes(status);
  };

  const approvedOpportunities = (hustleData?.active_opportunities || []).filter(isApprovedOpportunity);
  const candidateOpportunities = (hustleData?.active_opportunities || []).filter(
    (opp) => !isApprovedOpportunity(opp)
  );
  const candidateHustles = [
    ...(hustleData?.candidate_hustles || []),
    ...candidateOpportunities
  ];

  const approvalAlerts = candidateHustles.map((hustle, idx) => ({
    id: hustle.id || `candidate-${idx}`,
    title: hustle.name || hustle.title || hustle.description || `Hustle Candidate ${idx + 1}`,
    riskLevel: hustle.risk_level || hustle.risk || 'unknown',
    estimatedUpside: hustle.estimated_upside || hustle.potential_revenue || hustle.upside || 0,
    status: hustle.status || 'pending',
    context: hustle.context || hustle.notes || hustle.summary || ''
  }));

  const systemAlerts = [
    ...(operationsData?.unresolved_conflicts || []).map((conflict, idx) => ({
      id: conflict.id || `conflict-${idx}`,
      title: conflict.type || 'Conflict',
      description: conflict.description || 'No description provided',
      timestamp: conflict.timestamp,
      severity: conflict.severity || 'warning'
    })),
    ...(operationsData?.recent_rollbacks || []).map((rollback, idx) => ({
      id: rollback.id || `rollback-${idx}`,
      title: 'Rollback',
      description: rollback.reason || 'Rollback triggered',
      timestamp: rollback.timestamp,
      severity: 'warning'
    }))
  ];

  const approvalsCount = approvalAlerts.length;
  const alertsCount = systemAlerts.length;
  const approvedRevenueTotal = approvedOpportunities.reduce(
    (sum, opp) => sum + (opp.potential_revenue || opp.estimated_upside || 0),
    0
  );

  const openDetailModal = ({ title, items, emptyMessage, chatPrompt, modalType = 'generic' }) => {
    let contextData = null;
    
    // Generate appropriate context based on modal type and content
    if (items && items.length > 0) {
      if (modalType === 'approvals') {
        // For approval alerts (hustle candidates), generate approval context
        const firstHustle = items[0];
        contextData = generateApprovalContext(firstHustle);
      } else if (modalType === 'alerts') {
        // For system alerts, generate alert context
        const firstAlert = items[0];
        contextData = generateAlertContext(firstAlert);
      } else if (modalType === 'execution') {
        // For executions, generate execution context
        const execution = items[0];
        contextData = generateExecutionContext(execution);
      } else if (modalType === 'rollback') {
        // For rollbacks, generate rollback context
        const rollback = items[0];
        contextData = generateRollbackContext(rollback);
      } else if (modalType === 'opportunity') {
        // For opportunities, generate opportunity context
        const opportunity = items[0];
        contextData = generateOpportunityContext(opportunity);
      }
    }
    
    setDetailModal({ title, items, emptyMessage, contextData });
  };

  const handleDiscuss = (context) => {
    if (!context) return;
    try {
      // Serialize context object to JSON
      const contextPayload = typeof context === 'string' ? context : JSON.stringify(context);
      localStorage.setItem('whiteboard_context', contextPayload);
    } catch (error) {
      console.error('Failed to persist discussion context:', error);
    }
    navigate('/');
  };

  const renderDetailItem = (item, idx) => {
    if (!item) return null;
    if (typeof item === 'string') {
      return (
        <div key={idx} className="detail-list-item">
          <div className="detail-item-title">{item}</div>
        </div>
      );
    }

    const title = item.title || item.name || item.description || item.type || `Item ${idx + 1}`;
    const subtitle = item.reason || item.status || item.context || item.details || '';
    const timestamp = item.timestamp ? new Date(item.timestamp).toLocaleString() : null;
    const risk = item.riskLevel || item.risk_level || item.risk;
    const upside = item.estimatedUpside || item.potential_revenue || item.upside;

    return (
      <div key={item.id || idx} className="detail-list-item">
        <div className="detail-item-title">{title}</div>
        {subtitle && <div className="detail-item-sub">{subtitle}</div>}
        {(risk || upside) && (
          <div className="detail-item-meta">
            {risk && <span className={`risk-pill risk-${String(risk).toLowerCase()}`}>Risk: {risk}</span>}
            {upside !== undefined && <span className="upside-pill">Upside: ${Number(upside).toLocaleString()}</span>}
          </div>
        )}
        {timestamp && <div className="detail-item-time">{timestamp}</div>}
      </div>
    );
  };

  return (
    <div className="whiteboard-container" data-testid="whiteboard-root">
      {/* Inline Modals */}
      {selectedExecution && (
        <div className="modal-overlay" onClick={() => setSelectedExecution(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Execution Details</h3>
              <button onClick={() => setSelectedExecution(null)} className="modal-close">✕</button>
            </div>
            <div className="modal-body">
              <div className="detail-row">
                <span className="detail-label">Tool:</span>
                <span className="detail-value">{selectedExecution.tool_name}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Status:</span>
                <span className={`status-badge status-${selectedExecution.status?.toLowerCase()}`}>
                  {selectedExecution.status}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Execution Mode:</span>
                <span className="mode-badge" style={{ backgroundColor: getModeBadgeColor(selectedExecution.execution_mode) }}>
                  {selectedExecution.execution_mode}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Timestamp:</span>
                <span className="detail-value">{new Date(selectedExecution.timestamp).toLocaleString()}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Duration:</span>
                <span className="detail-value">{selectedExecution.execution_time_ms}ms</span>
              </div>
              {selectedExecution.risk_level && (
                <div className="detail-row">
                  <span className="detail-label">Risk Level:</span>
                  <span className={`risk-badge risk-${selectedExecution.risk_level?.toLowerCase()}`}>
                    {selectedExecution.risk_level}
                  </span>
                </div>
              )}
              {selectedExecution.output && (
                <div className="detail-row">
                  <span className="detail-label">Output:</span>
                  <pre className="detail-output">{JSON.stringify(selectedExecution.output, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {selectedSignal && (
        <div className="modal-overlay" onClick={() => setSelectedSignal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Learning Signal</h3>
              <button onClick={() => setSelectedSignal(null)} className="modal-close">✕</button>
            </div>
            <div className="modal-body">
              <div className="detail-row">
                <span className="detail-label">Signal:</span>
                <span className="detail-value">{selectedSignal.signal_type}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Confidence:</span>
                <span className="detail-value">{Math.round((selectedSignal.confidence_score || 0) * 100)}%</span>
              </div>
              {selectedSignal.context && (
                <div className="detail-row">
                  <span className="detail-label">Why confidence changed:</span>
                  <span className="detail-value">{selectedSignal.context}</span>
                </div>
              )}
              <div className="detail-row">
                <span className="detail-label">Source:</span>
                <span className="detail-value">{selectedSignal.source_tool || 'Unknown'}</span>
              </div>
              {selectedSignal.timestamp && (
                <div className="detail-row">
                  <span className="detail-label">Timestamp:</span>
                  <span className="detail-value">{new Date(selectedSignal.timestamp).toLocaleString()}</span>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="discuss-btn" onClick={() => handleDiscuss(generateConfidenceContext(selectedSignal))}>
                Discuss with Buddy
              </button>
            </div>
          </div>
        </div>
      )}

      {detailModal && (
        <div className="modal-overlay" onClick={() => setDetailModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{detailModal.title}</h3>
              <button onClick={() => setDetailModal(null)} className="modal-close">✕</button>
            </div>
            <div className="modal-body">
              {detailModal.items && detailModal.items.length > 0 ? (
                <div className="detail-list">
                  {detailModal.items.map((item, idx) => renderDetailItem(item, idx))}
                </div>
              ) : (
                <div className="no-alerts">{detailModal.emptyMessage || 'No records available.'}</div>
              )}
            </div>
            <div className="modal-footer">
              <button className="modal-secondary" onClick={() => setDetailModal(null)}>Close</button>
              {detailModal.contextData && (
                <button className="discuss-btn" onClick={() => handleDiscuss(detailModal.contextData)}>
                  Discuss with Buddy
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="whiteboard-shell">
        <aside className="whiteboard-sidebar">
          <div className="sidebar-brand">
            <img src="/buddy-clean.png" alt="Buddy" className="sidebar-buddy-img" />
            <div className="sidebar-title">Whiteboard</div>
            <div className="sidebar-subtitle">Shared memory & approvals ledger</div>
          </div>
          <button onClick={() => navigate('/')} className="back-to-chat">← Back to Chat</button>

          <div className="sidebar-stats">
            <button
              className="sidebar-stat"
              onClick={() => openDetailModal({
                title: 'Pending Approvals',
                items: approvalAlerts,
                emptyMessage: 'No approvals pending.',
                modalType: 'approvals'
              })}
            >
              <span className="sidebar-stat-label">Approvals</span>
              <span className={`sidebar-stat-value ${approvalsCount > 0 ? 'stat-alert' : ''}`}>{approvalsCount}</span>
            </button>
            <button
              className="sidebar-stat"
              onClick={() => openDetailModal({
                title: 'System Alerts',
                items: systemAlerts,
                emptyMessage: 'No active alerts.',
                modalType: 'alerts'
              })}
            >
              <span className="sidebar-stat-label">Alerts</span>
              <span className={`sidebar-stat-value ${alertsCount > 0 ? 'stat-alert' : ''}`}>{alertsCount}</span>
            </button>
          </div>
        </aside>

        <div className="whiteboard-main">
          <div className="whiteboard-header">
            <div>
              <h1>Whiteboard Ledger</h1>
              <p>System-of-record state, approvals, and explanations.</p>
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="whiteboard-content">
        
        {/* OPERATIONS SECTION */}
        <section id="operations" className={`whiteboard-section ${collapsed.operations ? 'collapsed' : ''}`}>
          <div className="section-header" onClick={() => toggleSection('operations')}>
            <div className="section-title">
              <span className="section-icon">⚙️</span>
              <h2>Operations</h2>
              {operationsData?.execution_mode && (
                <span 
                  className="mode-badge" 
                  style={{ backgroundColor: getModeBadgeColor(operationsData.execution_mode) }}
                >
                  {operationsData.execution_mode}
                </span>
              )}
            </div>
            <button className="collapse-btn">
              {collapsed.operations ? '▼' : '▲'}
            </button>
          </div>
          
          {!collapsed.operations && (
            <div className="section-body">
              {operationsData ? (
                <>
                  {/* Filters and Controls */}
                  <div className="controls-bar">
                    <div className="filter-group">
                      <label>Time:</label>
                      <select value={timeFilter} onChange={(e) => setTimeFilter(e.target.value)}>
                        <option value="24h">Last 24h</option>
                        <option value="7d">Last 7 days</option>
                        <option value="30d">Last 30 days</option>
                        <option value="all">All time</option>
                      </select>
                    </div>
                  </div>

                  <div className="metrics-grid">
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Active Missions',
                        items: operationsData.active_missions || [],
                        emptyMessage: 'No active missions.',
                        chatPrompt: (operationsData.active_missions?.length || 0) > 0
                          ? `Let's review ${operationsData.active_missions.length} active missions and their status.`
                          : 'No missions running right now.'
                      })}
                    >
                      <div className="metric-label">Active Missions</div>
                      <div className="metric-value" data-testid="active-missions-count">{operationsData.active_missions?.length || 0}</div>
                    </div>
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Active Goals',
                        items: operationsData.active_goals || [],
                        emptyMessage: 'No active goals.',
                        chatPrompt: (operationsData.active_goals?.length || 0) > 0
                          ? `Let's review ${operationsData.active_goals.length} active goals and their status.`
                          : 'Confirm there are no active goals right now.'
                      })}
                    >
                      <div className="metric-label">Active Goals</div>
                      <div className="metric-value" data-testid="active-goals-count">{operationsData.active_goals?.length || 0}</div>
                    </div>
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Active Tasks',
                        items: operationsData.active_tasks || [],
                        emptyMessage: 'No active tasks.',
                        chatPrompt: (operationsData.active_tasks?.length || 0) > 0
                          ? `Let's discuss ${operationsData.active_tasks.length} active tasks and their blockers.`
                          : 'Confirm there are no active tasks right now.'
                      })}
                    >
                      <div className="metric-label">Active Tasks</div>
                      <div className="metric-value">{operationsData.active_tasks?.length || 0}</div>
                    </div>
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Unresolved Conflicts',
                        items: operationsData.unresolved_conflicts || [],
                        emptyMessage: 'No unresolved conflicts.',
                        chatPrompt: (operationsData.unresolved_conflicts?.length || 0) > 0
                          ? `Let's talk about ${operationsData.unresolved_conflicts.length} unresolved conflicts.`
                          : 'Confirm there are no unresolved conflicts.'
                      })}
                    >
                      <div className="metric-label">Conflicts</div>
                      <div className="metric-value alert">{operationsData.unresolved_conflicts?.length || 0}</div>
                    </div>
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Recent Rollbacks',
                        items: operationsData.recent_rollbacks || [],
                        emptyMessage: 'No recent rollbacks.',
                        chatPrompt: (operationsData.recent_rollbacks?.length || 0) > 0
                          ? `Let's discuss ${operationsData.recent_rollbacks.length} recent rollbacks and their causes.`
                          : 'Confirm there are no recent rollbacks.'
                      })}
                    >
                      <div className="metric-label">Recent Rollbacks</div>
                      <div className="metric-value">{operationsData.recent_rollbacks?.length || 0}</div>
                    </div>
                  </div>

                  {filteredExecutions.length > 0 && (
                    <div className="data-table">
                      <h3>Tool Execution Log ({filteredExecutions.length} executions)</h3>
                      <div className="table-wrapper">
                        <table>
                          <thead>
                            <tr>
                              <th>Timestamp</th>
                              <th>Tool</th>
                              <th>Action</th>
                              <th>State</th>
                              <th>Outcome</th>
                              <th>Duration</th>
                              <th>Details</th>
                            </tr>
                          </thead>
                          <tbody>
                            {filteredExecutions.slice(0, 20).map((exec, idx) => (
                              <tr key={idx} className="execution-row">
                                <td className="timestamp-cell" title={new Date(exec.timestamp).toISOString()}>
                                  {new Date(exec.timestamp).toLocaleTimeString()}
                                </td>
                                <td className="tool-cell">{exec.tool_name}</td>
                                <td className="action-cell">{exec.action || 'Execute'}</td>
                                <td className="state-cell">
                                  <span 
                                    className="mode-badge-small" 
                                    style={{ backgroundColor: getModeBadgeColor(exec.execution_mode) }}
                                  >
                                    {exec.execution_mode}
                                  </span>
                                </td>
                                <td className="outcome-cell">
                                  <span className={`status-badge status-${exec.status?.toLowerCase()}`}>
                                    {exec.status}
                                  </span>
                                </td>
                                <td className="duration-cell">{exec.execution_time_ms}ms</td>
                                <td className="details-cell">
                                  <button 
                                    className="details-btn"
                                    onClick={() => setSelectedExecution(exec)}
                                    title="View details"
                                  >
                                    📋
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* State Transitions */}
                  {operationsData.system_health && (
                    <div className="state-panel">
                      <h3>System Health</h3>
                      <div className="health-metrics">
                        <div className="health-item">
                          <span className="health-label">Overall Status:</span>
                          <span className={`health-value health-${operationsData.system_health.overall_status?.toLowerCase()}`}>
                            {operationsData.system_health.overall_status}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Conflicts Section */}
                  {operationsData.unresolved_conflicts && operationsData.unresolved_conflicts.length > 0 && (
                    <div className="conflicts-panel">
                      <h3>⚠️ Unresolved Conflicts</h3>
                      <div className="conflicts-list">
                        {operationsData.unresolved_conflicts.map((conflict, idx) => (
                          <div key={idx} className="conflict-item">
                            <div className="conflict-icon">⚠️</div>
                            <div className="conflict-details">
                              <div className="conflict-type">{conflict.type || 'Conflict'}</div>
                              <div className="conflict-description">{conflict.description}</div>
                              <div className="conflict-timestamp">{new Date(conflict.timestamp).toLocaleString()}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Rollbacks Section */}
                  {operationsData.recent_rollbacks && operationsData.recent_rollbacks.length > 0 && (
                    <div className="rollbacks-panel">
                      <h3>🔄 Recent Rollbacks</h3>
                      <div className="rollbacks-list">
                        {operationsData.recent_rollbacks.map((rollback, idx) => (
                          <div key={idx} className="rollback-item">
                            <div className="rollback-icon">🔄</div>
                            <div className="rollback-details">
                              <div className="rollback-reason">{rollback.reason}</div>
                              <div className="rollback-timestamp">{new Date(rollback.timestamp).toLocaleString()}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="loading">Loading operations data...</div>
              )}
            </div>
          )}
        </section>

        {/* LEARNING SECTION */}
        <section id="learning" className={`whiteboard-section ${collapsed.learning ? 'collapsed' : ''}`}>
          <div className="section-header" onClick={() => toggleSection('learning')}>
            <div className="section-title">
              <span className="section-icon">📊</span>
              <h2>Learning</h2>
            </div>
            <button className="collapse-btn">
              {collapsed.learning ? '▼' : '▲'}
            </button>
          </div>
          
          {!collapsed.learning && (
            <div className="section-body">
              {learningData ? (
                <>
                  <div className="metrics-grid">
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Learning Signals',
                        items: displayLearningSignals || [],
                        emptyMessage: 'No learning signals yet.',
                        chatPrompt: (displayLearningSignals?.length || 0) > 0
                          ? `Let's review ${displayLearningSignals.length} learning signals and why confidence moved.`
                          : 'Confirm there are no learning signals yet.'
                      })}
                    >
                      <div className="metric-label">Learning Signals</div>
                      <div className="metric-value">{displayLearningSignals?.length || 0}</div>
                    </div>
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Confidence Context',
                        items: displayLearningSignals || [],
                        emptyMessage: 'No confidence signals available.',
                        chatPrompt: (displayLearningSignals?.length || 0) > 0
                          ? 'Explain why confidence changed based on recent learning signals.'
                          : 'Confirm there is no confidence data yet.'
                      })}
                    >
                      <div className="metric-label">Avg Confidence</div>
                      <div className="metric-value confidence-score">
                        {displayLearningSignals?.length > 0 
                          ? Math.round((displayLearningSignals.reduce((sum, s) => sum + (s.confidence_score || 0), 0) / displayLearningSignals.length) * 100)
                          : 0}%
                      </div>
                    </div>
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Competitor Insights',
                        items: learningData.competitor_insights || [],
                        emptyMessage: 'No competitor insights yet.',
                        chatPrompt: (learningData.competitor_insights?.length || 0) > 0
                          ? `Let's review ${learningData.competitor_insights.length} competitor insights.`
                          : 'Confirm there are no competitor insights yet.'
                      })}
                    >
                      <div className="metric-label">Competitor Insights</div>
                      <div className="metric-value">{learningData.competitor_insights?.length || 0}</div>
                    </div>
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Market Opportunities',
                        items: learningData.market_opportunities || [],
                        emptyMessage: 'No market opportunities identified.',
                        chatPrompt: (learningData.market_opportunities?.length || 0) > 0
                          ? `Let's discuss ${learningData.market_opportunities.length} market opportunities.`
                          : 'Confirm there are no market opportunities yet.'
                      })}
                    >
                      <div className="metric-label">Market Opportunities</div>
                      <div className="metric-value">{learningData.market_opportunities?.length || 0}</div>
                    </div>
                  </div>

                  {displayLearningSignals && displayLearningSignals.length > 0 && (
                    <div className="insight-panel">
                      <h3>Why confidence changed</h3>
                      <ul>
                        {displayLearningSignals.slice(0, 3).map((signal, idx) => (
                          <li key={idx}>
                            <strong>{signal.signal_type}</strong> — {Math.round((signal.confidence_score || 0) * 100)}% confidence. {signal.context || 'No context provided.'}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Confidence Trend Visualization */}
                  {displayLearningSignals && displayLearningSignals.length > 0 && (
                    <div className="chart-panel">
                      <h3>📈 Confidence Trends</h3>
                      <div className="confidence-chart">
                        {displayLearningSignals.slice(0, 10).map((signal, idx) => {
                          const confidence = (signal.confidence_score * 100).toFixed(0);
                          const height = confidence;
                          return (
                            <div key={idx} className="chart-bar-container" title={`${signal.signal_type}: ${confidence}%`}>
                              <div 
                                className="chart-bar" 
                                style={{ 
                                  height: `${height}%`,
                                  backgroundColor: confidence >= 80 ? '#10b981' : confidence >= 50 ? '#f59e0b' : '#ef4444'
                                }}
                              ></div>
                              <div className="chart-label">{idx + 1}</div>
                            </div>
                          );
                        })}
                      </div>
                      <div className="chart-legend">
                        <span className="legend-item"><span className="legend-color" style={{backgroundColor: '#10b981'}}></span>High (80%+)</span>
                        <span className="legend-item"><span className="legend-color" style={{backgroundColor: '#f59e0b'}}></span>Medium (50-80%)</span>
                        <span className="legend-item"><span className="legend-color" style={{backgroundColor: '#ef4444'}}></span>Low (&lt;50%)</span>
                      </div>
                    </div>
                  )}

                  {/* Learning Signals Feed */}
                  {displayLearningSignals && displayLearningSignals.length > 0 && (
                    <div className="signals-feed">
                      <h3>🔔 Learning Signals Feed</h3>
                      <div className="signal-filters">
                        <span className="signal-filter-label">Priority:</span>
                        {['CRITICAL', 'ECONOMIC', 'IMPORTANT', 'INFO'].map((priority) => (
                          <label key={priority} className="signal-filter-option">
                            <input
                              type="checkbox"
                              checked={signalPriorityFilter.includes(priority)}
                              onChange={() => toggleSignalPriority(priority)}
                            />
                            <span>{priority}</span>
                          </label>
                        ))}
                        <span className="signal-filter-summary">
                          Showing {displayLearningSignals.length} of {totalLearningSignals}
                        </span>
                      </div>
                      <div className="feed-container">
                        {displayLearningSignals.slice(0, 15).map((signal, idx) => (
                          <div 
                            key={idx} 
                            className="signal-item"
                            onClick={() => setSelectedSignal(signal)}
                            style={{ cursor: 'pointer' }}
                            title="Click for details"
                          >
                            <div className="signal-header">
                              <span className="signal-type">{signal.signal_type}</span>
                              <span 
                                className="signal-confidence"
                                style={{ color: signal.confidence_score >= 0.8 ? '#10b981' : '#f59e0b' }}
                              >
                                {(signal.confidence_score * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div className="signal-source">Source: {signal.source_tool}</div>
                            <div className="signal-timestamp">{new Date(signal.timestamp).toLocaleString()}</div>
                            {signal.context && (
                              <div className="signal-context">{signal.context}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Active Missions */}
                  {operationsData?.active_missions && operationsData.active_missions.length > 0 && (
                    <div className="progress-panel">
                      <h3>🚀 Active Missions</h3>
                      <div className="goals-list" data-testid="missions-list">
                        {operationsData.active_missions.slice(0, 10).map((mission, idx) => (
                          <div 
                            key={mission.mission_id || idx} 
                            className="goal-item"
                            data-testid="whiteboard-mission"
                            data-mission-id={mission.mission_id}
                          >
                            <div className="goal-header">
                              <span className="goal-title">{mission.objective || `Mission ${idx + 1}`}</span>
                              <span className="goal-status">{mission.status}</span>
                            </div>
                            <div className="mission-id" style={{ fontSize: '0.8em', color: '#888', marginTop: '4px' }}>
                              ID: {mission.mission_id?.substring(0, 12)}...
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Goal Progress */}
                  {operationsData?.active_goals && operationsData.active_goals.length > 0 && (
                    <div className="progress-panel">
                      <h3>🎯 Goal Progress</h3>
                      <div className="goals-list" data-testid="goals-list">
                        {operationsData.active_goals.slice(0, 5).map((goal, idx) => (
                          <div 
                            key={idx} 
                            className="goal-item"
                            data-testid="whiteboard-goal"
                            data-goal-id={goal.goal_id || goal.id}
                          >
                            <div className="goal-header">
                              <span className="goal-title">{goal.description || `Goal ${idx + 1}`}</span>
                              <span className="goal-percentage">{goal.progress || 0}%</span>
                            </div>
                            <div className="progress-bar">
                              <div 
                                className="progress-fill" 
                                style={{ width: `${goal.progress || 0}%` }}
                              ></div>
                            </div>
                            <div className="goal-status">{goal.status}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="loading">Loading learning data...</div>
              )}
            </div>
          )}
        </section>

        {/* HUSTLE & CAMPAIGNS SECTION */}
        <section id="hustle" className={`whiteboard-section ${collapsed.hustle ? 'collapsed' : ''}`}>
          <div className="section-header" onClick={() => toggleSection('hustle')}>
            <div className="section-title">
              <span className="section-icon">💰</span>
              <h2>Hustle & Campaigns</h2>
            </div>
            <button className="collapse-btn">
              {collapsed.hustle ? '▼' : '▲'}
            </button>
          </div>
          
          {!collapsed.hustle && (
            <div className="section-body">
              {hustleData ? (
                <>
                  <div className="metrics-grid">
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Approved Opportunities',
                        items: approvedOpportunities,
                        emptyMessage: 'No approved opportunities yet.',
                        chatPrompt: approvedOpportunities.length > 0
                          ? `Let's review ${approvedOpportunities.length} approved opportunities.`
                          : 'Confirm there are no approved opportunities yet.'
                      })}
                    >
                      <div className="metric-label">Approved Opportunities</div>
                      <div className="metric-value">{approvedOpportunities.length}</div>
                    </div>
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Approved Revenue Potential',
                        items: approvedOpportunities,
                        emptyMessage: 'No approved revenue yet.',
                        chatPrompt: approvedRevenueTotal > 0
                          ? `Let's discuss the $${approvedRevenueTotal.toLocaleString()} approved revenue potential.`
                          : 'Confirm there is no approved revenue potential yet.'
                      })}
                    >
                      <div className="metric-label">Approved Revenue</div>
                      <div className="metric-value">${approvedRevenueTotal.toLocaleString()}</div>
                    </div>
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Automated Tasks',
                        items: hustleData.automated_tasks || [],
                        emptyMessage: 'No automated tasks.',
                        chatPrompt: (hustleData.automated_tasks?.length || 0) > 0
                          ? `Let's discuss ${hustleData.automated_tasks.length} automated tasks tied to approved hustles.`
                          : 'Confirm there are no automated tasks yet.'
                      })}
                    >
                      <div className="metric-label">Automated Tasks (Approved)</div>
                      <div className="metric-value">{hustleData.automated_tasks?.length || 0}</div>
                    </div>
                    <div
                      className="metric-card clickable"
                      onClick={() => openDetailModal({
                        title: 'Income Streams',
                        items: hustleData.income_streams || [],
                        emptyMessage: 'No income streams.',
                        chatPrompt: (hustleData.income_streams?.length || 0) > 0
                          ? `Let's review ${hustleData.income_streams.length} approved income streams.`
                          : 'Confirm there are no approved income streams yet.'
                      })}
                    >
                      <div className="metric-label">Income Streams (Approved)</div>
                      <div className="metric-value">{hustleData.income_streams?.length || 0}</div>
                    </div>
                  </div>

                  {approvedOpportunities.length > 0 ? (
                    <div className="data-table">
                      <h3>Approved Opportunities</h3>
                      <table>
                        <thead>
                          <tr>
                            <th>Opportunity</th>
                            <th>Type</th>
                            <th>Approved Upside</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {approvedOpportunities.slice(0, 5).map((opp, idx) => (
                            <tr key={idx}>
                              <td>{opp.name || `Opportunity ${idx + 1}`}</td>
                              <td>{opp.type || '—'}</td>
                              <td>${(opp.potential_revenue || opp.estimated_upside || 0).toLocaleString()}</td>
                              <td>
                                <span className={`status-badge status-${opp.status?.toLowerCase() || 'approved'}`}>
                                  {opp.status || 'Approved'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="info-message">
                      <p>No approved hustles yet. Review pending approvals in Interaction & Approvals.</p>
                    </div>
                  )}
                </>
              ) : (
                <div className="loading">Loading hustle data...</div>
              )}
            </div>
          )}
        </section>

        {/* INTERACTION & APPROVALS SECTION */}
        <section id="interaction" className={`whiteboard-section ${collapsed.interaction ? 'collapsed' : ''}`}>
          <div className="section-header" onClick={() => toggleSection('interaction')}>
            <div className="section-title">
              <span className="section-icon">💬</span>
              <h2>Interaction & Approvals</h2>
            </div>
            <button className="collapse-btn">
              {collapsed.interaction ? '▼' : '▲'}
            </button>
          </div>
          
          {!collapsed.interaction && (
            <div className="section-body">
              <div className="metrics-grid">
                <div
                  className="metric-card clickable"
                  onClick={() => openDetailModal({
                    title: 'Pending Approvals',
                    items: approvalAlerts,
                    emptyMessage: 'No approvals pending.',
                    modalType: 'approvals'
                  })}
                >
                  <div className="metric-label">Pending Approvals</div>
                  <div className={`metric-value ${approvalsCount > 0 ? 'alert' : ''}`}>{approvalsCount}</div>
                </div>
                <div
                  className="metric-card clickable"
                  onClick={() => openDetailModal({
                    title: 'System Alerts',
                    items: systemAlerts,
                    emptyMessage: 'No active alerts.',
                    modalType: 'alerts'
                  })}
                >
                  <div className="metric-label">System Alerts</div>
                  <div className={`metric-value ${alertsCount > 0 ? 'alert' : ''}`}>{alertsCount}</div>
                </div>
              </div>

              <div className="approval-panel">
                <h3>Approval Queue</h3>
                {approvalAlerts.length > 0 ? (
                  <div className="approval-list">
                    {approvalAlerts.map((alert) => (
                      <div key={alert.id} className="approval-item">
                        <div className="approval-title">New Hustle Candidate</div>
                        <div className="approval-name">{alert.title}</div>
                        <div className="approval-meta">
                          <span className={`risk-pill risk-${String(alert.riskLevel).toLowerCase()}`}>Risk: {alert.riskLevel}</span>
                          <span className="upside-pill">Estimated Upside: ${Number(alert.estimatedUpside || 0).toLocaleString()}</span>
                        </div>
                        {alert.context && <div className="approval-context">{alert.context}</div>}
                        <div className="approval-status">Approval required to proceed</div>
                        <button
                          className="discuss-inline"
                          onClick={() => handleDiscuss(generateApprovalContext({
                            id: alert.id,
                            name: alert.title,
                            description: alert.context,
                            risk_level: alert.riskLevel,
                            estimated_upside: alert.estimatedUpside,
                            status: alert.status
                          }))}
                        >
                          Discuss with Buddy
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-alerts">No approvals pending.</div>
                )}
              </div>

              <div className="alerts-panel">
                <h3>System Alerts</h3>
                {systemAlerts.length > 0 ? (
                  <div className="alerts-list">
                    {systemAlerts.map((alert) => (
                      <div key={alert.id} className="alert-item">
                        <div className="alert-icon">⚠️</div>
                        <div className="alert-content">
                          <div className="alert-title">{alert.title}</div>
                          <div className="alert-description">{alert.description}</div>
                          {alert.timestamp && (
                            <div className="alert-timestamp">{new Date(alert.timestamp).toLocaleString()}</div>
                          )}
                        </div>
                        <button
                          className="discuss-inline"
                          onClick={() => handleDiscuss(generateAlertContext({
                            id: alert.id,
                            title: alert.title,
                            description: alert.description,
                            severity: alert.severity,
                            type: alert.type,
                            timestamp: alert.timestamp
                          }))}
                        >
                          Discuss
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-alerts">No active system alerts.</div>
                )}
              </div>
            </div>
          )}
        </section>

          </div>
        </div>
      </div>
    </div>
  );
}

export default BuddyWhiteboard;
