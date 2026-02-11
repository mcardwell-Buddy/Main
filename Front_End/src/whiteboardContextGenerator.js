/**
 * Whiteboard Context Generator
 * 
 * Generates structured context payloads for intelligent handoff to chat.
 * Buddy uses these to auto-generate contextual responses without manual prompting.
 */

/**
 * Generate context payload for rollback events
 */
export const generateRollbackContext = (rollback) => ({
  source: 'whiteboard',
  event_type: 'rollback',
  timestamp: new Date().toISOString(),
  summary: `System rolled back ${rollback.tool_name || 'unknown tool'} from ${rollback.failed_state} to ${rollback.recovered_state}`,
  context: {
    tool: rollback.tool_name,
    reason: rollback.reason || 'Execution failed',
    from_state: rollback.failed_state,
    to_state: rollback.recovered_state,
    timestamp: rollback.timestamp,
    execution_id: rollback.execution_id
  },
  expected_responses: [
    'Explain why the rollback happened',
    'Show me what failed in that execution',
    'How do we prevent this next time?',
    'Should we retry this tool?'
  ],
  buddy_prompt: `The system auto-rolled back a failed execution. Summarize what happened, why it matters, and ask if the user wants to retry or investigate further.`
});

/**
 * Generate context payload for approval alerts (hustle candidates)
 */
export const generateApprovalContext = (hustle) => ({
  source: 'whiteboard',
  event_type: 'approval',
  timestamp: new Date().toISOString(),
  summary: `New hustle candidate: "${hustle.name || hustle.title || 'Untitled'}" â€” ${hustle.risk_level || 'unknown'} risk, $${Number(hustle.estimated_upside || 0).toLocaleString()} upside`,
  context: {
    hustle_id: hustle.id,
    name: hustle.name || hustle.title || 'Untitled',
    description: hustle.description || hustle.context || 'No description provided',
    risk_level: hustle.risk_level || 'unknown',
    estimated_upside: hustle.estimated_upside || 0,
    status: hustle.status || 'pending',
    notes: hustle.notes || ''
  },
  expected_responses: [
    'Should I approve this hustle?',
    'What are the risks?',
    'How much effort to implement?',
    'What\'s the revenue potential?'
  ],
  buddy_prompt: `A new hustle candidate is pending approval. Summarize the opportunity (name, risk, upside), explain why this matters, and ask if the user wants to approve, reject, or get more details.`
});

/**
 * Generate context payload for system alerts (conflicts, issues)
 */
export const generateAlertContext = (alert) => ({
  source: 'whiteboard',
  event_type: 'alert',
  timestamp: new Date().toISOString(),
  summary: `Alert: ${alert.title || 'System Alert'} â€” ${alert.description || 'Details not available'}`,
  context: {
    alert_id: alert.id,
    title: alert.title || 'System Alert',
    description: alert.description || 'No description',
    severity: alert.severity || 'unknown',
    type: alert.type || 'unknown',
    timestamp: alert.timestamp
  },
  expected_responses: [
    'What\'s the impact of this alert?',
    'How do we fix this?',
    'Should I take action now?',
    'What caused this?'
  ],
  buddy_prompt: `A system alert has been triggered. Summarize the issue, explain its impact, and ask if the user wants to resolve it or investigate further.`
});

/**
 * Generate context payload for confidence changes
 */
export const generateConfidenceContext = (signal) => ({
  source: 'whiteboard',
  event_type: 'learning',
  timestamp: new Date().toISOString(),
  summary: `Confidence update: ${signal.signal_type || 'unknown'} â€” confidence now ${Math.round((signal.confidence_score || 0) * 100)}%`,
  context: {
    signal_id: signal.id,
    signal_type: signal.signal_type || 'unknown',
    confidence_score: signal.confidence_score || 0,
    context: signal.context || 'No context provided',
    related_tool: signal.related_tool || null,
    timestamp: signal.timestamp
  },
  expected_responses: [
    'Why did confidence change?',
    'Should this affect our strategy?',
    'What pattern triggered this?',
    'How reliable is this signal?'
  ],
  buddy_prompt: `A learning signal has updated our confidence. Summarize the signal type and new confidence level, explain what triggered it, and ask if the user wants to adjust strategy.`
});

/**
 * Generate context payload for execution details
 */
