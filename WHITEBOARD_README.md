# Buddy Whiteboard System

## Overview

The Buddy Whiteboard is a comprehensive real-time dashboard that displays critical metrics from Buddy's core systems. It aggregates data from multiple sources and presents it in an intuitive, interactive interface.

## Features

### 1. **API Usage Panel** 📡
- Total API requests
- Average latency
- Endpoint-level statistics
- Sortable by count or latency

### 2. **Costing Panel** 💰
- SerpAPI search usage (monthly quota tracking)
- OpenAI costs (token usage and dollar spend)
- Firestore costs (operations and dollar spend)
- Total spend summary

### 3. **Income Panel** 💵
- Gigs recommended
- Gigs hired (conversion tracking)
- Invoices received
- Conversion rate calculation
- Potential income estimates

### 4. **Tool Confidence Panel** 🎯
- Per-tool confidence percentages
- Selection frequency (% of missions using each tool)
- Confidence variation (consistency tracking)
- Sortable by confidence, selection, or variation

### 5. **Response Times Panel** ⚡
- Average latency
- P50 (median) latency
- P95 (95th percentile) latency
- Visual bar chart
- Health level indicators

### 6. **Session Stats Panel** 💬
- Total conversation sessions
- Total messages (sent/received)
- Per-session message counts
- Recent activity tracking
- Multi-source support (web, Telegram, etc.)

### 7. **Artifacts Panel** 🎨
- Artifact type breakdown (tables, charts, documents, code blocks, timelines, etc.)
- Visual bar chart with percentages
- Total artifact count
- Recent artifacts list

### 8. **Date Range Picker**
- Configurable time ranges (7, 30, 90, 180, 365 days)
- Default: 90 days
- Applies to most panels

## Architecture

### Backend Components

#### 1. **whiteboard_metrics.py**
Central aggregator for all whiteboard data.

**Functions:**
- `collect_api_usage(days)` - Aggregates API call data from `outputs/phase25/api_usage.jsonl`
- `collect_costing(days)` - Sums budget data from `data/budgets.jsonl`
- `collect_income(days)` - Parses revenue signals from `outputs/phase25/revenue_signals.jsonl`
- `collect_tool_confidence(days)` - Queries mission_store for tool execution stats
- `collect_response_times(days)` - Calculates latency percentiles from API logs
- `collect_session_stats()` - Summarizes conversation session data
- `collect_artifacts(days)` - Counts artifacts by type from `outputs/phase25/artifacts.jsonl`
- `collect_whiteboard_summary(days)` - **Master aggregator** - combines all metrics

**Data Sources:**
- `data/budgets.jsonl` (SerpAPI, OpenAI, Firestore costs)
- `outputs/phase25/api_usage.jsonl` (API call logs with latency)
- `outputs/phase25/revenue_signals.jsonl` (gigs, invoices)
- `outputs/phase25/artifacts.jsonl` (generated artifacts)
- Firebase Firestore: `missions` collection (tool_used, tool_confidence)
- Firebase Firestore: `conversation_sessions` collection (messages)

#### 2. **main.py Endpoints**

**Primary Endpoint:**
```http
GET /api/whiteboard/metrics?days=90
```
Returns complete metrics summary for all panels.

**Individual Panel Endpoints:**
```http
GET /api/whiteboard/metrics/api-usage?days=90
GET /api/whiteboard/metrics/costing?days=90
GET /api/whiteboard/metrics/income?days=90
GET /api/whiteboard/metrics/tool-confidence?days=90
GET /api/whiteboard/metrics/response-times?days=90
GET /api/whiteboard/metrics/session-stats
GET /api/whiteboard/metrics/artifacts?days=90
```

**API Usage Middleware:**
- Logs every HTTP request to `outputs/phase25/api_usage.jsonl`
- Records: timestamp, method, path, status_code, duration_ms, user_id

### Frontend Components

#### React Component Structure
```
Front_End/src/
├── App.js                                    # Main app with routing
├── App.css                                   # Global app styles
├── index.js                                  # Entry point
├── index.css                                 # Base styles
└── components/
    └── Whiteboard/
        ├── Whiteboard.jsx                    # Main whiteboard container
        ├── Whiteboard.css                    # Whiteboard styles
        ├── DateRangePicker.jsx               # Date range selector
        └── panels/
            ├── ApiUsagePanel.jsx             # API usage display
            ├── CostingPanel.jsx              # Costing breakdown
            ├── IncomePanel.jsx               # Income metrics
            ├── ToolConfidencePanel.jsx       # Tool confidence table
            ├── ResponseTimesPanel.jsx        # Latency metrics
            ├── SessionStatsPanel.jsx         # Session statistics
            └── ArtifactsPanel.jsx            # Artifacts visualization
```

