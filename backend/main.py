import os
import logging
import re
import asyncio
from datetime import datetime
from typing import Optional
import requests
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.composite_agent import execute_goal
from backend.iterative_executor import execute_goal_iteratively
from backend.config import Config
from backend.tool_registry import tool_registry
from backend.tool_performance import tracker
from backend.memory_manager import memory_manager
from backend.feedback_manager import feedback_manager
from backend.autonomy_manager import autonomy_manager
from backend.knowledge_graph import knowledge_graph
from backend.python_sandbox import sandbox
from backend.code_analyzer import analyze_file_for_improvements, build_suggestion, test_code_improvement
from backend.agent_reasoning import agent_reasoning, create_reasoning_session, get_reasoning_todos
from backend.self_improvement_engine import self_improvement_engine
from backend.buddys_soul import get_soul
from backend.buddys_discovery import discover_unknowns
from backend.success_tracker import success_tracker
from backend.gohighlevel_client import initialize_ghl
from backend import gohighlevel_tools
from backend import mployer_tools
from backend.screenshot_capture import capture_screenshot_as_base64, capture_page_state, capture_clickable_elements, capture_full_context
from backend.buddys_vision_core import BuddysVisionCore
from backend.buddys_arms import BuddysArms
from backend.buddys_vision import BuddysVision
from backend.buddy_core import handle_user_message, list_conversation_sessions, get_conversation_session, update_conversation_session, delete_conversation_session

# Phase 2: Graded Confidence & Approval Gates
from phase2_confidence import GradedConfidenceCalculator, ConfidenceFactors
from phase2_prevalidation import PreValidator
from phase2_approval_gates import ApprovalGates, ExecutionPath
from phase2_clarification import ClarificationGenerator
from phase2_soul_integration import MockSoulSystem
from phase2_response_schema import Phase2ResponseBuilder

# Phase 25: Autonomous Multi-Agent System
from backend.phase25_orchestrator import orchestrator, Goal, Task, ExecutionMode, TaskType, TaskPriority
from backend.phase25_dashboard_aggregator import dashboard_aggregator

# PHASE 3 INTEGRATION: Chat Session Handler + Response Envelope + Whiteboard
from backend.chat_session_handler import ChatSessionHandler
from backend.response_envelope import ResponseEnvelope
from backend.whiteboard.mission_whiteboard import get_mission_whiteboard, get_goal_whiteboard, list_goals
from backend.mission_approval_service import approve_mission

# Register all tools on startup
from backend import tools
from backend import additional_tools
from backend import extended_tools
from backend import web_tools

# Initialize tool registrations
tools.register_foundational_tools(tool_registry)
additional_tools.register_additional_tools(tool_registry)
extended_tools.register_extended_tools(tool_registry)
gohighlevel_tools.register_gohighlevel_tools(tool_registry)
mployer_tools.register_mployer_tools(tool_registry)
web_tools.register_web_tools(tool_registry)  # PHASE 5: Vision & Arms Integration

