import React, { useEffect, useMemo, useState } from 'react';
import './Phase8Authoring.css';
import AuthoringCanvas from './components/AuthoringCanvas';
import TaskPropertiesPanel from './components/TaskPropertiesPanel';
import SimulationTimeline from './components/SimulationTimeline';
import WorkflowSnapshotPanel from './components/WorkflowSnapshotPanel';
import ValidationEngine from './logic/ValidationEngine';
import SafeWorkflowExecutor from './logic/SafeWorkflowExecutor';
import ConfidenceOverlay from './logic/ConfidenceOverlay';
import WorkflowDagView from '../phase7/components/WorkflowDagView';
import BranchingView from '../phase7/components/BranchingView';
import TimelineReplay from '../phase7/components/TimelineReplay';

const DEFAULT_WORKFLOW = {
  id: 'workflow_sample',
  name: 'Sample Authoring Workflow',
  version: 'v1',
  nodes: [
    {
      id: 'task_a',
      title: 'Inspect site',
      tool: 'web_inspect',
      priority: 'HIGH',
      risk: 'LOW',
      retries: 1,
      confidence: 0.9,
      dependencies: [],
      position: { x: 60, y: 60 },
      branches: []
    },
    {
      id: 'task_b',
      title: 'Extract pricing',
      tool: 'web_extract',
      priority: 'MEDIUM',
      risk: 'LOW',
      retries: 1,
      confidence: 0.75,
      dependencies: ['task_a'],
      position: { x: 320, y: 60 },
      branches: [
        { condition: 'on_success', nextTaskId: 'task_c' },
        { condition: 'on_failure', nextTaskId: 'task_d' }
      ]
    },
    {
      id: 'task_c',
      title: 'Click upgrade',
      tool: 'web_click',
      priority: 'MEDIUM',
      risk: 'MEDIUM',
      retries: 2,
      confidence: 0.7,
      dependencies: ['task_b'],
      position: { x: 580, y: 20 },
      branches: []
    },
    {
      id: 'task_d',
      title: 'Fallback note',
      tool: 'reasoning_note',
      priority: 'LOW',
      risk: 'LOW',
      retries: 0,
      confidence: 0.6,
      dependencies: ['task_b'],
      position: { x: 580, y: 120 },
      branches: []
    }
  ]
};

const Phase8Authoring = () => {
  const [workflow, setWorkflow] = useState(DEFAULT_WORKFLOW);
  const [selectedTaskId, setSelectedTaskId] = useState('task_a');
  const [simulation, setSimulation] = useState(null);
  const [validation, setValidation] = useState({ errors: [], warnings: [] });
  const [snapshots, setSnapshots] = useState([]);
  const [activeSnapshotId, setActiveSnapshotId] = useState(null);

  useEffect(() => {
    const loadSnapshots = async () => {
      try {
        const response = await fetch('/workflow_snapshots.json');
        if (response.ok) {
          const data = await response.json();
          if (data?.snapshots) {
            setSnapshots(data.snapshots);
          }
        }
      } catch (err) {
        // ignore
      }
    };

    loadSnapshots();
  }, []);

  useEffect(() => {
    const result = ValidationEngine.validateWorkflow(workflow);
    setValidation(result);
  }, [workflow]);

  const selectedTask = useMemo(
    () => workflow.nodes.find(node => node.id === selectedTaskId),
    [workflow, selectedTaskId]
  );

  const handleNodeMove = (id, position) => {
    setWorkflow(prev => ({
      ...prev,
      nodes: prev.nodes.map(node => node.id === id ? { ...node, position } : node)
    }));
  };

  const handleTaskUpdate = (updatedTask) => {
    setWorkflow(prev => ({
      ...prev,
      nodes: prev.nodes.map(node => node.id === updatedTask.id ? updatedTask : node)
    }));
  };

  const handleSimulation = () => {
    const result = SafeWorkflowExecutor.simulate(workflow);
    setSimulation(result);
  };

  const handleSnapshotSave = (label) => {
    const snapshot = {
      id: `snapshot_${Date.now()}`,
      label,
      createdAt: new Date().toISOString(),
      workflow: JSON.parse(JSON.stringify(workflow))
    };
    const nextSnapshots = [snapshot, ...snapshots];
    setSnapshots(nextSnapshots);
    setActiveSnapshotId(snapshot.id);
    localStorage.setItem('buddy_workflow_snapshots', JSON.stringify(nextSnapshots));
  };

  const handleSnapshotLoad = (snapshotId) => {
    const snapshot = snapshots.find(item => item.id === snapshotId);
    if (snapshot) {
      setWorkflow(snapshot.workflow);
      setActiveSnapshotId(snapshot.id);
    }
  };

  const handleSnapshotImport = (importedSnapshots) => {
    setSnapshots(importedSnapshots);
  };

  const overlay = useMemo(() => ConfidenceOverlay.compute(workflow), [workflow]);

  return (
    <div className="phase8-root">
      <header className="phase8-header">
        <div>
          <h1>Phase 8: Workflow Authoring (Read-Only Execution)</h1>
          <p>Design and simulate workflows. No execution or tool dispatch.</p>
        </div>
        <div className="phase8-badges">
          <span className="badge read-only">Dry-Run Only</span>
          <span className="badge">No Execution</span>
        </div>
      </header>

      <div className="phase8-body">
        <div className="phase8-canvas">
          <AuthoringCanvas
            workflow={workflow}
            selectedTaskId={selectedTaskId}
            onSelectTask={setSelectedTaskId}
            onNodeMove={handleNodeMove}
            overlay={overlay}
          />
        </div>

        <div className="phase8-sidebar">
          <TaskPropertiesPanel
            task={selectedTask}
            workflow={workflow}
            onChange={handleTaskUpdate}
            validation={validation}
          />
          <WorkflowSnapshotPanel
            snapshots={snapshots}
            activeSnapshotId={activeSnapshotId}
            onSave={handleSnapshotSave}
            onLoad={handleSnapshotLoad}
            onImport={handleSnapshotImport}
          />
        </div>
      </div>

      <div className="phase8-panels">
        <SimulationTimeline
          simulation={simulation}
          onRunSimulation={handleSimulation}
          validation={validation}
        />
        <div className="panel">
          <div>
            <h2>Observatory Continuity (Read-Only)</h2>
            <div className="panel-subtitle">Phase 7 views embedded for continuity.</div>
            <div className="read-only-label">READ-ONLY</div>
          </div>
          <div className="phase8-observatory-grid">
            <WorkflowDagView
              queueState={{ tasks: workflow.nodes.map(node => ({
                id: node.id,
                description: node.title,
                status: 'pending',
                priority: node.priority,
                risk_level: node.risk,
                confidence_score: node.confidence,
                dependencies: node.dependencies.map(dep => ({ task_id: dep })),
                conditional_branches: node.branches || [],
                attempt_count: node.retries,
                metadata: { approval_outcome: node.approval } }
              )) }}
              taskIndex={[]}
              metrics={[]}
            />
            <BranchingView queueState={{ tasks: workflow.nodes.map(node => ({
              id: node.id,
              conditional_branches: node.branches || []
            })) }} metrics={simulation?.timeline || []} />
            <TimelineReplay metrics={simulation?.timeline || []} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Phase8Authoring;
