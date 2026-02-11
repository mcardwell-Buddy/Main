import React, { useEffect, useState } from 'react';
import './MissionVisualizer.css';

const MissionVisualizer = ({ missionId, onAction }) => {
  const [status, setStatus] = useState('idle');
  const [events, setEvents] = useState([]);
  const [objective, setObjective] = useState('');
  const [progress, setProgress] = useState(null);
  const [currentStep, setCurrentStep] = useState('');
  const [toolName, setToolName] = useState('');
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    if (!missionId) return undefined;

    setStatus('connecting');
    setEvents([]);
    setObjective('');
    setProgress(null);
    setCurrentStep('');
    setToolName('');
    setPreview(null);

    console.log(`[MissionVisualizer] Connecting to ws://localhost:8000/ws/stream/${missionId}`);
    const ws = new WebSocket(`ws://localhost:8000/ws/stream/${missionId}`);

    ws.onopen = () => {
      console.log(`[MissionVisualizer] WebSocket connected for mission ${missionId}`);
      setStatus('connected');
    };
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        console.log(`[MissionVisualizer] Received event: ${data.event_type}`, data);
        setEvents(prev => [...prev, data]);

        if (data.event_type === 'mission_start') {
          setObjective(data.data?.objective || '');
        }
        if (data.event_type === 'execution_step') {
          setProgress(data.data?.progress_percent ?? null);
          setCurrentStep(data.data?.message || data.data?.step_name || '');
        }
        if (data.event_type === 'tool_invoked') {
          setToolName(data.data?.tool_name || '');
        }
        if (data.event_type === 'tool_result' && data.data?.details) {
          setPreview(data.data.details);
        }
        if (data.event_type === 'artifact_preview' && data.data?.preview) {
          setPreview(data.data.preview);
        }
      } catch (e) {
        console.error(`[MissionVisualizer] Failed to parse message:`, evt.data, e);
      }
    };
    ws.onerror = (err) => {
      const errorMsg = err instanceof Event ? 'WebSocket connection error' : String(err);
      console.error(`[MissionVisualizer] WebSocket error for mission ${missionId}:`, errorMsg, err);
      setStatus('error');
    };
    ws.onclose = () => {
      console.log(`[MissionVisualizer] WebSocket closed for mission ${missionId}`);
      setStatus('closed');
    };

    return () => ws.close();
  }, [missionId]);

  if (!missionId) return null;

  return (
    <div className="mission-visualizer">
      <div className="mv-header">
        <div className="mv-title">Mission Visualizer</div>
        <span className={`mv-status mv-${status}`}>{status}</span>
      </div>

      {objective && <div className="mv-objective">{objective}</div>}

      {progress !== null && (
        <div className="mv-progress">
          <div className="mv-bar">
            <div className="mv-fill" style={{ width: `${progress}%` }} />
          </div>
          <span>{progress}%</span>
        </div>
      )}

      {currentStep && <div className="mv-step">{currentStep}</div>}
      {toolName && <div className="mv-tool">Tool: {toolName}</div>}

      <div className="mv-preview">
        {!preview && <div className="mv-empty">Waiting for live dataâ€¦</div>}

        {preview?.type === 'web_extraction' && (
          <div className="mv-sections">
            {(preview.sections || preview.items_preview || []).map((s, i) => (
              <div key={`${s.title || 'section'}-${i}`} className="mv-section">
                <div className="mv-section-title">{s.title || 'Section'}</div>
                <div className="mv-section-text">{s.text || s.snippet || ''}</div>
              </div>
            ))}
          </div>
        )}

        {preview?.type === 'web_search' && (
          <ul className="mv-list">
            {(preview.results || preview.items_preview || []).map((r, i) => (
              <li key={`${r.title || r.url || 'result'}-${i}`}>
                <div className="mv-list-title">{r.title || r.name}</div>
                <div className="mv-list-snippet">{r.snippet || r.url}</div>
              </li>
            ))}
          </ul>
        )}

        {preview?.type === 'calculation' && (
          <div className="mv-calc">
            <div>{preview.expression}</div>
            <strong>{preview.result}</strong>
          </div>
        )}

        {preview?.type === 'web_navigation' && (
          <div className="mv-nav">
            <div>{preview.title}</div>
            <div>{preview.url}</div>
          </div>
        )}

        {preview?.type === 'generic' && (
          <pre className="mv-json">{JSON.stringify(preview, null, 2)}</pre>
        )}
      </div>

      <div className="mv-note">
        â„¹ï¸ Mission data complete. Let Buddy know what you'd like to do next.
      </div>
    </div>
  );
};

export default MissionVisualizer;
