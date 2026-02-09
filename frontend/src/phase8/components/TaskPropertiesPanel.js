import React from 'react';

const TaskPropertiesPanel = ({ task, workflow, onChange, validation }) => {
  if (!task) {
    return (
      <div className="panel properties-panel">
        <h2>Task Properties</h2>
        <div className="panel-subtitle">Select a task to edit.</div>
      </div>
    );
  }

  const updateField = (field, value) => {
    onChange({ ...task, [field]: value });
  };

  return (
    <div className="panel properties-panel">
      <div>
        <h2>Task Properties</h2>
        <div className="panel-subtitle">Read-only execution. Editing is safe.</div>
      </div>

      {validation.errors.length > 0 && (
        <div className="validation-banner error">
          {validation.errors.slice(0, 2).map((err, idx) => (
            <div key={idx}>{err}</div>
          ))}
        </div>
      )}
      {validation.warnings.length > 0 && (
        <div className="validation-banner warning">
          {validation.warnings.slice(0, 2).map((warn, idx) => (
            <div key={idx}>{warn}</div>
          ))}
        </div>
      )}

      <label>Title</label>
      <input value={task.title} onChange={(e) => updateField('title', e.target.value)} />

      <label>Tool</label>
      <input value={task.tool} onChange={(e) => updateField('tool', e.target.value)} />

      <label>Priority</label>
      <select value={task.priority} onChange={(e) => updateField('priority', e.target.value)}>
        <option>CRITICAL</option>
        <option>HIGH</option>
        <option>MEDIUM</option>
        <option>LOW</option>
        <option>BACKGROUND</option>
      </select>

      <label>Risk</label>
      <select value={task.risk} onChange={(e) => updateField('risk', e.target.value)}>
        <option>LOW</option>
        <option>MEDIUM</option>
        <option>HIGH</option>
      </select>

      <label>Retries</label>
      <input
        type="number"
        min="0"
        value={task.retries}
        onChange={(e) => updateField('retries', Number(e.target.value))}
      />

      <label>Confidence</label>
      <input
        type="number"
        min="0"
        max="1"
        step="0.05"
        value={task.confidence}
        onChange={(e) => updateField('confidence', Number(e.target.value))}
      />

      <label>Dependencies (comma-separated task IDs)</label>
      <input
        value={task.dependencies.join(', ')}
        onChange={(e) => updateField('dependencies', e.target.value.split(',').map(v => v.trim()).filter(Boolean))}
      />

      <label>Branches (JSON array)</label>
      <textarea
        rows="3"
        value={JSON.stringify(task.branches || [])}
        onChange={(e) => {
          try {
            const parsed = JSON.parse(e.target.value);
            updateField('branches', parsed);
          } catch (err) {
            // ignore invalid json
          }
        }}
      />

      {task.risk === 'HIGH' && (
        <div className="validation-banner warning">High-risk task: requires explicit approval for live execution (not available here).</div>
      )}
    </div>
  );
};

export default TaskPropertiesPanel;
