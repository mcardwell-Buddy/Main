import React, { useMemo } from 'react';

const extractBranches = (queueState) => {
  if (!queueState?.tasks) return [];
  const branches = [];

  queueState.tasks.forEach(task => {
    if (task.conditional_branches && task.conditional_branches.length > 0) {
      task.conditional_branches.forEach(branch => {
        branches.push({
          taskId: task.id,
          condition: branch.condition_type,
          value: branch.condition_value,
          nextTaskId: branch.next_task_id,
          template: branch.next_task_template
        });
      });
    }
  });

  return branches;
};

const BranchingView = ({ queueState, metrics }) => {
  const branches = useMemo(() => extractBranches(queueState), [queueState]);
  const recentMetrics = metrics.slice(-6);

  return (
    <div className="panel">
      <div>
        <h2>Conditional Branching</h2>
        <div className="panel-subtitle">Read-only view of branch conditions and outcomes.</div>
        <div className="read-only-label">READ-ONLY</div>
      </div>

      {branches.length === 0 ? (
        <div className="small-text">No explicit branch metadata found in queue snapshots.</div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Task</th>
              <th>Condition</th>
              <th>Next Task</th>
            </tr>
          </thead>
          <tbody>
            {branches.map((branch, idx) => (
              <tr key={`${branch.taskId}-${idx}`}>
                <td>{branch.taskId}</td>
                <td>{branch.condition} {branch.value ? `= ${branch.value}` : ''}</td>
                <td>{branch.nextTaskId || 'template'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div>
        <div className="small-text">Recent branch-adjacent decisions</div>
        <table className="table">
          <thead>
            <tr>
              <th>Task</th>
              <th>Confidence</th>
              <th>Approval</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {recentMetrics.map((item, idx) => (
              <tr key={`${item.task_id}-${idx}`}>
                <td>{item.task_id}</td>
                <td>{item.confidence_score?.toFixed(2)}</td>
                <td>{item.approval_outcome}</td>
                <td>{item.execution_result}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default BranchingView;
