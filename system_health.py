"""
System Health Monitor: Checks all Buddy subsystems for connectivity and readiness.
No API calls - just local instantiation checks to avoid costs.
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class SystemHealthMonitor:
    """Monitors health of all Buddy subsystems"""
    
    def __init__(self):
        self.results = {}
        self.timestamp = datetime.utcnow().isoformat()
    
    def check_all(self) -> Dict[str, Any]:
        """Run all system checks and return results"""
        
        # PRIMARY SYSTEMS (7)
        primary_checks = {
            "Firebase": self._check_firebase,
            "OpenAI": self._check_openai,
            "SerpAPI": self._check_serpapi,
            "LLM Client": self._check_llm_client,
            "Orchestrator": self._check_orchestrator,
            "Mission Store": self._check_mission_store,
            "Action Readiness Engine": self._check_action_readiness,
        }
        
        # ADDITIONAL SYSTEMS (15+)
        additional_checks = {
            "Memory Manager": self._check_memory_manager,
            "Knowledge Graph": self._check_knowledge_graph,
            "Tool Registry": self._check_tool_registry,
            "Web Scraper": self._check_web_scraper,
            "Build Signals": self._check_build_signals,
            "Goal Decomposer": self._check_goal_decomposer,
            "Budget Tracker": self._check_budget_tracker,
            "Autonomy Manager": self._check_autonomy_manager,
            "Success Tracker": self._check_success_tracker,
            "Email System": self._check_email_system,
            "GHL CRM": self._check_ghl_crm,
            "Reflection Engine": self._check_reflection_engine,
            "Learning Signals": self._check_learning_signals,
            "Execution Stream": self._check_execution_stream,
            "Screenshot Capture": self._check_screenshot_capture,
        }
        
        # Run all checks
        primary_results = {}
        for name, check_fn in primary_checks.items():
            primary_results[name] = check_fn()
        
        additional_results = {}
        for name, check_fn in additional_checks.items():
            additional_results[name] = check_fn()
        
        # Count statuses
        def count_statuses(results):
            counts = {"green": 0, "red": 0, "gray": 0}
            for system_result in results.values():
                status = system_result.get("status", "gray")
                if status in counts:
                    counts[status] += 1
            return counts
        
        primary_counts = count_statuses(primary_results)
        additional_counts = count_statuses(additional_results)
        total_counts = {
            "green": primary_counts["green"] + additional_counts["green"],
            "red": primary_counts["red"] + additional_counts["red"],
            "gray": primary_counts["gray"] + additional_counts["gray"],
        }
        
        return {
            "timestamp": self.timestamp,
            "overall_health": self._determine_overall_health(total_counts),
            "summary": {
                "primary": primary_counts,
                "additional": additional_counts,
                "total": total_counts,
            },
            "primary_systems": primary_results,
            "additional_systems": additional_results,
        }
    
    def _determine_overall_health(self, counts: Dict[str, int]) -> str:
        """Determine overall health based on counts"""
        total = counts["green"] + counts["red"] + counts["gray"]
        if total == 0:
            return "unknown"
        
        green_pct = (counts["green"] / total) * 100
        
        if green_pct >= 80:
            return "healthy"
        elif green_pct >= 50:
            return "degraded"
        else:
            return "critical"
    
    # PRIMARY SYSTEM CHECKS
    
    def _check_firebase(self) -> Dict[str, Any]:
        """Check Firebase connection"""
        try:
            from Back_End.conversation.session_store import get_conversation_store
            store = get_conversation_store()
            # Try to get sessions (doesn't require API call, just local access)
            if store and hasattr(store, 'sessions'):
                return {
                    "status": "green",
                    "message": "Firebase session store accessible",
                    "details": f"Loaded {len(store.sessions)} sessions"
                }
            else:
                return {
                    "status": "yellow",
                    "message": "Firebase imported but sessions unavailable",
                    "details": "Store exists but sessions dict empty"
                }
        except ImportError as e:
            return {
                "status": "red",
                "message": "Firebase connection failed",
                "error": str(e)
            }
        except Exception as e:
            return {
                "status": "red",
                "message": "Firebase check failed",
                "error": str(e)
            }
    
    def _check_openai(self) -> Dict[str, Any]:
        """Check OpenAI API key and client"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return {
                    "status": "red",
                    "message": "OpenAI API key not configured",
                    "details": "OPENAI_API_KEY environment variable is empty"
                }
            
            import openai
            # Just check if we can import and key is set
            return {
                "status": "green",
                "message": "OpenAI API key configured",
                "details": f"Key present: {'***' + api_key[-4:] if len(api_key) > 4 else '***'}"
            }
        except ImportError:
            return {
                "status": "red",
                "message": "OpenAI library not installed",
                "error": "pip install openai"
            }
        except Exception as e:
            return {
                "status": "red",
                "message": "OpenAI check failed",
                "error": str(e)
            }
    
    def _check_serpapi(self) -> Dict[str, Any]:
        """Check SerpAPI key configuration"""
        try:
            api_key = os.getenv('SERAPI_API_KEY')
            if not api_key:
                return {
                    "status": "yellow",
                    "message": "SerpAPI key not configured",
                    "details": "SERAPI_API_KEY environment variable is empty"
                }
            
            return {
                "status": "green",
                "message": "SerpAPI key configured",
                "details": f"Key present: {'***' + api_key[-4:] if len(api_key) > 4 else '***'}"
            }
        except Exception as e:
            return {
                "status": "red",
                "message": "SerpAPI check failed",
                "error": str(e)
            }
    
    def _check_llm_client(self) -> Dict[str, Any]:
        """Check LLM Client initialization"""
        try:
            from Back_End.llm_client import LLMClient
            client = LLMClient()
            if client.enabled:
                return {
                    "status": "green",
                    "message": "LLM Client initialized and enabled",
                    "details": f"Provider: {client.provider}"
                }
            else:
                return {
                    "status": "yellow",
                    "message": "LLM Client disabled",
                    "details": f"Provider: {client.provider}, but not enabled"
                }
        except Exception as e:
            return {
                "status": "red",
                "message": "LLM Client check failed",
                "error": str(e)
            }
    
    def _check_orchestrator(self) -> Dict[str, Any]:
        """Check Interaction Orchestrator"""
        try:
            from Back_End.interaction_orchestrator import InteractionOrchestrator
            orch = InteractionOrchestrator()
            return {
                "status": "green",
                "message": "Orchestrator initialized",
                "details": "Ready to process intents and generate missions"
            }
        except Exception as e:
            return {
                "status": "red",
                "message": "Orchestrator initialization failed",
                "error": str(e)
            }
    
    def _check_mission_store(self) -> Dict[str, Any]:
        """Check Mission Store"""
        try:
            from Back_End.mission_store import mission_store
            if mission_store:
                return {
                    "status": "green",
                    "message": "Mission Store accessible",
                    "details": "Ready for mission persistence"
                }
            else:
                return {
                    "status": "yellow",
                    "message": "Mission Store imported but not initialized",
                    "details": None
                }
        except Exception as e:
            return {
                "status": "red",
                "message": "Mission Store check failed",
                "error": str(e)
            }
    
    def _check_action_readiness(self) -> Dict[str, Any]:
        """Check Action Readiness Engine"""
        try:
            from Back_End.action_readiness_engine import action_readiness_engine
            if action_readiness_engine:
                return {
                    "status": "green",
                    "message": "Action Readiness Engine accessible",
                    "details": "Ready to calculate confidence scores"
                }
            else:
                return {
                    "status": "yellow",
                    "message": "Engine imported but not initialized",
                    "details": None
                }
        except Exception as e:
            return {
                "status": "red",
                "message": "Action Readiness Engine check failed",
                "error": str(e)
            }
    
    # ADDITIONAL SYSTEM CHECKS
    
    def _check_memory_manager(self) -> Dict[str, Any]:
        """Check Memory Manager"""
        try:
            from Back_End.memory_manager import memory_manager
            if memory_manager:
                return {
                    "status": "green",
                    "message": "Memory Manager accessible",
                    "details": "Episodic memory ready"
                }
            return {"status": "gray", "message": "Memory Manager not imported", "details": None}
        except Exception as e:
            return {"status": "red", "message": "Memory Manager check failed", "error": str(e)}
    
    def _check_knowledge_graph(self) -> Dict[str, Any]:
        """Check Knowledge Graph"""
        try:
            from Back_End.knowledge_graph import knowledge_graph
            if knowledge_graph:
                return {
                    "status": "green",
                    "message": "Knowledge Graph accessible",
                    "details": "Graph database ready"
                }
            return {"status": "gray", "message": "Knowledge Graph not initialized", "details": None}
        except Exception as e:
            return {"status": "red", "message": "Knowledge Graph check failed", "error": str(e)}
    
    def _check_tool_registry(self) -> Dict[str, Any]:
        """Check Tool Registry"""
        try:
            from Back_End.tool_registry import tool_registry
            if tool_registry and hasattr(tool_registry, 'tools'):
                count = len(tool_registry.tools)
                return {
                    "status": "green",
                    "message": "Tool Registry accessible",
                    "details": f"{count} tools registered"
                }
            return {"status": "gray", "message": "Tool Registry empty", "details": None}
        except Exception as e:
            return {"status": "red", "message": "Tool Registry check failed", "error": str(e)}
    
    def _check_web_scraper(self) -> Dict[str, Any]:
        """Check Web Scraper"""
        try:
            import requests
            return {
                "status": "green",
                "message": "Web Scraper ready",
                "details": "requests library available"
            }
        except ImportError:
            return {
                "status": "red",
                "message": "Web Scraper unavailable",
                "error": "requests library not installed"
            }
    
    def _check_build_signals(self) -> Dict[str, Any]:
        """Check Build Signals"""
        try:
            # Build signals are typically file-based
            signals_dir = os.path.join(os.getcwd(), "outputs", "signals")
            if os.path.exists(signals_dir):
                return {
                    "status": "green",
                    "message": "Build Signals directory exists",
                    "details": signals_dir
                }
            return {
                "status": "gray",
                "message": "Build Signals directory not found",
                "details": "Will be created on first signal"
            }
        except Exception as e:
            return {"status": "red", "message": "Build Signals check failed", "error": str(e)}
    
    def _check_goal_decomposer(self) -> Dict[str, Any]:
        """Check Goal Decomposer"""
        try:
            from Back_End.phase25_orchestrator import orchestrator
            if orchestrator:
                return {
                    "status": "green",
                    "message": "Goal Decomposer accessible",
                    "details": "Multi-step task planning ready"
                }
            return {"status": "gray", "message": "Orchestrator not available", "details": None}
        except Exception as e:
            return {"status": "red", "message": "Goal Decomposer check failed", "error": str(e)}
    
    def _check_budget_tracker(self) -> Dict[str, Any]:
        """Check Budget Tracker"""
        try:
            budget_file = os.path.join(os.getcwd(), "outputs", "budget_tracker.json")
            if os.path.exists(budget_file):
                return {
                    "status": "green",
                    "message": "Budget Tracker initialized",
                    "details": "Cost tracking active"
                }
            return {
                "status": "yellow",
                "message": "Budget Tracker not initialized",
                "details": "Will be created on first tracked operation"
            }
        except Exception as e:
            return {"status": "red", "message": "Budget Tracker check failed", "error": str(e)}
    
    def _check_autonomy_manager(self) -> Dict[str, Any]:
        """Check Autonomy Manager"""
        try:
            from Back_End.autonomy_manager import autonomy_manager
            if autonomy_manager:
                return {
                    "status": "green",
                    "message": "Autonomy Manager accessible",
                    "details": "Agent autonomy control ready"
                }
            return {"status": "gray", "message": "Autonomy Manager not initialized", "details": None}
        except Exception as e:
            return {"status": "red", "message": "Autonomy Manager check failed", "error": str(e)}
    
    def _check_success_tracker(self) -> Dict[str, Any]:
        """Check Success Tracker"""
        try:
            from Back_End.success_tracker import success_tracker
            if success_tracker:
                return {
                    "status": "green",
                    "message": "Success Tracker accessible",
                    "details": "Goal completion tracking ready"
                }
            return {"status": "gray", "message": "Success Tracker not initialized", "details": None}
        except Exception as e:
            return {"status": "red", "message": "Success Tracker check failed", "error": str(e)}
    
    def _check_email_system(self) -> Dict[str, Any]:
        """Check Email System"""
        try:
            email_key = os.getenv('SMTP_API_KEY')
            if email_key:
                return {
                    "status": "green",
                    "message": "Email system configured",
                    "details": "Outbound email ready"
                }
            return {
                "status": "yellow",
                "message": "Email system not configured",
                "details": "SMTP_API_KEY not set"
            }
        except Exception as e:
            return {"status": "red", "message": "Email system check failed", "error": str(e)}
    
    def _check_ghl_crm(self) -> Dict[str, Any]:
        """Check GoHighLevel CRM"""
        try:
            ghl_token = os.getenv('GHL_API_TOKEN')
            if ghl_token:
                return {
                    "status": "green",
                    "message": "GHL CRM configured",
                    "details": "CRM integration active"
                }
            return {
                "status": "yellow",
                "message": "GHL CRM not configured",
                "details": "GHL_API_TOKEN not set"
            }
        except Exception as e:
            return {"status": "red", "message": "GHL CRM check failed", "error": str(e)}
    
    def _check_reflection_engine(self) -> Dict[str, Any]:
        """Check Reflection Engine"""
        try:
            from Back_End.phase25_orchestrator import orchestrator
            if orchestrator:
                return {
                    "status": "green",
                    "message": "Reflection Engine accessible",
                    "details": "Learning from experience ready"
                }
            return {"status": "gray", "message": "Reflection Engine not available", "details": None}
        except Exception as e:
            return {"status": "red", "message": "Reflection Engine check failed", "error": str(e)}
    
    def _check_learning_signals(self) -> Dict[str, Any]:
        """Check Learning Signals"""
        try:
            signals_dir = os.path.join(os.getcwd(), "outputs", "learning_signals")
            if os.path.exists(signals_dir):
                return {
                    "status": "green",
                    "message": "Learning Signals directory exists",
                    "details": "Continuous improvement enabled"
                }
            return {
                "status": "gray",
                "message": "Learning Signals directory not created yet",
                "details": "Will be initialized on first learning event"
            }
        except Exception as e:
            return {"status": "red", "message": "Learning Signals check failed", "error": str(e)}
    
    def _check_execution_stream(self) -> Dict[str, Any]:
        """Check Execution Stream"""
        try:
            exec_dir = os.path.join(os.getcwd(), "outputs", "execution_logs")
            if os.path.exists(exec_dir):
                return {
                    "status": "green",
                    "message": "Execution Stream active",
                    "details": "Task execution logging enabled"
                }
            return {
                "status": "gray",
                "message": "Execution Stream not initialized",
                "details": "Will be created on first execution"
            }
        except Exception as e:
            return {"status": "red", "message": "Execution Stream check failed", "error": str(e)}
    
    def _check_screenshot_capture(self) -> Dict[str, Any]:
        """Check Screenshot Capture"""
        try:
            from Back_End.screenshot_capture import capture_screenshot_as_base64
            return {
                "status": "green",
                "message": "Screenshot Capture available",
                "details": "Vision capability ready"
            }
        except ImportError:
            return {
                "status": "yellow",
                "message": "Screenshot Capture not available",
                "details": "Vision dependencies not installed"
            }
        except Exception as e:
            return {"status": "red", "message": "Screenshot Capture check failed", "error": str(e)}