app = FastAPI(title="Buddy API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-initialize GHL client from environment if available
try:
    ghl_token = os.getenv("GHL_API_TOKEN")
    ghl_location = os.getenv("GHL_LOCATION_ID")
    if ghl_token:
        initialize_ghl(ghl_token, ghl_location)
except Exception as e:
    logging.warning(f"GHL auto-init failed: {e}")

# ============================================================================
# PHASE 2: INITIALIZE SYSTEMS (Feature-Flagged)
# ============================================================================

# Feature flags from environment
PHASE2_ENABLED = os.getenv('PHASE2_ENABLED', 'False').lower() == 'true'
PHASE2_PRE_VALIDATION_ENABLED = os.getenv('PHASE2_PRE_VALIDATION_ENABLED', 'True').lower() == 'true'
PHASE2_APPROVAL_GATES_ENABLED = os.getenv('PHASE2_APPROVAL_GATES_ENABLED', 'True').lower() == 'true'
PHASE2_CLARIFICATION_ENABLED = os.getenv('PHASE2_CLARIFICATION_ENABLED', 'True').lower() == 'true'
PHASE2_GRADED_CONFIDENCE_ENABLED = os.getenv('PHASE2_GRADED_CONFIDENCE_ENABLED', 'True').lower() == 'true'
MULTI_STEP_LIVE_ENABLED = os.getenv('MULTI_STEP_LIVE_ENABLED', 'False').lower() == 'true'

HIGH_CONFIDENCE_THRESHOLD = float(os.getenv('HIGH_CONFIDENCE_THRESHOLD', '0.85'))
MEDIUM_CONFIDENCE_THRESHOLD = float(os.getenv('MEDIUM_CONFIDENCE_THRESHOLD', '0.55'))

# Initialize Phase 2 systems (only if enabled)
confidence_calculator = None
pre_validator = None
approval_gates = None
clarification_generator = None
soul_system = None
response_builder = None

if PHASE2_ENABLED:
    logging.info("Phase 2 systems initializing...")
    
    # Get available tool names for pre-validation
    available_tool_names = list(tool_registry.tools.keys()) if hasattr(tool_registry, 'tools') else []
    
    confidence_calculator = GradedConfidenceCalculator()
    pre_validator = PreValidator(available_tools=available_tool_names)
    soul_system = MockSoulSystem()  # Use real HTTPSoulClient in production
    approval_gates = ApprovalGates(
        soul_integration=soul_system,
        high_confidence_threshold=HIGH_CONFIDENCE_THRESHOLD,
        medium_confidence_threshold=MEDIUM_CONFIDENCE_THRESHOLD,
    )
    clarification_generator = ClarificationGenerator()
    response_builder = Phase2ResponseBuilder()
    
    logging.info(f"✓ Phase 2 initialized (confidence_calc, pre_val, gates, clarify, soul, response)")
    logging.info(f"  - Pre-validation: {PHASE2_PRE_VALIDATION_ENABLED}")
    logging.info(f"  - Approval gates: {PHASE2_APPROVAL_GATES_ENABLED}")
    logging.info(f"  - Clarification: {PHASE2_CLARIFICATION_ENABLED}")
    logging.info(f"  - Graded confidence: {PHASE2_GRADED_CONFIDENCE_ENABLED}")
    logging.info(f"  - High threshold: {HIGH_CONFIDENCE_THRESHOLD}")
    logging.info(f"  - Medium threshold: {MEDIUM_CONFIDENCE_THRESHOLD}")
else:
    logging.info("Phase 2 systems disabled (PHASE2_ENABLED=False)")


def _collect_tools_from_steps(steps: list) -> list:
    tools = set()
    for step in steps or []:
        decision = step.get('decision', {}) if isinstance(step, dict) else {}
        tool = decision.get('tool') if isinstance(decision, dict) else None
        if tool:
            tools.add(tool)
    return list(tools)


def _collect_tools_from_result(result: dict) -> list:
    tools = set()
    if not isinstance(result, dict):
        return []
    if result.get('steps'):
        tools.update(_collect_tools_from_steps(result.get('steps')))
    if result.get('execution_log'):
        for entry in result.get('execution_log', []):
            tool = entry.get('tool') if isinstance(entry, dict) else None
            if tool:
                tools.add(tool)
    if result.get('iterations'):
        for entry in result.get('iterations', []):
            tool = entry.get('tool') if isinstance(entry, dict) else None
            if tool:
                tools.add(tool)
    return list(tools)


class FeedbackRequest(BaseModel):
    goal_pattern: str
    tool: Optional[str] = None
    domain: Optional[str] = None
    verdict: str = "negative"
    reason: str = ""
    evidence: str = ""
    action: str = "penalize"
    impact: Optional[dict] = None
    human_id: str = "default_user"

class SimpleFeedback(BaseModel):
    goal: str
    feedback: str  # helpful, not_helpful, wrong
    timestamp: str

class TeachingCorrection(BaseModel):
    original_goal: str
    correction: str
    timestamp: str


class SandboxExecuteRequest(BaseModel):
    code: str


class SandboxValidateRequest(BaseModel):
    code: str


class CodeAnalyzeRequest(BaseModel):
    file_path: str


class CodeBuildRequest(BaseModel):
    file_path: str
    improvement: Optional[str] = "add error handling"


class CodeTestRequest(BaseModel):
    original_code: str
    improved_code: str
    test_case: Optional[str] = None


class SuggestionFeedbackRequest(BaseModel):
    suggestion_id: str
    verdict: str
    notes: Optional[str] = ""


class ReasoningRequest(BaseModel):
    goal: str
    context: Optional[dict] = None


class ConversationMessageRequest(BaseModel):
    session_id: Optional[str] = None
    source: str
    external_user_id: Optional[str] = None
    text: str

class LearningDataRequest(BaseModel):
    goal: str
    key_findings: list
    recommendations: list
    confidence: float
    tools_used: list

class SuccessFeedbackRequest(BaseModel):
    goal_id: str
    helpfulness: Optional[int] = None  # 1-5
    accuracy: Optional[int] = None      # 1-5
    completeness: Optional[int] = None  # 1-5
    actionability: Optional[int] = None # 1-5
    code_quality: Optional[int] = None  # 1-5
    notes: Optional[str] = ""

class GHLConfigRequest(BaseModel):
    api_token: str
    location_id: Optional[str] = None




class SelfImproveRequest(BaseModel):
    file_path: str
    improvement: str
    require_confirmation: bool = True
    confirmed: bool = False


class ApproveImprovementRequest(BaseModel):
    file_path: str
    improved_code: str
    approved: bool = False


class DemoReadRequest(BaseModel):
    url: Optional[str] = None


class DiscoveryRequest(BaseModel):
    goal: Optional[str] = ""
    domain: Optional[str] = ""
    context: Optional[dict] = None


# ============================================================================
# EXECUTION WIRING: Mission Executor Initialization
# ============================================================================

from backend.execution import executor
_executor_task = None

@app.on_event("startup")
async def startup_executor():
    """Start the mission executor loop on app startup."""
    global _executor_task
    try:
        from backend.mission_execution_runner import start_executor_background
        _executor_task = start_executor_background()
        logging.info("[MAIN] Mission executor started")
    except Exception as e:
        logging.error(f"[MAIN] Error starting executor: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_executor():
    """Stop the mission executor on app shutdown."""
    try:
        executor.stop()
        if _executor_task:
            _executor_task.cancel()
            try:
                await _executor_task
            except asyncio.CancelledError:
                pass
        logging.info("[MAIN] Mission executor stopped")
    except Exception as e:
        logging.error(f"[MAIN] Error stopping executor: {e}", exc_info=True)


@app.get("/")
async def root():
    return {"status": "running", "version": "1.0.0", "agent": "autonomous", "features": ["domains", "goal_decomposition"]}

@app.get("/tools")
async def list_tools():
    tools = []
    for name, info in tool_registry.tools.items():
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

@app.post("/ghl/configure")
async def configure_ghl(request: GHLConfigRequest):
    """
    Configure GoHighLevel API connection.
    
    Provide your GHL API token and optional location ID.
    This enables Buddy to add contacts, create opportunities, etc.
    """
    try:
        initialize_ghl(request.api_token, request.location_id)
        return JSONResponse(content={
            "success": True,
            "message": "GoHighLevel configured successfully"
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/ghl/status")
async def ghl_status():
    """Check if GoHighLevel is configured"""
    from backend.gohighlevel_client import ghl_client
    
    return JSONResponse(content={
        "configured": ghl_client is not None,
        "message": "GoHighLevel is ready" if ghl_client else "GoHighLevel not configured"
    })

# ============================================================================
# PHASE 25: AUTONOMOUS MULTI-AGENT SYSTEM ENDPOINTS
# ============================================================================

@app.get("/dashboards/operations")
async def get_operations_dashboard():
    """Get Operations Dashboard data for real-time execution monitoring"""
    try:
        data = dashboard_aggregator.get_operations_dashboard_data()
        return JSONResponse(content=data)
    except Exception as e:
        logging.error(f"Error fetching operations dashboard: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/dashboards/learning")
async def get_learning_dashboard():
    """Get Learning Dashboard data for market insights and GHL trends"""
    try:
        data = dashboard_aggregator.get_learning_dashboard_data()
        return JSONResponse(content=data)
    except Exception as e:
        logging.error(f"Error fetching learning dashboard: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/dashboards/side_hustle")
async def get_side_hustle_dashboard():
    """Get Side Hustle Dashboard data for revenue opportunities"""
    try:
        data = dashboard_aggregator.get_side_hustle_dashboard_data()
        return JSONResponse(content=data)
    except Exception as e:
        logging.error(f"Error fetching side hustle dashboard: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

class GoalRequest(BaseModel):
    description: str
    goal_type: str
    owner: str = "system"
    approval_required: bool = True
    expected_completion: Optional[str] = None
    success_metrics: Optional[list] = None
    tags: Optional[list] = None

@app.post("/goals/ingest")
async def ingest_goal(request: GoalRequest):
    """Ingest a new goal for autonomous execution"""
    try:
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            description=request.description,
            owner=request.owner,
            goal_type=request.goal_type,
            status="CREATED",
            approval_required=request.approval_required,
            created_at=datetime.utcnow().isoformat(),
            expected_completion=request.expected_completion,
            success_metrics=request.success_metrics or [],
            progress=0,
            tags=request.tags or []
        )
        success = orchestrator.ingest_goal(goal)
        if success:
            return JSONResponse(content={
                "success": True,
                "goal_id": goal.goal_id,
                "message": f"Goal '{goal.description}' ingested successfully"
            })
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Failed to ingest goal"}
            )
    except Exception as e:
        logging.error(f"Error ingesting goal: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

class TaskRequest(BaseModel):
    goal_id: str
    task_type: str
    priority: str = "MEDIUM"
    target_url: Optional[str] = None
    parameters: Optional[dict] = None

@app.post("/tasks/create")
async def create_task(request: TaskRequest):
    """Create a new task for a goal"""
    try:
        task_id = orchestrator.create_task(
            goal_id=request.goal_id,
            task_type=request.task_type,
            priority=request.priority,
            target_url=request.target_url or "",
            parameters=request.parameters or {}
        )
        return JSONResponse(content={
            "success": True,
            "task_id": task_id,
            "message": "Task created successfully"
        })
    except Exception as e:
        logging.error(f"Error creating task: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/goals")
async def get_goals(status: Optional[str] = None):
    """Query all goals or filter by status"""
    try:
        goals = orchestrator.get_goals(status=status)
        return JSONResponse(content={
            "goals": goals,
            "count": len(goals),
            "filter": status or "all"
        })
    except Exception as e:
        logging.error(f"Error fetching goals: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/tasks/{goal_id}")
async def get_tasks_for_goal(goal_id: str):
    """Get all tasks for a specific goal"""
    try:
        tasks = orchestrator.get_tasks_for_goal(goal_id)
        return JSONResponse(content={
            "goal_id": goal_id,
            "tasks": tasks,
            "count": len(tasks)
        })
    except Exception as e:
        logging.error(f"Error fetching tasks: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming of agent execution"""
    try:
        await websocket.accept()
        logging.info("WebSocket client connected")
        
        while True:
            try:
                data = await websocket.receive_json()
                logging.info(f"[WS] Received data: {data}")
                
                goal = data.get('goal')
                domain = data.get('domain', '_global')
                
                if not goal:
                    logging.warning("[WS] No goal provided in request")
                    await websocket.send_json({'error': 'Goal required'})
                    continue
                
                logging.info(f"[WS] Executing goal: {goal}")
                
                # Use streaming executor for real-time updates
                from backend.streaming_executor import StreamingExecutor
                executor = StreamingExecutor(websocket)
                
                result = await executor.execute_with_streaming(goal, domain)
                logging.info(f"[WS] Execution complete, sending final result")
                await websocket.send_json({
                    'type': 'done',
                    'result': result
                })
                
            except Exception as e:
                logging.error(f"[WS] Error in streaming execution: {e}", exc_info=True)
                try:
                    await websocket.send_json({'status': 'error', 'error': str(e)})
                except:
                    pass
                
    except WebSocketDisconnect:
        logging.info("WebSocket client disconnected")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011)
        except:
            pass
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

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    record = feedback_manager.submit_feedback(
        goal_pattern=request.goal_pattern,
        tool=request.tool,
        domain=request.domain or "_global",
        verdict=request.verdict,
        reason=request.reason,
        evidence=request.evidence,
        action=request.action,
        impact=request.impact,
        human_id=request.human_id,
    )
    return JSONResponse(content=record)

@app.post("/feedback/simple")
async def submit_simple_feedback(request: SimpleFeedback):
    """Simple feedback endpoint for UI buttons"""
    # Convert simple feedback to full feedback format
    verdict = "positive" if request.feedback == "helpful" else "negative"
    action = "reward" if request.feedback == "helpful" else "penalize"
    reason = f"User marked answer as {request.feedback}"
    
    # Save to memory
    memory_manager.store_observation({
        'type': 'user_feedback',
        'goal': request.goal,
        'feedback': request.feedback,
        'verdict': verdict,
        'timestamp': request.timestamp
    })
    
    # Track in feedback manager
    record = feedback_manager.submit_feedback(
        goal_pattern=request.goal,
        tool=None,
        domain="_global",
        verdict=verdict,
        reason=reason,
        evidence=f"User feedback: {request.feedback}",
        action=action,
        impact={'feedback_type': request.feedback},
        human_id="default_user",
    )
    
    return JSONResponse(content={'status': 'success', 'message': 'Feedback recorded', 'record': record})

@app.post("/teach")
async def submit_teaching_correction(request: TeachingCorrection):
    """Teaching mode - user submits corrections for wrong answers"""
    # Store the correction in memory as high-priority learning
    memory_manager.store_observation({
        'type': 'user_correction',
        'original_goal': request.original_goal,
        'correction': request.correction,
        'timestamp': request.timestamp,
        'priority': 'high',
        'learning_type': 'supervised'
    })
    
    # Store as strong negative feedback for the wrong answer
    feedback_manager.submit_feedback(
        goal_pattern=request.original_goal,
        tool=None,
        domain="_global",
        verdict="negative",
        reason="User provided correction",
        evidence=f"User correction: {request.correction}",
        action="penalize",
        impact={'correction': request.correction, 'learning_priority': 'high'},
        human_id="default_user",
    )
    
    # Log for tracking
    logging.info(f"Teaching correction received for '{request.original_goal}': {request.correction}")
    
    return JSONResponse(content={
        'status': 'success',
        'message': 'Correction received and stored for learning',
        'original_goal': request.original_goal,
        'correction': request.correction
    })

@app.get("/feedback")
async def list_feedback(domain: Optional[str] = None):
    records = feedback_manager.list_feedback(domain=domain)
    return {"count": len(records), "records": records}

@app.get("/autonomy/status")
async def get_autonomy_status():
    level = autonomy_manager.get_current_level()
    return JSONResponse(content={
        'current_level': level,
        'level_name': autonomy_manager.LEVELS.get(level),
        'next_level': level + 1 if level < 5 else None,
        'requirements_for_next': autonomy_manager.LEVEL_REQUIREMENTS.get(level + 1, {}),
        'current_metrics': autonomy_manager.session_stats
    })

@app.get("/knowledge/graph")
async def get_knowledge_graph(domain: str = "_global"):
    """Get knowledge graph visualization data"""
    graph_data = knowledge_graph.get_graph_data(domain=domain)
    return JSONResponse(content=graph_data)


@app.post("/sandbox/execute")
async def sandbox_execute(request: SandboxExecuteRequest):
    result = sandbox.execute(request.code)
    return JSONResponse(content=result)


@app.post("/sandbox/validate")
async def sandbox_validate(request: SandboxValidateRequest):
    syntax_valid, syntax_msg = sandbox.validate_syntax(request.code)
    safe, dangerous = sandbox.check_imports(request.code)
    return JSONResponse(content={
        'syntax_valid': syntax_valid,
        'syntax_message': syntax_msg,
        'safe': safe,
        'dangerous_operations': dangerous,
        'is_safe_to_run': syntax_valid and safe
    })


@app.post("/code/analyze")
async def code_analyze(request: CodeAnalyzeRequest):
    result = analyze_file_for_improvements(request.file_path)
    return JSONResponse(content=result)


@app.post("/code/build-suggestion")
async def code_build_suggestion(request: CodeBuildRequest):
    result = build_suggestion(request.file_path, request.improvement)
    return JSONResponse(content=result)


@app.post("/code/test-improvement")
async def code_test_improvement(request: CodeTestRequest):
    result = test_code_improvement(request.original_code, request.improved_code, request.test_case)
    return JSONResponse(content=result)


@app.post("/suggestion/feedback")
async def suggestion_feedback(request: SuggestionFeedbackRequest):
    try:
        # Store feedback in memory
        feedback_key = f"suggestion_{request.suggestion_id}_{request.verdict}"
        memory_manager.save_if_important(
            feedback_key,
            'suggestion_feedback',
            {
                'suggestion_id': request.suggestion_id,
                'verdict': request.verdict,
                'notes': request.notes,
                'timestamp': datetime.utcnow().isoformat()
            },
            domain="_global"
        )
        return JSONResponse(content={'status': 'success', 'message': 'Suggestion feedback recorded'})
    except Exception as e:
        logging.error(f"Error storing suggestion feedback: {e}")
        return JSONResponse(content={'status': 'error', 'message': str(e)}, status_code=500)


@app.post("/self-improve/scan")
async def scan_for_improvements():
    """Scan Buddy's codebase for improvement opportunities"""
    try:
        opportunities = self_improvement_engine.scan_codebase_for_improvements()
        return JSONResponse(content={
            "success": True,
            "opportunities": opportunities,
            "count": len(opportunities)
        })
    except Exception as e:
        logging.error(f"Error scanning for improvements: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/self-improve/execute")
async def execute_self_improvement(request: SelfImproveRequest):
    """
    Execute autonomous self-improvement on a file.
    
    Buddy will iteratively improve the code until tests pass.
    """
    try:
        # This runs the autonomous loop
        result = self_improvement_engine.autonomous_improve_until_tests_pass(
            file_path=request.file_path,
            improvement_description=request.improvement,
            require_confirmation=request.require_confirmation,
            confirmed=request.confirmed
        )
        
        return JSONResponse(content={
            "success": result.get('success', False),
            "result": result
        })
    except Exception as e:
        logging.error(f"Error executing self-improvement: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/self-improve/approve")
async def approve_improvement(request: ApproveImprovementRequest):
    """
    Approve and deploy an improvement.
    
    Writes the improved code to the actual file after creating a backup.
    """
    try:
        from pathlib import Path

        if not request.approved:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Approval flag required (approved=true)"}
            )
        
        # Write to file
        project_root = Path(__file__).parent.parent
        full_path = project_root / request.file_path
        
        # Backup original
        backup_path = full_path.with_suffix('.py.backup')
        with open(full_path, 'r') as f:
            with open(backup_path, 'w') as backup:
                backup.write(f.read())
        
        # Write improved version
        with open(full_path, 'w') as f:
            f.write(request.improved_code)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Improvement deployed to {request.file_path}",
            "backup_created": str(backup_path),
            "restart_required": True
        })
    except Exception as e:
        logging.error(f"Error approving improvement: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/demo/build-small")
async def demo_build_small():
    code = """
def build_small():
    items = [1, 2, 3, 4, 5]
    return sum(items)
 
result = build_small()
print(f"Build small result: {result}")
"""
    result = sandbox.execute(code)
    return JSONResponse(content=result)


@app.post("/discovery/unknowns")
async def discovery_unknowns(request: DiscoveryRequest):
    """Ask for unknowns and generate idea seeds aligned with Buddy's Soul."""
    try:
        result = discover_unknowns(goal=request.goal or "", domain=request.domain or "", context=request.context)
        return JSONResponse(content={"success": True, "result": result})
    except Exception as e:
        logging.error(f"Error generating discovery insights: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/demo/read-site")
async def demo_read_site(request: DemoReadRequest):
    url = request.url or "http://localhost:3000"
    try:
        response = requests.get(url, timeout=3)
        text = response.text or ""
        match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        title = match.group(1).strip() if match else "(no title found)"
        return JSONResponse(content={
            'success': True,
            'url': url,
            'status_code': response.status_code,
            'title': title,
            'content_length': len(text)
        })
    except Exception as e:
        return JSONResponse(content={'success': False, 'url': url, 'error': str(e)})

@app.post("/autonomy/request_escalation")
async def request_escalation(target_level: int, reason: str = ""):
    request = autonomy_manager.request_escalation(target_level, reason)
    return JSONResponse(content=request)

@app.post("/autonomy/approve_escalation")
async def approve_escalation(request_id: str, approved: bool, human_comment: str = ""):
    result = autonomy_manager.approve_escalation(request_id, approved, human_comment)
    return JSONResponse(content=result)

@app.get("/autonomy/requests")
async def get_pending_escalations(status: Optional[str] = None):
    requests = autonomy_manager.list_requests(status=status)
    return JSONResponse(content={'count': len(requests), 'requests': requests})

@app.post("/chat")
async def chat(goal: str, domain: Optional[str] = None):
    """Execute a goal (atomic or composite) and return full execution history"""
    goal_record = success_tracker.record_goal(goal=goal, domain=domain or "general", initial_confidence=0.5)
    result = execute_goal(goal, domain=domain)
    response_text = result.get('final_answer') or result.get('synthesis', {}).get('synthesis_narrative') or str(result)
    tools_used = _collect_tools_from_result(result)
    success_tracker.record_response(
        goal_id=goal_record.get('id'),
        response=response_text,
        tools_used=tools_used,
        tools_count=len(tools_used)
    )
    result['goal_id'] = goal_record.get('id')
    return JSONResponse(content=result)

@app.post("/chat/iterative")
async def chat_iterative(goal: str, domain: Optional[str] = None):
    """
    Execute a goal using SMART iterative decomposition.
    
    Unlike /chat which uses static decomposition:
    - Simple goals (e.g., "What is 2+2?") solved in 1 step
    - Complex goals iterate until sufficient info found
    - Each search result informs the next query
    - Stops when confidence is high, not after N steps
    
    Returns execution log showing each iteration and how it informed the next.
    """
    goal_record = success_tracker.record_goal(goal=goal, domain=domain or "general", initial_confidence=0.5)
    result = execute_goal_iteratively(goal, domain=domain)
    response_text = result.get('final_answer') or str(result)
    tools_used = _collect_tools_from_result(result)
    success_tracker.record_response(
        goal_id=goal_record.get('id'),
        response=response_text,
        tools_used=tools_used,
        tools_count=len(tools_used)
    )
    result['goal_id'] = goal_record.get('id')
    return JSONResponse(content=result)

@app.get("/chat/decompose")
async def decompose_goal(goal: str):
    """Preview how a goal would be decomposed (without execution)"""
    from backend.goal_decomposer import goal_decomposer
    classification = goal_decomposer.classify_goal(goal)
    return JSONResponse(content=classification)

@app.get("/chat/analyze-complexity")
async def analyze_complexity(goal: str):
    """Analyze goal complexity using iterative logic"""
    from backend.iterative_decomposer import iterative_decomposer
    analysis = iterative_decomposer.analyze_goal_complexity(goal)
    return JSONResponse(content=analysis)


@app.get("/conversation/sessions")
async def list_conversation_sessions_api():
    """List all conversation sessions across sources."""
    return JSONResponse(content={"sessions": list_conversation_sessions()})


@app.get("/conversation/sessions/{session_id}")
async def get_conversation_session_api(session_id: str):
    """Get a full conversation session by ID."""
    session = get_conversation_session(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return JSONResponse(content=session)


@app.patch("/conversation/sessions/{session_id}")
async def update_conversation_session_api(session_id: str, request: Request):
    """Update session metadata (title, archived status)."""
    body = await request.json()
    title = body.get('title')
    archived = body.get('archived')
    
    success = update_conversation_session(session_id, title=title, archived=archived)
    if not success:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return JSONResponse(content={"success": True})


@app.delete("/conversation/sessions/{session_id}")
async def delete_conversation_session_api(session_id: str):
    """Delete a conversation session."""
    success = delete_conversation_session(session_id)
    if not success:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return JSONResponse(content={"success": True})


@app.post("/conversation/message")
async def post_conversation_message(request: ConversationMessageRequest):
    """Route a conversation message through Buddy Core."""
    result = handle_user_message(
        source=request.source,
        text=request.text,
        session_id=request.session_id,
        external_user_id=request.external_user_id,
    )
    return JSONResponse(content=result)


# ============================================================================
# PHASE 3 INTEGRATION: Unified Chat Path (CANONICAL)
# ============================================================================

@app.post("/chat/integrated")
async def chat_integrated(request: ConversationMessageRequest):
    """
    CANONICAL CHAT PATH (Phase 3 Integration + Observability)
    
    Single source of truth for chat message handling with end-to-end tracing.
    
    Flow:
    1. Generate trace_id for observability
    2. Check for duplicate messages (backend guard)
    3. User message received
    4. ChatSessionHandler invoked
    5. InteractionOrchestrator classifies intent (with trace logging)
    6. Mission proposal (if applicable) created + signals emitted
    7. ResponseEnvelope returned with:
       - missions_spawned (proposed missions)
       - signals_emitted (navigation, extraction, signal events)
       - artifacts (any immediate results)
       - live_stream_id (if streaming)
    8. UI displays mission proposals and artifacts
    9. User can access mission details via /api/whiteboard/{mission_id}
    
    DEPRECATES:
    - /conversation/message (in-memory echo only)
    - /reasoning/execute (raw execution, no envelope)
    - /chat (direct execute_goal, no envelope)
    
    REPLACES: All three above with this single endpoint.
    """
    try:
        # Generate trace_id for observability
        from backend.observability import DuplicateDetector, ensure_observability_dirs
        from uuid import uuid4
        trace_id = str(uuid4())
        ensure_observability_dirs()
        
        # Extract or generate session_id
        session_id = request.session_id or f"chat_{uuid4()}"
        user_id = request.external_user_id or "anonymous"
        
        # Check for duplicate messages (backend guard)
        if DuplicateDetector.check_duplicate(session_id, request.text, trace_id):
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error": "Duplicate message detected (within 500ms)",
                    "trace_id": trace_id
                }
            )
        
        # Initialize handler with session_id AND user_id
        handler = ChatSessionHandler(session_id=session_id, user_id=user_id)
        
        # Create chat message with timestamp and trace_id
        from backend.chat_session_handler import ChatMessage
        from datetime import datetime, timezone
        
        chat_msg = ChatMessage(
            message_id=str(uuid4()),
            user_id=user_id,
            session_id=session_id,
            text=request.text,
            timestamp=datetime.now(timezone.utc).isoformat(),
            trace_id=trace_id  # Add trace_id for observability
        )
        
        # Process through orchestrator - pass ChatMessage object directly
        chat_response = handler.handle_message(chat_msg)
        
        # Return ResponseEnvelope as JSON
        return JSONResponse(
            content={
                "status": "success",
                "trace_id": trace_id,  # Echo trace_id for client-side correlation
                "chat_message_id": chat_response.message_id,
                "session_id": chat_response.session_id,
                "envelope": {
                    "response_type": chat_response.envelope.response_type.value,
                    "summary": chat_response.envelope.summary,
                    "missions_spawned": [
                        {
                            "mission_id": m.mission_id,
                            "status": m.status,
                            "objective_type": m.objective_type,
                            "objective_description": m.objective_description
                        } for m in chat_response.envelope.missions_spawned
                    ],
                    "signals_emitted": len(chat_response.envelope.signals_emitted),
                    "artifacts": [
                        {
                            "artifact_type": a.artifact_type.value if hasattr(a.artifact_type, 'value') else a.artifact_type,
                            "title": a.title,
                        } for a in chat_response.envelope.artifacts
                    ],
                    "live_stream_id": chat_response.envelope.live_stream_id
                }
            }
        )
    except Exception as e:
        logging.error(f"Error in /chat/integrated: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )


@app.post("/api/missions/{mission_id}/approve")
async def approve_mission_api(mission_id: str):
    """
    Approve a mission, transitioning from proposed → approved.
    
    IMPORTANT:
    - Changes mission status from "proposed" to "approved"
    - Writes exactly ONE status update record
    - Does NOT execute the mission
    - Does NOT select tools
    - Pure state transition only
    
    Args:
        mission_id: Mission to approve
        
    Returns:
        {
            "status": "success|error",
            "mission_id": str,
            "current_status": str,
            "message": str
        }
    """
    try:
        logging.info(f"[APPROVAL_API] Received approval request for mission: {mission_id}")
        
        result = approve_mission(mission_id)
        
        if result.get('success'):
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "mission_id": mission_id,
                    "current_status": "approved",
                    "message": f"Mission {mission_id} approved successfully"
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "mission_id": mission_id,
                    "message": result.get('message', 'Failed to approve mission')
                }
            )
    
    except Exception as e:
        logging.error(f"Error approving mission {mission_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "mission_id": mission_id,
                "message": str(e)
            }
        )


