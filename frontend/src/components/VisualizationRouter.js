import React from 'react';

/**
 * VisualizationRouter: Smart component selection based on artifact type and visualization strategy
 * 
 * Maps visualization strategies from ResultPresenter to appropriate React components
 * Handles:
 * - Table data (with sorting, filtering, pagination)
 * - Charts (bar, line, pie, scatter)
 * - Documents (markdown, HTML)
 * - Timelines
 * - Code blocks
 * - Raw JSON viewer
 * - Mixed/multiple visualizations
 */
const VisualizationRouter = ({ artifact, visualizationStrategy, data }) => {
  if (!artifact || !visualizationStrategy) {
    return <div className="visualization-error">No visualization strategy available</div>;
  }

  const primaryType = visualizationStrategy.primary_type;
  const config = visualizationStrategy.config || {};

  const containerStyle = {
    minHeight: visualizationStrategy.suggested_height || 'auto',
    maxHeight:
      visualizationStrategy.suggested_height === 'auto'
        ? 'none'
        : visualizationStrategy.suggested_height
  };

  const renderComponent = (type, data) => {
    switch (type) {
      case 'table':
        return <TableVisualization data={data} config={config} />;
      case 'chart':
        return <ChartVisualization data={data} config={config} />;
      case 'document':
        return <DocumentVisualization data={data} config={config} />;
      case 'timeline':
        return <TimelineVisualization data={data} config={config} />;
      case 'code':
        return <CodeVisualization data={data} config={config} />;
      case 'json':
        return <JSONVisualization data={data} config={config} />;
      case 'gallery':
        return <GalleryVisualization data={data} config={config} />;
      default:
        return <RawDataVisualization data={data} />;
    }
  };

  return (
    <div className="visualization-container" style={containerStyle}>
      <div className="visualization-wrapper">
        {primaryType === 'mixed' ? (
          <div className="mixed-visualizations">
            {visualizationStrategy.secondary_types &&
              visualizationStrategy.secondary_types.length > 0 &&
              visualizationStrategy.secondary_types.map((type, idx) => (
                <div key={idx} className="visualization-section">
                  {renderComponent(type, data)}
                </div>
              ))}
            <div className="visualization-section">
              {renderComponent(primaryType, data)}
            </div>
          </div>
        ) : (
          <>
            {renderComponent(primaryType, data)}
            {visualizationStrategy.secondary_types &&
              visualizationStrategy.secondary_types.length > 0 && (
                <div className="secondary-visualizations">
                  {visualizationStrategy.secondary_types.map((type, idx) => (
                    <details key={idx} className="secondary-viz">
                      <summary>View as {type}</summary>
                      <div className="secondary-viz-content">
                        {renderComponent(type, data)}
                      </div>
                    </details>
                  ))}
                </div>
              )}
          </>
        )}
      </div>

      {visualizationStrategy.export_formats &&
        visualizationStrategy.export_formats.length > 0 && (
          <div className="export-options">
            <span className="export-label">Export as:</span>
            {visualizationStrategy.export_formats.map((format, idx) => (
              <button key={idx} className="export-btn" onClick={() => handleExport(format, data)}>
                {format}
              </button>
            ))}
          </div>
        )}
    </div>
  );
};

/**
 * TableVisualization: Renders tabular data
 */
