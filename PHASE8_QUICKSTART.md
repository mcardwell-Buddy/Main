## Phase 8: Quick Reference & Integration Guide

---

## Quick Start (30 seconds)

```bash
# 1. Navigate to project
cd c:\Users\micha\Buddy

# 2. Ensure FastAPI and uvicorn are installed
pip install fastapi uvicorn

# 3. Start dashboard
python launch_dashboard.py

# 4. Open browser
# ➜ http://localhost:8000/
```

---

## Files Created

1. **phase8_dashboard_api.py** (500+ lines)
   - FastAPI application
   - 10 API endpoints
   - Analytics engine integration

2. **dashboard.html** (700+ lines)
   - Single-file HTML/CSS/JS dashboard
   - 6 monitor sections
   - Chart.js integrations
   - Real-time polling

3. **test_phase8.py** (400+ lines, 12+ tests)
   - Comprehensive unit tests
   - Mock analytics engine
   - Endpoint validation

4. **launch_dashboard.py** (200+ lines)
   - Server launcher
   - Port auto-detection
   - Developer mode

---

## API Endpoints Summary

```
GET /api/health                    → Service status
GET /api/                          → API docs
GET /api/analytics/agents          → Section 1: Agents
GET /api/analytics/capacity        → Section 2: Capacity
GET /api/analytics/pipeline        → Section 3: Task Pipeline
GET /api/analytics/costs           → Section 4: Costs
GET /api/analytics/learning        → Section 5: Learning
GET /api/analytics/risks           → Internal: Risk patterns
GET /api/analytics/recommendations → Internal: Recommendations
GET /api/analytics/all             → All data combined

POST /api/admin/cleanup            → Manual cleanup
POST /api/admin/aggregate          → Manual aggregation
```

---

## Dashboard Sections

| Section | Icon | Data Source | Purpose |
|---------|------|-------------|---------|
| **Agents** | 👥 | `/api/analytics/agents` | Agent status & health |
| **Capacity** | 📊 | `/api/analytics/capacity` | Predictive capacity |
| **Task Pipeline** | 📈 | `/api/analytics/pipeline` | Task success rates |
| **API Usage & Costing** | 💰 | `/api/analytics/costs` | Costs & token usage |
| **System Learning** | 🧠 | `/api/analytics/learning` | Tool confidence |
| **Top Tools** | 🛠️ | `/api/analytics/learning` | Tool rankings |

---

## Controls

**Refresh Now** 🔄
- Manual data refresh
- Useful for checking latest stats

**Auto-Refresh** ⏸
- Toggle ON/OFF
- Default: ON

**Speed** ⚡
- 2s (fast, more requests)
- 5s (balanced)
- 10s (slow, minimal requests)

---

## Data Flow

```
Phase 7 Analytics Engine
    ↓ (metrics recorded)
Tier 1/2/3 Storage
    ↓ (fastapi queries)
Phase 8 API Endpoints
    ↓ (http requests)
Dashboard Frontend
    ↓ (json parsing)
User Browser Display
```

---

## Integration Checklist

- [x] Phase 7 AnalyticsEngine created
- [x] Phase 7 metrics collection working
- [x] Phase 8 FastAPI server created
- [x] Phase 8 Dashboard HTML created
- [x] Phase 8 Tests written
- [x] Phase 8 Launcher script created
- [ ] **TODO:** Hook `record_task_execution()` calls in task_queue_processor.py
- [ ] **TODO:** Add hourly aggregation cron job
- [ ] **TODO:** Add daily cleanup cron job
- [ ] **TODO:** Deploy dashboard to production URL

---

## Next Integration: Hook into Task Execution

In **Back_End/task_queue_processor.py** (around task completion):

```python
# After task completes successfully/fails
try:
    # Record to analytics (Phase 7/8)
    self.agent.record_task_execution(
        task_id=task.id,
        tool_name=result.tool_used,
        duration_seconds=result.duration,
        success=result.success,
        cost_actual=result.cost,
        tokens_used=result.tokens,
        human_effort_level=result.effort_level,
        browser_used=hasattr(result, 'browser') and result.browser
    )
except Exception as e:
    logger.warning(f"Failed to record metrics: {e}")
```

---

## Environment Setup

### Required Packages
```bash
pip install fastapi uvicorn
```

### Optional (for testing)
```bash
pip install pytest httpx
```

### Verify Installation
```bash
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
python -c "import uvicorn; print(f'Uvicorn {uvicorn.__version__}')"
```

---

## Running Tests

### All tests
```bash
python -m unittest test_phase8.py -v
```

