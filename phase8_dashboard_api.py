"""
Phase 8: Dashboard API Server
FastAPI REST endpoints exposing Phase 7 Analytics Engine

Serves real-time monitoring data for browser-based dashboard
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

# Import analytics engine from parent directory
import sys
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from analytics_engine import AnalyticsEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Buddy Dashboard API",
    description="Real-time monitoring dashboard for Buddy system",
    version="1.0.0"
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global analytics engine instance
analytics_engine = None


def init_analytics(engine: Optional[AnalyticsEngine] = None):
    """Initialize analytics engine for dashboard."""
    global analytics_engine
    if engine is None:
        analytics_engine = AnalyticsEngine()
    else:
        analytics_engine = engine
    logger.info("✅ Dashboard API initialized with analytics engine")


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    init_analytics()


# ============ HEALTH CHECK ============

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Buddy Dashboard API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ============ ANALYTICS API ENDPOINTS ============

@app.get("/api/analytics/agents")
async def get_agents_status():
    """Get current status of all agents."""
    try:
        if not analytics_engine:
            return {"error": "Analytics engine not initialized"}
        
        result = analytics_engine.get_agents_status()
        return result
    except Exception as e:
        logger.error(f"Error getting agents status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/capacity")
async def get_predictive_capacity():
    """Get predicted capacity for all agents."""
    try:
        if not analytics_engine:
            return {"error": "Analytics engine not initialized"}
        
        result = analytics_engine.get_predictive_capacity()
        return result
    except Exception as e:
        logger.error(f"Error getting predictive capacity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/pipeline")
async def get_task_pipeline():
    """Get current task pipeline status."""
    try:
        if not analytics_engine:
            return {"error": "Analytics engine not initialized"}
        
        result = analytics_engine.get_task_pipeline()
        return result
    except Exception as e:
        logger.error(f"Error getting task pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/costs")
async def get_api_usage_and_costing():
    """Get API usage and costing information."""
    try:
        if not analytics_engine:
            return {"error": "Analytics engine not initialized"}
        
        result = analytics_engine.get_api_usage_and_costing()
        return result
    except Exception as e:
        logger.error(f"Error getting API usage and costing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/learning")
async def get_system_learning():
    """Get system learning profiles and confidence metrics."""
    try:
        if not analytics_engine:
            return {"error": "Analytics engine not initialized"}
        
        result = analytics_engine.get_system_learning()
        return result
    except Exception as e:
        logger.error(f"Error getting system learning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ INTERNAL APIS (NOT DISPLAYED) ============

@app.get("/api/analytics/risks")
async def get_risk_patterns():
    """Get risk patterns (internal use only)."""
    try:
        if not analytics_engine:
            return {"error": "Analytics engine not initialized"}
        
        result = analytics_engine.get_risk_patterns()
        return result
    except Exception as e:
        logger.error(f"Error getting risk patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/recommendations")
async def get_tool_recommendations():
    """Get tool optimization recommendations (internal use only)."""
    try:
        if not analytics_engine:
            return {"error": "Analytics engine not initialized"}
        
        result = analytics_engine.get_tool_recommendations()
        return result
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ ADMIN ENDPOINTS ============

@app.post("/api/admin/cleanup")
async def trigger_cleanup():
    """Manually trigger data cleanup."""
    try:
        if not analytics_engine:
            return {"error": "Analytics engine not initialized"}
        
        analytics_engine.cleanup_old_data()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "message": "✅ Cleanup completed successfully"
        }
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/aggregate")
async def trigger_aggregation():
    """Manually trigger hourly aggregation."""
    try:
        if not analytics_engine:
            return {"error": "Analytics engine not initialized"}
        
        analytics_engine.run_hourly_aggregation()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "message": "✅ Aggregation completed successfully"
        }
    except Exception as e:
        logger.error(f"Error during aggregation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ DASHBOARD HTML SERVING ============

@app.get("/")
async def serve_dashboard():
    """Serve dashboard HTML."""
    dashboard_path = Path(__file__).parent / "dashboard.html"
    
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    else:
        return {"error": "Dashboard HTML not found"}


# ============ BATCH ENDPOINTS ============

@app.get("/api/analytics/all")
async def get_all_analytics():
    """Get all analytics data in one call."""
    try:
        if not analytics_engine:
            return {"error": "Analytics engine not initialized"}
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "agents": analytics_engine.get_agents_status(),
            "capacity": analytics_engine.get_predictive_capacity(),
            "pipeline": analytics_engine.get_task_pipeline(),
            "costs": analytics_engine.get_api_usage_and_costing(),
            "learning": analytics_engine.get_system_learning()
        }
        
        return result
    except Exception as e:
        logger.error(f"Error getting all analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ ROOT ENDPOINTS ============

@app.get("/api/")
async def api_root():
    """API root endpoint with documentation."""
    return {
        "service": "Buddy Dashboard API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "analytics": {
                "agents": "/api/analytics/agents",
                "capacity": "/api/analytics/capacity",
                "pipeline": "/api/analytics/pipeline",
                "costs": "/api/analytics/costs",
                "learning": "/api/analytics/learning",
                "all": "/api/analytics/all"
            },
            "internal": {
                "risks": "/api/analytics/risks",
                "recommendations": "/api/analytics/recommendations"
            },
            "admin": {
                "cleanup": "/api/admin/cleanup (POST)",
                "aggregate": "/api/admin/aggregate (POST)"
            }
        },
        "dashboard": "/"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 70)
    logger.info("🚀 STARTING BUDDY DASHBOARD API SERVER")
    logger.info("=" * 70)
    
    # Initialize analytics engine
    init_analytics()
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
