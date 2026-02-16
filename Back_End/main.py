import os
import sys
import logging
import re
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import asdict
import requests
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# GAP-C3: Set up sanitized logging BEFORE any other logging
try:
    from Back_End.log_sanitizer import setup_sanitized_logging
    setup_sanitized_logging(
        level=logging.INFO,
        enable_email_redaction=False,  # Keep emails visible for debugging (can enable in prod)
        enable_phone_redaction=False   # Keep phones visible for debugging
    )
except Exception as e:
    # Fallback to regular logging if sanitizer fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    logging.warning(f"⚠️  Log sanitizer not available, using standard logging: {e}")

# ============================================================================
# IMPORT WITH FALLBACK PATTERNS
# Handles both "from Back_End" and "from current directory" deployments
# ============================================================================

try:
    from Back_End.whiteboard_metrics import collect_whiteboard_summary, log_api_usage
    from Back_End.composite_agent import execute_goal
    from Back_End.iterative_executor import execute_goal_iteratively
    from Back_End.config import Config
    from Back_End.tool_registry import tool_registry
    from Back_End.tool_performance import tracker
    from Back_End.memory_manager import memory_manager
    from Back_End.feedback_manager import feedback_manager
    from Back_End.autonomy_manager import autonomy_manager
    from Back_End.knowledge_graph import knowledge_graph
    from Back_End.python_sandbox import sandbox
    from Back_End.code_analyzer import analyze_file_for_improvements, build_suggestion, test_code_improvement
    from Back_End.agent_reasoning import agent_reasoning, create_reasoning_session, get_reasoning_todos
    from Back_End.self_improvement_engine import self_improvement_engine
    from Back_End.buddys_soul import get_soul
    from Back_End.buddys_discovery import discover_unknowns
    from Back_End.success_tracker import success_tracker
    from Back_End.gohighlevel_client import initialize_ghl
    from Back_End import gohighlevel_tools
    from Back_End.screenshot_capture import capture_screenshot_as_base64, capture_page_state, capture_clickable_elements, capture_full_context
    from Back_End.buddy_core import handle_user_message, list_conversation_sessions, get_conversation_session, update_conversation_session, delete_conversation_session
    # GAP-C2: Tenant Isolation Security
    from Back_End.tenant_isolation import tenant_isolation_middleware, require_tenant_access, get_current_tenant
    from Back_End.conversation.session_store import get_conversation_store
    # GAP-H2: API Rate Limiting
    from Back_End.api_rate_limiter import rate_limit, RateLimitTier, get_rate_limit_info
    # GAP-H3: Audit Logging
    from Back_End.audit_logger import audit_log, query_audit_logs, AuditAction, AuditSeverity
    # Phase 18 Security imports
    from Back_End.buddy_log_sanitizer import sanitize_log_data
    from Back_End.buddy_security_config import get_allowed_origins, SECURITY_HEADERS, is_public_endpoint
except (ImportError, ModuleNotFoundError) as e:
    logging.debug(f"Fallback import mode (Back_End not in path): {e}")
    # Fallback: import from current directory (works when deployed directly)
    from whiteboard_metrics import collect_whiteboard_summary, log_api_usage
    from composite_agent import execute_goal
    from iterative_executor import execute_goal_iteratively
    from config import Config
    from tool_registry import tool_registry
    from tool_performance import tracker
    from memory_manager import memory_manager
    from feedback_manager import feedback_manager
    from autonomy_manager import autonomy_manager
    from knowledge_graph import knowledge_graph
    from python_sandbox import sandbox
    from code_analyzer import analyze_file_for_improvements, build_suggestion, test_code_improvement
    from agent_reasoning import agent_reasoning, create_reasoning_session, get_reasoning_todos
    from self_improvement_engine import self_improvement_engine
    from buddys_soul import get_soul
    from buddys_discovery import discover_unknowns
    from success_tracker import success_tracker
    from gohighlevel_client import initialize_ghl
    import gohighlevel_tools
    from screenshot_capture import capture_screenshot_as_base64, capture_page_state, capture_clickable_elements, capture_full_context
    from buddy_core import handle_user_message, list_conversation_sessions, get_conversation_session, update_conversation_session, delete_conversation_session
    from conversation.session_store import get_conversation_store

try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    from firebase_admin import credentials as firebase_credentials
    _FIREBASE_AUTH_AVAILABLE = True
except Exception:
    firebase_admin = None
    firebase_auth = None
    firebase_credentials = None
    _FIREBASE_AUTH_AVAILABLE = False

# Phase 2: Graded Confidence & Approval Gates
try:
    from Back_End.phase2_confidence import GradedConfidenceCalculator, ConfidenceFactors
    from Back_End.phase2_prevalidation import PreValidator
    from Back_End.phase2_approval_gates import ApprovalGates, ExecutionPath
    from Back_End.phase2_clarification import ClarificationGenerator
    from Back_End.phase2_soul_integration import MockSoulSystem
    from Back_End.phase2_response_schema import Phase2ResponseBuilder
except (ImportError, ModuleNotFoundError):
    # Fallback to current directory 
    from phase2_confidence import GradedConfidenceCalculator, ConfidenceFactors
    from phase2_prevalidation import PreValidator
    from phase2_approval_gates import ApprovalGates, ExecutionPath
    from phase2_clarification import ClarificationGenerator
    from phase2_soul_integration import MockSoulSystem
    from phase2_response_schema import Phase2ResponseBuilder

# Phase 25: Autonomous Multi-Agent System
try:
    from Back_End.phase25_orchestrator import orchestrator, Goal, Task, ExecutionMode, TaskType, TaskPriority
    from Back_End.phase25_dashboard_aggregator import dashboard_aggregator
except (ImportError, ModuleNotFoundError):
    from phase25_orchestrator import orchestrator, Goal, Task, ExecutionMode, TaskType, TaskPriority
    from phase25_dashboard_aggregator import dashboard_aggregator

# PHASE 3 INTEGRATION: Chat Session Handler + Response Envelope + Whiteboard
try:
    from Back_End.chat_session_handler import ChatSessionHandler
    from Back_End.response_envelope import ResponseEnvelope
    from Back_End.whiteboard.mission_whiteboard import get_mission_whiteboard, get_goal_whiteboard, list_goals
    from Back_End.mission_approval_service import approve_mission
except (ImportError, ModuleNotFoundError):
    from chat_session_handler import ChatSessionHandler
    from response_envelope import ResponseEnvelope
    from whiteboard.mission_whiteboard import get_mission_whiteboard, get_goal_whiteboard, list_goals
    from mission_approval_service import approve_mission

# PHASE 6: WebSocket Streaming for Real-time Progress Updates
try:
    from Back_End.websocket_streaming import router as websocket_router
    from Back_End.streaming_events_integration import StreamingEventsIntegration
    from Back_End.routes.ws_execution import router as ws_execution_router
except (ImportError, ModuleNotFoundError) as e:
    logging.warning(f"WebSocket streaming modules unavailable: {e}")
    websocket_router = None
    StreamingEventsIntegration = None
    ws_execution_router = None

# PHASE 8: Phase25 Autonomous Multi-Agent Integration
try:
    from Back_End.phase25_mission_bridge import get_phase25_bridge
except (ImportError, ModuleNotFoundError) as e:
    logging.warning(f"Phase25 bridge unavailable: {e}")
    get_phase25_bridge = None

# PHASE 9: Cloud Task Scheduler
try:
    from Back_End.cloud_task_scheduler import get_cloud_scheduler
except (ImportError, ModuleNotFoundError) as e:
    logging.warning(f"Cloud task scheduler unavailable: {e}")
    get_cloud_scheduler = None

# PHASE 10: Mission Recipe System
try:
    from Back_End.mission_recipe_system import get_recipe_system
except (ImportError, ModuleNotFoundError) as e:
    logging.warning(f"Mission recipe system unavailable: {e}")
    get_recipe_system = None

# PHASE 19: Customer Onboarding & Signup
try:
    from Back_End.buddy_signup_service import SignupService
    import stripe
    # Initialize Stripe with API key from environment
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")
    _SIGNUP_SERVICE_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    logging.warning(f"Phase 19 signup service unavailable: {e}")
    SignupService = None
    stripe = None
    _SIGNUP_SERVICE_AVAILABLE = False

# PHASE 18B: Embedded Billing Dashboard
try:
    from Back_End.buddy_billing_dashboard import BillingDashboardService
    _BILLING_DASHBOARD_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    logging.warning(f"Phase 18B billing dashboard service unavailable: {e}")
    BillingDashboardService = None
    _BILLING_DASHBOARD_AVAILABLE = False

# Register all tools on startup
try:
    from Back_End import tools
    from Back_End import additional_tools
    from Back_End import extended_tools
except (ImportError, ModuleNotFoundError):
    import tools
    import additional_tools
    import extended_tools

# Initialize tool registrations
tools.register_foundational_tools(tool_registry)
additional_tools.register_additional_tools(tool_registry)
extended_tools.register_extended_tools(tool_registry)
gohighlevel_tools.register_gohighlevel_tools(tool_registry)

try:
    from Back_End import web_tools
    web_tools.register_web_tools(tool_registry)  # PHASE 5: Vision & Arms Integration
except Exception as e:
    logging.warning(f"Web tools unavailable: {e}")

try:
    from Back_End import google_search_free  # Auto-registers on import
    logging.info("✅ Free Google search tool loaded (cost-saving alternative to SERPAPI)")
except Exception as e:
    logging.warning(f"Free Google search unavailable: {e}")

# Load Phase 2-3 frameworks (auto-register tools)
try:
    from Back_End import multi_agent_orchestrator
    logging.info("✅ Multi-agent orchestration loaded (buddy_multiply tool)")
except Exception as e:
    logging.warning(f"Multi-agent orchestration unavailable: {e}")

try:
    from Back_End import batch_processor
    logging.info("✅ Batch processing loaded (batch_process tool)")
except Exception as e:
    logging.warning(f"Batch processing unavailable: {e}")

try:
    from Back_End import workflow_orchestrator
    logging.info("✅ Workflow orchestration loaded (execute_pipeline tool)")
except Exception as e:
    logging.warning(f"Workflow orchestration unavailable: {e}")

try:
    from Back_End import alert_manager
    logging.info("✅ Alert manager loaded (create_threshold_alert tool)")
except Exception as e:
    logging.warning(f"Alert manager unavailable: {e}")

# Load 32 Free API Integrations
try:
    from Back_End import weather_api_tools
    logging.info("✅ Weather APIs loaded (3 providers: OpenWeatherMap, WeatherAPI.com, NWS)")
except Exception as e:
    logging.warning(f"Weather APIs unavailable: {e}")

try:
    from Back_End import financial_api_tools
    logging.info("✅ Financial APIs loaded (4 providers: Alpha Vantage, FMP, CoinGecko, ExchangeRate)")
except Exception as e:
    logging.warning(f"Financial APIs unavailable: {e}")

try:
    from Back_End import knowledge_api_tools
    logging.info("✅ Knowledge APIs loaded (4 providers: Wikipedia, Wikidata, Open Library, PubMed)")
except Exception as e:
    logging.warning(f"Knowledge APIs unavailable: {e}")

try:
    from Back_End import news_api_tools
    logging.info("✅ News APIs loaded (3 providers: NewsAPI, GNews, NY Times)")
except Exception as e:
    logging.warning(f"News APIs unavailable: {e}")

try:
    from Back_End import maps_api_tools
    logging.info("✅ Maps APIs loaded (5 tools: geocode, reverse_geocode, find_places, directions, search)")
except Exception as e:
    logging.warning(f"Maps APIs unavailable: {e}")

try:
    from Back_End import government_data_tools
    logging.info("✅ Government Data APIs loaded (4 providers: Data.gov, Census, World Bank, FRED)")
except Exception as e:
    logging.warning(f"Government Data APIs unavailable: {e}")

try:
    from Back_End import utility_api_tools
    logging.info("✅ Utility APIs loaded (9 tools: Stack Overflow, barcode, food, flight, country, IP, user, timezone)")
except Exception as e:
    logging.warning(f"Utility APIs unavailable: {e}")

app = FastAPI(title="Buddy API", version="1.0.0")

# ============================================================================
# EARLY ROUTER REGISTRATION (Before middleware)
# Intelligence API must be registered immediately after app creation
# ============================================================================
logging.info("[PHASE4] Registering Intelligence API Router (early registration)...")
try:
    from Back_End.routes.intelligence_api import router as intelligence_router
    logging.info(f"[PHASE4] Imported intelligence_router successfully")
    app.include_router(intelligence_router)
    logging.info("✅[PHASE4] Intelligence API registered with /api/intelligence/*, /api/intelligence/insights, /api/intelligence/predict, /api/intelligence/analyze-failure")
except Exception as e:
    logging.warning(f"[PHASE4] Intelligence API early registration failed: {e}", exc_info=True)

# ============================================================================
# BOOT-TIME HEALTH CHECKS
# Verify critical systems can be imported without errors
# ============================================================================

_BOOT_CHECKS = {
    "whiteboard_metrics": False,
    "chat_handlers": False,
    "essential_tools": False,
    "mission_systems": False,
}

_BOOT_ERRORS = {}

def _perform_boot_checks() -> None:
    """Verify critical systems can be imported and initialized at boot time."""
    global _BOOT_CHECKS, _BOOT_ERRORS
    
    logger = logging.getLogger(__name__)
    
    try:
        # Check whiteboard metrics - critical for dashboard
        from Back_End.whiteboard_metrics import collect_whiteboard_summary
        _BOOT_CHECKS["whiteboard_metrics"] = True
        logger.info("✓ Whiteboard metrics loaded")
    except Exception as e:
        logger.error(f"✗ Whiteboard metrics failed: {e}")
        _BOOT_ERRORS["whiteboard_metrics"] = str(e)
    
    try:
        # Check chat handlers - critical for user interaction
        from Back_End.chat_session_handler import ChatSessionHandler
        _BOOT_CHECKS["chat_handlers"] = True
        logger.info("✓ Chat session handlers loaded")
    except Exception as e:
        logger.error(f"✗ Chat handlers failed: {e}")
        _BOOT_ERRORS["chat_handlers"] = str(e)
    
    try:
        # Check tool registry - critical for agent functionality
        from Back_End.tool_registry import tool_registry
        # tool_registry is a singleton instance with .tools dict
        num_tools = len(tool_registry.tools) if hasattr(tool_registry, 'tools') else 0
        _BOOT_CHECKS["essential_tools"] = True  # If we can import it, it's good
        logger.info(f"✓ Tool registry loaded with {num_tools} tools")
    except Exception as e:
        logger.error(f"✗ Tool registry failed: {e}")
        _BOOT_ERRORS["essential_tools"] = str(e)
    
    try:
        # Check mission systems - critical for task execution
        from Back_End.mission_store import get_mission_store
        store = get_mission_store()
        _BOOT_CHECKS["mission_systems"] = True
        logger.info("✓ Mission store loaded")
    except Exception as e:
        logger.error(f"✗ Mission systems failed: {e}")
        _BOOT_ERRORS["mission_systems"] = str(e)
    
    critical_systems_ok = all(_BOOT_CHECKS.values())
    if critical_systems_ok:
        logger.info(f"✓ All critical systems loaded successfully")
    else:
        failed = [k for k, v in _BOOT_CHECKS.items() if not v]
        logger.warning(f"⚠ Some systems failed to load: {', '.join(failed)}")