@app.post("/api/missions/{mission_id}/execute")
async def execute_mission_api(mission_id: str):
    """
    Execute an approved mission.
    
    IMPORTANT CONSTRAINTS:
    - Mission MUST be in status="approved" to execute
    - Execution happens exactly once per explicit trigger
    - This is NOT auto-execution (approval does NOT trigger execution)
    - Synchronous: returns when complete or fails
    
    Args:
        mission_id: Mission to execute
    
    Returns:
        HTTP 200: {"status": "success", "mission_id": "...", "result": {...}}
        HTTP 400: {"status": "error", "message": "..."}
        HTTP 500: {"status": "error", "message": "..."}
    """
    try:
        from backend.execution_service import execute_mission
        
        logging.info(f"[API] POST /api/missions/{mission_id}/execute")
        
        # Call execution service
        result = execute_mission(mission_id)
        
        # Check if execution succeeded
        if result.get('success'):
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "mission_id": mission_id,
                    "execution_status": result.get('status'),
                    "tool_used": result.get('tool_used'),
                    "tool_confidence": result.get('tool_confidence'),
                    "result_summary": result.get('result_summary', 'Execution completed'),
                    "artifact_reference": result.get('artifact_reference'),
                    "artifact_message": result.get('artifact_message'),
                    "result": result.get('execution_result'),
                    "message": f"Mission executed successfully using {result.get('tool_used')}"
                }
            )
        else:
            # Check if it's an approval issue
            if 'not "approved"' in result.get('error', ''):
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "mission_id": mission_id,
                        "current_status": result.get('current_status'),
                        "message": "Mission must be approved before execution"
                    }
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "mission_id": mission_id,
                        "message": result.get('error', 'Execution failed')
                    }
                )
    
    except Exception as e:
        logging.error(f"Error executing mission {mission_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "mission_id": mission_id,
                "message": str(e)
            }
        )


