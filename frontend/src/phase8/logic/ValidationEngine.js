const ValidationEngine = {
  validateWorkflow(workflow) {
    const errors = [];
    const warnings = [];

    const ids = new Set(workflow.nodes.map(node => node.id));

    workflow.nodes.forEach(node => {
      (node.dependencies || []).forEach(dep => {
        if (!ids.has(dep)) {
          warnings.push(`Task ${node.id} depends on missing task ${dep}.`);
        }
      });
    });

    // Cycle detection (DFS)
    const visited = new Set();
    const stack = new Set();

    const visit = (nodeId) => {
      if (stack.has(nodeId)) {
        errors.push(`Circular dependency detected at ${nodeId}.`);
        return;
      }
      if (visited.has(nodeId)) return;

      visited.add(nodeId);
      stack.add(nodeId);
      const node = workflow.nodes.find(n => n.id === nodeId);
      if (node) {
        (node.dependencies || []).forEach(dep => visit(dep));
      }
      stack.delete(nodeId);
    };

    workflow.nodes.forEach(node => visit(node.id));

    // Branch validation
    workflow.nodes.forEach(node => {
      (node.branches || []).forEach(branch => {
        if (!branch.condition || !branch.nextTaskId) {
          warnings.push(`Task ${node.id} has an invalid branch entry.`);
        }
      });
    });

    return { errors, warnings };
  }
};

export default ValidationEngine;
