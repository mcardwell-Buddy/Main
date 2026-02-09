import React, { useEffect, useMemo, useState } from 'react';
import './Phase7Observatory.css';
import SchedulerPanel from './components/SchedulerPanel';
import WorkflowDagView from './components/WorkflowDagView';
import TimelineReplay from './components/TimelineReplay';
import BranchingView from './components/BranchingView';
import RecoveryView from './components/RecoveryView';
import DataSourcePanel from './components/DataSourcePanel';

const DEFAULT_SOURCES = {
  metrics: '/outputs/end_to_end/wave_metrics.jsonl',
  workflowSummaries: '/outputs/end_to_end/workflow_summaries.json',
  schedulerHealth: '/outputs/end_to_end/scheduler_health.json',
  queueState: '/outputs/task_scheduler_metrics/queue_state.json'
};

const parseJsonl = (text) => {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  const records = [];
  for (const line of lines) {
    try {
      records.push(JSON.parse(line));
    } catch (err) {
      // ignore malformed lines
    }
  }
  return records;
};

const normalizeMetrics = (records) => {
  return records.map((item) => ({
    task_id: item.task_id,
    workflow_id: item.workflow_id,
    wave: item.wave,
    tool_used: item.tool_used,
    risk_level: item.risk_level,
    confidence_score: item.confidence_score,
    approval_outcome: item.approval_outcome,
    approval_state: item.approval_state,
    execution_result: item.execution_result,
    retries: item.retries,
    execution_time_ms: item.execution_time_ms || 0,
    scheduler_queue_depth: item.scheduler_queue_depth,
    dependency_wait_time_ms: item.dependency_wait_time_ms || 0,
    timestamp: item.timestamp,
    phase_invoked: item.phase_invoked || [],
    failure_reason: item.failure_reason || item.error || null,
    session_id: item.session_id
  }));
};

const normalizeQueueState = (state) => {
  if (!state || !state.tasks) return null;
  return {
    timestamp: state.timestamp,
    version: state.version,
    metrics: state.metrics,
    tasks: state.tasks.map(task => ({
      id: task.id,
      description: task.description,
      status: task.status?.toLowerCase() || 'unknown',
      priority: task.priority,
      risk_level: task.risk_level,
      confidence_score: task.confidence_score,
      dependencies: (task.dependencies || []).map(dep => dep.task_id),
      conditional_branches: task.conditional_branches || [],
      metadata: task.metadata || {},
      attempt_count: task.attempt_count || 0,
      created_at: task.created_at,
      started_at: task.started_at,
      completed_at: task.completed_at,
      error: task.error
    }))
  };
};

const deriveTaskIndex = (metrics, queueState) => {
  const taskIndex = new Map();

  if (queueState?.tasks) {
    queueState.tasks.forEach(task => {
      taskIndex.set(task.id, { ...task, source: 'queue_state' });
    });
  }

  metrics.forEach(record => {
    if (!record.task_id) return;
    const existing = taskIndex.get(record.task_id) || {};
    taskIndex.set(record.task_id, {
      ...existing,
      id: record.task_id,
      description: existing.description || record.tool_used || 'Task',
      status: record.execution_result || existing.status,
      risk_level: record.risk_level || existing.risk_level,
      confidence_score: record.confidence_score ?? existing.confidence_score,
      attempt_count: record.retries ?? existing.attempt_count,
      metadata: { ...existing.metadata, tool_used: record.tool_used, approval_outcome: record.approval_outcome },
      source: existing.source || 'metrics'
    });
  });

  return Array.from(taskIndex.values());
};

const Phase7Observatory = () => {
  const [metrics, setMetrics] = useState([]);
  const [workflowSummaries, setWorkflowSummaries] = useState([]);
  const [schedulerHealth, setSchedulerHealth] = useState(null);
  const [queueState, setQueueState] = useState(null);
  const [loadStatus, setLoadStatus] = useState({});

  useEffect(() => {
    const loadDefaultSources = async () => {
      const status = {};

      try {
        const response = await fetch(DEFAULT_SOURCES.metrics);
        if (response.ok) {
          const text = await response.text();
          const records = parseJsonl(text);
          setMetrics(normalizeMetrics(records));
          status.metrics = 'loaded';
        } else {
          status.metrics = 'missing';
        }
      } catch (err) {
        status.metrics = 'missing';
      }

      try {
        const response = await fetch(DEFAULT_SOURCES.workflowSummaries);
        if (response.ok) {
          const data = await response.json();
          setWorkflowSummaries(data);
          status.workflowSummaries = 'loaded';
        } else {
          status.workflowSummaries = 'missing';
        }
      } catch (err) {
        status.workflowSummaries = 'missing';
      }

      try {
        const response = await fetch(DEFAULT_SOURCES.schedulerHealth);
        if (response.ok) {
          const data = await response.json();
          setSchedulerHealth(data);
          status.schedulerHealth = 'loaded';
        } else {
          status.schedulerHealth = 'missing';
        }
      } catch (err) {
        status.schedulerHealth = 'missing';
      }

      try {
        const response = await fetch(DEFAULT_SOURCES.queueState);
        if (response.ok) {
          const data = await response.json();
          setQueueState(normalizeQueueState(data));
          status.queueState = 'loaded';
        } else {
          status.queueState = 'missing';
        }
      } catch (err) {
        status.queueState = 'missing';
      }

      setLoadStatus(status);
    };

    loadDefaultSources();
  }, []);

  const taskIndex = useMemo(() => deriveTaskIndex(metrics, queueState), [metrics, queueState]);

  return (
    <div className="phase7-root">
      <header className="phase7-header">
        <div>
          <h1>Phase 7: Visual Workflow & Execution Observatory</h1>
          <p className="phase7-subtitle">Read-only observability layer. No execution or edits.</p>
        </div>
        <div className="phase7-badges">
          <span className="badge read-only">Read-Only</span>
          <span className="badge">Execution Agnostic</span>
        </div>
      </header>

      <DataSourcePanel
        loadStatus={loadStatus}
        onMetricsLoaded={(records) => setMetrics(normalizeMetrics(records))}
        onWorkflowSummariesLoaded={setWorkflowSummaries}
        onSchedulerHealthLoaded={setSchedulerHealth}
        onQueueStateLoaded={(state) => setQueueState(normalizeQueueState(state))}
      />

      <div className="phase7-grid">
        <SchedulerPanel
          metrics={metrics}
          schedulerHealth={schedulerHealth}
          taskIndex={taskIndex}
        />

        <WorkflowDagView
          queueState={queueState}
          taskIndex={taskIndex}
          metrics={metrics}
        />

        <BranchingView
          queueState={queueState}
          metrics={metrics}
        />

        <TimelineReplay
          metrics={metrics}
        />

        <RecoveryView
          queueState={queueState}
          metrics={metrics}
        />
      </div>
    </div>
  );
};

export default Phase7Observatory;