@app.get("/api/whiteboard/{mission_id}")
async def get_mission_whiteboard_api(mission_id: str):
    """
    READ-ONLY Whiteboard API (Phase 3)
    
    Returns mission state reconstruction from outputs/phase25/learning_signals.jsonl
    
    Usage:
    - After chat endpoint returns missions_spawned
    - UI calls this with mission_id to get full mission details
    - Returns mission state: status, progress, navigation_summary, signals
    
    No caching, no new logic - direct read from JSONL.
    """
    try:
        mission_state = get_mission_whiteboard(mission_id)
        if not mission_state:
            return JSONResponse(
                status_code=404,
                content={"error": f"Mission {mission_id} not found in whiteboard"}
            )
        return JSONResponse(content={"mission_id": mission_id, "state": mission_state})
    except Exception as e:
        logging.error(f"Error reading whiteboard for {mission_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/whiteboard/goals")
async def list_mission_goals_api():
    """
    List all active goals from whiteboard (read-only).
    
    Returns aggregated goal state.
    """
    try:
        goals = list_goals()
        return JSONResponse(content={"goals": goals})
    except Exception as e:
        logging.error(f"Error listing goals: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/budget/status")
async def get_budget_status():
    """
    Get current budget status for all services.
    
    Returns:
        {
            'serpapi': {
                'type': 'credits',
                'tier': 'free',
                'monthly_quota': 250,
                'credits_used': 50,
                'credits_remaining': 200,
                'todays_budget': 35,
                'daily_rollover': 10,
                'pace': {'on_pace': True, 'daily_rate': 2.5, ...},
                'days_until_reset': 20
            },
            'openai': {
                'type': 'dollars',
                'monthly_limit': 100.00,
                'spent': 5.25,
                'remaining': 94.75
            },
            'firestore': {
                'type': 'dollars',
                'monthly_limit': 50.00,
                'spent': 0.10,
                'remaining': 49.90
            }
        }
    """
    try:
        from backend.budget_enforcer import get_budget_enforcer
        from backend.cost_estimator import ServiceTier
        
        enforcer = get_budget_enforcer()
        
        # Get status for FREE tier by default (would get from user settings in production)
        status = enforcer.get_budget_status_summary(ServiceTier.FREE)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "budgets": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logging.error(f"Error getting budget status: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/debug/trace/{trace_id}")
