import React, { useState } from 'react';
import './UnifiedMissionProposal.css';

/**
 * UnifiedMissionProposal: Single cohesive mission proposal component
 * 
 * Replaces fragmented proposal display with unified card showing:
 * - What Buddy will do (automated steps)
 * - What human must do (manual steps, approvals)
 * - Costs (upfront, broken down by service)
 * - Time requirements (Buddy + human)
 * - Approval/rejection options
 * 
 * Philosophy:
 * - Show facts, not recommendations
 * - User decides if worth the investment
 * - "Buddy amplifies human, doesn't compete"
 */
const UnifiedMissionProposal = ({ proposal, onApprove, onReject, onModify }) => {
  const [expanded, setExpanded] = useState(false);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [renderError, setRenderError] = useState(null);

  if (!proposal) {
    return (
      <div className="proposal-error">
        <div className="error-icon">⚠️</div>
        <div className="error-message">No proposal data available. Please try again.</div>
      </div>
    );
  }

  try {
    const {
      mission_title,
      objective,
      executive_summary,
      metrics,
      costs,
      time,
      human_involvement,
      task_breakdown,
    next_steps
  } = proposal;

  const handleApprove = () => {
    if (onApprove) {
      onApprove(proposal.mission_id);
    }
  };

  const handleReject = () => {
    if (onReject) {
      onReject(proposal.mission_id);
    }
  };

  const handleModify = () => {
    if (onModify) {
      onModify(proposal.mission_id);
    }
  };

  const renderCostBreakdown = () => {
    if (!costs || !costs.breakdown || costs.breakdown.length === 0) {
      return <div className="no-costs">No API costs for this mission</div>;
    }

    return (
      <div className="cost-breakdown">
        {costs.breakdown.map((cost, idx) => (
          <div key={idx} className="cost-item">
            <div className="cost-service">
              <span className="service-name">{cost.service}</span>
              <span className="service-tier">{cost.tier || ''}</span>
            </div>
            <div className="cost-details">
              <span className="cost-amount">${cost.cost_usd.toFixed(4)}</span>
              <span className="cost-ops">{cost.operations} operations</span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderSteps = () => {
    if (!task_breakdown || !task_breakdown.steps) {
      return null;
    }

    return (
      <div className="steps-list">
        {task_breakdown.steps.map((step) => (
          <div key={step.step_number} className={`step-item step-${step.step_type}`}>
            <div className="step-header">
              <span className="step-number">{step.step_number}</span>
              <span className="step-type-badge">{step.step_type.replace('_', ' ')}</span>
              {step.is_blocking && <span className="blocking-badge">Blocking</span>}
            </div>
            <div className="step-description">{step.description}</div>
            <div className="step-meta">
              {step.estimated_cost && (
                <span className="step-cost">${step.estimated_cost.total_usd.toFixed(4)}</span>
              )}
              {step.estimated_buddy_time && (
                <span className="step-time">~{step.estimated_buddy_time.toFixed(1)}s</span>
              )}
              {step.estimated_human_time > 0 && (
                <span className="step-human-time">You: {step.estimated_human_time}min</span>
              )}
            </div>
            {step.human_actions && step.human_actions.length > 0 && (
              <div className="step-human-actions">
                <div className="human-actions-title">Required Actions:</div>
                {step.human_actions.map((action, idx) => (
                  <div key={idx} className="human-action">
                    • {action.action}: {action.description} ({action.estimated_minutes}min)
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderOverview = () => (
    <div className="tab-content overview-tab">
      <div className="executive-summary">
        <h4>Summary</h4>
        <p>{executive_summary}</p>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Total Steps</div>
          <div className="metric-value">{metrics.total_steps}</div>
        </div>
        <div className="metric-card buddy">
          <div className="metric-label">Buddy Steps</div>
          <div className="metric-value">{metrics.buddy_steps}</div>
        </div>
        <div className="metric-card human">
          <div className="metric-label">Your Steps</div>
          <div className="metric-value">{metrics.human_steps}</div>
        </div>
        <div className="metric-card hybrid">
          <div className="metric-label">Hybrid Steps</div>
          <div className="metric-value">{metrics.hybrid_steps}</div>
        </div>
      </div>

      <div className="cost-time-summary">
        <div className="summary-section">
          <h4>Cost</h4>
          <div className="total-cost">${costs.total_usd.toFixed(4)}</div>
          {renderCostBreakdown()}
        </div>
        <div className="summary-section">
          <h4>Time</h4>
          <div className="time-breakdown">
            <div className="time-item">
              <span>Buddy:</span>
              <span>{time.buddy_seconds.toFixed(1)}s</span>
            </div>
            <div className="time-item">
              <span>You:</span>
              <span>{time.human_minutes}min</span>
            </div>
            <div className="time-item total">
              <span>Total:</span>
              <span>~{time.total_minutes}min</span>
            </div>
          </div>
        </div>
      </div>

      {human_involvement.requires_approval && (
        <div className="approval-notice">
          <span className="notice-icon">ℹ️</span>
          <span>Your approval is required before execution</span>
        </div>
      )}

      {human_involvement.has_blocking_steps && (
        <div className="blocking-notice">
          <span className="notice-icon">⚠️</span>
          <span>Some steps will pause and wait for your input</span>
        </div>
      )}

      <div className="what-happens-next">
        <h4>What Happens Next</h4>
        <p>{next_steps.what_happens_next}</p>
      </div>
    </div>
  );

  const renderStepsTab = () => (
    <div className="tab-content steps-tab">
      <div className="steps-header">
        <h4>Detailed Breakdown ({task_breakdown?.steps?.length || 0} steps)</h4>
      </div>
      {renderSteps()}
    </div>
  );

  try {
    return (
      <div className="unified-mission-proposal">
        <div className="proposal-header">
          <h3>{mission_title || 'Mission'}</h3>
          <p className="objective">{objective || 'No objective provided'}</p>
        </div>

        <div className="proposal-tabs">
          <button
            className={`tab ${selectedTab === 'overview' ? 'active' : ''}`}
            onClick={() => setSelectedTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab ${selectedTab === 'steps' ? 'active' : ''}`}
            onClick={() => setSelectedTab('steps')}
          >
            Detailed Steps
          </button>
        </div>

        <div className="proposal-body">
          {selectedTab === 'overview' && renderOverview()}
          {selectedTab === 'steps' && renderStepsTab()}
        </div>

        <div className="proposal-actions">
          <button className="btn-approve" onClick={handleApprove}>
            {next_steps?.approval_options?.[0] || 'Approve'}
          </button>
          {onModify && (
            <button className="btn-modify" onClick={handleModify}>
              {next_steps?.approval_options?.[1] || 'Modify'}
            </button>
          )}
          <button className="btn-reject" onClick={handleReject}>
            {next_steps?.approval_options?.[next_steps?.approval_options?.length - 1] || 'Reject'}
          </button>
        </div>
      </div>
    );
  } catch (error) {
    console.error('Error rendering UnifiedMissionProposal:', error);
    return (
      <div className="proposal-error">
        <div className="error-icon">⚠️</div>
        <div className="error-message">Error displaying proposal: {error.message}</div>
        <div className="error-detail">Please try again or contact support.</div>
      </div>
    );
  }
  } else {
    return (
      <div className="proposal-error">
        <div className="error-icon">❌</div>
        <div className="error-message">Invalid proposal structure</div>
      </div>
    );
  }
};

export default UnifiedMissionProposal;
