import React, { useEffect, useState } from 'react';
import './MissionTimeline.css';

const formatTime = (iso) => {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return '';
  }
};

const getProgressFromEvent = (event) => {
  const percent = event?.data?.progress_percent;
  if (typeof percent === 'number') return Math.max(0, Math.min(100, percent));
  return null;
};

const getStepLabel = (event) => {
  const data = event?.data || {};
  if (data.message) return data.message;
  if (data.current_step) return data.current_step;
  if (data.step_name) return `${data.step_name} (${data.step_status || 'in_progress'})`;
  return event?.event_type || 'update';
};

const MissionTimeline = ({ missionId }) => {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState('idle');

  useEffect(() => {
    if (!missionId) return undefined;

    setEvents([]);
    setStatus('connecting');

    const ws = new WebSocket(`ws://localhost:8000/ws/stream/${missionId}`);

    ws.onopen = () => setStatus('connected');
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        setEvents(prev => [...prev, data]);
      } catch {
        // ignore malformed
      }
    };
    ws.onerror = () => setStatus('error');
    ws.onclose = () => setStatus('closed');

    return () => ws.close();
  }, [missionId]);

  if (!missionId) {
    return (
      <div className="mission-timeline empty">
        <div className="mission-title">Mission Timeline</div>
        <div className="mission-empty">No active mission stream</div>
      </div>
    );
  }

  const lastEvent = events[events.length - 1];
  const progress = getProgressFromEvent(lastEvent);

  return (
    <div className="mission-timeline">
      <div className="mission-title">
        Mission Timeline
        <span className={`mission-status status-${status}`}>{status}</span>
      </div>
      <div className="mission-id">{missionId}</div>

      {progress !== null && (
        <div className="mission-progress">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <span className="progress-label">{progress}%</span>
        </div>
      )}

      <div className="mission-current">
        {getStepLabel(lastEvent)}
      </div>

      <details className="mission-log">
        <summary>Event log ({events.length})</summary>
        <div className="mission-log-items">
          {events.map((event, idx) => (
            <div key={`${event.sequence_number || idx}`} className="mission-log-item">
              <span className="mission-log-time">{formatTime(event.timestamp)}</span>
              <span className="mission-log-type">{event.event_type}</span>
              <span className="mission-log-msg">{getStepLabel(event)}</span>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
};

export default MissionTimeline;
