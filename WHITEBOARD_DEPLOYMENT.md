# Buddy Whiteboard - Deployment Guide

## Quick Start

### 1. Backend Deployment (Already Complete! ✅)

The backend is already integrated into the existing FastAPI application.

**What was added:**
- `Back_End/whiteboard_metrics.py` - Metrics aggregator
- `/api/whiteboard/metrics` endpoint in `main.py`
- API usage logging middleware
- 7 individual metric endpoints

**No additional deployment needed** - the endpoints are live when you run the FastAPI server.

---

### 2. Frontend Deployment

#### Step 1: Verify Dependencies

```bash
cd Front_End
npm install
```

This installs:
- react ^18.2.0
- react-dom ^18.2.0
- react-router-dom ^7.13.0
- axios ^1.6.0

#### Step 2: Build the React App

```bash
npm run build
```

This creates an optimized production build in `Front_End/build/`.

#### Step 3: Deploy to Firebase Hosting

**Option A: Full Deployment**
```bash
firebase deploy
```

**Option B: Hosting Only**
```bash
firebase deploy --only hosting
```

The Firebase configuration (`firebase.json`) already has the correct rewrites to route API calls to the Cloud Run backend.

---

## Testing Locally

### 1. Start Backend

```bash
cd Back_End
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend Dev Server

```bash
cd Front_End
npm start
```

This opens `http://localhost:3000` with hot reloading.

### 3. Access Whiteboard

1. Navigate to `http://localhost:3000/whiteboard`
2. Sign in with Yahoo
3. Whiteboard displays with real data!

---

## Verify Deployment

### Backend Health Check

```bash
# Test main metrics endpoint
curl -X GET "https://buddy-app-501753640467.us-east4.run.app/api/whiteboard/metrics?days=90" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected response:
{
  "range": {...},
  "api_usage": {...},
  "costing": {...},
  "income": {...},
  "tool_confidence": {...},
  "response_times": {...},
  "session_stats": {...},
  "artifacts": {...}
}
```

### Frontend Health Check

1. Open `https://buddy-aeabf.web.app/whiteboard`
2. Login with Yahoo
3. Verify all 8 panels display data
4. Test date range picker
5. Test refresh button

---

## Firebase Hosting Configuration

Your `firebase.json` already has the correct setup:

```json
{
  "hosting": {
    "public": "build",
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "buddy-app-501753640467",
          "region": "us-east4"
        }
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

This ensures:
- All `/api/*` requests are proxied to the Cloud Run backend
- All other routes serve the React app (client-side routing)

---

## Environment Variables

### Development (.env.development)
```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

### Production (.env.production)
```env
REACT_APP_BACKEND_URL=https://buddy-app-501753640467.us-east4.run.app
```

**Note:** With Firebase Hosting rewrites, the React app uses relative URLs (`/api/whiteboard/metrics`), so the backend URL is handled automatically in production.

---

## Data Initialization

### Required JSONL Files

Create these files if they don't exist:

```bash
# API usage log
mkdir -p outputs/phase25
touch outputs/phase25/api_usage.jsonl

# Revenue signals
touch outputs/phase25/revenue_signals.jsonl

# Artifacts log
touch outputs/phase25/artifacts.jsonl

# Budget log
mkdir -p data
touch data/budgets.jsonl
```

### Sample Data (Optional)

For testing, you can add sample entries:

**data/budgets.jsonl:**
```json
{"event_type": "serpapi_usage", "service": "serpapi", "searches_used": 10, "mission_id": "test-001", "timestamp": "2025-01-15T12:00:00Z"}
{"event_type": "openai_usage", "service": "openai", "cost_usd": 1.25, "mission_id": "test-002", "timestamp": "2025-01-15T13:00:00Z"}
```

**outputs/phase25/api_usage.jsonl:**
```json
{"timestamp": "2025-01-15T12:00:00Z", "method": "GET", "path": "/api/whiteboard/metrics", "status_code": 200, "duration_ms": 45.5, "user_id": "user123"}
{"timestamp": "2025-01-15T12:05:00Z", "method": "POST", "path": "/conversation/message", "status_code": 200, "duration_ms": 320.2, "user_id": "user123"}
```

---

## Post-Deployment Checklist

- [ ] Backend API endpoints respond with 200 OK
- [ ] Firebase Auth login works
- [ ] Whiteboard page loads after login
- [ ] All 8 panels display (even if empty)
- [ ] Date range picker changes update data
- [ ] Refresh button works
- [ ] No console errors
- [ ] Mobile responsive view works
- [ ] Logout button functions correctly

---

## Rollback Plan

If issues occur:

### Backend Rollback
The whiteboard endpoints are **additive only** - they don't modify existing functionality. Safe to leave deployed.

To disable temporarily:
```python
# In main.py, comment out:
# @app.get("/api/whiteboard/metrics")
# async def get_whiteboard_metrics(days: int = 90):
#     ...
```

### Frontend Rollback
```bash
# Restore previous build
cd Front_End/build
git checkout HEAD~1 .

# Redeploy
firebase deploy --only hosting
```

---

## Production Monitoring

### Key Metrics to Watch

1. **API Response Times**
   - Whiteboard metrics endpoint should respond in < 500ms
   - If > 1s, optimize aggregation queries

2. **Error Rate**
   - Watch backend logs for exceptions in `collect_*` functions
   - Check frontend console for fetch failures

3. **Data Freshness**
   - Verify JSONL files are being appended
   - Check Firebase mission writes are happening

### Logging

Backend logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=buddy-app-501753640467" --limit 50
```

Firebase Hosting logs:
```bash
firebase hosting:logs
```

---

## Support

For issues:
1. Check [WHITEBOARD_README.md](./WHITEBOARD_README.md) for troubleshooting
2. Review backend logs for exceptions
3. Test individual endpoints with curl
4. Verify data sources have content

---

**Deployment Complete!** 🚀

Your new Buddy Whiteboard is live at:
- **Production:** https://buddy-aeabf.web.app/whiteboard
- **Local Dev:** http://localhost:3000/whiteboard