# Run boot checks immediately
_perform_boot_checks()

FIREBASE_AUTH_ENABLED = os.getenv("FIREBASE_AUTH_ENABLED", "true").lower() == "true"
FIREBASE_AUTH_ALLOWED_EMAILS = {
    value.strip().lower()
    for value in os.getenv("FIREBASE_AUTH_ALLOWED_EMAILS", "").split(",")
    if value.strip()
}
FIREBASE_AUTH_ALLOWLIST = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/status",
    "/api/email/oauth/setup",
    "/api/email/oauth/callback",
    "/api/email/status",
    "/boot/health",
    "/system/health",
    "/system/test-flow",
    "/favicon.ico",
    # Phase 19: Customer onboarding endpoints (public access)
    "/api/auth/signup",
    "/api/stripe/webhook",
    "/api/billing/publishable-key",
}

FIREBASE_AUTH_ALLOWLIST_PREFIXES = [
    "/api/whiteboard",
    "/api/recipes",
    "/api/missions",
    "/api/intelligence",  # Allow anonymous access to predictions and insights
    "/api/security",  # Allow anonymous access to security monitoring (Phase 13)
    "/api/voice",  # Allow anonymous access to AI phone system (Phase 9)
    "/api/twilio",  # Allow anonymous Twilio webhooks
    "/conversation",  # Allow anonymous access to conversation sessions
    "/chat/integrated"  # Allow anonymous chat access
]


def _init_firebase_admin() -> bool:
    if not FIREBASE_AUTH_ENABLED:
        return False
    if not _FIREBASE_AUTH_AVAILABLE:
        logging.error("Firebase Auth is enabled but firebase_admin is unavailable")
        return False
    if firebase_admin._apps:
        return True

    try:
        # Priority 1: Check for local credentials file
        from pathlib import Path
        local_creds_path = Path(__file__).parent / "firebase-adminsdk.json"
        if local_creds_path.exists():
            cred = firebase_credentials.Certificate(str(local_creds_path))
            firebase_admin.initialize_app(cred)
            logging.info(f"Initialized Firebase Admin with local credentials: {local_creds_path}")
            return True
        
        # Priority 2: Check for environment variable path
        if Config.FIREBASE_CREDENTIALS_PATH:
            cred = firebase_credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            logging.info(f"Initialized Firebase Admin with credentials from: {Config.FIREBASE_CREDENTIALS_PATH}")
            return True
        
        # Priority 3: Check for JSON string in environment
        if Config.FIREBASE_CREDENTIALS_JSON:
            payload = json.loads(Config.FIREBASE_CREDENTIALS_JSON)
            cred = firebase_credentials.Certificate(payload)
            firebase_admin.initialize_app(cred)
            logging.info("Initialized Firebase Admin with JSON credentials")
            return True
        
        # Priority 4: Check for individual credential environment variables
        if Config.FIREBASE_PROJECT_ID and Config.FIREBASE_CLIENT_EMAIL and Config.FIREBASE_PRIVATE_KEY:
            private_key = Config.FIREBASE_PRIVATE_KEY.replace("\\n", "\n")
            payload = {
                "type": "service_account",
                "project_id": Config.FIREBASE_PROJECT_ID,
                "client_email": Config.FIREBASE_CLIENT_EMAIL,
                "private_key": private_key,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            cred = firebase_credentials.Certificate(payload)
            firebase_admin.initialize_app(cred)
            logging.info("Initialized Firebase Admin with environment variables")
            return True
    except Exception as e:
        logging.error(f"Failed to initialize Firebase Admin: {e}", exc_info=True)
        return False

    logging.error("Firebase Auth enabled but no service account credentials found")
    return False


def _extract_bearer_token(authorization_header: str) -> Optional[str]:
    if not authorization_header:
        return None
    parts = authorization_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def _verify_firebase_token(id_token: str) -> Optional[dict]:
    if not id_token:
        return None
    if not _init_firebase_admin():
        return None
    try:
        return firebase_auth.verify_id_token(id_token)
    except Exception as e:
        logging.warning(f"Firebase token verification failed: {e}")
        return None


def _is_path_allowed(path: str) -> bool:
    if path in FIREBASE_AUTH_ALLOWLIST:
        return True
    for prefix in FIREBASE_AUTH_ALLOWLIST_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _is_email_allowed(decoded: Optional[dict]) -> bool:
    if not FIREBASE_AUTH_ALLOWED_EMAILS:
        return True
    if not decoded:
        return False
    email = (decoded.get("email") or "").lower()
    return email in FIREBASE_AUTH_ALLOWED_EMAILS


async def _require_ws_auth(websocket: WebSocket) -> bool:
    if not FIREBASE_AUTH_ENABLED:
        return True
    auth_header = websocket.headers.get("Authorization", "")
    id_token = _extract_bearer_token(auth_header)
    if not id_token:
        id_token = websocket.query_params.get("token") or websocket.query_params.get("auth")
    decoded = _verify_firebase_token(id_token)
    if not decoded:
        await websocket.close(code=4401)
        return False
    if not _is_email_allowed(decoded):
        await websocket.close(code=4403)
        return False
    websocket.state.user = decoded
    return True


@app.middleware("http")
async def firebase_auth_middleware(request: Request, call_next):
    if not FIREBASE_AUTH_ENABLED or _is_path_allowed(request.url.path):
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    id_token = _extract_bearer_token(auth_header)
    decoded = _verify_firebase_token(id_token)
    if not decoded:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not _is_email_allowed(decoded):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})

    request.state.user = decoded
    
    # Phase 19: Add tenant_id lookup for authenticated users
    if _SIGNUP_SERVICE_AVAILABLE:
        try:
            signup_service = SignupService()
            tenant_id = signup_service.get_tenant_by_firebase_uid(decoded.get("uid"))
            request.state.tenant_id = tenant_id
        except Exception as e:
            logging.warning(f"Failed to lookup tenant_id for user {decoded.get('uid')}: {e}")
            request.state.tenant_id = None
    else:
        request.state.tenant_id = None
    
    return await call_next(request)


