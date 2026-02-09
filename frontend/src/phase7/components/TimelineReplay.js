import React, { useMemo } from 'react';

const TimelineReplay = ({ metrics }) => {
  const timeline = useMemo(() => {
    return [...metrics]
      .filter(item => item.timestamp)
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      .map(item => ({
        ...item,
        duration: Math.max(1, Math.round(item.execution_time_ms || 0))
      }));
  }, [metrics]);

  const maxDuration = Math.max(1, ...timeline.map(item => item.duration));

  return (
    <div className="panel">
      <div>
        <h2>Execution Timeline (Replay)</h2>
        <div className="panel-subtitle">Read-only replay of task order and durations.</div>
        <div className="read-only-label">READ-ONLY</div>
      </div>

      {timeline.length === 0 ? (
        <div className="small-text">No timeline data loaded.</div>
      ) : (
        <div className="panel-grid">
          {timeline.slice(-15).map((item, idx) => (
            <div key={`${item.task_id}-${idx}`} className="timeline-row">
              <div className="small-text">{item.task_id || 'n/a'}</div>
              <div className={`timeline-bar ${item.execution_result === 'failed' ? 'failed' : ''}`}>
                <span style={{ width: `${(item.duration / maxDuration) * 100}%` }}></span>
              </div>
              <div className="small-text">{item.duration} ms</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TimelineReplay;