const TableVisualization = ({ data, config }) => {
  if (!data || !data.columns || !data.rows) {
    return <div>No tabular data available</div>;
  }

  const [sortCol, setSortCol] = React.useState(null);
  const [sortDir, setSortDir] = React.useState('asc');
  const [filterText, setFilterText] = React.useState('');
  const [currentPage, setCurrentPage] = React.useState(0);

  const pageSize = config.page_size || 25;

  const filteredRows = filterText
    ? data.rows.filter((row) =>
        row.some((cell) => String(cell).toLowerCase().includes(filterText.toLowerCase()))
      )
    : data.rows;

  const sortedRows =
    sortCol !== null
      ? [...filteredRows].sort((a, b) => {
          const aVal = a[sortCol];
          const bVal = b[sortCol];
          const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
          return sortDir === 'asc' ? cmp : -cmp;
        })
      : filteredRows;

  const paginatedRows =
    config.paginated !== false
      ? sortedRows.slice(currentPage * pageSize, (currentPage + 1) * pageSize)
      : sortedRows;

  const totalPages = Math.ceil(sortedRows.length / pageSize);

  return (
    <div className="table-visualization">
      {config.filterable && (
        <input
          type="text"
          placeholder="Filter..."
          value={filterText}
          onChange={(e) => {
            setFilterText(e.target.value);
            setCurrentPage(0);
          }}
          className="table-filter"
        />
      )}

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              {data.columns.map((col, idx) => (
                <th
                  key={idx}
                  onClick={() => {
                    if (config.sortable) {
                      if (sortCol === idx) {
                        setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
                      } else {
                        setSortCol(idx);
                        setSortDir('asc');
                      }
                    }
                  }}
                  style={{ cursor: config.sortable ? 'pointer' : 'default' }}
                >
                  {col}
                  {config.sortable && sortCol === idx && (
                    <span style={{ marginLeft: '4px' }}>{sortDir === 'asc' ? '▲' : '▼'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedRows.map((row, idx) => (
              <tr key={idx}>
                {row.map((cell, jdx) => (
                  <td key={jdx}>{String(cell)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {config.paginated && totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
            disabled={currentPage === 0}
          >
            Prev
          </button>
          <span>
            Page {currentPage + 1} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
            disabled={currentPage === totalPages - 1}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

/**
 * ChartVisualization: Renders charts (bar, line, pie, scatter)
 * Note: This is a placeholder. In production, integrate with recharts, chart.js, or similar
 */
const ChartVisualization = ({ data, config }) => {
  return (
    <div className="chart-visualization">
      <div className="chart-placeholder">
        Chart visualization requires chart library integration. Data keys: {Object.keys(data).join(', ')}
      </div>
    </div>
  );
};

/**
 * DocumentVisualization: Renders formatted document (markdown, HTML)
 */
const DocumentVisualization = ({ data, config }) => {
  if (!data || !data.sections) {
    return <div>No document data available</div>;
  }

  return (
    <div className="document-visualization">
      {data.sections.map((section, idx) => (
        <div key={idx} className="document-section">
          {section.heading && <h3>{section.heading}</h3>}
          <div className="document-content">{section.content}</div>
        </div>
      ))}
    </div>
  );
};

/**
 * TimelineVisualization: Renders timeline of events
 */
const TimelineVisualization = ({ data, config }) => {
  if (!data || !data.events) {
    return <div>No timeline data available</div>;
  }

  return (
    <div className="timeline-visualization">
      {data.events.map((event, idx) => (
        <div key={idx} className="timeline-event">
          <div className="timeline-dot"></div>
          <div className="timeline-content">
            <div className="timeline-time">{event.timestamp}</div>
            <div className="timeline-event-name">{event.event}</div>
            {event.status && <div className="timeline-status">{event.status}</div>}
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * CodeVisualization: Renders code with syntax highlighting
 */
const CodeVisualization = ({ data, config }) => {
  if (!data || !data.code) {
    return <div>No code data available</div>;
  }

  return (
    <div className="code-visualization">
      <pre>
        <code className={`language-${data.language || 'text'}`}>{data.code}</code>
      </pre>
    </div>
  );
};

/**
 * JSONVisualization: Renders raw JSON with expandable nodes
 */
const JSONVisualization = ({ data, config }) => {
  return (
    <div className="json-visualization">
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};

/**
 * GalleryVisualization: Renders image gallery
 */
const GalleryVisualization = ({ data, config }) => {
  if (!Array.isArray(data)) {
    return <div>No gallery data available</div>;
  }

  return (
    <div className="gallery-visualization">
      {data.map((item, idx) => (
        <img
          key={idx}
          src={item.src || item}
          alt={item.alt || `Image ${idx + 1}`}
          className="gallery-image"
        />
      ))}
    </div>
  );
};

/**
 * RawDataVisualization: Fallback for unknown data types
 */
const RawDataVisualization = ({ data }) => {
  return (
    <div className="raw-data-visualization">
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};

const handleExport = (format, data) => {
  console.log(`Exporting as ${format}:`, data);
  // TODO: Implement export functionality
};

export default VisualizationRouter;