export const generateExecutionContext = (execution) => ({
  source: 'whiteboard',
  event_type: 'execution',
  timestamp: new Date().toISOString(),
  summary: `Execution: ${execution.tool_name || 'unknown tool'} â€” ${execution.status || 'unknown'} status, took ${execution.duration_ms || 0}ms`,
  context: {
    execution_id: execution.id,
    tool_name: execution.tool_name || 'unknown',
    action: execution.action || 'unknown',
    status: execution.status || 'unknown',
    mode: execution.execution_mode || 'unknown',
    duration_ms: execution.duration_ms || 0,
    timestamp: execution.timestamp,
    output: execution.output || null
  },
  expected_responses: [
    'Why did this take so long?',
    'Was this successful?',
    'What was the output?',
    'Should we optimize this tool?'
  ],
  buddy_prompt: `An execution has completed. Summarize the tool, status, and duration. If there are issues, highlight them. Ask if the user wants to review the full output or retry.`
});

/**
 * Generate context payload for opportunity reviews
 */
export const generateOpportunityContext = (opportunity) => ({
  source: 'whiteboard',
  event_type: 'opportunity',
  timestamp: new Date().toISOString(),
  summary: `Income opportunity: ${opportunity.name || 'Unnamed'} â€” approved, potential revenue $${Number(opportunity.potential_revenue || 0).toLocaleString()}`,
  context: {
    opportunity_id: opportunity.id,
    name: opportunity.name || 'Unnamed',
    description: opportunity.description || 'No description',
    potential_revenue: opportunity.potential_revenue || 0,
    automated_tasks: opportunity.automated_tasks || 0,
    status: opportunity.status || 'unknown',
    next_actions: opportunity.next_actions || []
  },
  expected_responses: [
    'What\'s the next step?',
    'How are we tracking this?',
    'Should we allocate more resources?',
    'What\'s the timeline?'
  ],
  buddy_prompt: `An approved income opportunity is ready for action. Summarize the opportunity name, revenue potential, and current status. Ask what the user wants to do next.`
});

/**
 * Auto-generate Buddy's contextual response based on whiteboard context
 */
export const generateBuddyResponse = (context) => {
  const { event_type, summary, context: details } = context;

  const responses = {
    rollback: `I see that the system rolled back an execution. **${summary}**\n\nThis suggests the ${details.tool} tool encountered an issue in the ${details.from_state} state. Rolling back to ${details.recovered_state} keeps the system stable.\n\n**What would you like to do?**\n1. Investigate what caused the failure\n2. Retry the execution with different parameters\n3. Review the tool's recent history\n4. Move on to the next task`,

    approval: `A new hustle has been flagged for approval. **${summary}**\n\n**Key details:**\nâ€¢ Risk Level: ${details.risk_level}\nâ€¢ Estimated Upside: $${Number(details.estimated_upside || 0).toLocaleString()}\nâ€¢ Status: ${details.status}\n\n${details.description ? `**Description:** ${details.description}\n` : ''}\n**Next step:** Do you want to approve this, request more analysis, or reject it?`,

    alert: `A system alert requires attention. **${summary}**\n\nSeverity: ${details.severity || 'unknown'}\n\n**Should I:**\n1. Help you fix this now?\n2. Gather more diagnostic information?\n3. Log it for later review?\n4. Assess the impact on current tasks?`,

    learning: `Your confidence in this area has been updated. **${summary}**\n\n**Signal:** ${details.signal_type}\n${details.context ? `**Why it matters:** ${details.context}` : ''}\n\n**Question:** Does this change how you want to approach the next task?`,

    execution: `An execution has completed. **${summary}**\n\n**Status:** ${details.status}\n**Duration:** ${details.duration_ms}ms\n\n${details.status === 'FAILED' ? 'âŒ This execution failed. Would you like me to troubleshoot?' : 'âœ… Execution successful.'}\n\n**What\'s next?**`,

    opportunity: `An income opportunity is ready to move forward. **${summary}**\n\n**Potential Revenue:** $${Number(details.potential_revenue || 0).toLocaleString()}\n**Automated Tasks:** ${details.automated_tasks || 0}\n\nThis opportunity is approved and ready to execute. **What\'s your next move?**`
  };

  return responses[event_type] || `I've pulled up some context from the Whiteboard. **${summary}**\n\nWhat would you like to explore?`;
};