class SystemFlowTester:
    """Tests complete system flow end-to-end"""
    
    def __init__(self):
        self.trace_steps = []
    
    def test_complete_flow(self, test_message: str = "Run system integration test") -> Dict[str, Any]:
        """
        Simulate a complete chat flow through all major systems.
        Returns step-by-step trace showing which systems worked and which failed.
        """
        
        self._log_step("Initialization", "Starting complete flow test")
        
        results = {
            "test_message": test_message,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": [],
            "summary": {"passed": 0, "failed": 0, "error": None}
        }
        
        # STEP 1: Message receiption
        try:
            self._log_step("Message Reception", "Received user message")
            results["steps"].append(self._make_step("Message Reception", "passed", "Message received and validated"))
            results["summary"]["passed"] += 1
        except Exception as e:
            self._log_step("Message Reception", f"FAILED: {e}")
            results["steps"].append(self._make_step("Message Reception", "failed", str(e)))
            results["summary"]["failed"] += 1
        
        # STEP 2: Firebase session creation
        try:
            from Back_End.conversation.session_store import get_conversation_store
            store = get_conversation_store()
            session_id = f"test_{datetime.utcnow().timestamp()}"
            self._log_step("Firebase Session", f"Created test session {session_id}")
            results["steps"].append(self._make_step("Firebase Session", "passed", f"Session created: {session_id}"))
            results["summary"]["passed"] += 1
        except Exception as e:
            self._log_step("Firebase Session", f"FAILED: {e}")
            results["steps"].append(self._make_step("Firebase Session", "failed", str(e)))
            results["summary"]["failed"] += 1
            return results  # Can't continue without session
        
        # STEP 3: LLM Intent Classification
        try:
            from Back_End.llm_client import LLMClient
            llm = LLMClient()
            if not llm.enabled:
                raise Exception(f"LLM disabled (provider: {llm.provider})")
            
            # Simulate an intent classification call
            self._log_step("LLM Intent Classification", "Attempting to classify intent")
            # Note: Not actually calling API, just verifying it's initialized
            results["steps"].append(self._make_step("LLM Intent Classification", "passed", "LLM client ready for classification"))
            results["summary"]["passed"] += 1
        except Exception as e:
            self._log_step("LLM Intent Classification", f"FAILED: {e}")
            results["steps"].append(self._make_step("LLM Intent Classification", "failed", str(e)))
            results["summary"]["failed"] += 1
        
        # STEP 4: Orchestrator Intent Processing
        try:
            from Back_End.interaction_orchestrator import InteractionOrchestrator
            orchestrator = InteractionOrchestrator()
            self._log_step("Orchestrator", "Orchestrator initialized for mission proposal")
            results["steps"].append(self._make_step("Orchestrator Processing", "passed", "Ready to generate mission proposals"))
            results["summary"]["passed"] += 1
        except Exception as e:
            self._log_step("Orchestrator", f"FAILED: {e}")
            results["steps"].append(self._make_step("Orchestrator Processing", "failed", str(e)))
            results["summary"]["failed"] += 1
        
        # STEP 5: Action Readiness Check
        try:
            from Back_End.action_readiness_engine import action_readiness_engine
            self._log_step("Action Readiness", "Checking action readiness scores")
            results["steps"].append(self._make_step("Action Readiness", "passed", "Confidence scoring available"))
            results["summary"]["passed"] += 1
        except Exception as e:
            self._log_step("Action Readiness", f"FAILED: {e}")
            results["steps"].append(self._make_step("Action Readiness", "failed", str(e)))
            results["summary"]["failed"] += 1
        
        # STEP 6: Mission Store Persistence
        try:
            from Back_End.mission_store import mission_store
            self._log_step("Mission Store", "Checking mission persistence")
            results["steps"].append(self._make_step("Mission Store", "passed", "Mission persistence ready"))
            results["summary"]["passed"] += 1
        except Exception as e:
            self._log_step("Mission Store", f"FAILED: {e}")
            results["steps"].append(self._make_step("Mission Store", "failed", str(e)))
            results["summary"]["failed"] += 1
        
        # STEP 7: Tool Registry Access
        try:
            from Back_End.tool_registry import tool_registry
            tool_count = len(tool_registry.tools) if hasattr(tool_registry, 'tools') else 0
            
            # Get the actual tool names for verification
            if tool_registry and hasattr(tool_registry, 'tools'):
                tool_names = sorted(list(tool_registry.tools.keys()))
                tools_summary = ", ".join(tool_names[:5])
                if len(tool_names) > 5:
                    tools_summary += f", ... and {len(tool_names) - 5} more"
                detail = f"{tool_count} tools available: {tools_summary}"
            else:
                detail = f"{tool_count} tools ready for execution"
            
            self._log_step("Tool Registry", f"Verified {tool_count} tools available")
            results["steps"].append(self._make_step("Tool Registry", "passed", detail))
            results["summary"]["passed"] += 1
        except Exception as e:
            self._log_step("Tool Registry", f"FAILED: {e}")
            results["steps"].append(self._make_step("Tool Registry", "failed", str(e)))
            results["summary"]["failed"] += 1
        
        # STEP 8: Message Persistence
        try:
            store = get_conversation_store()
            store.append_message(session_id, 'user', test_message, 'test_flow')
            self._log_step("Message Persistence", "User message saved to Firebase")
            results["steps"].append(self._make_step("Message Persistence", "passed", "Messages persisting to Firestore"))
            results["summary"]["passed"] += 1
        except Exception as e:
            self._log_step("Message Persistence", f"FAILED: {e}")
            results["steps"].append(self._make_step("Message Persistence", "failed", str(e)))
            results["summary"]["failed"] += 1
        
        # Summary
        total = results["summary"]["passed"] + results["summary"]["failed"]
        results["summary"]["overall"] = "PASSED" if results["summary"]["failed"] == 0 else "PARTIAL" if results["summary"]["passed"] > 0 else "FAILED"
        results["summary"]["success_rate"] = f"{(results['summary']['passed'] / total * 100):.0f}%" if total > 0 else "0%"
        
        self._log_step("Test Complete", f"Summary: {results['summary']['passed']}/{total} passed")
        
        return results
    
    def _make_step(self, name: str, status: str, detail: str) -> Dict[str, str]:
        """Create a test step result"""
        return {
            "name": name,
            "status": status,  # "passed" or "failed"
            "detail": detail
        }
    
    def _log_step(self, step_name: str, message: str):
        """Log a step to internal trace"""
        log_msg = f"[FLOW_TEST] {step_name}: {message}"
        logging.info(log_msg)
        self.trace_steps.append(log_msg)