@app.middleware("http")
async def api_usage_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    user = getattr(request.state, "user", None)
    user_id = None
    if isinstance(user, dict):
        user_id = user.get("uid") or user.get("user_id") or user.get("email")

    # Phase 18: Sanitize log data before writing
    log_data = sanitize_log_data({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": round(duration_ms, 2),
        "user_id": user_id,
    })
    log_api_usage(log_data)
    return response


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Phase 18: Add security headers to all responses"""
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),  # Phase 18: Restricted to specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
    expose_headers=["Content-Length", "Content-Type"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# GAP-C2: Tenant Isolation Middleware
# Enforces multi-tenant data isolation across all API endpoints
app.middleware("http")(tenant_isolation_middleware)
logging.info("✅ Tenant Isolation middleware enabled (GAP-C2)")

# PHASE 6: Include WebSocket Streaming Router
# Enables real-time progress updates via ws://localhost:8000/ws/stream/{mission_id}
if websocket_router:
    app.include_router(websocket_router)

# PHASE 3: Include WebSocket Execution Router
# Enables real-time execution streaming via ws://localhost:8000/ws/missions/{mission_id}
if ws_execution_router:
    app.include_router(ws_execution_router)

# Include Integration Manager Router
# Provides REST API for managing all 42+ integrations
try:
    from Back_End.integration_manager import router as integration_router
    app.include_router(integration_router)
    logging.info("✅ Integration Manager API loaded")
except Exception as e:
    logging.warning(f"Integration Manager API unavailable: {e}")

# Include GHL Voice Webhooks Router
# Handles inbound calls from GoHighLevel (410.403.3017)
try:
    from Back_End.ghl_webhooks import ghl_webhooks_router
    app.include_router(ghl_webhooks_router)
    logging.info("✅ GHL Voice Webhooks API loaded")
except Exception as e:
    logging.warning(f"GHL Voice Webhooks API unavailable: {e}")

# Include Twilio Voice Webhooks Router
# Handles inbound/outbound calls via Twilio with GHL sync
try:
    from Back_End.twilio_webhooks import twilio_router
    app.include_router(twilio_router)
    logging.info("✅ Twilio Voice Webhooks API loaded")
except Exception as e:
    logging.warning(f"Twilio Voice Webhooks API unavailable: {e}")

# Include AI Voice System Router (Phase 9)
# Complete AI phone agent with intent classification, sentiment, outbound calling
try:
    from Back_End.voice_api import voice_router
    app.include_router(voice_router)
    logging.info("✅ AI Voice System API loaded (inbound/outbound calling, intent classification)")
except Exception as e:
    logging.warning(f"AI Voice System API unavailable: {e}")

# Include Security Testing API Router (Phase 13)
# Self-defense system monitoring and vulnerability scanning
try:
    from Back_End.routes.security_api import router as security_router
    app.include_router(security_router)
    logging.info("✅ Security Testing API loaded")
except Exception as e:
    logging.warning(f"Security Testing API unavailable: {e}")

# PHASE 4: Intelligence API Router already registered early (before middleware)
# See line ~300 for early registration

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


# PHASE 19: Customer Onboarding Models
class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    phone: Optional[str] = None
    plan: str  # "STARTER" or "PROFESSIONAL"
    trial_days: Optional[int] = 14


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

from Back_End.execution import executor
_executor_task = None

@app.on_event("startup")
async def startup_executor():
    """Start the mission executor loop on app startup."""
    global _executor_task
    
    # Log Firebase Auth status
    logging.info(f"[MAIN] Firebase Auth Enabled: {FIREBASE_AUTH_ENABLED}")
    if FIREBASE_AUTH_ENABLED and _FIREBASE_AUTH_AVAILABLE:
        firebase_init_result = _init_firebase_admin()
        if firebase_init_result:
            logging.info("[MAIN] Firebase Admin SDK initialized successfully")
        else:
            logging.warning("[MAIN] Firebase Admin SDK failed to initialize")
    elif not _FIREBASE_AUTH_AVAILABLE:
        logging.warning("[MAIN] Firebase Auth unavailable - firebase_admin module not found")
    
    try:
        from Back_End.mission_execution_runner import start_executor_background
        _executor_task = start_executor_background()
        logging.info("[MAIN] Mission executor started")
    except Exception as e:
        logging.error(f"[MAIN] Error starting executor: {e}", exc_info=True)
    
    # PHASE 4: Start Intelligence Scheduler (Daily hypothesis refresh at 2am UTC)
    try:
        from Back_End.intelligence_scheduler import start_intelligence_scheduler
        _intelligence_task = start_intelligence_scheduler()
        logging.info("[MAIN] ✅ Intelligence scheduler started (runs daily at 2am UTC)")
    except Exception as e:
        logging.warning(f"[MAIN] Intelligence scheduler unavailable: {e}")

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


@app.get("/api/status")
async def root():
    return {"status": "running", "version": "1.0.0", "agent": "autonomous", "features": ["domains", "goal_decomposition"]}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# GAP-H2: Rate Limit Info Endpoint
@app.get("/api/rate-limit/{tier}")
async def rate_limit_status(http_request: Request, tier: str):
    """
    Get current rate limit status for a tier.
    
    Example: GET /api/rate-limit/mission
    Returns: remaining requests, reset times
    """
    try:
        tier_enum = RateLimitTier(tier)
        info = await get_rate_limit_info(http_request, tier_enum)
        return JSONResponse(content=info)
    except ValueError:
        valid_tiers = [t.value for t in RateLimitTier]
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid tier",
                "valid_tiers": valid_tiers
            }
        )


@app.get("/boot/health")
async def boot_health():
    """
    Boot-time health check reporting.
    
    Verifies that all critical systems were able to import and initialize
    when the service started. Use this to diagnose startup issues.
    
    Returns:
      - status: "healthy" if all systems loaded, "degraded" if some failed
      - boot_checks: Dictionary of each system's load status (True/False)
      - errors: Details of any failures
      - all_critical_systems_up: Boolean indicating if service is fully operational
    """
    all_up = all(_BOOT_CHECKS.values())
    return {
        "status": "healthy" if all_up else "degraded",
        "boot_checks": _BOOT_CHECKS,
        "errors": _BOOT_ERRORS if _BOOT_ERRORS else None,
        "all_critical_systems_up": all_up,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/system/health")
async def system_health_check():
    """
    Comprehensive system health check for all Buddy subsystems.
    Returns status of 7 primary systems + 15+ additional systems.
    Zero API costs - just checks if systems can be instantiated locally.
    
    Status codes:
    - green: System available and ready
    - yellow: System configured but not optimal
    - red: System failed or unavailable
    - gray: System status unknown
    
    Returns:
    {
        "overall_health": "healthy" | "degraded" | "critical" | "unknown",
        "summary": {
            "primary": {"green": X, "red": Y, "gray": Z},
            "additional": {"green": X, "red": Y, "gray": Z},
            "total": {"green": X, "red": Y, "gray": Z}
        },
        "primary_systems": {...},
        "additional_systems": {...}
    }
    """
    try:
        # Try importing from Back_End package first (normal deployment)
        # Then fall back to direct import (development/deployed from Back_End)
        try:
            from Back_End.system_health import SystemHealthMonitor
        except ImportError:
            from system_health import SystemHealthMonitor
        
        monitor = SystemHealthMonitor()
        return monitor.check_all()
    except Exception as e:
        logging.error(f"System health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Health check failed", "detail": str(e)}
        )


@app.get("/system/test-flow")
async def system_test_flow():
    """
    Run a complete end-to-end simulation of the chat flow through all systems.
    Tests message reception, Firebase session, LLM intent classification, 
    orchestrator processing, action readiness, mission store, tool registry, 
    and message persistence.
    
    Returns step-by-step trace showing which systems passed and which failed.
    
    Returns:
    {
        "test_message": "...",
        "timestamp": "...",
        "steps": [
            {"name": "Step Name", "status": "passed|failed", "detail": "details"},
            ...
        ],
        "summary": {
            "passed": X,
            "failed": Y,
            "overall": "PASSED|PARTIAL|FAILED",
            "success_rate": "X%"
        }
    }
    """
    try:
        # Try importing from Back_End package first (normal deployment)
        # Then fall back to direct import (development/deployed from Back_End)
        try:
            from Back_End.system_health import SystemFlowTester
        except ImportError:
            from system_health import SystemFlowTester
        
        tester = SystemFlowTester()
        return tester.test_complete_flow()
    except Exception as e:
        logging.error(f"System flow test failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Flow test failed", "detail": str(e)}
        )


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
    from Back_End.gohighlevel_client import ghl_client
    
    return JSONResponse(content={
        "configured": ghl_client is not None,
        "message": "GoHighLevel is ready" if ghl_client else "GoHighLevel not configured"
    })

# ============================================================================
# PHASE 19: CUSTOMER ONBOARDING & SIGNUP ENDPOINTS
# ============================================================================

@app.post("/api/auth/signup")
@rate_limit(tier=RateLimitTier.AUTH)  # GAP-H2: 5 req/min, 20 req/hour
async def customer_signup(http_request: Request, request: SignupRequest):
    """
    Customer signup endpoint - Creates Firebase user, tenant, and Stripe checkout session.
    
    Flow:
    1. Validate email, password, plan
    2. Create Firebase user (authentication)
    3. Create tenant in tenant database (status=PENDING)
    4. Create Stripe customer and checkout session
    5. Return checkout_url for payment redirect
    6. After payment, webhook activates tenant (status=ACTIVE)
    
    Returns:
    {
        "success": true,
        "checkout_url": "https://checkout.stripe.com/...",
        "tenant_id": "...",
        "firebase_uid": "...",
        "message": "Account created. Complete payment to activate."
    }
    """
    if not _SIGNUP_SERVICE_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "Signup service unavailable", "detail": "SignupService not initialized"}
        )
    
    try:
        signup_service = SignupService()
        
        # Validate inputs
        email_valid, email_msg = signup_service.validate_email(request.email)
        if not email_valid:
            return JSONResponse(status_code=400, content={"error": "Invalid email", "detail": email_msg})
        
        password_valid, password_msg = signup_service.validate_password(request.password)
        if not password_valid:
            return JSONResponse(status_code=400, content={"error": "Invalid password", "detail": password_msg})
        
        plan_valid, plan_msg = signup_service.validate_plan(request.plan)
        if not plan_valid:
            return JSONResponse(status_code=400, content={"error": "Invalid plan", "detail": plan_msg})
        
        # Create customer account (Firebase + Tenant + Stripe)
        result = signup_service.create_customer_account(
            email=request.email,
            password=request.password,
            name=request.name,
            phone=request.phone,
            plan=request.plan,
            trial_days=request.trial_days
        )
        
        return JSONResponse(content={
            "success": True,
            "checkout_url": result["checkout_url"],
            "tenant_id": result["tenant_id"],
            "firebase_uid": result["firebase_uid"],
            "message": "Account created successfully. Complete payment to activate your subscription."
        })
        
    except Exception as e:
        logging.error(f"Signup failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Signup failed", "detail": str(e)}
        )


@app.post("/api/stripe/webhook")
@rate_limit(tier=RateLimitTier.WEBHOOK)  # GAP-H2: 100 req/min, 10k req/hour
async def stripe_webhook(request: Request):
    """
    Stripe webhook handler - Processes payment events and activates tenants.
    
    Events handled:
    - checkout.session.completed: Activate tenant after successful payment
    - invoice.payment_failed: Suspend tenant for failed payment
    - customer.subscription.updated: Update tenant subscription status
    - customer.subscription.deleted: Deactivate tenant
    
    Verifies Stripe webhook signature for security.
    """
    if not _SIGNUP_SERVICE_AVAILABLE or not stripe:
        return JSONResponse(
            status_code=503,
            content={"error": "Webhook service unavailable"}
        )
    
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        logging.error("STRIPE_WEBHOOK_SECRET not configured")
        return JSONResponse(status_code=500, content={"error": "Webhook not configured"})
    
    try:
        # Get raw body and signature
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            logging.error(f"Invalid webhook payload: {e}")
            return JSONResponse(status_code=400, content={"error": "Invalid payload"})
        except stripe.error.SignatureVerificationError as e:
            logging.error(f"Invalid webhook signature: {e}")
            return JSONResponse(status_code=400, content={"error": "Invalid signature"})
        
        # Handle event
        event_type = event["type"]
        event_data = event["data"]["object"]
        
        signup_service = SignupService()
        
        if event_type == "checkout.session.completed":
            # Payment successful - activate tenant
            session = event_data
            customer_id = session.get("customer")
            
            if customer_id:
                success = signup_service.activate_tenant_after_payment(customer_id)
                if success:
                    logging.info(f"Tenant activated for Stripe customer: {customer_id}")
                else:
                    logging.error(f"Failed to activate tenant for customer: {customer_id}")
        
        elif event_type == "invoice.payment_failed":
            # Payment failed - could suspend tenant
            invoice = event_data
            customer_id = invoice.get("customer")
            logging.warning(f"Payment failed for customer: {customer_id}")
            # TODO: Implement tenant suspension logic
        
        elif event_type == "customer.subscription.updated":
            # Subscription changed - could update tenant plan
            subscription = event_data
            customer_id = subscription.get("customer")
            status = subscription.get("status")
            logging.info(f"Subscription updated for customer {customer_id}: {status}")
            # TODO: Implement plan update logic
        
        elif event_type == "customer.subscription.deleted":
            # Subscription canceled - could deactivate tenant
            subscription = event_data
            customer_id = subscription.get("customer")
            logging.warning(f"Subscription canceled for customer: {customer_id}")
            # TODO: Implement tenant deactivation logic
        
        return JSONResponse(content={"received": True, "event_type": event_type})
        
    except Exception as e:
        logging.error(f"Webhook processing failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Webhook processing failed", "detail": str(e)}
        )

# ============================================================================
# PHASE 18B: EMBEDDED BILLING DASHBOARD ENDPOINTS
# ============================================================================

@app.get("/api/billing/subscription")
async def get_billing_subscription(request: Request):
    """
    Get current subscription details for authenticated customer.
    
    Returns:
    {
        'subscription_id': str,
        'status': 'active'|'trialing'|'past_due'|'canceled',
        'plan': 'STARTER'|'PROFESSIONAL',
        'current_period_start': datetime,
        'current_period_end': datetime,
        'cancel_at_period_end': bool,
        'default_payment_method': {...}
    }
    """
    if not _BILLING_DASHBOARD_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "Billing dashboard service unavailable"}
        )
    
    try:
        # Get tenant_id from auth middleware
        tenant_id = getattr(request.state, 'tenant_id', None)
        if not tenant_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        # Get tenant's Stripe customer ID
        from Back_End.buddy_tenant_manager import TenantManager
        tenant_manager = TenantManager()
        tenant = tenant_manager.get_tenant(tenant_id)
        
        if not tenant or not tenant.stripe_customer_id:
            return JSONResponse(
                status_code=404,
                content={"error": "No billing account found"}
            )
        
        # Fetch subscription details
        billing_service = BillingDashboardService()
        details = billing_service.get_subscription_details(tenant.stripe_customer_id)
        
        return JSONResponse(content=details)
        
    except Exception as e:
        logging.error(f"Failed to get subscription details: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to fetch subscription", "detail": str(e)}
        )


@app.get("/api/billing/invoices")
async def get_billing_invoices(request: Request, limit: int = 10):
    """
    Get paginated list of customer invoices.
    
    Query params:
    - limit: Maximum number of invoices (default: 10)
    
    Returns: List of invoices with PDF download links
    """
    if not _BILLING_DASHBOARD_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "Billing dashboard service unavailable"}
        )
    
    try:
        tenant_id = getattr(request.state, 'tenant_id', None)
        if not tenant_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        from Back_End.buddy_tenant_manager import TenantManager
        tenant_manager = TenantManager()
        tenant = tenant_manager.get_tenant(tenant_id)
        
        if not tenant or not tenant.stripe_customer_id:
            return JSONResponse(
                status_code=404,
                content={"error": "No billing account found"}
            )
        
        billing_service = BillingDashboardService()
        invoices = billing_service.get_invoices(tenant.stripe_customer_id, limit=limit)
        
        return JSONResponse(content={"invoices": invoices})
        
    except Exception as e:
        logging.error(f"Failed to get invoices: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to fetch invoices", "detail": str(e)}
        )


@app.get("/api/billing/usage")
async def get_billing_usage(request: Request):
    """
    Get current billing period usage summary.
    
    Returns:
    {
        'period_start': datetime,
        'period_end': datetime,
        'usage_items': [{description, quantity, unit, included_in_plan, overage}],
        'upcoming_invoice_total': int
    }
    """
    if not _BILLING_DASHBOARD_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "Billing dashboard service unavailable"}
        )
    
    try:
        tenant_id = getattr(request.state, 'tenant_id', None)
        if not tenant_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        from Back_End.buddy_tenant_manager import TenantManager
        tenant_manager = TenantManager()
        tenant = tenant_manager.get_tenant(tenant_id)
        
        if not tenant or not tenant.stripe_customer_id:
            return JSONResponse(
                status_code=404,
                content={"error": "No billing account found"}
            )
        
        billing_service = BillingDashboardService()
        usage = billing_service.get_usage_summary(tenant.stripe_customer_id)
        
        return JSONResponse(content=usage)
        
    except Exception as e:
        logging.error(f"Failed to get usage summary: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to fetch usage", "detail": str(e)}
        )


@app.post("/api/billing/payment-method/setup")
async def setup_payment_method(request: Request):
    """
    Create a SetupIntent for updating payment method.
    
    Returns:
    {
        'client_secret': str,  # Pass to Stripe.js confirmSetup()
        'setup_intent_id': str
    }
    """
    if not _BILLING_DASHBOARD_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "Billing dashboard service unavailable"}
        )
    
    try:
        tenant_id = getattr(request.state, 'tenant_id', None)
        if not tenant_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        from Back_End.buddy_tenant_manager import TenantManager
        tenant_manager = TenantManager()
        tenant = tenant_manager.get_tenant(tenant_id)
        
        if not tenant or not tenant.stripe_customer_id:
            return JSONResponse(
                status_code=404,
                content={"error": "No billing account found"}
            )
        
        billing_service = BillingDashboardService()
        setup_intent = billing_service.create_payment_method_setup_intent(tenant.stripe_customer_id)
        
        return JSONResponse(content=setup_intent)
        
    except Exception as e:
        logging.error(f"Failed to create SetupIntent: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to setup payment method", "detail": str(e)}
        )


class PlanChangeRequest(BaseModel):
    new_plan: str  # "STARTER" or "PROFESSIONAL"


@app.post("/api/billing/subscription/preview-change")
async def preview_plan_change(request: Request, body: PlanChangeRequest):
    """
    Preview proration for plan change.
    
    Request body:
    {
        "new_plan": "PROFESSIONAL"
    }
    
    Returns:
    {
        'immediate_charge': int,  # in cents (positive = charge, negative = credit)
        'next_invoice_total': int,
        'proration_date': datetime
    }
    """
    if not _BILLING_DASHBOARD_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "Billing dashboard service unavailable"}
        )
    
    try:
        tenant_id = getattr(request.state, 'tenant_id', None)
        if not tenant_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        # Validate plan
        if body.new_plan.upper() not in ['STARTER', 'PROFESSIONAL']:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid plan. Must be STARTER or PROFESSIONAL"}
            )
        
        # Get price ID from environment
        if body.new_plan.upper() == 'STARTER':
            new_price_id = os.getenv('STRIPE_STARTER_PRICE_ID')
        else:
            new_price_id = os.getenv('STRIPE_PROFESSIONAL_PRICE_ID')
        
        if not new_price_id:
            return JSONResponse(
                status_code=500,
                content={"error": f"Price ID not configured for {body.new_plan}"}
            )
        
        from Back_End.buddy_tenant_manager import TenantManager
        tenant_manager = TenantManager()
        tenant = tenant_manager.get_tenant(tenant_id)
        
        if not tenant or not tenant.stripe_customer_id:
            return JSONResponse(
                status_code=404,
                content={"error": "No billing account found"}
            )
        
        billing_service = BillingDashboardService()
        preview = billing_service.preview_plan_change(
            tenant.stripe_customer_id,
            new_price_id
        )
        
        return JSONResponse(content=preview)
        
    except Exception as e:
        logging.error(f"Failed to preview plan change: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to preview plan change", "detail": str(e)}
        )


@app.post("/api/billing/subscription/change-plan")
async def change_subscription_plan(request: Request, body: PlanChangeRequest):
    """
    Change subscription plan with proration.
    
    Request body:
    {
        "new_plan": "PROFESSIONAL"
    }
    
    Returns:
    {
        'success': True,
        'subscription_id': str,
        'new_plan': 'PROFESSIONAL',
        'effective_date': datetime
    }
    """
    if not _BILLING_DASHBOARD_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "Billing dashboard service unavailable"}
        )
    
    try:
        tenant_id = getattr(request.state, 'tenant_id', None)
        if not tenant_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        # Validate plan
        if body.new_plan.upper() not in ['STARTER', 'PROFESSIONAL']:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid plan. Must be STARTER or PROFESSIONAL"}
            )
        
        # Get price ID from environment
        if body.new_plan.upper() == 'STARTER':
            new_price_id = os.getenv('STRIPE_STARTER_PRICE_ID')
        else:
            new_price_id = os.getenv('STRIPE_PROFESSIONAL_PRICE_ID')
        
        if not new_price_id:
            return JSONResponse(
                status_code=500,
                content={"error": f"Price ID not configured for {body.new_plan}"}
            )
        
        from Back_End.buddy_tenant_manager import TenantManager
        tenant_manager = TenantManager()
        tenant = tenant_manager.get_tenant(tenant_id)
        
        if not tenant or not tenant.stripe_customer_id:
            return JSONResponse(
                status_code=404,
                content={"error": "No billing account found"}
            )
        
        billing_service = BillingDashboardService()
        result = billing_service.change_subscription_plan(
            tenant.stripe_customer_id,
            new_price_id
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logging.error(f"Failed to change subscription plan: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to change plan", "detail": str(e)}
        )


class CancelSubscriptionRequest(BaseModel):
    immediately: bool = False


@app.post("/api/billing/subscription/cancel")
async def cancel_subscription(request: Request, body: CancelSubscriptionRequest):
    """
    Cancel subscription (immediately or at period end).
    
    Request body:
    {
        "immediately": false  # true = cancel now, false = cancel at period end
    }
    
    Returns:
    {
        'success': True,
        'subscription_id': str,
        'canceled_at': datetime,
        'ends_at': datetime
    }
    """
    if not _BILLING_DASHBOARD_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "Billing dashboard service unavailable"}
        )
    
    try:
        tenant_id = getattr(request.state, 'tenant_id', None)
        if not tenant_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        from Back_End.buddy_tenant_manager import TenantManager
        tenant_manager = TenantManager()
        tenant = tenant_manager.get_tenant(tenant_id)
        
        if not tenant or not tenant.stripe_customer_id:
            return JSONResponse(
                status_code=404,
                content={"error": "No billing account found"}
            )
        
        billing_service = BillingDashboardService()
        result = billing_service.cancel_subscription(
            tenant.stripe_customer_id,
            immediately=body.immediately
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logging.error(f"Failed to cancel subscription: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to cancel subscription", "detail": str(e)}
        )


@app.get("/api/billing/publishable-key")
async def get_stripe_publishable_key():
    """
    Get Stripe publishable key for client-side Stripe.js initialization.
    Public endpoint (no auth required).
    """
    publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
    if not publishable_key:
        return JSONResponse(
            status_code=500,
            content={"error": "Stripe publishable key not configured"}
        )
    
    return JSONResponse(content={"publishable_key": publishable_key})


# ============================================================================
# PHASE 24: PAYMENT VAULT ENDPOINTS (Autonomous API Acquisition)
# ============================================================================

class StorePaymentMethodRequest(BaseModel):
    card_number: str
    expiry_month: str
    expiry_year: str
    cvc: str
    name_on_card: str
    billing_address: Dict[str, str]
    spending_limits: Optional[Dict[str, float]] = None
    label: str = 'primary'


@app.post("/api/payment/store")
async def store_payment_method(request: Request, body: StorePaymentMethodRequest):
    """
    Store user's payment method for autonomous API purchases.
    
    Request body:
    {
        "card_number": "4111111111111111",
        "expiry_month": "12",
        "expiry_year": "2028",
        "cvc": "123",
        "name_on_card": "John Doe",
        "billing_address": {
            "line1": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip": "10001",
            "country": "US"
        },
        "spending_limits": {
            "single": 100.0,
            "daily": 200.0,
            "monthly": 1000.0
        },
        "label": "primary"
    }
    
    Returns:
    {
        'success': true,
        'message': 'Payment method stored securely'
    }
    """
    try:
        # Get user ID from authentication (use tenant_id for now)
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        from Back_End.buddy_payment_vault import get_payment_vault
        vault = get_payment_vault()
        
        success = vault.store_payment_method(
            user_id=user_id,
            card_number=body.card_number,
            expiry_month=body.expiry_month,
            expiry_year=body.expiry_year,
            cvc=body.cvc,
            name_on_card=body.name_on_card,
            billing_address=body.billing_address,
            label=body.label,
            spending_limits=body.spending_limits
        )
        
        if success:
            return JSONResponse(content={
                "success": True, 
                "message": "Payment method stored securely"
            })
        else:
            return JSONResponse(
                status_code=500, 
                content={"error": "Failed to store payment method"}
            )
    
    except Exception as e:
        logging.error(f"Error storing payment method: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"error": str(e)}
        )


@app.get("/api/payment/info")
async def get_payment_info(request: Request):
    """
    Get payment method info (safe details only - no full card number).
    
    Returns:
    {
        'has_payment_method': true,
        'methods': [{
            'label': 'primary',
            'card_type': 'visa',
            'last_4_digits': '1111',
            'spending_limits': {'single': 100.0, 'daily': 200.0, 'monthly': 1000.0},
            'is_default': true
        }],
        'spent_today': 40.00,
        'spent_this_month': 150.00
    }
    """
    try:
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        from Back_End.buddy_payment_vault import get_payment_vault
        vault = get_payment_vault()
        
        methods = vault.list_payment_methods(user_id)
        
        if not methods:
            return JSONResponse(content={"has_payment_method": False})
        
        # Return safe details only (no full card numbers)
        return JSONResponse(content={
            "has_payment_method": True,
            "methods": methods,
            "spent_today": vault.get_spending_today(user_id),
            "spent_this_month": vault.get_spending_this_month(user_id)
        })
    
    except Exception as e:
        logging.error(f"Error getting payment info: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"error": str(e)}
        )


@app.get("/api/payment/spending")
async def get_spending_history(request: Request, days: int = 30):
    """
    Get autonomous API spending history.
    
    Query params:
    - days: Number of days to look back (default: 30)
    
    Returns:
    {
        'spending': [{
            'provider': 'OpenWeatherMap',
            'amount': 40.00,
            'description': 'Startup tier subscription',
            'status': 'completed',
            'timestamp': '2026-02-13T10:30:00Z'
        }],
        'total_spent': 150.00
    }
    """
    try:
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        from Back_End.buddy_payment_vault import get_payment_vault
        vault = get_payment_vault()
        
        entries = vault.get_spending_history(user_id, days=days)
        
        spending_list = [entry.to_dict() for entry in entries]
        total = sum(e['amount'] for e in spending_list if e['status'] == 'completed')
        
        return JSONResponse(content={
            "spending": spending_list,
            "total_spent": total
        })
    
    except Exception as e:
        logging.error(f"Error getting spending history: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"error": str(e)}
        )


@app.delete("/api/payment/method/{label}")
async def delete_payment_method(request: Request, label: str):
    """
    Delete a payment method.
    
    Path params:
    - label: Payment method label (e.g., 'primary', 'backup')
    
    Returns:
    {
        'success': true,
        'message': 'Payment method deleted'
    }
    """
    try:
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        from Back_End.buddy_payment_vault import get_payment_vault
        vault = get_payment_vault()
        
        deleted = vault.delete_payment_method(user_id, label)
        
        if deleted:
            return JSONResponse(content={
                "success": True,
                "message": "Payment method deleted"
            })
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "Payment method not found"}
            )
    
    except Exception as e:
        logging.error(f"Error deleting payment method: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# ============================================================================
# PHASE 24: API ACQUISITION APPROVAL SYSTEM
# ============================================================================

class ApprovalPreferencesRequest(BaseModel):
    automation_mode: Optional[str] = None
    auto_approve_free_apis: Optional[bool] = None
    auto_approve_under_amount: Optional[float] = None
    api_budget_monthly: Optional[float] = None
    default_payment_method: Optional[str] = None


class ApprovalRequestPayload(BaseModel):
    provider: str
    estimated_cost: float = 0.0
    free_tier: bool = True
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ApprovalDecisionPayload(BaseModel):
    request_id: str
    approved: bool
    decision_notes: Optional[str] = None


@app.get("/api/approval/preferences")
async def get_approval_preferences(request: Request):
    """Get approval preferences for autonomous API acquisition."""
    try:
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})

        from Back_End.api_acquisition_approval import get_approval_store
        store = get_approval_store()
        prefs = store.get_preferences(user_id)

        return JSONResponse(content={"success": True, "preferences": prefs})

    except Exception as e:
        logging.error(f"Error getting approval preferences: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/approval/preferences")
async def update_approval_preferences(request: Request, body: ApprovalPreferencesRequest):
    """Update approval preferences for autonomous API acquisition."""
    try:
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})

        from Back_End.api_acquisition_approval import get_approval_store
        store = get_approval_store()
        updates = body.dict(exclude_none=True)
        prefs = store.update_preferences(user_id, updates)

        return JSONResponse(content={"success": True, "preferences": prefs})

    except Exception as e:
        logging.error(f"Error updating approval preferences: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/approval/pending")
async def get_pending_approvals(request: Request):
    """Get pending approval requests for the current user."""
    try:
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})

        from Back_End.api_acquisition_approval import get_approval_store
        store = get_approval_store()
        pending = store.list_pending(user_id)

        return JSONResponse(content={"success": True, "requests": pending})

    except Exception as e:
        logging.error(f"Error fetching pending approvals: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/approval/request")
async def create_approval_request(request: Request, body: ApprovalRequestPayload):
    """Create a new approval request for API acquisition."""
    try:
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})

        from Back_End.api_acquisition_approval import get_approval_store
        store = get_approval_store()
        req = store.create_request(
            user_id=user_id,
            provider=body.provider,
            estimated_cost=body.estimated_cost,
            free_tier=body.free_tier,
            reason=body.reason,
            metadata=body.metadata
        )

        return JSONResponse(content={"success": True, "request": req})

    except Exception as e:
        logging.error(f"Error creating approval request: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/approval/decision")
async def decide_approval_request(request: Request, body: ApprovalDecisionPayload):
    """Approve or deny a pending API acquisition request."""
    try:
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})

        from Back_End.api_acquisition_approval import get_approval_store
        store = get_approval_store()
        result = store.decide_request(
            user_id=user_id,
            request_id=body.request_id,
            approved=body.approved,
            decision_notes=body.decision_notes
        )

        status_code = 200 if result.get("success") else 404
        return JSONResponse(status_code=status_code, content=result)

    except Exception as e:
        logging.error(f"Error deciding approval request: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/usage/monitor")
async def get_usage_monitor(request: Request, days: int = 30):
    """Get API usage summary and alerts for autonomous API spending."""
    try:
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})

        from Back_End.api_usage_monitor import get_usage_summary
        summary = get_usage_summary(user_id, days=days)
        return JSONResponse(content=summary)

    except Exception as e:
        logging.error(f"Error getting usage monitor: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


# ============================================================================
# GAP-H3: AUDIT LOG QUERY ENDPOINTS
# ============================================================================

@app.get("/api/audit/logs")
@rate_limit(tier=RateLimitTier.READ)  # GAP-H2: 300 req/min
async def get_audit_logs_endpoint(
    http_request: Request,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    limit: int = 100
):
    """
    Query audit logs for current tenant.
    
    Query params:
    - user_id: Filter by user
    - action: Filter by action (e.g., "mission.create")
    - resource_type: Filter by resource type
    - resource_id: Filter by specific resource
    - limit: Max results (default 100, max 1000)
    """
    try:
        tenant_id = get_current_tenant(http_request)
        if not tenant_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        # Validate limit
        limit = min(limit, 1000)  # Cap at 1000
        
        # Convert action string to AuditAction enum if provided
        action_enum = None
        if action:
            try:
                action_enum = AuditAction(action)
            except ValueError:
                pass
        
        # Query audit logs
        logs = query_audit_logs(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action_enum,
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit
        )
        
        return JSONResponse(content={
            "logs": logs,
            "count": len(logs),
            "tenant_id": tenant_id
        })
    
    except Exception as e:
        logging.error(f"Error querying audit logs: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/audit/actions")
async def get_audit_actions_list():
    """Get list of all available audit actions for filtering."""
    actions = []
    for action in AuditAction:
        category = action.value.split(".")[0]
        actions.append({
            "value": action.value,
            "category": category
        })
    
    return JSONResponse(content={"actions": actions})


# ============================================================================
# PHASE 24: ACQUISITION COORDINATOR ENDPOINTS
# ============================================================================

class AcquisitionRequestPayload(BaseModel):
    integration_id: str
    estimated_cost: float = 0.0
    free_tier: bool = True
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AcquisitionExecutePayload(BaseModel):
    integration_id: str
    user_email: str
    user_password: str
    request_id: Optional[str] = None
    payment_method_label: str = "primary"
    approve_paid: bool = False


@app.post("/api/acquisition/request")
async def request_api_acquisition(request: Request, body: AcquisitionRequestPayload):
    """Create approval request for autonomous API acquisition."""
    try:
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})

        from Back_End.buddy_acquisition_coordinator import get_acquisition_coordinator
        coordinator = get_acquisition_coordinator()
        req = coordinator.create_request(
            user_id=user_id,
            integration_id=body.integration_id,
            estimated_cost=body.estimated_cost,
            free_tier=body.free_tier,
            reason=body.reason,
            metadata=body.metadata
        )

        return JSONResponse(content={"success": True, "request": req})

    except Exception as e:
        logging.error(f"Error creating acquisition request: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/acquisition/execute")
async def execute_api_acquisition(request: Request, body: AcquisitionExecutePayload):
    """Execute autonomous API acquisition after approval."""
    try:
        user_id = getattr(request.state, 'tenant_id', None)
        if not user_id:
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})

        from Back_End.buddy_acquisition_coordinator import get_acquisition_coordinator
        coordinator = get_acquisition_coordinator()
        result = await coordinator.execute_acquisition(
            user_id=user_id,
            integration_id=body.integration_id,
            user_email=body.user_email,
            user_password=body.user_password,
            payment_method_label=body.payment_method_label,
            approve_paid=body.approve_paid,
            request_id=body.request_id
        )

        status_code = 200 if result.get("success") else 400
        return JSONResponse(status_code=status_code, content=result)

    except Exception as e:
        logging.error(f"Error executing acquisition: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


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
@rate_limit(tier=RateLimitTier.MISSION)  # GAP-H2: 30 req/min, 200 req/hour
async def create_task(http_request: Request, request: TaskRequest):
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
        if not await _require_ws_auth(websocket):
            return
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
                from Back_End.streaming_executor import StreamingExecutor
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
    from Back_End.goal_decomposer import goal_decomposer
    classification = goal_decomposer.classify_goal(goal)
    return JSONResponse(content=classification)

@app.get("/chat/analyze-complexity")
async def analyze_complexity(goal: str):
    """Analyze goal complexity using iterative logic"""
    from Back_End.iterative_decomposer import iterative_decomposer
    analysis = iterative_decomposer.analyze_goal_complexity(goal)
    return JSONResponse(content=analysis)


@app.get("/conversation/sessions")
async def list_conversation_sessions_api():
    """List all conversation sessions across sources."""
    return JSONResponse(content={"sessions": list_conversation_sessions()})


@app.post("/conversation/sessions/create")
async def create_conversation_session_api(request: Request):
    """Create a new conversation session and return its ID."""
    body = await request.json()
    source = body.get("source") or "chat_ui"
    external_user_id = body.get("external_user_id")
    session_id = body.get("session_id") or f"session_{uuid.uuid4().hex[:8]}"

    store = get_conversation_store()
    session = store.get_or_create(
        session_id=session_id,
        source=source,
        external_user_id=external_user_id,
    )
    return JSONResponse(content={"status": "success", "session_id": session.session_id})


@app.get("/conversation/sessions/{session_id}")
async def get_conversation_session_api(session_id: str):
    """Get a full conversation session by ID."""
    session = get_conversation_session(session_id)
    if not session:
        # Create-on-read to prevent UI 404s after deploys or cache misses.
        store = get_conversation_store()
        created = store.get_or_create(
            session_id=session_id,
            source="chat_ui",
            external_user_id=None,
        )
        return JSONResponse(content=created.to_dict())
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
        from Back_End.observability import DuplicateDetector, ensure_observability_dirs
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
        from Back_End.chat_session_handler import ChatMessage
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
        
        # CRITICAL: Persist messages to ConversationStore for Firebase sync
        from Back_End.conversation.session_store import get_conversation_store
        try:
            store = get_conversation_store()
            # IMPORTANT: Ensure session exists in Firebase BEFORE appending messages
            store.get_or_create(
                session_id=session_id,
                source=request.source or 'chat_ui',
                external_user_id=user_id if user_id != "anonymous" else None
            )
            # Now save user message
            store.append_message(session_id, 'user', request.text, 'chat_ui')
            # Save assistant response
            store.append_message(session_id, 'assistant', chat_response.envelope.summary, 'chat_ui')
            logging.info(f"[MESSAGE_PERSISTENCE] Saved user + assistant messages to session {session_id}")
        except Exception as e:
            logging.error(f"[MESSAGE_PERSISTENCE_ERROR] Failed to save messages: {e}")
            # Continue anyway - don't block response
        
        envelope_dict = chat_response.envelope.to_dict()
        envelope_payload = {
            "response_type": envelope_dict.get("response_type"),
            "summary": envelope_dict.get("summary"),
            "missions_spawned": envelope_dict.get("missions_spawned", []),
            "signals_emitted": len(envelope_dict.get("signals_emitted", [])),
            "artifacts": envelope_dict.get("artifacts", []),
            "live_stream_id": envelope_dict.get("live_stream_id"),
            "ui_hints": envelope_dict.get("ui_hints"),
            "metadata": envelope_dict.get("metadata"),
            "reality_assessment": envelope_dict.get("reality_assessment"),
            "timestamp": envelope_dict.get("timestamp"),
        }

        # Return ResponseEnvelope as JSON
        return JSONResponse(
            content={
                "status": "success",
                "trace_id": trace_id,  # Echo trace_id for client-side correlation
                "chat_message_id": chat_response.message_id,
                "session_id": chat_response.session_id,
                "envelope": envelope_payload
            }
        )
    except Exception as e:
        logging.error(f"Error in /chat/integrated: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )


def _simple_approve_mission(mission_id: str) -> Dict[str, Any]:
    """
    Simple approval function that transitions mission from proposed → approved.
    Updates mission status directly in mission_store.
    """
    try:
        from Back_End.mission_store import get_mission_store, Mission
        store = get_mission_store()
        
        # Find the mission
        mission = store.find_mission(mission_id)
        if not mission:
            return {
                'success': False,
                'message': f'Mission {mission_id} not found'
            }
        
        # Check current status
        if mission.status != 'proposed':
            return {
                'success': False,
                'message': f'Mission is in state "{mission.status}", not "proposed"'
            }
        
        # Write approval event
        approval_event = Mission(
            mission_id=mission_id,
            event_type='mission_status_update',
            status='approved',
            objective=mission.objective,
            metadata={'reason': 'user_approval'}
        )
        
        store.write_mission_event(approval_event)
        
        return {
            'success': True,
            'mission_id': mission_id,
            'status': 'approved'
        }
    except Exception as e:
        logging.error(f"Error in simple approve: {e}", exc_info=True)
        return {
            'success': False,
            'message': str(e)
        }


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
        
        result = _simple_approve_mission(mission_id)
        
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
        from Back_End.execution_service import execute_mission
        
        logging.info(f"[API] POST /api/missions/{mission_id}/execute")
        
        # Call execution service
        result = execute_mission(mission_id)
        
        # Check if execution succeeded
        if result.get('success'):
            response_content = {
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
            
            # Include quality score if available
            if result.get('quality_score'):
                response_content['quality'] = result.get('quality_score')
            
            return JSONResponse(
                status_code=200,
                content=response_content
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


@app.get("/api/missions/{mission_id}")
async def get_mission_details(mission_id: str):
    """
    Get mission details including events and current status.
    """
    try:
        from Back_End.mission_store import get_mission_store
        store = get_mission_store()
        
        # Get mission
        mission = store.find_mission(mission_id)
        if not mission:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"Mission {mission_id} not found"}
            )
        
        # Get all events for this mission
        events = store.get_mission_events(mission_id)
        
        # Format response
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "mission_id": mission_id,
                "current_status": mission.status,
                "objective": mission.objective,
                "events": [{
                    "event_type": e.event_type,
                    "status": e.status,
                    "metadata": e.metadata
                } for e in events]
            }
        )
    except Exception as e:
        logging.error(f"Error getting mission {mission_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/missions/{mission_id}/progress")
async def get_mission_progress(mission_id: str):
    """
    Get current execution progress for a mission.
    
    PHASE 1.2: Firebase-persisted progress retrieval
    
    Args:
        mission_id: Mission ID to get progress for
    
    Returns:
        HTTP 200: {
            "status": "success",
            "mission_id": "...",
            "progress_percent": 0-100,
            "current_step": {...},
            "completed_steps": [...],
            "elapsed_seconds": float,
            "estimated_time_remaining": float,
            "execution_status": "in_progress" | "completed" | "failed"
        }
        HTTP 404: {"status": "error", "message": "Mission not found"}
    """
    try:
        from Back_End.mission_store import get_mission_store
        
        logging.info(f"[API] GET /api/missions/{mission_id}/progress")
        
        mission_store = get_mission_store()
        progress = mission_store.get_mission_progress(mission_id)
        
        if 'error' in progress:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "mission_id": mission_id,
                    "message": progress['error']
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "mission_id": mission_id,
                "progress_percent": progress.get('progress_percent', 0),
                "current_step": progress.get('current_step'),
                "completed_steps": progress.get('completed_steps', []),
                "elapsed_seconds": progress.get('elapsed_seconds', 0),
                "estimated_time_remaining": progress.get('estimated_time_remaining', 0),
                "execution_status": progress.get('status', 'unknown')
            }
        )
    except Exception as e:
        logging.error(f"Error retrieving progress for mission {mission_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "mission_id": mission_id,
                "message": str(e)
            }
        )


@app.put("/api/missions/{mission_id}/update")
async def update_mission_api(mission_id: str, request_body: dict):
    """
    Update/clarify a mission during execution.
    
    PHASE 2: Mission Update Endpoint
    
    Allows users to modify missions without restarting execution:
    - Add clarifications
    - Update scope constraints
    - Refine objectives
    - Update metadata
    
    Args:
        mission_id: Mission to update
        request_body: {
            "update_type": "clarification" | "scope_change" | "objective_refinement" | "metadata_update",
            "update_data": {...},
            "reason": "optional explanation"
        }
    
    Returns:
        HTTP 200: {"status": "success", "mission_id": "...", "update_id": "..."}
        HTTP 400: {"status": "error", "message": "..."}
        HTTP 500: {"status": "error", "message": "..."}
    """
    try:
        from Back_End.mission_updater import get_mission_updater
        from Back_End.mission_store import get_mission_store
        
        logging.info(f"[API] PUT /api/missions/{mission_id}/update")
        
        # Validate mission exists
        mission_store = get_mission_store()
        mission = mission_store.find_mission(mission_id)
        if not mission:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "mission_id": mission_id,
                    "message": f"Mission {mission_id} not found"
                }
            )
        
        # Parse update request
        update_type = request_body.get('update_type')
        update_data = request_body.get('update_data', {})
        reason = request_body.get('reason')
        
        # Validate update_type
        valid_types = ['clarification', 'scope_change', 'objective_refinement', 'metadata_update']
        if update_type not in valid_types:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "mission_id": mission_id,
                    "message": f"Invalid update_type. Must be one of: {', '.join(valid_types)}"
                }
            )
        
        # Get mission updater and apply update
        updater = get_mission_updater()
        success = False
        
        if update_type == 'clarification':
            clarification = update_data.get('text') or update_data.get('clarification')
            success = updater.add_clarification(mission_id, clarification, reason)
        elif update_type == 'scope_change':
            success = updater.update_scope(mission_id, update_data, reason)
        elif update_type == 'objective_refinement':
            refinement = update_data.get('refinement') or update_data.get('refined_objective')
            success = updater.refine_objective(mission_id, refinement, reason)
        elif update_type == 'metadata_update':
            success = updater.update_metadata(mission_id, update_data, reason)
        
        if success:
            # Get update summary
            summary = updater.get_mission_update_summary(mission_id)
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "mission_id": mission_id,
                    "update_type": update_type,
                    "total_updates": summary['total_updates'],
                    "message": f"Mission updated successfully"
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "mission_id": mission_id,
                    "message": "Failed to apply update"
                }
            )
    
    except Exception as e:
        logging.error(f"Error updating mission {mission_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "mission_id": mission_id,
                "message": str(e)
            }
        )


@app.get("/api/missions/{mission_id}/updates")
async def get_mission_updates(mission_id: str):
    """
    Get all updates/clarifications for a mission.
    
    Args:
        mission_id: Mission ID
    
    Returns:
        HTTP 200: {
            "status": "success",
            "mission_id": "...",
            "total_updates": int,
            "clarifications": [...],
            "scope_changes": [...],
            "objective_refinements": [...],
            "metadata_updates": [...],
            "last_update": ISO timestamp
        }
        HTTP 404: {"status": "error", "message": "Mission not found"}
    """
    try:
        from Back_End.mission_updater import get_mission_updater
        from Back_End.mission_store import get_mission_store
        
        logging.info(f"[API] GET /api/missions/{mission_id}/updates")
        
        # Validate mission exists
        mission_store = get_mission_store()
        mission = mission_store.find_mission(mission_id)
        if not mission:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "mission_id": mission_id,
                    "message": f"Mission {mission_id} not found"
                }
            )
        
        # Get update summary
        updater = get_mission_updater()
        summary = updater.get_mission_update_summary(mission_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "mission_id": mission_id,
                "total_updates": summary['total_updates'],
                "clarifications": summary['clarifications'],
                "scope_changes": summary['scope_changes'],
                "objective_refinements": summary['objective_refinements'],
                "metadata_updates": summary['metadata_updates'],
                "last_update": summary['last_update']
            }
        )
    except Exception as e:
        logging.error(f"Error retrieving updates for mission {mission_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "mission_id": mission_id,
                "message": str(e)
            }
        )


@app.post("/api/missions/{mission_id}/survey")
async def submit_mission_survey(mission_id: str, request_body: dict):
    """
    Submit mission completion survey response.
    
    PHASE 4: Capture user satisfaction feedback
    """
    try:
        from Back_End.survey_collector import get_survey_collector
        from Back_End.mission_store import get_mission_store
        
        logging.info(f"[API] POST /api/missions/{mission_id}/survey")
        
        mission_store = get_mission_store()
        mission = mission_store.find_mission(mission_id)
        if not mission:
            return JSONResponse(status_code=404, content={"status": "error", "message": f"Mission {mission_id} not found"})
        
        try:
            result_quality = int(request_body.get('result_quality', 3))
            execution_speed = int(request_body.get('execution_speed', 3))
            tool_appropriateness = int(request_body.get('tool_appropriateness', 3))
            overall_satisfaction = int(request_body.get('overall_satisfaction', 3))
            would_use_again = bool(request_body.get('would_use_again', True))
            improvements = request_body.get('improvements')
            notes = request_body.get('notes')
            
            for score in [result_quality, execution_speed, tool_appropriateness, overall_satisfaction]:
                if not (1 <= score <= 5):
                    return JSONResponse(status_code=400, content={"status": "error", "message": "Scores must be 1-5"})
        except (ValueError, TypeError) as e:
            return JSONResponse(status_code=400, content={"status": "error", "message": f"Invalid score format: {e}"})
        
        collector = get_survey_collector()
        success = collector.submit_survey_response(
            mission_id=mission_id,
            result_quality=result_quality,
            execution_speed=execution_speed,
            tool_appropriateness=tool_appropriateness,
            overall_satisfaction=overall_satisfaction,
            would_use_again=would_use_again,
            improvements=improvements,
            notes=notes
        )
        
        if success:
            survey = collector.get_survey_response(mission_id)
            return JSONResponse(status_code=200, content={"status": "success", "mission_id": mission_id, "average_score": survey['average_score']})
        else:
            return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to save survey"})
    except Exception as e:
        logging.error(f"Error submitting survey: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.get("/api/missions/{mission_id}/survey")
async def get_mission_survey(mission_id: str):
    """Get mission survey (check if completed)."""
    try:
        from Back_End.survey_collector import get_survey_collector
        from Back_End.mission_store import get_mission_store
        
        logging.info(f"[API] GET /api/missions/{mission_id}/survey")
        
        mission_store = get_mission_store()
        mission = mission_store.find_mission(mission_id)
        if not mission:
            return JSONResponse(status_code=404, content={"status": "error", "message": f"Mission {mission_id} not found"})
        
        collector = get_survey_collector()
        survey = collector.get_survey_response(mission_id)
        
        if survey:
            return JSONResponse(status_code=200, content={"status": "completed", "mission_id": mission_id, "survey": survey})
        else:
            return JSONResponse(status_code=200, content={"status": "pending", "mission_id": mission_id, "questions": collector.get_survey_questions()})
    except Exception as e:
        logging.error(f"Error retrieving survey: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.post("/api/missions/{mission_id}/survey")
async def submit_mission_survey(mission_id: str, request_body: dict):
    """
    Submit mission completion survey with tool choice feedback.
    
    Body:
    {
        "result_quality_score": 1-5,
        "execution_speed_score": 1-5,
        "tool_appropriateness_score": 1-5,
        "overall_satisfaction_score": 1-5,
        "would_use_again": bool,
        "recommended_tool": "str",  # What was recommended
        "chosen_tool": "str",        # What user selected
        "tool_choice_reason": "fastest|cheapest|reliable|quality|other",
        "improvements": "str",
        "additional_notes": "str"
    }
    """
    try:
        from Back_End.survey_collector import get_survey_collector
        from Back_End.mission_store import get_mission_store
        
        logging.info(f"[API] POST /api/missions/{mission_id}/survey")
        
        mission_store = get_mission_store()
        mission = mission_store.find_mission(mission_id)
        if not mission:
            return JSONResponse(
                status_code=404, 
                content={"status": "error", "message": f"Mission {mission_id} not found"}
            )
        
        # Extract survey data with defaults
        result_quality = request_body.get("result_quality_score", 3)
        execution_speed = request_body.get("execution_speed_score", 3)
        tool_appropriateness = request_body.get("tool_appropriateness_score", 3)
        overall_satisfaction = request_body.get("overall_satisfaction_score", 3)
        would_use_again = request_body.get("would_use_again", True)
        improvements = request_body.get("improvements")
        notes = request_body.get("additional_notes")
        
        # Extract tool choice feedback
        recommended_tool = request_body.get("recommended_tool")
        chosen_tool = request_body.get("chosen_tool")
        tool_choice_reason = request_body.get("tool_choice_reason")
        
        # Validate scores
        for score in [result_quality, execution_speed, tool_appropriateness, overall_satisfaction]:
            if not (1 <= int(score) <= 5):
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": f"Invalid score: {score} (must be 1-5)"}
                )
        
        # Submit survey
        collector = get_survey_collector()
        success = collector.submit_survey_response(
            mission_id=mission_id,
            result_quality=int(result_quality),
            execution_speed=int(execution_speed),
            tool_appropriateness=int(tool_appropriateness),
            overall_satisfaction=int(overall_satisfaction),
            would_use_again=bool(would_use_again),
            improvements=improvements,
            notes=notes,
            recommended_tool=recommended_tool,
            chosen_tool=chosen_tool,
            tool_choice_reason=tool_choice_reason
        )
        
        if success:
            # Log tool choice learning signal if choice differs from recommendation
            if recommended_tool and chosen_tool and recommended_tool != chosen_tool:
                logging.info(
                    f"[LEARNING] User overrode tool selection: "
                    f"recommended={recommended_tool}, chosen={chosen_tool}, reason={tool_choice_reason}"
                )
                
                # Store in memory for learning
                memory_manager.store_observation({
                    'type': 'tool_choice_override',
                    'mission_id': mission_id,
                    'recommended_tool': recommended_tool,
                    'chosen_tool': chosen_tool,
                    'reason': tool_choice_reason,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            return JSONResponse(
                status_code=200, 
                content={
                    "status": "success", 
                    "mission_id": mission_id, 
                    "message": "Survey submitted successfully",
                    "tool_choice_captured": bool(chosen_tool)
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Failed to submit survey"}
            )
    except Exception as e:
        logging.error(f"Error submitting survey: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})



@app.get("/api/surveys/summary")
async def get_surveys_summary():
    """Get aggregate survey statistics across all missions."""
    try:
        from Back_End.survey_collector import get_survey_collector
        
        logging.info("[API] GET /api/surveys/summary")
        
        collector = get_survey_collector()
        summary = collector.get_survey_summary(limit=1000)
        
        return JSONResponse(status_code=200, content={"status": "success", "summary": summary})
    except Exception as e:
        logging.error(f"Error retrieving survey summary: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.get("/api/tools/choice/audit")
async def get_tool_choice_audit(domain: str = "_global"):
    """Get audit data on tool selection recommendations vs user choices.
    
    Returns comprehensive statistics on:
    - Tool pair frequency (when X was recommended, how often was Y chosen?)
    - Override reasons (user preference patterns)
    - Adoption rates (how often was recommended tool actually used?)
    
    Response:
    {
        "total_overrides": int,
        "tool_pairs": {
            "recommended_tool": {
                "chosen_tool": count,
                ...
            },
            ...
        },
        "override_reasons": {
            "fastest": count,
            "cheapest": count,
            "reliable": count,
            ...
        },
        "adoption_rates": {
            "tool_name": {
                "recommended_count": int,
                "adopted_count": int,
                "adoption_rate": 0.75
            },
            ...
        },
        "most_common_pairs": [
            {
                "recommended_tool": "web_search",
                "chosen_tool": "web_navigate",
                "count": 5,
                "percentage": 25.0
            },
            ...
        ],
        "domain": "_global"
    }
    
    Can be used to:
    - Audit when users reject recommendations and why
    - Identify cost/speed preference patterns
    - Improve recommendation algorithm
    - Generate learning signals for tool_selector
    """
    try:
        logging.info(f"[API] GET /api/tools/choice/audit?domain={domain}")
        
        audit_data = memory_manager.get_tool_choice_audit(domain=domain)
        
        return JSONResponse(
            status_code=200, 
            content={
                "status": "success",
                "audit": audit_data
            }
        )
    except Exception as e:
        logging.error(f"Error retrieving tool choice audit: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, 
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/tools/{tool_name}/roi/{mission_type}")
async def get_tool_roi(tool_name: str, mission_type: str):
    """
    Get ROI and cost metrics for a tool on a mission type.
    
    PHASE 5: Investment-aware tool selection
    
    Returns:
        HTTP 200: {
            "tool": "web_search",
            "mission_type": "tutorial_search",
            "usage_count": 50,
            "success_rate": 0.92,
            "avg_cost": 0.15,
            "avg_satisfaction": 4.2,
            "roi_score": 3.63,
            "cost_efficiency_ratio": 28.8
        }
    """
    try:
        from Back_End.investment_connector import get_investment_connector
        
        logging.info(f"[API] GET /api/tools/{tool_name}/roi/{mission_type}")
        
        connector = get_investment_connector()
        profile = connector.get_tool_investment_profile(tool_name, mission_type)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": profile.to_dict()
            }
        )
    except Exception as e:
        logging.error(f"Error retrieving ROI: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.get("/api/tools/comparison/{mission_type}")
async def compare_tools_by_roi(mission_type: str):
    """
    Compare all tools by ROI/cost-benefit for a mission type.
    
    PHASE 5: Helps users understand tool cost-effectiveness
    
    Returns:
        HTTP 200: {
            "mission_type": "tutorial_search",
            "tools": [
                {
                    "tool": "web_search",
                    "roi_score": 3.63,
                    "efficiency_ratio": 28.8,
                    "recommendation": "Excellent value"
                },
                ...
            ]
        }
    """
    try:
        from Back_End.investment_connector import get_investment_connector
        
        logging.info(f"[API] GET /api/tools/comparison/{mission_type}")
        
        connector = get_investment_connector()
        analysis = connector.get_cost_benefit_analysis(mission_type)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": analysis
            }
        )
    except Exception as e:
        logging.error(f"Error retrieving tool comparison: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.get("/api/whiteboard/metrics")
async def get_whiteboard_metrics(days: int = 90):
    """
    Whiteboard Metrics API
    
    Returns aggregated metrics for the new whiteboard dashboard.
    
    Query Parameters:
    - days: Number of days to aggregate (default: 90)
    
    Returns:
    {
        "range": {"days": 90, "start": "2024-01-01T00:00:00+00:00", "end": "2024-04-01T00:00:00+00:00"},
        "api_usage": {...},
        "costing": {...},
        "income": {...},
        "tool_confidence": {...},
        "response_times": {...},
        "session_stats": {...},
        "artifacts": {...},
        "data_sources": {...}
    }
    """
    try:
        if days < 1:
            return JSONResponse(
                status_code=400,
                content={"error": "days parameter must be >= 1"}
            )
        if days > 365:
            return JSONResponse(
                status_code=400,
                content={"error": "days parameter must be <= 365"}
            )
        
        metrics = collect_whiteboard_summary(days)
        return JSONResponse(content=metrics)
    except Exception as e:
        logging.error(f"Error collecting whiteboard metrics: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/whiteboard/metrics/api-usage")
async def get_api_usage_metrics(days: int = 90):
    """Get API usage metrics for the past N days."""
    try:
        if days < 1 or days > 365:
            return JSONResponse(status_code=400, content={"error": "days must be between 1 and 365"})
        from Back_End.whiteboard_metrics import collect_api_usage
        return JSONResponse(content={"api_usage": collect_api_usage(days), "days": days})
    except Exception as e:
        logging.error(f"Error collecting API usage metrics: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/whiteboard/metrics/costing")
async def get_costing_metrics(days: int = 90):
    """Get costing metrics for the past N days."""
    try:
        if days < 1 or days > 365:
            return JSONResponse(status_code=400, content={"error": "days must be between 1 and 365"})
        from Back_End.whiteboard_metrics import collect_costing
        return JSONResponse(content={"costing": collect_costing(days), "days": days})
    except Exception as e:
        logging.error(f"Error collecting costing metrics: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/whiteboard/metrics/income")
async def get_income_metrics(days: int = 90):
    """Get income metrics for the past N days."""
    try:
        if days < 1 or days > 365:
            return JSONResponse(status_code=400, content={"error": "days must be between 1 and 365"})
        from Back_End.whiteboard_metrics import collect_income
        return JSONResponse(content={"income": collect_income(days), "days": days})
    except Exception as e:
        logging.error(f"Error collecting income metrics: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/whiteboard/metrics/tool-confidence")
async def get_tool_confidence_metrics(days: int = 90):
    """Get tool confidence metrics for the past N days."""
    try:
        if days < 1 or days > 365:
            return JSONResponse(status_code=400, content={"error": "days must be between 1 and 365"})
        from Back_End.whiteboard_metrics import collect_tool_confidence
        return JSONResponse(content={"tool_confidence": collect_tool_confidence(days), "days": days})
    except Exception as e:
        logging.error(f"Error collecting tool confidence metrics: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/whiteboard/metrics/response-times")
async def get_response_times_metrics(days: int = 90):
    """Get response time metrics for the past N days."""
    try:
        if days < 1 or days > 365:
            return JSONResponse(status_code=400, content={"error": "days must be between 1 and 365"})
        from Back_End.whiteboard_metrics import collect_response_times
        return JSONResponse(content={"response_times": collect_response_times(days), "days": days})
    except Exception as e:
        logging.error(f"Error collecting response time metrics: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/whiteboard/metrics/session-stats")
async def get_session_stats_metrics():
    """Get conversation session statistics."""
    try:
        from Back_End.whiteboard_metrics import collect_session_stats
        return JSONResponse(content={"session_stats": collect_session_stats()})
    except Exception as e:
        logging.error(f"Error collecting session stats metrics: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/whiteboard/metrics/artifacts")
async def get_artifacts_metrics(days: int = 90):
    """Get artifacts metrics for the past N days."""
    try:
        if days < 1 or days > 365:
            return JSONResponse(status_code=400, content={"error": "days must be between 1 and 365"})
        from Back_End.whiteboard_metrics import collect_artifacts
        return JSONResponse(content={"artifacts": collect_artifacts(days), "days": days})
    except Exception as e:
        logging.error(f"Error collecting artifacts metrics: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/analytics/all")
async def get_analytics_dashboard():
    """Analytics Dashboard API - Returns all data for Phase 8 dashboard."""
    try:
        from Back_End.whiteboard_metrics import collect_analytics_dashboard
        data = collect_analytics_dashboard()
        return JSONResponse(content=data)
    except Exception as e:
        logging.error(f"Error collecting analytics dashboard: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


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


# ============================================================================
# PHASE 5C: ARTIFACT RETRIEVAL API ENDPOINTS
# ============================================================================

@app.get("/api/artifacts/{artifact_id}")
async def get_artifact_by_id(artifact_id: str):
    """
    Retrieve a single artifact by ID.
    
    Searches all mission results for an artifact with matching ID.
    
    Args:
        artifact_id: UUID of the artifact
        
    Returns:
        {
            "success": True,
            "artifact": {
                "artifact_id": "...",
                "type": "table|document|code",
                "title": "...",
                "content": {...},
                "metadata": {...}
            }
        }
    """
    try:
        from Back_End.mission_store import get_mission_store
        
        store = get_mission_store()
        
        # Search for artifact across all missions
        artifact_data = store.get_artifact_by_id(artifact_id)
        
        if not artifact_data:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Artifact {artifact_id} not found"}
            )
        
        return JSONResponse(
            content={"success": True, "artifact": artifact_data}
        )
    except Exception as e:
        logging.error(f"Error retrieving artifact {artifact_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/missions/{mission_id}/artifacts")
async def get_mission_artifacts(mission_id: str):
    """
    Get all artifacts for a specific mission.
    
    Returns all ResponseEnvelope artifacts created during mission execution.
    
    Args:
        mission_id: UUID of the mission
        
    Returns:
        {
            "success": True,
            "mission_id": "...",
            "artifacts": [
                {
                    "artifact_id": "...",
                    "type": "table",
                    "title": "...",
                    "content": {...},
                    "metadata": {...}
                },
                ...
            ]
        }
    """
    try:
        from Back_End.mission_store import get_mission_store
        
        store = get_mission_store()
        
        # Get mission
        mission = store.get_mission(mission_id)
        if not mission:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Mission {mission_id} not found"}
            )
        
        # Load artifacts for mission
        artifacts = store.get_mission_artifacts(mission_id)
        
        return JSONResponse(
            content={
                "success": True,
                "mission_id": mission_id,
                "artifacts": artifacts or [],
                "count": len(artifacts or [])
            }
        )
    except Exception as e:
        logging.error(f"Error retrieving artifacts for mission {mission_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/missions/{mission_id}/result")
async def get_mission_execution_result(mission_id: str):
    """
    Get complete execution result with artifacts and governance metadata.
    
    Returns full ResponseEnvelope that includes:
    - summary: Text summary of execution
    - artifacts: All artifacts produced (table, document, code)
    - governance: Decision details (AUTO_APPROVE, REQUIRE_APPROVAL, REJECT)
    - execution_time_seconds: How long execution took
    - execution_timestamp: When execution completed
    
    Args:
        mission_id: UUID of the mission
        
    Returns:
        {
            "success": True,
            "mission_id": "...",
            "status": "success|error",
            "execution_result": {
                "summary": "Found 3 results",
                "response_type": "text"
            },
            "artifacts": [
                {
                    "artifact_id": "...",
                    "type": "table",
                    "title": "...",
                    "content": {...},
                    "metadata": {...}
                },
                ...
            ],
            "governance": {
                "decision": "AUTO_APPROVE",
                "confidence": 0.92,
                "checks": {
                    "budget_check": True,
                    "risk_check": True,
                    ...
                }
            },
            "execution_time_seconds": 1.5,
            "execution_timestamp": "2024-01-01T..."
        }
    """
    try:
        from Back_End.mission_store import get_mission_store
        
        store = get_mission_store()
        
        # Get mission from store
        mission = store.get_mission(mission_id)
        if not mission:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Mission {mission_id} not found"}
            )
        
        # Get execution result with artifacts
        result = store.get_mission_execution_result(mission_id)
        
        if not result:
            return JSONResponse(
                content={
                    "success": True,
                    "mission_id": mission_id,
                    "status": "pending",
                    "message": "Mission execution in progress or not yet started"
                }
            )
        
        return JSONResponse(
            content={
                "success": True,
                "mission_id": mission_id,
                **result  # Unpack result to include all fields
            }
        )
    except Exception as e:
        logging.error(f"Error retrieving execution result for mission {mission_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/missions/{mission_id}/feedback")
async def post_mission_feedback(mission_id: str, request: Request):
    """
    Store user feedback on mission execution and governance decision.
    
    Feedback types:
    - governance_decision: User's assessment of the governance decision
    - execution_quality: Quality of the execution result
    - artifact_quality: Quality of produced artifacts
    
    Ratings:
    - helpful: Feedback was helpful/correct
    - partially_helpful: Partially helpful
    - unhelpful: Feedback was not helpful
    
    Confidence levels:
    - very_confident: Very confident in assessment
    - somewhat_confident: Somewhat confident
    - uncertain: Uncertain about assessment
    
    Args:
        mission_id: UUID of the mission
        
    Request body:
        {
            "governance_decision_id": "dec_xyz",
            "feedback_type": "governance_decision",
            "rating": "helpful",
            "confidence": "very_confident",
            "comment": "Decision was correct",
            "tags": ["accurate", "fast"],
            "was_correct": true
        }
        
    Returns:
        {
            "success": True,
            "feedback_id": "...",
            "mission_id": "...",
            "stored_at": "2024-01-01T...",
            "stats": {
                "total_feedback": 5,
                "accuracy": 0.8,
                "avg_confidence": 0.9
            }
        }
    """
    try:
        from Back_End.feedback_manager import feedback_manager
        from uuid import uuid4
        
        body = await request.json()
        
        governance_decision_id = body.get("governance_decision_id", str(uuid4()))
        feedback_type = body.get("feedback_type", "governance_decision")
        rating = body.get("rating", "helpful")
        confidence = body.get("confidence", "somewhat_confident")
        tags = body.get("tags", [])
        comment = body.get("comment", "")
        was_correct = body.get("was_correct", True)
        
        # Submit feedback and get stored record
        feedback_record = feedback_manager.submit_governance_feedback(
            mission_id=mission_id,
            governance_decision_id=governance_decision_id,
            feedback_type=feedback_type,
            rating=rating,
            confidence=confidence,
            tags=tags,
            comment=comment,
            was_correct=was_correct,
        )
        
        # Get accuracy stats for this decision
        stats = feedback_manager.get_decision_accuracy_stats(governance_decision_id)
        
        return JSONResponse(
            content={
                "success": True,
                "feedback_id": governance_decision_id,
                "mission_id": mission_id,
                "stored_at": feedback_record.get("timestamp"),
                "stats": stats
            }
        )
    except Exception as e:
        logging.error(f"Error storing feedback for mission {mission_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
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
        from Back_End.budget_enforcer import get_budget_enforcer
        from Back_End.cost_estimator import ServiceTier
        
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
        from Back_End import mployer_tools
        
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
    if not await _require_ws_auth(websocket):
        return
    await websocket.accept()
    try:
        while True:
            from Back_End import mployer_tools
            
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
        from Back_End import mployer_tools
        try:
            from Back_End.buddys_vision_core import BuddysVisionCore
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"Vision core unavailable: {e}"}
            )
        
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
        from Back_End import mployer_tools
        
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
        from Back_End import mployer_tools
        try:
            from Back_End.buddys_arms import BuddysArms
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"Vision arms unavailable: {e}"}
            )
        
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
        from Back_End import mployer_tools
        try:
            from Back_End.buddys_vision import BuddysVision
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"Vision analyzer unavailable: {e}"}
            )
        
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
        from Back_End.artifact_delivery_flow import get_delivery_orchestrator
        
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
        from Back_End.artifact_delivery_flow import get_delivery_orchestrator
        
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
        from Back_End.email_client import YahooOAuthClient
        
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
        from Back_End.email_client import YahooOAuthClient
        
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


@app.get("/api/email/status")
async def get_email_status():
    """Check if email OAuth has been configured"""
    try:
        from pathlib import Path
        
        tokens_path = Path("data/yahoo_tokens.json")
        oauth_configured = tokens_path.exists()
        
        return JSONResponse(content={
            "oauth_configured": oauth_configured,
            "email": os.getenv("BUDDY_YAHOO_EMAIL", "Not configured")
        })
    except Exception as e:
        logging.error(f"Email status check error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"oauth_configured": False, "error": str(e)}
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
        from Back_End.email_client import get_email_client
        
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
        from Back_End.email_client import get_email_client
        
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
        from Back_End.email_client import get_comprehension_engine
        
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
        from Back_End.onedrive_client import OneDriveOAuthClient
        
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
        from Back_End.onedrive_client import OneDriveOAuthClient
        
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
        from Back_End.onedrive_client import get_onedrive_client
        
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


# PHASE 7: Artifact Preview Endpoints - Rich Media Support
@app.post("/api/artifacts/preview")
async def generate_artifact_preview(artifact: dict):
    """
    Generate rich preview for an artifact (Phase 7 expansion).
    
    Supports:
    - HTML rendering hints
    - Chart configurations
    - Code syntax highlighting
    - Image galleries
    - Table rendering
    - Markdown formatting
    
    Body:
        artifact_type: str (web_extraction, web_search, chart_data, code_snippet, etc.)
        artifact: dict (the artifact data)
    """
    try:
        from Back_End.artifact_preview_generator import ArtifactPreviewGenerator
        
        generator = ArtifactPreviewGenerator()
        preview = generator.generate_preview(artifact)
        
        return JSONResponse(content={
            "success": True,
            "preview": preview,
            "artifact_type": artifact.get("artifact_type", "unknown"),
        })
    except Exception as e:
        logging.error(f"Artifact preview generation error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/artifacts/preview-schema")
async def get_artifact_preview_schema():
    """
    Get schema for rich artifact previews (Phase 7).
    
    Returns information about:
    - Supported artifact types
    - Rich media capabilities
    - Rendering hints available
    - Chart types supported
    - Code languages supported
    """
    try:
        schema = {
            "artifact_types": [
                "web_extraction_result",
                "web_search_result",
                "web_navigation_result",
                "calculation_result",
                "data_table",
                "chart_data",
                "code_snippet",
                "image_gallery",
                "html_content",
                "json_data",
            ],
            "rendering_hints": [
                "document",
                "table",
                "chart",
                "code",
                "gallery",
                "json",
                "text",
            ],
            "rich_media_support": {
                "html_rendering": True,
                "chart_visualization": True,
                "syntax_highlighting": True,
                "image_gallery": True,
                "table_rendering": True,
                "markdown_formatting": True,
            },
            "chart_types": [
                "line",
                "bar",
                "pie",
                "scatter",
                "radar",
            ],
            "code_languages": [
                "python",
                "javascript",
                "java",
                "cpp",
                "sql",
                "html",
                "css",
                "json",
            ],
        }
        return JSONResponse(content=schema)
    except Exception as e:
        logging.error(f"Preview schema error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# PHASE 8: Phase25 Autonomous Multi-Agent Integration Endpoints
@app.post("/api/missions/{mission_id}/route-to-phase25")
async def route_mission_to_phase25(mission_id: str, route_request: dict = None):
    """
    Route a mission to Phase25 for autonomous multi-agent execution.
    
    Phase25 enables:
    - Multi-agent task orchestration
    - Goal planning and decomposition
    - Autonomous task coordination
    - Cross-agent learning
    
    Body (optional):
        execution_mode: "dry_run" (default) or "live"
        priority: "HIGH", "NORMAL" (default), or "LOW"
    """
    try:
        from Back_End.mission_store import get_mission_store
        
        mission_store = get_mission_store()
        bridge = get_phase25_bridge()
        
        # Get mission details
        mission_doc = mission_store.get_mission(mission_id)
        if not mission_doc:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Mission {mission_id} not found"}
            )
        
        mission_data = mission_doc.to_dict() if hasattr(mission_doc, 'to_dict') else mission_doc
        objective = mission_data.get("objective") or mission_data.get("description", "")
        
        # Convert mission to Phase25 goal
        goal_id = bridge.mission_to_goal(
            mission_id=mission_id,
            objective=objective,
            context={
                "mission_type": mission_data.get("mission_type"),
                "tools": mission_data.get("selected_tools", []),
                "parameters": mission_data.get("parameters", {}),
                "estimated_cost": mission_data.get("estimated_cost", 0),
            }
        )
        
        if not goal_id:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to create Phase25 goal"}
            )
        
        return JSONResponse(content={
            "success": True,
            "mission_id": mission_id,
            "goal_id": goal_id,
            "phase25_routing": True,
            "message": "Mission routed to Phase25 for autonomous execution"
        })
    except Exception as e:
        logging.error(f"Phase25 routing error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/phase25/goal/{goal_id}")
async def get_phase25_goal_status(goal_id: str):
    """
    Get Phase25 goal status and associated tasks.
    
    Returns:
    ```json
    {
        "goal_id": str,
        "objective": str,
        "status": "pending|in_progress|completed|failed",
        "tasks": [
            {
                "task_id": str,
                "description": str,
                "status": str,
                "priority": str
            }
        ],
        "execution_count": int,
        "success_rate": float
    }
    ```
    """
    try:
        bridge = get_phase25_bridge()
        
        # Get goal status
        goal_data = bridge.get_goal_status(goal_id)
        if not goal_data:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Goal {goal_id} not found"}
            )
        
        # Get goal tasks
        tasks = bridge.get_goal_tasks(goal_id)
        
        return JSONResponse(content={
            "success": True,
            "goal": goal_data,
            "task_count": len(tasks),
            "tasks": tasks,
        })
    except Exception as e:
        logging.error(f"Phase25 goal status error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/phase25/task-execution")
async def log_phase25_task_execution(execution_data: dict):
    """
    Log task execution to Phase25 for audit trail and learning.
    
    Body:
        task_id: str
        tool_name: str
        action_type: str (execute, retry, etc.)
        status: str (success, failed, retrying)
        result: dict (optional, execution result)
        duration_ms: int (optional, execution time)
    """
    try:
        bridge = get_phase25_bridge()
        
        success = bridge.log_task_execution(
            task_id=execution_data.get("task_id", ""),
            tool_name=execution_data.get("tool_name", ""),
            action_type=execution_data.get("action_type", "execute"),
            status=execution_data.get("status", "unknown"),
            result=execution_data.get("result"),
            duration_ms=execution_data.get("duration_ms", 0),
        )
        
        return JSONResponse(content={
            "success": success,
            "message": "Execution logged to Phase25"
        })
    except Exception as e:
        logging.error(f"Phase25 execution logging error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/phase25/learning-signal")
async def log_phase25_learning_signal(signal_data: dict):
    """
    Log learning signal from mission execution to Phase25.
    
    Signals are used for:
    - Tool performance analysis
    - Efficiency optimization
    - Safety improvements
    - Cross-agent learning
    
    Body:
        tool_name: str
        signal_type: str (success, efficiency, safety, etc.)
        insight: str (description of insight)
        confidence: float (0-1, confidence score)
        recommended_action: str (what should happen next)
    """
    try:
        bridge = get_phase25_bridge()
        
        success = bridge.log_learning_signal(
            tool_name=signal_data.get("tool_name", ""),
            signal_type=signal_data.get("signal_type", ""),
            insight=signal_data.get("insight", ""),
            confidence=float(signal_data.get("confidence", 0.5)),
            recommended_action=signal_data.get("recommended_action", ""),
        )
        
        return JSONResponse(content={
            "success": success,
            "message": "Learning signal logged to Phase25"
        })
    except Exception as e:
        logging.error(f"Phase25 learning signal error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/phase25/dashboard")
async def get_phase25_dashboard():
    """
    Get consolidated Phase25 autonomous execution dashboard.
    
    Shows:
    - Active goals and their status
    - Task execution metrics
    - System health
    - Learning signals summary
    - Agent performance
    """
    try:
        from Back_End.phase25_dashboard_aggregator import Phase25DashboardAggregator
        
        aggregator = Phase25DashboardAggregator()
        
        # Collect dashboard data
        dashboard = {
            "goals_count": len(aggregator.get_all_goals()),
            "active_goals": aggregator.get_active_goals(),
            "tasks_summary": aggregator.get_tasks_summary(),
            "system_health": aggregator.get_system_health(),
            "learning_signals": aggregator.get_recent_signals(),
            "execution_summary": aggregator.get_execution_summary(),
        }
        
        return JSONResponse(content={
            "success": True,
            "dashboard": dashboard
        })
    except Exception as e:
        logging.error(f"Phase25 dashboard error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/onedrive/list")
async def list_onedrive_files(folder: str = "/"):
    """List files in OneDrive folder"""
    try:
        from Back_End.onedrive_client import get_onedrive_client
        
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


# PHASE 9: Cloud Task Scheduler Endpoints
@app.post("/api/missions/schedule/one-time")  
async def schedule_mission_one_time(schedule_request: dict):
    """
    Schedule a mission to run once at a specific time.
    
    Body:
        mission_id: str
        mission_objective: str
        run_at: str (ISO 8601 datetime)
        timezone: str (optional, default: UTC)
    """
    try:
        scheduler = get_cloud_scheduler()
        
        from datetime import datetime
        run_at = datetime.fromisoformat(schedule_request.get("run_at", ""))
        
        schedule_id = scheduler.schedule_one_time(
            mission_id=schedule_request.get("mission_id", ""),
            mission_objective=schedule_request.get("mission_objective", ""),
            run_at=run_at,
            timezone=schedule_request.get("timezone", "UTC"),
        )
        
        if not schedule_id:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to schedule mission"}
            )
        
        return JSONResponse(content={
            "success": True,
            "schedule_id": schedule_id,
            "run_at": run_at.isoformat(),
        })
    except Exception as e:
        logging.error(f"Schedule mission error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/missions/schedule/recurring")
async def schedule_mission_recurring(schedule_request: dict):
    """
    Schedule a mission to run on a recurring cron schedule.
    
    Body:
        mission_id: str
        mission_objective: str
        cron_expression: str (e.g., "0 9 * * MON" for 9 AM Mondays)
        timezone: str (optional, default: UTC)
    
    Cron examples:
        "0 9 * * *"        → Every day at 9 AM
        "0 9 * * MON"      → Every Monday at 9 AM
        "0 */4 * * *"      → Every 4 hours
    """
    try:
        scheduler = get_cloud_scheduler()
        
        schedule_id = scheduler.schedule_recurring(
            mission_id=schedule_request.get("mission_id", ""),
            mission_objective=schedule_request.get("mission_objective", ""),
            cron_expression=schedule_request.get("cron_expression", ""),
            timezone=schedule_request.get("timezone", "UTC"),
        )
        
        if not schedule_id:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to schedule mission"}
            )
        
        return JSONResponse(content={
            "success": True,
            "schedule_id": schedule_id,
            "cron": schedule_request.get("cron_expression"),
        })
    except Exception as e:
        logging.error(f"Schedule recurring error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/missions/schedule/delayed")
async def schedule_mission_delayed(schedule_request: dict):
    """
    Schedule a mission to run after a delay.
    
    Body:
        mission_id: str
        mission_objective: str
        delay_minutes: int (wait this many minutes before execution)
    """
    try:
        scheduler = get_cloud_scheduler()
        
        schedule_id = scheduler.schedule_delayed(
            mission_id=schedule_request.get("mission_id", ""),
            mission_objective=schedule_request.get("mission_objective", ""),
            delay_minutes=int(schedule_request.get("delay_minutes", 0)),
        )
        
        if not schedule_id:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to schedule mission"}
            )
        
        return JSONResponse(content={
            "success": True,
            "schedule_id": schedule_id,
            "delay_minutes": schedule_request.get("delay_minutes"),
        })
    except Exception as e:
        logging.error(f"Schedule delayed error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/missions/schedule/{schedule_id}")
async def get_schedule_status(schedule_id: str):
    """
    Get status of a scheduled mission.
    """
    try:
        scheduler = get_cloud_scheduler()
        schedule = scheduler.get_schedule(schedule_id)
        
        if not schedule:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Schedule {schedule_id} not found"}
            )
        
        return JSONResponse(content={
            "success": True,
            "schedule": {
                "schedule_id": schedule.schedule_id,
                "mission_id": schedule.mission_id,
                "status": schedule.status,
                "schedule_type": schedule.schedule_type,
                "next_run": schedule.next_run,
                "execution_count": schedule.execution_count,
            }
        })
    except Exception as e:
        logging.error(f"Get schedule error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# PHASE 10: Mission Recipe System Endpoints
@app.get("/api/recipes")
async def list_recipes(category: str = None, tag: str = None):
    """
    List available mission recipes.
    
    Query params:
        category: Filter by category (web_extraction, web_search, etc.)
        tag: Filter by tag
    """
    try:
        recipe_system = get_recipe_system()
        recipes = recipe_system.list_recipes(category=category, tag=tag)
        
        recipe_list = [{
            "recipe_id": r.recipe_id,
            "name": r.name,
            "description": r.description,
            "category": r.category,
            "estimated_duration_minutes": r.estimated_duration_minutes,
            "estimated_cost": r.estimated_cost,
            "success_rate": r.success_rate,
            "tags": r.tags,
        } for r in recipes]
        
        return JSONResponse(content={
            "success": True,
            "recipes": recipe_list,
            "count": len(recipe_list),
        })
    except Exception as e:
        logging.error(f"List recipes error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/recipes/{recipe_id}")
async def get_recipe(recipe_id: str):
    """
    Get detailed recipe information.
    """
    try:
        recipe_system = get_recipe_system()
        recipe = recipe_system.get_recipe(recipe_id)
        
        if not recipe:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Recipe {recipe_id} not found"}
            )
        
        return JSONResponse(content={
            "success": True,
            "recipe": {
                "recipe_id": recipe.recipe_id,
                "name": recipe.name,
                "description": recipe.description,
                "category": recipe.category,
                "version": recipe.version,
                "steps": [{
                    "step_name": s.step_name,
                    "tool": s.tool,
                    "parameters": s.parameters,
                    "error_handling": s.error_handling,
                    "timeout_seconds": s.timeout_seconds,
                } for s in recipe.steps],
                "estimated_duration_minutes": recipe.estimated_duration_minutes,
                "estimated_cost": recipe.estimated_cost,
                "success_rate": recipe.success_rate,
                "tags": recipe.tags,
                "examples": recipe.examples,
            }
        })
    except Exception as e:
        logging.error(f"Get recipe error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/recipes/instantiate/{recipe_id}")
async def instantiate_recipe(recipe_id: str, parameters: dict = None):
    """
    Instantiate a recipe into a concrete mission and trigger planning.
    
    Replaces parameter placeholders with actual values, then automatically
    generates a multi-step execution plan for user review.
    
    Body:
        parameters: dict of parameter substitutions
        
    Returns:
        Mission with execution plan ready for review/approval
    """
    try:
        recipe_system = get_recipe_system()
        mission = recipe_system.instantiate_recipe(
            recipe_id=recipe_id,
            parameters=parameters or {}
        )
        
        if not mission:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"Failed to instantiate recipe {recipe_id}"}
            )
        
        mission_id = mission.get('mission_id')
        
        # CRITICAL: Trigger mission planning so user can review the plan
        try:
            from Back_End.action_readiness_engine import (
                ActionReadinessEngine, ReadinessDecision
            )
            from Back_End.multi_step_mission_planner import MultiStepMissionPlanner
            from Back_End.mission_store import get_mission_store, Mission
            
            # Create a synthetic readiness result for recipe-based missions
            # Recipes are pre-validated, so they're automatically READY
            readiness_result = type('ReadinessResult', (), {
                'decision': ReadinessDecision.READY,
                'action_object': mission.get('objective'),
                'confidence': 0.95,
                'reasoning': f"Recipe-based mission: {mission.get('recipe_name')}"
            })()
            
            # Generate mission plan
            planner = MultiStepMissionPlanner()
            unified_proposal = planner.plan_mission(
                readiness_result=readiness_result,
                raw_chat_message=mission.get('objective', ''),
                user_id="recipe_user"
            )
            
            # Save plan to mission store (FIX #1)
            store = get_mission_store()
            
            # Extract step data from unified proposal
            steps_data = []
            for step in unified_proposal.task_breakdown.steps:
                step_name = getattr(step, 'step_name', None) or getattr(step, 'name', None) or step.description
                selected_tool = None
                if getattr(step, 'tools_used', None):
                    selected_tool = step.tools_used[0]
                estimated_cost_usd = None
                if getattr(step, 'estimated_cost', None):
                    estimated_cost_usd = getattr(step.estimated_cost, 'total_usd', None)
                step_dict = {
                    'step_name': step_name,
                    'selected_tool': selected_tool,
                    'tool_confidence': getattr(step, 'confidence', None),
                    'estimated_duration_seconds': getattr(step, 'estimated_buddy_time', None),
                    'estimated_cost_usd': estimated_cost_usd,
                    'description': step.description,
                    'dependencies': getattr(step, 'dependencies', None) or [],
                }
                steps_data.append(step_dict)
            
            # Create mission_plan_created event
            plan_event = Mission(
                mission_id=mission_id,
                event_type='mission_plan_created',
                status='planned',
                objective=mission.get('objective'),
                metadata={
                    'plan_data': {
                        'steps': steps_data,
                        'total_estimated_cost': getattr(unified_proposal, 'total_cost_usd', 0.0),
                        'total_estimated_duration': int(
                            (getattr(unified_proposal, 'estimated_buddy_time_seconds', 0) or 0)
                            + (getattr(unified_proposal, 'estimated_human_time_minutes', 0) or 0) * 60
                        ),
                        'mission_title': unified_proposal.mission_title,
                        'source': 'recipe_planner'
                    }
                }
            )
            
            store.write_mission_event(plan_event)
            
            logging.info(
                f"[RECIPE] Generated plan for mission {mission_id}: "
                f"{len(steps_data)} steps, "
                f"est_cost=${getattr(unified_proposal, 'total_cost_usd', 0.0):.4f}, "
                f"est_duration={int((getattr(unified_proposal, 'estimated_buddy_time_seconds', 0) or 0) + (getattr(unified_proposal, 'estimated_human_time_minutes', 0) or 0) * 60)}s"
            )
            
            # Add plan to response
            mission['plan'] = {
                'steps': steps_data,
                'total_cost_estimate': getattr(unified_proposal, 'total_cost_usd', 0.0),
                'total_duration_estimate': int(
                    (getattr(unified_proposal, 'estimated_buddy_time_seconds', 0) or 0)
                    + (getattr(unified_proposal, 'estimated_human_time_minutes', 0) or 0) * 60
                ),
                'mission_title': unified_proposal.mission_title,
            }
            mission['message'] = (
                f"Mission plan created with {len(steps_data)} steps. "
                f"Review and approve to execute."
            )
            
        except Exception as planning_error:
            logging.warning(
                f"[RECIPE] Planning failed for {mission_id}, "
                f"mission still created: {planning_error}"
            )
            # Don't fail the whole request if planning fails
            mission['planning_warning'] = str(planning_error)
        
        return JSONResponse(content={
            "success": True,
            "mission": mission,
        })
    except Exception as e:
        logging.error(f"Instantiate recipe error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/recipes/search")
async def search_recipes(query: str = ""):
    """
    Search recipes by name or description.
    
    Query params:
        query: Search term
    """
    try:
        recipe_system = get_recipe_system()
        recipes = recipe_system.search_recipes(query)
        
        recipe_list = [{
            "recipe_id": r.recipe_id,
            "name": r.name,
            "description": r.description,
            "category": r.category,
            "estimated_cost": r.estimated_cost,
            "success_rate": r.success_rate,
        } for r in recipes]
        
        return JSONResponse(content={
            "success": True,
            "query": query,
            "recipes": recipe_list,
            "count": len(recipe_list),
        })
    except Exception as e:
        logging.error(f"Search recipes error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============================================================================
# TASK 8: FORECASTING EVALUATION ENDPOINTS
# ============================================================================

# Global evaluation harness instance
_evaluation_harness = None

def get_evaluation_harness():
    """Get or initialize forecasting evaluation harness."""
    global _evaluation_harness
    if _evaluation_harness is None:
        from Back_End.forecasting_evaluation import ForecastingEvaluationHarness
        _evaluation_harness = ForecastingEvaluationHarness()
    return _evaluation_harness


@app.post("/api/forecasts/{forecast_id}/evaluate")
async def evaluate_forecast(forecast_id: str, evaluation_data: Dict[str, Any]):
    """
    Record actual outcome for a forecast and evaluate accuracy.
    
    Expected request body:
    {
        "domain": "system_health",
        "metric": "agent_availability",
        "predicted_value": 85.0,
        "actual_value": 87.0,
        "confidence": 0.87
    }
    
    Returns:
        HTTP 201: {
            "forecast_id": "...",
            "absolute_error": 2.0,
            "relative_error": 0.023,
            "confidence_calibrated": true,
            "health_score": 82.5,
            "health_status": "good"
        }
    """
    try:
        from Back_End.forecasting_evaluation import ForecastEvaluation
        
        logging.info(f"[API] POST /api/forecasts/{forecast_id}/evaluate - Recording evaluation")
        
        harness = get_evaluation_harness()
        
        # Create evaluation record
        evaluation = ForecastEvaluation(
            forecast_id=forecast_id,
            domain=evaluation_data.get("domain", "unknown"),
            metric=evaluation_data.get("metric", "unknown"),
            predicted_value=float(evaluation_data.get("predicted_value", 0)),
            actual_value=float(evaluation_data.get("actual_value", 0)),
            confidence=float(evaluation_data.get("confidence", 0.5))
        )
        
        # Record it
        harness.record_evaluation(evaluation)
        
        # Get current health
        health_score, health_status = harness.get_heath_score()
        
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "forecast_id": forecast_id,
                "absolute_error": round(evaluation.absolute_error, 4),
                "relative_error": round(evaluation.relative_error, 4),
                "error_percent": round(evaluation.error_percent, 2),
                "confidence_calibrated": evaluation.confidence_calibrated,
                "health_score": round(health_score, 1),
                "health_status": health_status
            }
        )
    except Exception as e:
        logging.error(f"Error evaluating forecast: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/forecasts/evaluation/metrics")
async def get_evaluation_metrics(domain: Optional[str] = None):
    """
    Get accuracy metrics for all forecasts or a specific domain.
    
    Query params:
        ?domain=system_health  (optional)
    
    Returns:
        HTTP 200: {
            "health_score": 82.5,
            "health_status": "good",
            "total_evaluations": 150,
            "domains_tracked": 4,
            "domain_metrics": {
                "system_health:agent_availability": {
                    "domain": "system_health",
                    "metric": "agent_availability",
                    "n_evaluations": 45,
                    "avg_absolute_error": 2.1,
                    "confidence_calibration_ratio": 0.89,
                    ...
                },
                ...
            }
        }
    """
    try:
        logging.info(f"[API] GET /api/forecasts/evaluation/metrics - domain={domain}")
        
        harness = get_evaluation_harness()
        health_score, health_status = harness.get_heath_score()
        
        # Filter metrics by domain if specified
        domain_metrics = harness.domain_metrics
        if domain:
            domain_metrics = {k: v for k, v in domain_metrics.items() if v.domain == domain}
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "health_score": round(health_score, 1),
                "health_status": health_status,
                "total_evaluations": len(harness.evaluations),
                "domains_tracked": len(set(e.domain for e in harness.evaluations)),
                "domain_metrics": {k: v.to_dict() for k, v in domain_metrics.items()}
            }
        )
    except Exception as e:
        logging.error(f"Error retrieving evaluation metrics: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/forecasts/evaluation/drift")
async def get_drift_warnings():
    """
    Get model drift warnings - alerts when accuracy degrades.
    
    Returns:
        HTTP 200: {
            "drift_warnings": [
                {
                    "domain": "system_health",
                    "metric": "agent_availability",
                    "severity": "medium",
                    "message": "Forecast accuracy degraded 18.2%...",
                    "previous_error_rate": 3.2,
                    "current_error_rate": 3.8,
                    "degradation_percent": 18.75,
                    "recommendation": "Consider retraining for system_health:agent_availability",
                    "detected_at": "2024-01-15T10:30:00+00:00"
                },
                ...
            ],
            "active_warnings": 2,
            "critical_count": 0,
            "recommendations": [...]
        }
    """
    try:
        logging.info(f"[API] GET /api/forecasts/evaluation/drift - Retrieving drift warnings")
        
        harness = get_evaluation_harness()
        
        critical = [w for w in harness.drift_warnings if w.severity == "high"]
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "drift_warnings": [asdict(w) for w in harness.drift_warnings[-20:]],  # Last 20
                "active_warnings": len(harness.drift_warnings),
                "critical_count": len(critical),
                "recommendations": harness._generate_recommendations()
            }
        )
    except Exception as e:
        logging.error(f"Error retrieving drift warnings: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/forecasts/evaluation/health")
async def get_system_health():
    """
    Get overall forecasting system health and monitoring report.
    
    Returns:
        HTTP 200: {
            "timestamp": "2024-01-15T10:30:00+00:00",
            "overall_health": {
                "score": 82.5,
                "status": "good",
                "interpretation": "System performing well..."
            },
            "evaluation_summary": {
                "total_evaluations": 150,
                "domains_tracked": 4,
                "evaluation_period": "Last 30 days"
            },
            "monitoring_report": {
                "domain_metrics": {...},
                "drift_warnings": [...],
                "recommendations": [...]
            }
        }
    """
    try:
        logging.info(f"[API] GET /api/forecasts/evaluation/health - Retrieving system health")
        
        harness = get_evaluation_harness()
        report = harness.generate_monitoring_report()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "monitoring_report": report
            }
        )
    except Exception as e:
        logging.error(f"Error retrieving system health: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.post("/api/forecasts/evaluation/retrain")
async def suggest_retraining():
    """
    Get retraining suggestions for models showing drift or poor accuracy.
    
    Returns:
        HTTP 200: {
            "urgent": ["system_health:agent_availability"],
            "recommended": ["research:completion_success"],
            "optional": ["external_events:api_availability"],
            "next_retrain_timestamp": "2024-01-20T10:30:00+00:00"
        }
    """
    try:
        logging.info(f"[API] POST /api/forecasts/evaluation/retrain - Getting retraining suggestions")
        
        harness = get_evaluation_harness()
        retrain_suggestions = harness.suggest_retraining()
        
        # Calculate next retraining window (7 days if urgent, 14 days if recommended)
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        if retrain_suggestions['urgent']:
            next_retrain = now + timedelta(days=1)  # ASAP
        elif retrain_suggestions['recommended']:
            next_retrain = now + timedelta(days=7)
        else:
            next_retrain = now + timedelta(days=14)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "urgent": retrain_suggestions['urgent'],
                "recommended": retrain_suggestions['recommended'],
                "optional": retrain_suggestions['optional'],
                "next_retrain_timestamp": next_retrain.isoformat(),
                "total_models_to_retrain": sum(len(v) for k, v in retrain_suggestions.items())
            }
        )
    except Exception as e:
        logging.error(f"Error suggesting retraining: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# End of API routes