#### Component Features
- **Real-time data fetching** on mount and date range change
- **Firebase authentication** integration
- **Responsive design** with CSS Grid
- **Interactive sorting** for tables
- **Visual charts and graphs** using CSS
- **Auto-refresh capability**
- **Error handling** with retry mechanism

## Data Flow

1. **Mission Execution** → Records tool_used, tool_confidence to Firebase `missions` collection
2. **API Calls** → Middleware logs to `api_usage.jsonl`
3. **Budget Events** → budget_tracker writes to `budgets.jsonl`
4. **Revenue Signals** → Written to `revenue_signals.jsonl`
5. **Artifacts** → Recorded in `artifacts.jsonl`
6. **Conversation** → Messages stored in Firebase `conversation_sessions` collection

↓

7. **Whiteboard Metrics Aggregator** (`whiteboard_metrics.py`) reads from all sources
8. **API Endpoint** (`/api/whiteboard/metrics`) exposes aggregated data
9. **React Frontend** fetches and displays in panels

## Installation & Setup

### Backend Setup

1. Ensure all dependencies are installed:
```bash
pip install fastapi firebase-admin pydantic
```

2. Verify Firebase configuration in `Back_End/config.py`

3. Run the FastAPI server:
```bash
cd Back_End
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Install Node.js dependencies:
```bash
cd Front_End
npm install
```

2. Set environment variables (create `.env.development` and `.env.production`):
```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

3. Start development server:
```bash
npm start
```

4. Build for production:
```bash
npm run build
```

5. Deploy to Firebase Hosting:
```bash
firebase deploy --only hosting
```

## Usage

### Accessing the Whiteboard

1. **Login:** Navigate to the Buddy frontend and sign in with Yahoo auth
2. **Dashboard:** Once authenticated, you'll be redirected to `/whiteboard`
3. **Date Range:** Use the date range picker in the header (default: 90 days)
4. **Refresh:** Click the refresh button to fetch latest data
5. **Sorting:** Click column headers or sort buttons to reorder data

### API Testing

Test individual endpoints with:
```bash
# Get full metrics
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/whiteboard/metrics?days=90

# Get specific panel data
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/whiteboard/metrics/tool-confidence?days=90
```

## Data Storage

### JSONL Files (Append-Only)
- `data/budgets.jsonl` - Budget tracking
- `outputs/phase25/api_usage.jsonl` - API call logs
- `outputs/phase25/revenue_signals.jsonl` - Income signals
- `outputs/phase25/artifacts.jsonl` - Generated artifacts

Format: One JSON object per line (newline-delimited)

### Firebase Collections
- `missions/{mission_id}/events` - Mission lifecycle with tool stats
- `conversation_sessions/{session_id}` - Conversation history

## Configuration

### Time Range Defaults
Edit `DateRangePicker.jsx` to change preset time ranges:
```javascript
const presets = [
  { label: '7 Days', value: 7 },
  { label: '30 Days', value: 30 },
  { label: '90 Days', value: 90 },  // Default
  { label: '180 Days', value: 180 },
  { label: '1 Year', value: 365 }
];
```

### API Endpoint Limits
Endpoints validate `days` parameter between 1 and 365.

To modify, edit validation in `main.py`:
```python
if days < 1 or days > 365:
    return JSONResponse(status_code=400, content={"error": "days must be between 1 and 365"})
```

## Troubleshooting

### No Data Displayed
- Verify JSONL files exist and have data
- Check Firebase collections are populated
- Confirm date range includes recent data
- Check browser console for API errors

### Authentication Issues
- Verify Firebase Auth token is stored in localStorage
- Check token is included in API request headers
- Test token validity with Firebase Auth

### Slow Loading
- Reduce date range (smaller `days` value)
- Check JSONL file sizes (large files slow linear scans)
- Consider adding pagination for large datasets

### API Errors
- Check backend logs for exceptions
- Verify all data sources are accessible
- Confirm Firebase credentials are valid

## Future Enhancements

- [ ] Real-time WebSocket updates for live metrics
- [ ] Export data as CSV/JSON
- [ ] Custom date range picker (start/end dates)
- [ ] Panel customization (hide/show, reorder)
- [ ] Drill-down views for detailed analysis
- [ ] Historical trend charts (time-series)
- [ ] Alert thresholds and notifications
- [ ] Mobile-optimized view
- [ ] Dark mode theme

## Contributing

When adding new metrics:

1. Add collection function to `whiteboard_metrics.py`
2. Update `collect_whiteboard_summary()` to include new metric
3. Add API endpoint to `main.py`
4. Create React panel component
5. Import and add panel to `Whiteboard.jsx`
6. Update this README with new metric details

## License

Proprietary - Buddy Autonomous Agent System

---

**Last Updated:** January 2025  
**Author:** Buddy Development Team  
**Version:** 1.0.0