async def get_execution_trace(trace_id: str):
    """
    Get complete execution trace for a single chat request.
    
    Queries outputs/debug/decision_traces.jsonl for all decision points
    matching the trace_id, enabling end-to-end visibility into:
    - Intent classification and reasoning
    - Routing decisions
    - Deterministic shortcuts (math, etc)
    - Mission creation (if applicable)
    
    Usage:
    GET /api/debug/trace/12345678-1234-1234-1234-123456789012
    
    Returns:
    {
        "trace_id": "...",
        "decision_points": [
            {
                "decision_point": "intent_classification",
                "chosen_intent": "request_execution",
                "confidence": 0.85,
                "reasoning": "..."
            },
            {
                "decision_point": "routing",
                "chosen_handler": "execute",
                "reasoning": "..."
            },
            ...
        ],
        "summary": "..."
    }
    """
    try:
        from pathlib import Path
        import json
        
        traces_file = Path('outputs/debug/decision_traces.jsonl')
        
        if not traces_file.exists():
            return JSONResponse(
                status_code=404,
                content={"error": "No trace data available", "trace_id": trace_id}
            )
        
        # Read all traces matching trace_id
        matching_traces = []
        with open(traces_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if record.get('trace_id') == trace_id:
                        matching_traces.append(record)
                except json.JSONDecodeError:
                    continue
        
        if not matching_traces:
            return JSONResponse(
                status_code=404,
                content={"error": f"No trace records found for trace_id: {trace_id}", "trace_id": trace_id}
            )
        
        # Build summary
        summary_parts = []
        decision_points = []
        
        for trace in matching_traces:
            dp = trace.get('decision_point', 'unknown')
            decision_points.append(trace)
            
            if dp == 'intent_classification':
                summary_parts.append(f"Intent: {trace.get('chosen_intent')} ({trace.get('confidence', 0):.2f})")
            elif dp == 'routing':
                summary_parts.append(f"Routed to: {trace.get('chosen_handler')}")
            elif dp == 'deterministic_shortcut':
                summary_parts.append(f"Shortcut: {trace.get('shortcut_type')}")
            elif dp == 'mission_creation':
                summary_parts.append(f"Mission: {trace.get('mission_id')[:8]}... ({trace.get('objective_type')})")
        
        return JSONResponse(
            content={
                "trace_id": trace_id,
                "decision_points": decision_points,
                "summary": " → ".join(summary_parts)
            }
        )
    except Exception as e:
        logging.error(f"Error reading trace {trace_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace_id": trace_id}
        )


