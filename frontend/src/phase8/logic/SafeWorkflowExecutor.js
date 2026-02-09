const SafeWorkflowExecutor = {
  simulate(workflow) {
    const nodes = workflow.nodes;
    const nodeMap = new Map(nodes.map(node => [node.id, node]));
    const timeline = [];

    const completed = new Set();
    const failed = new Set();

    const pending = new Set(nodes.map(node => node.id));
    let guard = 0;

    while (pending.size > 0 && guard < 1000) {
      guard += 1;
      let progressed = false;

      for (const nodeId of Array.from(pending)) {
        const node = nodeMap.get(nodeId);
        const depsSatisfied = (node.dependencies || []).every(dep => completed.has(dep));
        if (!depsSatisfied) continue;

        const threshold = 0.7;
        let status = 'completed';
        let retries = 0;

        if (node.confidence < threshold) {
          if (node.retries > 0 && node.confidence >= threshold * 0.9) {
            retries = 1;
            status = 'completed';
          } else {
            status = 'failed';
          }
        }

        const branch = node.branches?.find(branch => {
          if (branch.condition === 'on_success') return status === 'completed';
          if (branch.condition === 'on_failure') return status === 'failed';
          return false;
        });

        if (status === 'completed') {
          completed.add(nodeId);
        } else {
          failed.add(nodeId);
        }

        pending.delete(nodeId);
        progressed = true;

        timeline.push({
          task_id: nodeId,
          execution_result: status,
          retries,
          confidence_score: node.confidence,
          branch: branch ? `${branch.condition} -> ${branch.nextTaskId}` : null,
          timestamp: new Date().toISOString(),
          execution_time_ms: 200 + retries * 100
        });
      }

      if (!progressed) break;
    }

    return {
      summary: `Simulated ${timeline.length} tasks`,
      timeline
    };
  }
};

export default SafeWorkflowExecutor;
