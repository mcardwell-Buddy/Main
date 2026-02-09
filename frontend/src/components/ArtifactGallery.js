import React from 'react';
import './ArtifactGallery.css';

const ArtifactPreviewCard = ({ preview }) => {
  if (!preview) return null;
  const type = preview.type || 'generic';
  const summary = preview.summary || '';
  const items = preview.items_preview || [];

  return (
    <div className={`artifact-preview-card type-${type}`}>
      <div className="artifact-preview-type">{type.replace('_', ' ')}</div>
      <div className="artifact-preview-summary">{summary}</div>
      {items.length > 0 && (
        <ul className="artifact-preview-items">
          {items.map((item, index) => (
            <li key={`${type}-${index}`}>
              {item.title || item.url || item.text || item.value || 'Item'}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

const ArtifactGallery = ({ items = [] }) => {
  if (!items.length) {
    return (
      <div className="artifact-gallery empty">
        <div className="artifact-gallery-title">Artifact Gallery</div>
        <div className="artifact-gallery-empty">No artifacts yet</div>
      </div>
    );
  }

  return (
    <div className="artifact-gallery">
      <div className="artifact-gallery-title">Artifact Gallery</div>
      <div className="artifact-gallery-grid">
        {items.map((item) => (
          <div key={item.mission_id} className="artifact-gallery-card">
            <div className="artifact-gallery-header">
              <div className="artifact-gallery-objective">
                {item.objective_description || 'Mission'}
              </div>
              <div className={`artifact-gallery-status status-${item.status || 'unknown'}`}>
                {item.status || 'unknown'}
              </div>
            </div>
            <div className="artifact-gallery-previews">
              {(item.artifacts || []).map((artifact) => (
                <ArtifactPreviewCard
                  key={artifact.artifact_id || Math.random().toString(36)}
                  preview={artifact.preview}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ArtifactGallery;
