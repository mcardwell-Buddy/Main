import React, { useMemo, useState } from 'react';

const buildDag = (tasks) => {
  const nodes = tasks.map(task => ({
    id: task.id,
    title: task.description || task.id,
    status: task.status || 'unknown',
    risk: task.risk_level || 'low',
    priority: task.priority || 'MEDIUM',
    retries: task.attempt_count || 0,
    confidence: task.confidence_score ?? null,
    approval: task.metadata?.approval_outcome,
    dependencies: task.dependencies || []
  }));

  const nodeMap = new Map(nodes.map(n => [n.id, n]));

  const edges = [];
  nodes.forEach(node => {
    (node.dependencies || []).forEach(dep => {
      if (nodeMap.has(dep)) {
        edges.push({ from: dep, to: node.id });
      }
    });
  });

  return { nodes, edges };
};

const computeLayout = (nodes, edges) => {
  const depth = new Map();
  const incoming = new Map();

  nodes.forEach(node => {
    incoming.set(node.id, 0);
  });
  edges.forEach(edge => {
    incoming.set(edge.to, (incoming.get(edge.to) || 0) + 1);
  });

  const queue = nodes.filter(node => (incoming.get(node.id) || 0) === 0).map(n => n.id);
  queue.forEach(id => depth.set(id, 0));

  while (queue.length) {
    const current = queue.shift();
    const currentDepth = depth.get(current) || 0;
    edges.filter(edge => edge.from === current).forEach(edge => {
      const nextDepth = Math.max(depth.get(edge.to) || 0, currentDepth + 1);
      depth.set(edge.to, nextDepth);
      incoming.set(edge.to, (incoming.get(edge.to) || 1) - 1);
      if (incoming.get(edge.to) === 0) {
        queue.push(edge.to);
      }
    });
  }

  const columns = {};
  nodes.forEach(node => {
    const col = depth.get(node.id) || 0;
    if (!columns[col]) columns[col] = [];
    columns[col].push(node.id);
  });

  const positions = {};
  Object.entries(columns).forEach(([col, ids]) => {
    ids.forEach((id, idx) => {
      positions[id] = {
        x: parseInt(col, 10) * 220,
        y: idx * 120
      };
    });
  });

  return positions;
};

const WorkflowDagView = ({ queueState, taskIndex, metrics }) => {
  const [zoom, setZoom] = useState(1);

  const data = useMemo(() => {
    const tasks = queueState?.tasks || taskIndex || [];
    return buildDag(tasks);
  }, [queueState, taskIndex]);

  const layout = useMemo(() => computeLayout(data.nodes, data.edges), [data]);

  return (
    <div className="panel">
      <div>
        <h2>Workflow DAG (Read-Only)</h2>
        <div className="panel-subtitle">Nodes = tasks, edges = dependencies</div>
        <div className="read-only-label">READ-ONLY</div>
      </div>

      <div className="overlay-row">
        <label className="small-text">Zoom</label>
        <input
          type="range"
          min="0.6"
          max="1.6"
          step="0.1"
          value={zoom}
          onChange={(e) => setZoom(parseFloat(e.target.value))}
        />
      </div>

      <div className="dag-container">
        <svg className="dag-stage" style={{ transform: `scale(${zoom})` }} width="1200" height="600">
          {data.edges.map((edge, idx) => {
            const from = layout[edge.from];
            const to = layout[edge.to];
            if (!from || !to) return null;
            return (
              <line
                key={`${edge.from}-${edge.to}-${idx}`}
                className="dag-edge"
                x1={from.x + 160}
                y1={from.y + 30}
                x2={to.x}
                y2={to.y + 30}
              />
            );
          })}
        </svg>
        <div className="dag-stage" style={{ transform: `scale(${zoom})` }}>
          {data.nodes.map(node => {
            const pos = layout[node.id] || { x: 0, y: 0 };
            return (
              <div
                key={node.id}
                className="dag-node"
                style={{ left: pos.x, top: pos.y, borderColor: node.risk === 'HIGH' ? '#f87171' : '#334155' }}
              >
                <div className="node-title">{node.title}</div>
                <div className="overlay-row">
                  <span className={`tag status-${node.status}`}>{node.status}</span>
                  <span className={`tag ${node.risk?.toLowerCase()}`}>{node.risk}</span>
                </div>
                <div className="small-text">Retries: {node.retries}</div>
                <div className="small-text">Confidence: {node.confidence?.toFixed(2) ?? 'n/a'}</div>
                <div className="small-text">Approval: {node.approval || 'n/a'}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default WorkflowDagView;
