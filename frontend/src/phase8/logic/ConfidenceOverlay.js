const ConfidenceOverlay = {
  compute(workflow) {
    const overlay = {};
    workflow.nodes.forEach(node => {
      let status = 'pending';
      let warning = null;

      if (node.confidence < 0.55) {
        status = 'deferred';
        warning = 'Low confidence - likely needs clarification';
      } else if (node.confidence < 0.7) {
        status = 'pending';
        warning = 'Medium confidence - approval recommended';
      } else {
        status = 'completed';
      }

      if (node.risk === 'HIGH') {
        warning = 'High-risk task - requires explicit approval';
      }

      overlay[node.id] = { status, warning };
    });

    return overlay;
  }
};

export default ConfidenceOverlay;
