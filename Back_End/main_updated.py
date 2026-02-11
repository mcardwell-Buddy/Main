import os
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from Back_End.composite_agent import execute_goal
from Back_End.config import Config
from Back_End.tool_registry import tool_registry
from Back_End.tool_performance import tracker
from Back_End.memory_manager import memory_manager

app = FastAPI(title="Autonomous Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "running", "version": "1.0.0", "agent": "autonomous", "features": ["domains", "goal_decomposition"]}

@app.get("/tools")
async def list_tools():
    """List all available tools with performance metrics"""
    tools = []
    for name, info in tool_registry.tools.items():
        # Get global stats
        stats = tracker.get_stats(name, domain="_global")
        tools.append({
            "name": name,
            "description": info.get('description', ''),
            "mock_available": info.get('mock_func') is not None,
            "performance": {
                "total_calls": stats['total_calls'] if stats else 0,
                "success_rate": stats['successful_calls'] / stats['total_calls'] if stats and stats['total_calls'] > 0 else 0.0,
                "avg_latency_ms": stats['avg_latency_ms'] if stats else 0.0,
                "usefulness_score": tracker.get_usefulness_score(name, domain="_global")
            }
        })
    return {"tools": tools, "count": len(tools)}

@app.get("/tools/by-domain")
async def list_tools_by_domain(domain: str = "_global"):
    """List tools with performance metrics for specific domain"""
    tools = []
    for name, info in tool_registry.tools.items():
        stats = tracker.get_stats(name, domain=domain)
        tools.append({
            "name": name,
            "description": info.get('description', ''),
            "domain": domain,
            "performance": {
                "total_calls": stats['total_calls'] if stats else 0,
                "success_rate": stats['successful_calls'] / stats['total_calls'] if stats and stats['total_calls'] > 0 else 0.0,
                "avg_latency_ms": stats['avg_latency_ms'] if stats else 0.0,
                "usefulness_score": tracker.get_usefulness_score(name, domain=domain)
            }
        })
    return {"tools": tools, "domain": domain, "count": len(tools)}

@app.get("/memory/insights")
async def get_memory_insights(goal: str = "", domain: str = "_global"):
    """Get intelligent summary of what the agent has learned"""
    if goal:
        learnings = memory_manager.summarize_learnings(goal, domain=domain)
        return {"goal": goal, "domain": domain, "learnings": learnings}
    return {"error": "Please provide a goal parameter"}

@app.post("/chat")
async def chat(goal: str, domain: str = None):
    """Execute a goal (atomic or composite) and return full execution history"""
    result = execute_goal(goal, domain=domain)
    return JSONResponse(content=result)

@app.get("/chat/decompose")
async def decompose_goal(goal: str):
    """Preview how a goal would be decomposed (without execution)"""
    from Back_End.goal_decomposer import goal_decomposer
    classification = goal_decomposer.classify_goal(goal)
    return JSONResponse(content=classification)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time goal execution streaming"""
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        goal = data.get('goal', '')
        domain = data.get('domain', None)
        
        # Execute goal and stream results
        result = execute_goal(goal, domain=domain)
        
        # Stream the result
        await websocket.send_json(result)
        
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected.")
    except Exception as e:
        await websocket.send_json({'error': str(e)})
        logging.error(f"WebSocket error: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