@app.get("/api/debug/duplicates")
async def get_duplicate_detection_records():
    """
    Get all duplicate message detection records.
    
    Returns:
    {
        "total_duplicates": N,
        "recent_duplicates": [...]
    }
    """
    try:
        from pathlib import Path
        import json
        
        dup_file = Path('outputs/debug/duplicates.jsonl')
        
        if not dup_file.exists():
            return JSONResponse(
                content={"total_duplicates": 0, "recent_duplicates": []}
            )
        
        duplicates = []
        with open(dup_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    duplicates.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        # Return last 10
        recent = duplicates[-10:] if duplicates else []
        
        return JSONResponse(
            content={
                "total_duplicates": len(duplicates),
                "recent_duplicates": recent
            }
        )
    except Exception as e:
        logging.error(f"Error reading duplicates: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/reasoning/execute")
async def execute_reasoning(request: ReasoningRequest):
    """
    Execute full reasoning loop on a goal with Phase 2 integration.
    
    Phase 1 (Existing):
    1. Understand - What is user really asking?
    2. Plan - Create strategy
    3. Execute - Run tools
    4. Reflect - Did it work?
    5. Decide - Continue or stop?
    6. Respond - Compile response
    
    Phase 2 (New - if enabled):
    1. Pre-Validation - Check goal feasibility before reasoning
    2. Graded Confidence - Calculate continuous confidence (0.0-1.0)
    3. Approval Gates - Route by confidence (auto-execute, request approval, clarify)
    4. Clarification - Generate questions for ambiguous goals
    5. Soul Integration - Approval workflow and context tracking
    
    Returns: {success, result, confidence, approval_state, execution_path, soul_request_id}
    """
    try:
        goal = (request.goal or "").strip()
        session_id = request.session_id or str(uuid.uuid4())
        
        if not goal:
            return JSONResponse(content={
                "success": False,
                "result": {
                    "message": "Invalid goal: goal must be a non-empty string.",
                    "summary": "Invalid request",
                    "key_findings": [],
                    "recommendations": [],
                    "next_steps": [],
                    "confidence": 0.0,
                    "tools_used": [],
                    "tool_results": [],
                    "understanding": {}
                },
                "approval_state": "none",
                "execution_path": "rejected",
                "timestamp": datetime.now().isoformat(),
            })
        
        # ====================================================================
        # PHASE 2: PRE-VALIDATION (if enabled)
        # ====================================================================
        
        confidence_adjustment = 0.0
        
        if PHASE2_ENABLED and PHASE2_PRE_VALIDATION_ENABLED and pre_validator:
            validation_result = pre_validator.validate_goal(goal)
            
            if validation_result.validation_status == "pre_validation_failed":
                # Early exit - goal failed pre-validation
                return JSONResponse(content={
                    "success": False,
                    "result": {
                        "message": f"Pre-validation failed: {validation_result.recommendation}",
                        "summary": "Goal validation failed",
                        "key_findings": [f.message for f in validation_result.failures],
                        "recommendations": validation_result.suggested_questions,
                        "next_steps": [],
                        "confidence": 0.0,
                        "tools_used": [],
                        "tool_results": [],
                        "understanding": {"pre_validation_failures": [f.to_dict() for f in validation_result.failures]},
                    },
                    "approval_state": "none",
                    "execution_path": "rejected",
                    "timestamp": datetime.now().isoformat(),
                })
            
            # Pre-validation passed - adjust confidence
            confidence_adjustment = validation_result.total_confidence_delta
            logging.info(f"Pre-validation passed with confidence adjustment: {confidence_adjustment:+.2f}")
        
        # ====================================================================
        # PHASE 1: AGENT REASONING (Existing)
        # ====================================================================
        
        reasoning_result = agent_reasoning.reason_about_goal(goal)
        
        # ====================================================================
        # PHASE 2: GRADED CONFIDENCE CALCULATION (if enabled)
        # ====================================================================
        
        if PHASE2_ENABLED and PHASE2_GRADED_CONFIDENCE_ENABLED and confidence_calculator:
            # Extract factors from reasoning result
            goal_understanding = reasoning_result.get('understanding', {}).get('clarity', 0.5)
            if isinstance(goal_understanding, str):
                goal_understanding = 0.5  # Default if not numeric
            
            tools_proposed = reasoning_result.get('tools_used', [])
            tools_available_count = len([t for t in tools_proposed if t in tool_registry.tools])
            tool_availability = tools_available_count / max(len(tools_proposed), 1) if tools_proposed else 0.5
            
            context_richness = 0.5  # Could be enhanced with session history
            tool_confidence = 0.8  # Could be enhanced with tool metadata
            
            factors = ConfidenceFactors(
                goal_understanding=goal_understanding,
                tool_availability=tool_availability,
                context_richness=context_richness,
                tool_confidence=tool_confidence,
            )
            
            base_confidence = confidence_calculator.calculate(factors)
            confidence = max(0.0, min(1.0, base_confidence + confidence_adjustment))
            
            logging.info(f"Graded confidence: {confidence:.2%} (base: {base_confidence:.2%}, adjustment: {confidence_adjustment:+.2f})")
        else:
            # Phase 1 fallback: binary confidence
            confidence = reasoning_result.get('confidence', 0.7) if reasoning_result.get('success', False) else 0.0
        
        # ====================================================================
        # PHASE 2: APPROVAL GATES (if enabled)
        # ====================================================================
        
        if PHASE2_ENABLED and PHASE2_APPROVAL_GATES_ENABLED and approval_gates:
            decision = approval_gates.decide(
                confidence=confidence,
                goal=goal,
                reasoning_summary=reasoning_result.get('summary', ''),
                tools_proposed=reasoning_result.get('tools_used', []),
                is_ambiguous=(confidence < MEDIUM_CONFIDENCE_THRESHOLD),
            )
            
            # Route by execution path
            if decision.execution_path == ExecutionPath.HIGH_CONFIDENCE:
                # HIGH CONFIDENCE: Execute immediately
                logging.info(f"HIGH_CONFIDENCE path (confidence={confidence:.2%}) - executing immediately")
                
                return JSONResponse(content={
                    "success": True,
                    "result": reasoning_result,
                    "confidence": confidence,
                    "approval_state": "none",
                    "execution_path": "high_confidence",
                    "timestamp": datetime.now().isoformat(),
                })
            
            elif decision.execution_path == ExecutionPath.APPROVED:
                # MEDIUM CONFIDENCE: Request approval
                logging.info(f"APPROVED path (confidence={confidence:.2%}) - requesting approval")
                
                approval_request_id = str(uuid.uuid4())
                approval_request = decision.approval_request
                approval_request.approval_callback_url = f"/approval/respond/{approval_request_id}"
                
                # Send to Soul system
                soul_result = soul_system.validate_approval_request(approval_request.to_dict())
                
                return JSONResponse(content={
                    "success": True,
                    "result": reasoning_result,
                    "confidence": confidence,
                    "approval_state": "awaiting_approval",
                    "execution_path": "approved",
                    "soul_request_id": approval_request_id,
                    "approval_request": approval_request.to_dict(),
                    "timestamp": datetime.now().isoformat(),
                })
            
            elif decision.execution_path == ExecutionPath.CLARIFICATION:
                # LOW CONFIDENCE: Request clarification
                logging.info(f"CLARIFICATION path (confidence={confidence:.2%}) - requesting clarification")
                
                if PHASE2_CLARIFICATION_ENABLED and clarification_generator:
                    clarification_request = clarification_generator.generate_clarification(
                        goal=goal,
                        confidence=confidence,
                        goal_understanding=factors.goal_understanding if 'factors' in locals() else 0.3,
                    )
                    
                    # Validate with Soul
                    soul_result = soul_system.validate_clarification(clarification_request.to_dict())
                    
                    return JSONResponse(content={
                        "success": False,
                        "result": reasoning_result,
                        "confidence": confidence,
                        "approval_state": "none",
                        "execution_path": "clarification",
                        "soul_request_id": clarification_request.request_id,
                        "clarification_request": clarification_request.to_dict(),
                        "suggested_questions": clarification_request.questions,
                        "timestamp": datetime.now().isoformat(),
                    })
                else:
                    # Clarification disabled - just return low confidence
                    return JSONResponse(content={
                        "success": False,
                        "result": reasoning_result,
                        "confidence": confidence,
                        "approval_state": "none",
                        "execution_path": "suggested",
                        "message": "Confidence too low for execution",
                        "timestamp": datetime.now().isoformat(),
                    })
            
            else:  # REJECTED
                logging.info(f"REJECTED path (confidence={confidence:.2%}) - execution blocked")
                
                return JSONResponse(content={
                    "success": False,
                    "result": reasoning_result,
                    "confidence": confidence,
                    "approval_state": "none",
                    "execution_path": "rejected",
                    "message": "Goal confidence too low for execution",
                    "timestamp": datetime.now().isoformat(),
                })
        
        # ====================================================================
        # PHASE 1 FALLBACK: No approval gates, just execute if success=true
        # ====================================================================
        
        return JSONResponse(content={
            "success": reasoning_result.get('success', False),
            "result": reasoning_result,
            "confidence": confidence,
            "approval_state": "none",
            "execution_path": "suggested",
            "timestamp": datetime.now().isoformat(),
        })
        
    except BaseException as e:
        logging.error(f"Error in /reasoning/execute: {e}", exc_info=True)
        return JSONResponse(content={
            "success": False,
            "result": {
                "message": "Execution failed while processing the goal.",
                "summary": "Execution error",
                "key_findings": [],
                "recommendations": [],
                "next_steps": [],
                "confidence": 0.0,
                "tools_used": [],
                "tool_results": [],
                "understanding": {"error": str(e)}
            },
            "approval_state": "none",
            "execution_path": "rejected",
            "timestamp": datetime.now().isoformat(),
        })

@app.get("/reasoning/todos")
async def get_reasoning_todos_endpoint():
    """Get current reasoning todos/steps"""
    todos = agent_reasoning.get_todos()
    return JSONResponse(content={
        "success": True,
        "todos": todos,
        "current_goal": agent_reasoning.current_goal,
        "confidence": agent_reasoning.confidence
    })

@app.post("/reasoning/understand")
async def understand_goal(request: ReasoningRequest):
    """Just run the understanding stage (no execution)"""
    try:
        understanding = agent_reasoning.understand_goal(request.goal, request.context)
        return JSONResponse(content={
            "success": True,
            "understanding": understanding,
            "todos": agent_reasoning.get_todos()
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/reasoning/reset")
async def reset_reasoning():
    """Reset reasoning state for new goal"""
    agent_reasoning.reset()
    return JSONResponse(content={"success": True, "message": "Reasoning reset"})

# ============================================================================
# PHASE 2: APPROVAL RESPONSE ENDPOINT
# ============================================================================

class ApprovalResponse(BaseModel):
    """Response to an approval request"""
    request_id: str
    approved: bool
    feedback: str = ""
    approver_id: Optional[str] = None

@app.post("/approval/respond/{request_id}")
async def submit_approval(request_id: str, response: ApprovalResponse):
    """
    Handle approval decision from Soul/user.
    
    Phase 2: This endpoint receives approval decisions for goals that required
    user/Soul approval (medium confidence: 0.55-0.85).
    """
    try:
        if not PHASE2_ENABLED or not approval_gates:
            return JSONResponse(content={
                "success": False,
                "error": "Phase 2 approval system not enabled",
            })
        
        # Store approval decision in Soul
        if soul_system:
            soul_system.validate_approval_request({
                "request_id": request_id,
                "approved": response.approved,
                "feedback": response.feedback,
                "approver_id": response.approver_id or "unknown",
                "timestamp": datetime.now().isoformat(),
            })
        
        if response.approved:
            # Approval granted - would execute tools here in full implementation
            # For now, just return success
            return JSONResponse(content={
                "success": True,
                "decision_id": request_id,
                "message": "Goal approved - execution authorized",
                "approved": True,
            })
        else:
            # Approval denied
            return JSONResponse(content={
                "success": False,
                "decision_id": request_id,
                "message": "Goal execution denied by user/Soul",
                "approved": False,
                "feedback": response.feedback,
            })
    
    except Exception as e:
        logging.error(f"Error in /approval/respond: {e}", exc_info=True)
        return JSONResponse(content={
            "success": False,
            "error": str(e),
        })

@app.post("/reasoning/store-learning")
async def store_learning_data(request: LearningDataRequest):
    """
    Store internal learning data (key findings, recommendations) in memory.
    
    This data is NOT shown to the user - it's for the agent's knowledge base.
    """
    try:
        # Store in memory manager for future learning
        memory_manager.save_if_important(
            key=f"learning:{request.goal}",
            item_type="learning",
            data={
                "goal": request.goal,
                "findings": request.key_findings or [],
                "recommendations": request.recommendations or [],
                "confidence": request.confidence or 0.0,
                "tools_used": request.tools_used or [],
            },
            context={"source": "reasoning_store_learning"},
            domain="_global",
        )
        
        return JSONResponse(content={
            "success": True,
            "message": "Learning data stored"
        })
    except Exception as e:
        logging.exception(f"Error storing learning data: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/success/record-goal")
async def record_goal(request: ReasoningRequest):
    """
    Record the start of a goal attempt.
    
    Returns goal_id for tracking through completion.
    """
    try:
        goal_record = success_tracker.record_goal(
            goal=request.goal,
            domain=request.context.get('domain', 'general') if request.context else 'general',
            initial_confidence=request.context.get('initial_confidence', 0.5) if request.context else 0.5
        )
        
        return JSONResponse(content={
            "success": True,
            "goal_id": goal_record['id']
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/success/submit-feedback")
async def submit_feedback(request: SuccessFeedbackRequest):
    """
    Submit feedback on Buddy's response.
    
    This is the KEY metric that drives improvement!
    Feedback dimensions:
    - helpfulness: Was the response helpful? (1-5)
    - accuracy: Was it accurate? (1-5)
    - completeness: Did it fully answer? (1-5)
    - actionability: Can I act on it? (1-5)
    - code_quality: (for code) Was it working? (1-5)
    """
    try:
        result = success_tracker.submit_feedback(
            goal_id=request.goal_id,
            helpfulness=request.helpfulness,
            accuracy=request.accuracy,
            completeness=request.completeness,
            actionability=request.actionability,
            code_quality=request.code_quality,
            notes=request.notes
        )
        
        if result:
            return JSONResponse(content={
                "success": True,
                "success_score": result.get('success_score'),
                "message": "Feedback recorded"
            })
        else:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Goal not found"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/success/stats")
async def get_success_stats(domain: str = None):
    """Get success statistics"""
    try:
        stats = success_tracker.get_success_stats(domain=domain)
        return JSONResponse(content={
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/success/failure-analysis")
async def analyze_failures(domain: str = None):
    """Analyze what causes failures - for improvement"""
    try:
        analysis = success_tracker.analyze_failure_patterns(domain=domain)
        return JSONResponse(content={
            "success": True,
            "analysis": analysis
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============ VISION & BROWSER LEARNING ENDPOINTS ============

@app.post("/vision/capture")
async def vision_capture(request: dict):
    """Capture full browser context: screenshot, page state, and clickable elements"""
    try:
        from backend import mployer_tools
        
        if not mployer_tools._mployer_scraper or not mployer_tools._mployer_scraper.driver:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "No active browser session"}
            )
        
        context = capture_full_context(mployer_tools._mployer_scraper.driver)
        return JSONResponse(content={
            "success": True,
            "context": context
        })
    except Exception as e:
        logging.error(f"Vision capture error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.websocket("/vision/stream")
async def vision_stream(websocket: WebSocket):
    """Stream live browser frames over WebSocket"""
    await websocket.accept()
    try:
        while True:
            from backend import mployer_tools
            
            if not mployer_tools._mployer_scraper or not mployer_tools._mployer_scraper.driver:
                await websocket.send_json({
                    "type": "error",
                    "error": "No active browser session"
                })
                await asyncio.sleep(1.0)
                continue
            
            context = capture_full_context(mployer_tools._mployer_scraper.driver)
            frame = context.get('screenshot')
            if frame and frame.get('base64'):
                await websocket.send_json({
                    "type": "frame",
                    "frame": frame,
                    "page_state": context.get('page_state', {}),
                    "clickables": context.get('clickables', [])
                })
            
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logging.info("Vision stream disconnected")
    except Exception as e:
        logging.error(f"Vision stream error: {e}", exc_info=True)
        try:
            await websocket.close(code=1011)
        except:
            pass


@app.post("/vision/inspect")
async def vision_inspect(request: dict):
    """Inspect page structure using Buddy's vision system"""
    try:
        from backend import mployer_tools
        
        if not mployer_tools._mployer_scraper or not mployer_tools._mployer_scraper.driver:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "No active browser session"}
            )
        
        vision_core = BuddysVisionCore(mployer_tools._mployer_scraper.driver)
        page_structure = vision_core.inspect_website()
        
        return JSONResponse(content={
            "success": True,
            "structure": page_structure
        })
    except Exception as e:
        logging.error(f"Vision inspect error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/vision/learn")
async def vision_learn(request: dict):
    """Capture screenshot and record learning from current page"""
    try:
        from backend import mployer_tools
        
        if not mployer_tools._mployer_scraper or not mployer_tools._mployer_scraper.driver:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "No active browser session"}
            )
        
        # Capture context
        context = capture_full_context(mployer_tools._mployer_scraper.driver)
        
        # Log as learning observation
        page_state = context.get('page_state', {})
        observation = f"Learned from {page_state.get('url', 'unknown')} - {page_state.get('title', 'unknown')}"
        
        # Store in memory
        memory_manager.log_observation(
            observation=observation,
            importance=0.7,
            category="web_learning",
            metadata={
                "url": page_state.get('url'),
                "title": page_state.get('title'),
                "screenshot_available": context['screenshot'] is not None
            }
        )
        
        return JSONResponse(content={
            "success": True,
            "context": context,
            "learned_from": observation
        })
    except Exception as e:
        logging.error(f"Vision learn error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/vision/interact")
async def vision_interact(request: dict):
    """Execute interaction using Buddy's arms and capture result"""
    try:
        from backend import mployer_tools
        
        if not mployer_tools._mployer_scraper or not mployer_tools._mployer_scraper.driver:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "No active browser session"}
            )
        
        action_type = request.get('action_type')  # click, fill, scroll, etc
        selector = request.get('selector')
        value = request.get('value')  # For fill operations
        click_x = request.get('x')
        click_y = request.get('y')
        text = request.get('text')
        
        arms = BuddysArms(mployer_tools._mployer_scraper.driver)
        result = None
        
        if action_type == 'click':
            result = arms.click_by_text(selector)
        elif action_type == 'click_at':
            if click_x is None or click_y is None:
                result = False
            else:
                result = mployer_tools._mployer_scraper.driver.execute_script(
                    """
                    const x = arguments[0];
                    const y = arguments[1];
                    const el = document.elementFromPoint(x, y);
                    if (el) { el.click(); return true; }
                    return false;
                    """,
                    click_x,
                    click_y
                )
        elif action_type == 'fill':
            result = arms.fill_field(selector, value)
        elif action_type == 'type':
            active = mployer_tools._mployer_scraper.driver.switch_to.active_element
            if active and text:
                active.send_keys(text)
                result = True
            else:
                result = False
        elif action_type == 'scroll':
            mployer_tools._mployer_scraper.driver.execute_script("window.scrollBy(0, arguments[0])", value or 300)
            result = True
        elif action_type == 'submit':
            element = mployer_tools._mployer_scraper.driver.find_element('xpath', f"//*[text()='{selector}']")
            element.submit()
            result = True
        
        # Capture new state
        import time
        time.sleep(0.5)  # Let page settle
        context = capture_full_context(mployer_tools._mployer_scraper.driver)
        
        return JSONResponse(content={
            "success": True,
            "action": action_type,
            "executed": result is not None,
            "context": context
        })
    except Exception as e:
        logging.error(f"Vision interact error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/vision/analyze")
async def vision_analyze(request: dict):
    """Analyze current page and return insights"""
    try:
        from backend import mployer_tools
        
        if not mployer_tools._mployer_scraper or not mployer_tools._mployer_scraper.driver:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "No active browser session"}
            )
        
        vision = BuddysVision(mployer_tools._mployer_scraper.driver)
        analysis = vision.analyze_and_learn()
        
        return JSONResponse(content={
            "success": True,
            "analysis": analysis
        })
    except Exception as e:
        logging.error(f"Vision analyze error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ==================== ARTIFACT DELIVERY & EMAIL ENDPOINTS ====================

@app.post("/api/artifacts/offer-delivery")
async def offer_artifact_delivery(request: dict):
    """
    Offer to deliver completed mission artifacts to user.
    
    Body:
        mission_id: str
        artifacts: List[str] - paths to files
        user_email: str
    """
    try:
        from backend.artifact_delivery_flow import get_delivery_orchestrator
        
        orchestrator = get_delivery_orchestrator()
        offer = orchestrator.offer_delivery(
            mission_id=request.get("mission_id"),
            artifacts=request.get("artifacts", []),
            user_email=request.get("user_email")
        )
        
        return JSONResponse(content={
            "success": True,
            "offer": offer
        })
    except Exception as e:
        logging.error(f"Offer delivery error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/artifacts/handle-delivery-response")
async def handle_artifact_delivery_response(request: dict):
    """
    Handle user's natural language response to delivery offer.
    
    Body:
        mission_id: str
        user_response: str - natural language like "yes email it"
    """
    try:
        from backend.artifact_delivery_flow import get_delivery_orchestrator
        
        orchestrator = get_delivery_orchestrator()
        result = orchestrator.handle_delivery_response(
            mission_id=request.get("mission_id"),
            user_response=request.get("user_response")
        )
        
        return JSONResponse(content={
            "success": result.get("success", False),
            "result": result
        })
    except Exception as e:
        logging.error(f"Handle delivery response error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/email/oauth/setup")
async def get_email_oauth_url():
    """Get Yahoo OAuth authorization URL for email setup"""
    try:
        from backend.email_client import YahooOAuthClient
        
        oauth_client = YahooOAuthClient()
        auth_url = oauth_client.get_authorization_url()
        
        return JSONResponse(content={
            "success": True,
            "authorization_url": auth_url,
            "instructions": "Open this URL in browser, authorize access, and return with the code"
        })
    except Exception as e:
        logging.error(f"Email OAuth setup error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/email/oauth/callback")
async def email_oauth_callback(request: dict):
    """
    Handle OAuth callback with authorization code.
    
    Body:
        code: str - authorization code from OAuth flow
    """
    try:
        from backend.email_client import YahooOAuthClient
        
        oauth_client = YahooOAuthClient()
        tokens = oauth_client.exchange_code_for_tokens(request.get("code"))
        
        return JSONResponse(content={
            "success": True,
            "message": "Email access configured successfully!",
            "expires_at": tokens.get("expires_at")
        })
    except Exception as e:
        logging.error(f"Email OAuth callback error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/email/send")
async def send_email(request: dict):
    """
    Send email with optional attachments.
    
    Body:
        to: str
        subject: str
        body: str
        attachments: List[str] (optional)
        html: bool (optional)
    """
    try:
        from backend.email_client import get_email_client
        
        email_client = get_email_client()
        result = email_client.send_email(
            to=request.get("to"),
            subject=request.get("subject"),
            body=request.get("body"),
            attachments=request.get("attachments"),
            cc=request.get("cc"),
            bcc=request.get("bcc"),
            html=request.get("html", False)
        )
        
        return JSONResponse(content={
            "success": result.get("success", False),
            "result": result
        })
    except Exception as e:
        logging.error(f"Send email error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/email/fetch")
async def fetch_emails(
    folder: str = "INBOX",
    limit: int = 10,
    unread_only: bool = False
):
    """Fetch emails from mailbox"""
    try:
        from backend.email_client import get_email_client
        
        email_client = get_email_client()
        emails = email_client.fetch_emails(
            folder=folder,
            limit=limit,
            unread_only=unread_only
        )
        
        return JSONResponse(content={
            "success": True,
            "emails": emails,
            "count": len(emails)
        })
    except Exception as e:
        logging.error(f"Fetch emails error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/email/comprehend")
async def comprehend_email(request: dict):
    """
    Use LLM to comprehend email content.
    
    Body:
        email: dict - parsed email object
    """
    try:
        from backend.email_client import get_comprehension_engine
        
        engine = get_comprehension_engine()
        comprehension = engine.comprehend_email(request.get("email"))
        
        return JSONResponse(content={
            "success": True,
            "comprehension": comprehension
        })
    except Exception as e:
        logging.error(f"Comprehend email error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/onedrive/oauth/setup")
async def get_onedrive_oauth_url():
    """Get Microsoft OAuth authorization URL for OneDrive setup"""
    try:
        from backend.onedrive_client import OneDriveOAuthClient
        
        oauth_client = OneDriveOAuthClient()
        auth_url = oauth_client.get_authorization_url()
        
        return JSONResponse(content={
            "success": True,
            "authorization_url": auth_url,
            "instructions": "Open this URL in browser, authorize access, and return with the code"
        })
    except Exception as e:
        logging.error(f"OneDrive OAuth setup error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/onedrive/oauth/callback")
async def onedrive_oauth_callback(request: dict):
    """
    Handle OneDrive OAuth callback with authorization code.
    
    Body:
        code: str - authorization code from OAuth flow
    """
    try:
        from backend.onedrive_client import OneDriveOAuthClient
        
        oauth_client = OneDriveOAuthClient()
        tokens = oauth_client.exchange_code_for_tokens(request.get("code"))
        
        return JSONResponse(content={
            "success": True,
            "message": "OneDrive access configured successfully!",
            "expires_at": tokens.get("expires_at")
        })
    except Exception as e:
        logging.error(f"OneDrive OAuth callback error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/onedrive/upload")
async def upload_to_onedrive(request: dict):
    """
    Upload file to OneDrive.
    
    Body:
        file_path: str
        onedrive_folder: str (optional, default: /Buddy Artifacts)
        custom_name: str (optional)
    """
    try:
        from backend.onedrive_client import get_onedrive_client
        
        onedrive = get_onedrive_client()
        result = onedrive.upload_file(
            file_path=request.get("file_path"),
            onedrive_folder=request.get("onedrive_folder", "/Buddy Artifacts"),
            custom_name=request.get("custom_name")
        )
        
        return JSONResponse(content={
            "success": result.get("success", False),
            "result": result
        })
    except Exception as e:
        logging.error(f"OneDrive upload error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/onedrive/list")
async def list_onedrive_files(folder: str = "/"):
    """List files in OneDrive folder"""
    try:
        from backend.onedrive_client import get_onedrive_client
        
        onedrive = get_onedrive_client()
        files = onedrive.list_files(folder_path=folder)
        
        return JSONResponse(content={
            "success": True,
            "files": files,
            "count": len(files)
        })
    except Exception as e:
        logging.error(f"OneDrive list error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