### Specific test
```bash
python -m unittest test_phase8.TestDashboardAPI.test_health_check -v
```

### Quick verification
```bash
python -c "
import unittest
loader = unittest.TestLoader()
suite = loader.discover('.', pattern='test_phase8.py')
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
print(f'\nTests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}')
"
```

---

## Endpoints Detail

### GET /api/analytics/agents
```json
{
  "timestamp": "2026-02-11T10:00:00",
  "total_agents": 2,
  "agents": [
    {
      "agent_id": "local-aspire5-abc123",
      "status": "IDLE",
      "tasks_completed_today": 10,
      "avg_response_time": 2.5,
      "success_rate": 0.95,
      "last_activity": "2026-02-11T10:00:00"
    }
  ]
}
```

### GET /api/analytics/costs
```json
{
  "timestamp": "2026-02-11T10:00:00",
  "api_usage": {
    "total_tasks_24h": 50,
    "total_tokens_24h": 5000,
    "avg_tokens_per_task": 100
  },
  "costing": {
    "execution_costs_24h": 0.50,
    "storage_costs_daily": 0.00001,
    "total_daily_cost": 0.50001
  },
  "storage": {
    "tier1_raw_records": 100,
    "tier2_hourly_summaries": 24,
    "estimated_size_mb": 0.05
  }
}
```

---

## Customization

### Change Port
```bash
python launch_dashboard.py --port 9000
```

### Change Refresh Rate (in JavaScript)
```javascript
// In dashboard.html, find:
let REFRESH_INTERVAL = 2000;  // Change to 5000 for 5 seconds
```

### Customize Theme (in CSS)
```css
/* In dashboard.html <style> section */
:root {
    --primary: #4CAF50;        /* Change green color */
    --accent: #FFC107;         /* Change yellow color */
}
```

---

## Debugging

### Check if FastAPI is working
```bash
curl http://localhost:8000/api/health
```

### Check specific endpoint
```bash
curl http://localhost:8000/api/analytics/agents
```

### Monitor logs
```bash
python -m uvicorn phase8_dashboard_api:app --log-level debug
```

### Browser Console (F12)
```javascript
// Check if fetch is working
fetch('/api/analytics/agents').then(r => r.json()).then(console.log)
```

---

## Performance Tips

1. **Increase refresh interval** if CPU usage high
   - Use ⚡ Speed button: 2s → 5s → 10s

2. **Reduce agents displayed** if many connected
   - Edit dashboard.html to show only top N agents

3. **Enable caching** on reverse proxy
   - Cache /api/health for 10 seconds
   - Cache static assets (CSS, JS) for 1 hour

4. **Use WebSockets** for real-time (Phase 9+)
   - Replace polling with Server-Sent Events

---

## Production Deployment

### Linux/Docker
```bash
python -m uvicorn phase8_dashboard_api:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name buddy.example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_read_timeout 60s;
    }
}
```

### Systemd Service
```ini
[Unit]
Description=Buddy Dashboard
After=network.target

[Service]
Type=simple
User=buddy
WorkingDirectory=/home/buddy/Buddy
ExecStart=/usr/bin/python3 launch_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Troubleshooting

### "Port already in use"
```bash
# Find and kill existing process
lsof -i :8000
kill -9 <PID>

# Or use different port
python launch_dashboard.py --port 8080
```

### "Module not found: fastapi"
```bash
pip install fastapi uvicorn
```

### "No data in dashboard"
1. Check Phase 7 is recording metrics
2. Call `python -c "from analytics_engine import AnalyticsEngine; e = AnalyticsEngine(); print(e.get_agents_status())"`
3. Verify database file exists: `ls -la local_data/analytics.db`

### "Charts not rendering"
1. Open browser F12 → Console (check for errors)
2. Verify Chart.js CDN is loading
3. Check JSON response has valid data

---

## Status

✅ **Phase 8 Complete**
- FastAPI backend: 500+ lines ✓
- Dashboard frontend: 700+ lines ✓
- Tests: 12+ tests ✓
- Launcher: Auto-detection ✓
- Documentation: Complete ✓

🚀 **Ready for Phase 9: Optimization Features**

---

## URLs

```
Dashboard: http://localhost:8000/
API Docs:  http://localhost:8000/api/
Health:    http://localhost:8000/api/health
Raw Data:  http://localhost:8000/api/analytics/all
```

---

## Next Phase: Phase 9

### Planned Features
- WebSocket real-time updates
- Historical data view (date ranges)
- Alert/notification system
- Export to PDF/CSV
- Custom dashboard layouts
- Tool-specific analytics
- Performance insights
- Predictive recommendations

**Ready when you are!** 🚀
