"""
WebNavigatorAgent - Phase 1 Steps 1-3 Complete, Phase 2 Step 1 Added

A wrapper agent that exposes existing Selenium tooling (BuddysVisionCore + BuddysArms)
through a standardized agent interface with pagination and learning signal instrumentation.

Phase 1 Step 1: Navigation and extraction wrapper
Phase 1 Step 2: Bounded pagination traversal
Phase 1 Step 3: Selector-level learning signal instrumentation
Phase 2 Step 1: Goal-guided navigation intent layer (ranking only, no action)
"""

import time
import logging
import hashlib
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timezone

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

from Back_End.buddys_vision_core import BuddysVisionCore
from Back_End.buddys_arms import BuddysArms
from Back_End.phase25_orchestrator import Phase25Orchestrator
from Back_End.agents.navigation_intent_engine import NavigationIntentEngine
from Back_End.mission_control.mission_contract import MissionContract
from Back_End.mission_control.mission_registry import MissionRegistry
from Back_End.mission_control.mission_progress_tracker import MissionProgressTracker
from Back_End.learning.signal_priority import apply_signal_priority
from Back_End.mission_control.regret_registry import log_regret
from Back_End.mission_evaluator import MissionEvaluator
from Back_End.explainability.decision_rationale import DecisionRationaleEmitter

logger = logging.getLogger(__name__)

MULTI_STEP_LIVE_ENABLED = os.getenv('MULTI_STEP_LIVE_ENABLED', 'False').lower() == 'true'


class WebNavigatorAgent:
    """
    Agent wrapper for web navigation and extraction with pagination and learning signals.
    
    Wraps existing Selenium tooling (BuddysVisionCore + BuddysArms) without
    adding new behavior. Instruments selector attempts for learning signal emission.
    
    Phase 1 Step 1: Basic navigation and extraction wrapper
    Phase 1 Step 2: Bounded pagination traversal (max_pages enforcement)
    Phase 1 Step 3: Selector-level learning signals (instrumentation only)
    Phase 1 Step 5: Adaptive selector selection (use ranking data)
    Phase 2 Step 1: Goal-guided navigation intent (ranking only, no auto-action)
    """
    
    def __init__(self, headless: bool = True, orchestrator: Optional[Phase25Orchestrator] = None):
        """Initialize the agent."""
        self.headless = headless
        self.orchestrator = orchestrator or Phase25Orchestrator()
        self.mission_registry = MissionRegistry()
        self.driver = None
        self.vision_core = None
        self.arms = None
        
        # Phase 1 Step 3: Learning signal tracking
        self.selector_signals = []
        self.current_page_number = 1
        self.run_start_time = None
        
        # Phase 1 Step 5: Load selector rankings
        self.selector_rankings = self._load_selector_rankings()
        self.ranked_selector_used = False
        self.fallback_used = False
        self.mission_evaluator = MissionEvaluator()
        
    def _initialize_browser(self) -> None:
        """Initialize Chrome browser."""
        if self.driver is not None:
            return
            
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            chromedriver_path = Path.home() / ".wdm" / "drivers" / "chromedriver" / "win64" / "144.0.7559.133" / "chromedriver-win32" / "chromedriver.exe"
            
            if chromedriver_path.exists():
                logger.info("Using cached ChromeDriver")
                service = Service(str(chromedriver_path))
            else:
                logger.info("Using webdriver-manager to install ChromeDriver")
                service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.vision_core = BuddysVisionCore(self.driver, timeout=10)
            self.arms = BuddysArms(self.driver, self.vision_core, timeout=15)
            
            logger.info("✓ Browser and Selenium wrappers initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    def _close_browser(self) -> None:
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self.vision_core = None
                self.arms = None
    
    # === PHASE 1 STEP 5: ADAPTIVE SELECTOR SELECTION ===
    
    def _load_selector_rankings(self) -> List[Dict[str, Any]]:
        """Load selector rankings from analysis output."""
        try:
            rankings_file = Path(__file__).parent.parent.parent / "outputs" / "phase25" / "selector_rankings.json"
            if rankings_file.exists():
                with open(rankings_file, 'r') as f:
                    rankings = json.load(f)
                logger.info(f"Loaded {len(rankings)} selector rankings")
                return rankings
            else:
                logger.debug("No selector rankings file found, using default order")
                return []
        except Exception as e:
            logger.warning(f"Failed to load selector rankings: {e}")
            return []
    
    def _get_ranked_pagination_selectors(self) -> List[Dict[str, Any]]:
        """Get pagination selectors ordered by rank."""
        if not self.selector_rankings:
            return []
        
        # Filter for likely pagination selectors
        pagination_keywords = ["next", "rel", "page", "pagination", "aria"]
        pagination_selectors = []
        
        for ranking in self.selector_rankings:
            selector = ranking.get("selector", "").lower()
            # Check if selector is likely pagination-related
            if any(keyword in selector for keyword in pagination_keywords):
                pagination_selectors.append(ranking)
        
        # Sort by rank (already sorted from file, but ensure)
        pagination_selectors.sort(key=lambda x: x.get("rank", 999))
        
        return pagination_selectors
    
    # === PHASE 1 STEP 3: LEARNING SIGNAL EMISSION ===
    
    def _emit_selector_signal(
        self,
        selector: str,
        selector_type: str,
        outcome: str,
        duration_ms: int,
        retry_count: int = 0,
        mission_id: Optional[str] = None
    ) -> None:
        """Emit a selector-level learning signal."""
        signal = {
            "signal_type": "selector_outcome",
            "tool_name": "web_navigator_agent",
            "selector": selector,
            "selector_type": selector_type,
            "page_number": self.current_page_number,
            "outcome": outcome,
            "duration_ms": duration_ms,
            "retry_count": retry_count,
            "confidence": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if mission_id:
            signal["mission_id"] = mission_id
        
        self.selector_signals.append(signal)
        logger.debug(f"[SIGNAL] {selector_type}:{selector} → {outcome} ({duration_ms}ms, {retry_count} retries)")
    
    def _emit_aggregate_signals(self, execution_id: str) -> None:
        """Emit aggregate learning signals at end of run."""
        if not self.selector_signals:
            return
        
        successful = sum(1 for s in self.selector_signals if s["outcome"] == "success")
        failed = sum(1 for s in self.selector_signals if s["outcome"] == "failure")
        total = len(self.selector_signals)
        success_rate = successful / total if total > 0 else 0.0
        
        pagination_signals = [s for s in self.selector_signals 
                             if "rel='next'" in s["selector"] or "aria-label" in s["selector"] or "Next" in s["selector"]]
        pagination_successful = sum(1 for s in pagination_signals if s["outcome"] == "success")
        pagination_success_rate = pagination_successful / len(pagination_signals) if pagination_signals else 0.0
        
        total_duration_ms = sum(s["duration_ms"] for s in self.selector_signals)
        avg_duration_ms = total_duration_ms / total if total > 0 else 0
        
        total_retries = sum(s["retry_count"] for s in self.selector_signals)
        avg_retries = total_retries / total if total > 0 else 0
        
        aggregate_signal = {
            "signal_type": "selector_aggregate",
            "signal_layer": "aggregate",
            "signal_source": "web_navigator",
            "tool_name": "web_navigator_agent",
            "execution_id": execution_id,
            "total_selectors_attempted": total,
            "selectors_succeeded": successful,
            "selectors_failed": failed,
            "overall_success_rate": success_rate,
            "pagination_signals_count": len(pagination_signals),
            "pagination_success_rate": pagination_success_rate,
            "ranked_selector_used": self.ranked_selector_used,
            "fallback_used": self.fallback_used,
            "selector_rankings_loaded": len(self.selector_rankings) > 0,
            "total_duration_ms": total_duration_ms,
            "average_duration_ms": avg_duration_ms,
            "total_retries": total_retries,
            "average_retries": avg_retries,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._persist_learning_signal(aggregate_signal)
        logger.info(f"[AGGREGATE] {total} selectors: {successful} success, {failed} failed (rate: {success_rate:.1%})")
    
    def _persist_learning_signal(self, signal: Dict[str, Any]) -> None:
        """Persist a learning signal to learning_signals.jsonl."""
        try:
            signal = apply_signal_priority(signal)
            if hasattr(self.orchestrator, 'log_learning_signal'):
                self.orchestrator.log_learning_signal(signal)
            else:
                outputs_dir = Path(__file__).parent.parent.parent / "outputs" / "phase25"
                outputs_dir.mkdir(parents=True, exist_ok=True)
                signal_file = outputs_dir / "learning_signals.jsonl"
                with open(signal_file, 'a') as f:
                    f.write(json.dumps(signal) + '\n')
        except Exception as e:
            logger.warning(f"Failed to persist learning signal: {e}")

    def _emit_multi_step_metrics(self, status: str, reason: str, mission: Optional[MissionContract] = None) -> None:
        """
        Emit lightweight multi-step metrics after mission completion/failure.

        Read-only: no effect on mission execution.
        """
        if not MULTI_STEP_LIVE_ENABLED:
            return

        duration_ms = None
        if self.run_start_time:
            duration_ms = int((time.time() - self.run_start_time) * 1000)

        signal = {
            "signal_type": "multi_step_step_metrics",
            "signal_layer": "multi_step",
            "signal_source": "web_navigator_agent",
            "mission_id": getattr(mission, "mission_id", None),
            "status": status,
            "reason": reason,
            "objective": getattr(getattr(mission, "objective", None), "description", None),
            "goal_id": getattr(mission, "goal_id", None),
            "thread_id": getattr(mission, "mission_thread_id", None),
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._persist_learning_signal(signal)
    
    # === PHASE 2 STEP 4: MISSION CONTROL ===
    
    def _log_mission_status(self, mission_id: str, status: str, reason: str) -> None:
        signal = {
            "signal_type": "mission_status_update",
            "mission_id": mission_id,
            "status": status,
            "reason": reason,
            "signal_layer": "mission",
            "signal_source": "mission_control",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        # Phase 4 Step 1: Add mission_thread_id if present
        if self.current_mission_thread_id:
            signal["mission_thread_id"] = self.current_mission_thread_id
        self._persist_learning_signal(signal)
    
    def _log_mission_progress(self, mission_id: str, items_collected: int) -> None:
        signal = {
            "signal_type": "mission_progress_update",
            "mission_id": mission_id,
            "items_collected": items_collected,
            "signal_layer": "mission",
            "signal_source": "mission_control",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        # Phase 4 Step 1: Add mission_thread_id if present
        if self.current_mission_thread_id:
            signal["mission_thread_id"] = self.current_mission_thread_id
        self._persist_learning_signal(signal)
    
    def _log_mission_completed(self, mission_id: str, reason: str, mission: Optional[MissionContract] = None) -> None:
        self.mission_evaluator.emit_mission_outcome(
            mission_id=mission_id,
            status="completed",
            reason=reason,
            mission_thread_id=self.current_mission_thread_id,
            mission_created_at=getattr(mission, "created_at", None) if mission else None
        )
        self._emit_multi_step_metrics(status="completed", reason=reason, mission=mission)
    
    def _log_mission_failed(self, mission_id: str, reason: str, mission: Optional[MissionContract] = None) -> None:
        self.mission_evaluator.emit_mission_outcome(
            mission_id=mission_id,
            status="failed",
            reason=reason,
            mission_thread_id=self.current_mission_thread_id,
            mission_created_at=getattr(mission, "created_at", None) if mission else None
        )
        self._emit_multi_step_metrics(status="failed", reason=reason, mission=mission)
        
        # Phase 4 Step 6: Log regret for high-cost failures
        if mission:
            self._log_mission_regret(mission, reason)
    
    def _log_mission_regret(self, mission: MissionContract, failure_reason: str) -> None:
        """
        Log a regret entry when mission fails with high cost.
        
        Phase 4 Step 6: Regret Registry - Record irreversible failures
        """
        # Estimate cost of failure
        estimated_cost = {
            "time_lost": mission.scope.max_duration_seconds,  # Full max time was potentially wasted
            "trust_impact": 15,  # Failed missions reduce trust
            "opportunities_lost": 0  # No opportunities were collected
        }
        
        # Determine if failure is irreversible
        irreversible = failure_reason in ["no_progress", "navigation_blocked"]
        
        # Log the regret
        log_regret(
            mission_id=mission.mission_id,
            action="mission_execution",
            failure_reason=failure_reason,
            irreversible=irreversible,
            estimated_cost=estimated_cost,
            context={
                "objective": mission.objective.description,
                "goal_id": mission.goal_id,
                "program_id": mission.program_id,
                "thread_id": self.current_mission_thread_id
            }
        )
    
    # === PHASE 3 STEP 1: GOAL SATISFACTION EVALUATION ===
    
    def _evaluate_goal_satisfaction(
        self,
        mission_id: str,
        mission_objective: str,
        items_collected: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> None:
        """Deprecated shim. Use MissionEvaluator instead."""
        self.mission_evaluator.evaluate_after_execution(
            mission_id=mission_id,
            objective_description=mission_objective,
            items_collected=items_collected,
            context=context,
            outcome_summary={
                "status": "completed",
                "items_collected": len(items_collected or []),
                "reason": "legacy_call"
            },
        )
    
    # === PHASE 4 STEP 2: EXPECTATION DELTA EVALUATION ===
    
    def _evaluate_expectation_delta(
        self,
        mission_id: str,
        objective: Any,  # MissionObjective
        outcome_summary: Dict[str, Any],
        mission_thread_id: Optional[str] = None
    ) -> None:
        """Deprecated shim. Use MissionEvaluator instead."""
        self.mission_evaluator.evaluate_after_execution(
            mission_id=mission_id,
            objective_description=getattr(objective, "description", ""),
            items_collected=[],
            context={},
            outcome_summary=outcome_summary,
            objective=objective,
            mission_thread_id=mission_thread_id,
        )

    # === PHASE 4 STEP 3: CONCEPT DRIFT DETECTION ===

    def _evaluate_concept_drift(self) -> None:
        """Deprecated shim. Use MissionEvaluator instead."""
        self.mission_evaluator.evaluate_after_execution(
            mission_id="",
            objective_description="",
            items_collected=[],
            context={},
            outcome_summary={"status": "completed", "items_collected": 0, "reason": "legacy_call"}
        )
    
    # === PHASE 3 STEP 2: OPPORTUNITY NORMALIZATION ===
    
    def _normalize_opportunities(
        self,
        mission_id: str,
        mission_objective: str,
        items_collected: List[Dict[str, Any]],
        context: Dict[str, Any],
        mission: Optional[MissionContract] = None
    ) -> None:
        """Deprecated shim. Use MissionEvaluator instead."""
        self.mission_evaluator.evaluate_after_execution(
            mission_id=mission_id,
            objective_description=mission_objective,
            items_collected=items_collected,
            context=context,
            outcome_summary={
                "status": "completed",
                "items_collected": len(items_collected or []),
                "reason": "legacy_call"
            },
            mission_created_at=getattr(mission, "created_at", None)
        )
    
    def _count_opportunity_types(self, opportunities: List[Any]) -> Dict[str, int]:
        """Deprecated shim. Use MissionEvaluator instead."""
        return self.mission_evaluator._count_opportunity_types(opportunities)

    def _evaluate_ambiguity(
        self,
        mission_id: str,
        mission_status: str,
        items_collected: int
    ) -> None:
        """Deprecated shim. Use MissionEvaluator instead."""
        self.mission_evaluator.evaluate_after_execution(
            mission_id=mission_id,
            objective_description="",
            items_collected=[],
            context={},
            outcome_summary={
                "status": mission_status,
                "items_collected": items_collected,
                "reason": "legacy_call"
            },
        )
    
    def _compute_mission_costs(self, mission_id: str) -> None:
        """Deprecated shim. Use MissionEvaluator instead."""
        self.mission_evaluator.evaluate_after_execution(
            mission_id=mission_id,
            objective_description="",
            items_collected=[],
            context={},
            outcome_summary={"status": "completed", "items_collected": 0, "reason": "legacy_call"}
        )
    
    def _enforce_mission_limits(
        self,
        mission: MissionContract,
        start_time: float
    ) -> Optional[Dict[str, str]]:
        """Check mission stop conditions. Returns dict with status/reason if stop triggered."""
        elapsed = int(time.time() - start_time)
        if mission.scope.max_duration_seconds and elapsed > mission.scope.max_duration_seconds:
            return {"status": "aborted", "reason": "max_duration_exceeded"}
        return None
    
    # === PHASE 2 STEP 1: GOAL-GUIDED NAVIGATION (INTENT LAYER) ===
    
    def _rank_and_log_intent(
        self,
        goal_description: str,
        inspection_data: Dict[str, Any],
        current_url: str
    ) -> Optional[NavigationIntentEngine]:
        """
        Rank navigation candidates and log intent signals.
        
        Phase 2 Step 1: Pure reasoning layer - ranks options but does NOT navigate.
        
        Args:
            goal_description: Natural language goal
            inspection_data: Page inspection from BuddysVisionCore
            current_url: Current page URL
            
        Returns:
            NavigationIntentEngine instance or None if ranking failed
        """
        try:
            # Initialize intent engine
            intent_engine = NavigationIntentEngine(
                goal_description=goal_description,
                page_context=inspection_data,
                current_url=current_url
            )
            
            # Get top 5 ranked candidates
            top_candidates = intent_engine.get_top_candidates(n=5)
            
            if top_candidates:
                logger.info(f"Intent ranking: {len(top_candidates)} candidates for goal: '{goal_description}'")
                
                # Log top 5
                for idx, candidate in enumerate(top_candidates, 1):
                    logger.info(
                        f"  #{idx}: [{candidate['score']}] {candidate['text'][:50]} "
                        f"→ {candidate['href'][:60]} | signals: {', '.join(candidate['signals'][:3])}"
                    )
                
                # Emit intent signal
                top = top_candidates[0]
                intent_signal = intent_engine.emit_intent_signal(top)
                if self.current_mission_id:
                    intent_signal["mission_id"] = self.current_mission_id
                self._persist_learning_signal(intent_signal)
                
                return intent_engine
            else:
                logger.debug("No navigation candidates found for intent ranking")
                return None
        
        except Exception as e:
            logger.warning(f"Intent ranking failed: {e}")
            return None
    
    def _execute_intent_action(self, action: Dict[str, Any], goal: str) -> None:
        """
        Phase 2 Step 2: Execute intent-driven navigation action.
        
        Args:
            action: Action dict from intent_engine.select_action()
            goal: Goal description for logging
        """
        try:
            text = action.get("text", "")
            href = action.get("href", "")
            confidence = action.get("confidence", 0.0)
            
            logger.info(f"[INTENT ACTION] Navigating to: '{text}' → {href} (confidence={confidence:.2f})")
            
            # Use BuddysArms to navigate
            self.arms.navigate(href)
            
            # Log intent action taken
            signal = {
                "signal_type": "intent_action_taken",
                "signal_layer": "intent",
                "signal_source": "navigation_intent_engine",
                "goal": goal,
                "action": {
                    "text": text,
                    "href": href,
                    "score": action.get("score"),
                    "signals": action.get("signals", [])
                },
                "confidence": confidence,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            if self.current_mission_id:
                signal["mission_id"] = self.current_mission_id
            self._persist_learning_signal(signal)
            
            # Emit decision rationale (deterministic explanation)
            if self.current_mission_id:
                emitter = DecisionRationaleEmitter()
                rationale = emitter.explain_intent_action_taken(
                    action=action,
                    goal=goal,
                    confidence=confidence,
                    score=action.get("score", 0),
                    total_candidates=action.get("total_candidates", 1)
                )
                if emitter.should_emit_signal(rationale):
                    rationale_signal = rationale.to_signal(self.current_mission_id)
                    self._persist_learning_signal(rationale_signal)
            
            logger.info(f"[INTENT ACTION] Navigation successful. Current URL: {self.driver.current_url}")
            
        except Exception as e:
            logger.error(f"Intent action execution failed: {e}")
    
    def _log_intent_action_blocked(self, intent_engine: NavigationIntentEngine, goal: str) -> None:
        """
        Phase 2 Step 2: Log when intent action is blocked by safety gates.
        
        Args:
            intent_engine: Intent engine instance
            goal: Goal description for logging
        """
        # Get top candidate for context
        candidates = intent_engine.rank_navigation_candidates()
        top_candidate = candidates[0] if candidates else None
        
        reason = "no_candidates"
        confidence = 0.0
        
        if top_candidate:
            score = top_candidate.get("score", 0)
            confidence = min(max(score / 10.0, 0.0), 1.0)
            
            if confidence < 0.25:
                reason = "confidence_below_threshold"
            elif not top_candidate.get("href"):
                reason = "element_not_clickable"
            elif top_candidate.get("href") == intent_engine.current_url:
                reason = "href_equals_current_url"
            else:
                reason = "unknown_gate"
        
        signal = {
            "signal_type": "intent_action_blocked",
            "signal_layer": "intent",
            "signal_source": "navigation_intent_engine",
            "goal": goal,
            "reason": reason,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if self.current_mission_id:
            signal["mission_id"] = self.current_mission_id
        self._persist_learning_signal(signal)
        
        logger.debug(f"[INTENT ACTION] Blocked: {reason} (confidence={confidence:.2f})")
    
    # === PHASE 1 STEP 3: LEARNING SIGNAL EMISSION ===
    
    def _compute_learning_metrics(self) -> Dict[str, Any]:
        """Compute aggregate learning metrics from accumulated signals."""
        if not self.selector_signals:
            return {
                "total_attempted": 0,
                "total_succeeded": 0,
                "total_failed": 0,
                "success_rate": 0.0
            }
        
        total = len(self.selector_signals)
        succeeded = sum(1 for s in self.selector_signals if s["outcome"] == "success")
        failed = total - succeeded
        success_rate = succeeded / total if total > 0 else 0.0
        
        return {
            "total_attempted": total,
            "total_succeeded": succeeded,
            "total_failed": failed,
            "success_rate": success_rate
        }
    
    def _flush_selector_signals(self, execution_id: str) -> None:
        """Persist all accumulated selector signals to learning_signals.jsonl."""
        for signal in self.selector_signals:
            self._persist_learning_signal(signal)
        logger.debug(f"Flushed {len(self.selector_signals)} selector signals")
    
    def run(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single navigation + extraction run."""
        start_time = time.time()
        execution_id = f"nav_{datetime.now().timestamp()}"
        
        # Phase 1 Step 3: Initialize learning signal tracking
        self.selector_signals = []
        self.current_page_number = 1
        self.run_start_time = start_time
        self.current_mission_id = None  # Phase 2 Step 6: Mission attribution
        self.current_mission_thread_id = None  # Phase 4 Step 1: Mission Threading
        
        target_url = input_payload.get("target_url")
        page_type = input_payload.get("page_type", "unknown")
        expected_fields = input_payload.get("expected_fields", [])
        max_pages = input_payload.get("max_pages", 1)
        execution_mode = input_payload.get("execution_mode", "DRY_RUN")
        mission_contract_data = input_payload.get("mission_contract")
        mission = None
        mission_stop_reason = None
        mission_status = None
        
        if mission_contract_data:
            if isinstance(mission_contract_data, MissionContract):
                mission = mission_contract_data
            else:
                mission = MissionContract.from_dict(mission_contract_data)
            
            self.mission_registry.register_mission(mission)
            mission.status = "active"
            self.mission_registry.update_status(mission.mission_id, "active", "mission_started")
            self._log_mission_status(mission.mission_id, "active", "mission_started")
            mission.metadata.setdefault("progress", MissionProgressTracker().to_dict())
            
            self.current_mission_id = mission.mission_id  # Phase 2 Step 6: Set for signal attribution
            self.current_mission_thread_id = mission.mission_thread_id  # Phase 4 Step 1: Set for threading
            self.current_mission_thread_id = mission.mission_thread_id  # Phase 4 Step 1: Set for threading
            
            if mission.scope.max_pages and max_pages > mission.scope.max_pages:
                max_pages = mission.scope.max_pages
                mission_stop_reason = "max_pages_exceeded"
        
        if not target_url:
            if mission:
                self.mission_registry.update_status(mission.mission_id, "failed", "target_url_missing")
                self._log_mission_status(mission.mission_id, "failed", "target_url_missing")
            return self._build_error_response(execution_id=execution_id, error="target_url is required", start_time=start_time)
        
        logger.info(f"[WebNavigatorAgent] Starting navigation to {target_url}")
        logger.info(f"  Max pages: {max_pages}")
        
        try:
            if mission:
                stop_check = self._enforce_mission_limits(mission, start_time)
                if stop_check:
                    mission_status = stop_check["status"]
                    mission_stop_reason = stop_check["reason"]
                    self.mission_registry.update_status(mission.mission_id, mission_status, mission_stop_reason)
                    self._log_mission_status(mission.mission_id, mission_status, mission_stop_reason)
                    return self._build_error_response(execution_id=execution_id, error=mission_stop_reason, start_time=start_time)
            
            self._initialize_browser()
            logger.info(f"Navigating to {target_url}...")
            self.arms.navigate(target_url)
            
            if max_pages > 1:
                logger.info("Multi-page extraction enabled")
                extracted_data, pagination_metadata = self._paginate_and_extract(
                    expected_fields=expected_fields, page_type=page_type, max_pages=max_pages
                )
            else:
                logger.info("Single-page extraction (max_pages=1)")
                inspection_data = self.vision_core.inspect_website(
                    url=self.driver.current_url, expand_interactive=True, max_scrolls=4
                )
                
                # Phase 2 Step 1: Rank navigation candidates based on goal
                # Phase 2 Step 2: Intent-aware action selection
                goal_description = input_payload.get("goal_description")
                intent_engine = None
                if goal_description:
                    intent_engine = self._rank_and_log_intent(goal_description, inspection_data, self.driver.current_url)
                    
                    # Phase 2 Step 2: Execute intent action if safety gates pass
                    if intent_engine:
                        intent_action = intent_engine.select_action(confidence_threshold=0.25)
                        if intent_action:
                            self._execute_intent_action(intent_action, goal_description)
                        else:
                            self._log_intent_action_blocked(intent_engine, goal_description)
                
                extracted_data = self._extract_data_from_inspection(
                    inspection_data=inspection_data, expected_fields=expected_fields, page_type=page_type
                )
                pagination_metadata = {
                    "pages_visited": 1,
                    "pagination_detected": False,
                    "pagination_method": None,
                    "pagination_stopped_reason": "single_page_mode"
                }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if mission:
                stop_check = self._enforce_mission_limits(mission, start_time)
                stop_enforced = stop_check is not None
                if stop_check:
                    mission_status = stop_check["status"]
                    mission_stop_reason = stop_check["reason"]
                elif mission_stop_reason == "max_pages_exceeded":
                    mission_status = "aborted"
                else:
                    mission_status = "completed"
                
                if not stop_enforced and mission_stop_reason != "max_pages_exceeded":
                    # Phase 2 Step 5: Progress tracking and completion detection
                    progress_data = mission.metadata.get("progress", {})
                    tracker = MissionProgressTracker.from_dict(progress_data)
                    items_collected = len(extracted_data.get("items", []))
                    pages_visited = pagination_metadata.get("pages_visited", 1)
                    tracker.update(items_collected_this_step=items_collected, pages_visited=pages_visited)
                    mission.metadata["progress"] = tracker.to_dict()
                    
                    self._log_mission_progress(mission.mission_id, tracker.total_items_collected)
                    
                    objective_type = mission.objective.type
                    target = mission.objective.target
                    
                    if objective_type == "quantitative" and target is not None:
                        if tracker.total_items_collected >= target:
                            mission_status = "completed"
                            mission_stop_reason = "target_reached"
                            self._log_mission_completed(mission.mission_id, "target_reached", mission)
                        elif tracker.pages_since_last_increase >= mission.failure_conditions.no_progress_pages:
                            mission_status = "failed"
                            mission_stop_reason = "no_progress"
                            self._log_mission_failed(mission.mission_id, "no_progress", mission)
            
            # Phase 1 Step 3: Emit learning signals
            self._flush_selector_signals(execution_id)
            self._emit_aggregate_signals(execution_id)
            learning_metrics = self._compute_learning_metrics()
            
            self.orchestrator.log_execution(
                task_id=execution_id,
                tool_name="web_navigator_agent",
                action_type="navigate_and_extract",
                status="COMPLETED",
                data={
                    "url": target_url,
                    "items_extracted": len(extracted_data.get("items", [])),
                    "pages_visited": pagination_metadata.get("pages_visited", 1),
                    "selectors_attempted": learning_metrics["total_attempted"],
                    "selector_success_rate": learning_metrics["success_rate"]
                },
                duration_ms=duration_ms
            )
            
            response = {
                "status": "COMPLETED",
                "data": extracted_data,
                "metadata": {
                    "execution_id": execution_id,
                    "duration_ms": duration_ms,
                    "items_extracted": len(extracted_data.get("items", [])),
                    "url": target_url,
                    "page_type": page_type,
                    "execution_mode": execution_mode,
                    "selectors_attempted": learning_metrics["total_attempted"],
                    "selectors_succeeded": learning_metrics["total_succeeded"],
                    "selector_success_rate": learning_metrics["success_rate"],
                    **pagination_metadata
                }
            }
            
            if mission:
                final_reason = mission_stop_reason or "execution_completed"
                final_status = mission_status or "completed"
                completed_at = datetime.now(timezone.utc).isoformat()
                self.mission_registry.update_status(mission.mission_id, final_status, final_reason, completed_at=completed_at)
                self._log_mission_status(mission.mission_id, final_status, final_reason)
                
                # Mission evaluation (centralized, observe-only)
                self.mission_evaluator.evaluate_after_execution(
                    mission_id=mission.mission_id,
                    objective_description=mission.objective.description,
                    items_collected=extracted_data.get("items", []),
                    context={
                        "page_title": extracted_data.get("page_title"),
                        "page_url": extracted_data.get("page_url"),
                        "page_type": page_type,
                        "items_count": len(extracted_data.get("items", []))
                    },
                    outcome_summary={
                        "status": final_status,
                        "items_collected": len(extracted_data.get("items", [])),
                        "reason": final_reason
                    },
                    objective=mission.objective,
                    mission_thread_id=mission.mission_thread_id,
                    mission_created_at=mission.created_at
                )
            
            logger.info(f"✓ Navigation completed: {len(extracted_data.get('items', []))} items, {pagination_metadata['pages_visited']} page(s)")
            return response
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}", exc_info=True)
            if mission:
                self.mission_registry.update_status(mission.mission_id, "failed", str(e))
                self._log_mission_status(mission.mission_id, "failed", str(e))
            return self._build_error_response(execution_id=execution_id, error=str(e), start_time=start_time)
        
        finally:
            self._close_browser()
    
    def _extract_data_from_inspection(
        self, inspection_data: Dict[str, Any], expected_fields: List[str], page_type: str
    ) -> Dict[str, Any]:
        """Extract structured data from BuddysVisionCore inspection results."""
        extracted = {
            "page_title": inspection_data.get("page_title", ""),
            "page_url": inspection_data.get("page_url", ""),
            "page_type": page_type,
            "items": [],
            "structure": {
                "forms_count": len(inspection_data.get("forms", [])),
                "buttons_count": len(inspection_data.get("buttons", [])),
                "inputs_count": len(inspection_data.get("inputs", [])),
                "links_count": len(inspection_data.get("links", []))
            }
        }
        
        links = inspection_data.get("links", [])
        
        for link in links[:50]:
            item = {}
            if "name" in expected_fields:
                item["name"] = link.get("text", "").strip()
            if "url" in expected_fields:
                item["url"] = link.get("href", "")
            if "category" in expected_fields:
                item["category"] = link.get("class", "").split()[0] if link.get("class") else ""
            if "location" in expected_fields:
                item["location"] = ""
            
            if item.get("name") or item.get("url"):
                extracted["items"].append(item)
        
        logger.info(f"Extracted {len(extracted['items'])} items from inspection")
        return extracted
    
    def _detect_pagination(self) -> Optional[Tuple[WebElement, str]]:
        """Detect pagination control on current page."""
        try:
            # Phase 1 Step 5: Try ranked selectors first
            ranked_selectors = self._get_ranked_pagination_selectors()
            
            for ranking in ranked_selectors:
                selector = ranking.get("selector", "")
                selector_type = ranking.get("selector_type", "")
                rank = ranking.get("rank", 0)
                
                try:
                    attempt_start = time.time()
                    element = None
                    
                    # Try selector based on type
                    if selector_type == "css":
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    elif selector_type == "xpath":
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        continue
                    
                    duration = int((time.time() - attempt_start) * 1000)
                    
                    # Find first visible and enabled element
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            element = elem
                            break
                    
                    if element:
                        self._emit_selector_signal(selector, selector_type, "success", duration, 0, mission_id=self.current_mission_id)
                        self.ranked_selector_used = True
                        
                        # Emit decision rationale for selector choice
                        if self.current_mission_id:
                            emitter = DecisionRationaleEmitter()
                            success_rate = ranking.get("success_rate")
                            rationale = emitter.explain_selector_choice(
                                selector=selector,
                                selector_type=selector_type,
                                ranked=True,
                                fallback_used=False,
                                success_rate=success_rate,
                                page_number=self.current_page_number
                            )
                            if emitter.should_emit_signal(rationale):
                                rationale_signal = rationale.to_signal(self.current_mission_id)
                                self._persist_learning_signal(rationale_signal)
                        
                        logger.info(f"Pagination detected using ranked selector (rank #{rank}): {selector_type}:{selector}")
                        return (element, f"ranked_{selector_type}")
                    else:
                        self._emit_selector_signal(selector, selector_type, "failure", duration, 0, mission_id=self.current_mission_id)
                
                except (NoSuchElementException, StaleElementReferenceException):
                    self._emit_selector_signal(selector, selector_type, "failure", 50, 0, mission_id=self.current_mission_id)
                except Exception as e:
                    logger.debug(f"Error trying ranked selector {selector}: {e}")
            
            # If ranked selectors failed, mark fallback usage
            if ranked_selectors:
                self.fallback_used = True
                logger.debug("Ranked selectors unsuccessful, falling back to static strategies")
            
            # Strategy 1: rel="next" (existing fallback logic preserved)
            try:
                attempt_start = time.time()
                next_link = self.driver.find_element(By.CSS_SELECTOR, "a[rel='next']")
                duration = int((time.time() - attempt_start) * 1000)
                if next_link.is_displayed() and next_link.is_enabled():
                    self._emit_selector_signal("a[rel='next']", "css", "success", duration, 0, mission_id=self.current_mission_id)
                    
                    # Emit decision rationale for fallback selector
                    if self.current_mission_id:
                        emitter = DecisionRationaleEmitter()
                        rationale = emitter.explain_selector_choice(
                            selector="a[rel='next']",
                            selector_type="css",
                            ranked=False,
                            fallback_used=True,
                            page_number=self.current_page_number
                        )
                        if emitter.should_emit_signal(rationale):
                            rationale_signal = rationale.to_signal(self.current_mission_id)
                            self._persist_learning_signal(rationale_signal)
                    
                    logger.info("Pagination detected: rel='next' link")
                    return (next_link, "rel_next")
                else:
                    self._emit_selector_signal("a[rel='next']", "css", "failure", duration, 0, mission_id=self.current_mission_id)
            except NoSuchElementException:
                self._emit_selector_signal("a[rel='next']", "css", "failure", 50, 0, mission_id=self.current_mission_id)
            
            # Strategy 2: aria-label containing "next"
            try:
                attempt_start = time.time()
                next_elements = self.driver.find_elements(By.XPATH, 
                    "//*[contains(translate(@aria-label, 'NEXT', 'next'), 'next') and (self::a or self::button)]")
                duration = int((time.time() - attempt_start) * 1000)
                for elem in next_elements:
                    if elem.is_displayed() and elem.is_enabled():
                        self._emit_selector_signal("aria-label contains 'next'", "aria", "success", duration, 0, mission_id=self.current_mission_id)
                        logger.info(f"Pagination detected: aria-label='{elem.get_attribute('aria-label')}'")
                        return (elem, "aria_label")
                if next_elements:
                    self._emit_selector_signal("aria-label contains 'next'", "aria", "failure", duration, 0, mission_id=self.current_mission_id)
            except NoSuchElementException:
                self._emit_selector_signal("aria-label contains 'next'", "aria", "failure", 50, 0, mission_id=self.current_mission_id)
            
            # Strategy 3: Text patterns
            next_patterns = ["Next", "next", "NEXT", ">", "→", "More", "more", "Next Page", "next page"]
            for pattern in next_patterns:
                try:
                    attempt_start = time.time()
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    duration = int((time.time() - attempt_start) * 1000)
                    for btn in buttons:
                        if btn.text.strip() == pattern and btn.is_displayed() and btn.is_enabled():
                            self._emit_selector_signal(f"button:'{pattern}'", "text", "success", duration, 0, mission_id=self.current_mission_id)
                            logger.info(f"Pagination detected: button text='{pattern}'")
                            return (btn, "text_match")
                    
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        if link.text.strip() == pattern and link.is_displayed() and link.is_enabled():
                            self._emit_selector_signal(f"a:'{pattern}'", "text", "success", duration, 0, mission_id=self.current_mission_id)
                            logger.info(f"Pagination detected: link text='{pattern}'")
                            return (link, "text_match")
                    
                    self._emit_selector_signal(f"text:'{pattern}'", "text", "failure", duration, 0, mission_id=self.current_mission_id)
                except (NoSuchElementException, StaleElementReferenceException):
                    self._emit_selector_signal(f"text:'{pattern}'", "text", "failure", 50, 0, mission_id=self.current_mission_id)
            
            # Strategy 4: Page numbers
            try:
                attempt_start = time.time()
                page_links = self.driver.find_elements(By.XPATH, "//a[string(number(text())) != 'NaN' and self::a]")
                duration = int((time.time() - attempt_start) * 1000)
                if page_links:
                    current_page = 1
                    for link in page_links:
                        classes = link.get_attribute("class") or ""
                        if "active" in classes.lower() or "current" in classes.lower():
                            try:
                                current_page = int(link.text.strip())
                            except ValueError:
                                pass
                    
                    next_page = current_page + 1
                    for link in page_links:
                        try:
                            page_num = int(link.text.strip())
                            if page_num == next_page and link.is_displayed() and link.is_enabled():
                                self._emit_selector_signal(f"page_number:{next_page}", "page_number", "success", duration, 0, mission_id=self.current_mission_id)
                                logger.info(f"Pagination detected: page number {next_page}")
                                return (link, "page_number")
                        except ValueError:
                            pass
                    self._emit_selector_signal("page_number", "page_number", "failure", duration, 0, mission_id=self.current_mission_id)
            except (NoSuchElementException, StaleElementReferenceException):
                self._emit_selector_signal("page_number", "page_number", "failure", 50, 0, mission_id=self.current_mission_id)
            
            logger.info("No pagination control detected")
            return None
            
        except Exception as e:
            logger.warning(f"Error detecting pagination: {e}")
            return None
    
    def _go_to_next_page(self, element: WebElement) -> bool:
        """Click pagination element and verify navigation occurred."""
        try:
            nav_start = time.time()
            current_url = self.driver.current_url
            current_content_hash = self._get_page_content_hash()
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            clicked = False
            retry_count = 0
            for attempt in range(3):
                try:
                    element.click()
                    clicked = True
                    break
                except Exception:
                    retry_count += 1
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        clicked = True
                        break
                    except Exception:
                        if attempt < 2:
                            time.sleep(0.5)
            
            if not clicked:
                nav_duration = int((time.time() - nav_start) * 1000)
                self._emit_selector_signal("pagination_element.click()", "interaction", "failure", nav_duration, retry_count, mission_id=self.current_mission_id)
                logger.warning("Failed to click pagination element")
                return False
            
            time.sleep(2)
            new_url = self.driver.current_url
            new_content_hash = self._get_page_content_hash()
            nav_duration = int((time.time() - nav_start) * 1000)
            
            if new_url != current_url or new_content_hash != current_content_hash:
                self._emit_selector_signal("pagination_element.click()", "interaction", "success", nav_duration, retry_count, mission_id=self.current_mission_id)
                logger.info("Navigation successful")
                return True
            
            self._emit_selector_signal("pagination_element.click()", "interaction", "failure", nav_duration, retry_count, mission_id=self.current_mission_id)
            logger.warning("Navigation failed: No URL or content change detected")
            return False
            
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            return False
    
    def _get_page_content_hash(self) -> str:
        """Get hash of page content for duplicate detection."""
        try:
            title = self.driver.title or ""
            body = self.driver.find_element(By.TAG_NAME, "body").text[:1000]
            content = f"{title}|{body}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""
    
    def _paginate_and_extract(
        self, expected_fields: List[str], page_type: str, max_pages: int
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Extract data across multiple pages with pagination."""
        all_items = []
        pages_visited = 0
        pagination_detected = False
        pagination_method = None
        stopped_reason = None
        seen_urls = set()
        seen_content_hashes = set()
        
        logger.info(f"Starting pagination: max_pages={max_pages}")
        
        while pages_visited < max_pages:
            pages_visited += 1
            self.current_page_number = pages_visited
            logger.info(f"Extracting from page {pages_visited}/{max_pages}")
            
            current_hash = self._get_page_content_hash()
            if current_hash in seen_content_hashes:
                logger.info("Duplicate page content detected, stopping")
                stopped_reason = "duplicate"
                break
            seen_content_hashes.add(current_hash)
            
            try:
                inspection_data = self.vision_core.inspect_website(
                    url=self.driver.current_url, expand_interactive=True, max_scrolls=4
                )
                page_data = self._extract_data_from_inspection(
                    inspection_data=inspection_data, expected_fields=expected_fields, page_type=page_type
                )
                
                for item in page_data.get("items", []):
                    item_url = item.get("url", "")
                    if item_url and item_url not in seen_urls:
                        all_items.append(item)
                        seen_urls.add(item_url)
                    elif not item_url:
                        all_items.append(item)
                
                logger.info(f"Extracted {len(page_data.get('items', []))} items from page {pages_visited} (total: {len(all_items)})")
                
            except Exception as e:
                logger.error(f"Error extracting from page {pages_visited}: {e}")
                stopped_reason = "extraction_error"
                break
            
            if pages_visited >= max_pages:
                logger.info("Reached max_pages limit")
                stopped_reason = "max_pages"
                break
            
            pagination_result = self._detect_pagination()
            
            if pagination_result is None:
                logger.info("No pagination control found, stopping")
                stopped_reason = "no_next"
                break
            
            element, method = pagination_result
            pagination_detected = True
            pagination_method = method
            
            if not self._go_to_next_page(element):
                logger.info("Failed to navigate to next page, stopping")
                stopped_reason = "navigation_failed"
                break
            
            time.sleep(1)
        
        extracted_data = {
            "page_title": self.driver.title,
            "page_url": self.driver.current_url,
            "page_type": page_type,
            "items": all_items,
            "structure": {
                "total_items": len(all_items),
                "pages_extracted": pages_visited
            }
        }
        
        pagination_metadata = {
            "pages_visited": pages_visited,
            "pagination_detected": pagination_detected,
            "pagination_method": pagination_method,
            "pagination_stopped_reason": stopped_reason or "completed"
        }
        
        logger.info(f"Pagination complete: {pages_visited} pages, {len(all_items)} items, stopped: {stopped_reason}")
        
        return extracted_data, pagination_metadata
    
    def _build_error_response(self, execution_id: str, error: str, start_time: float) -> Dict[str, Any]:
        """Build error response and log to orchestrator."""
        duration_ms = int((time.time() - start_time) * 1000)
        
        self.orchestrator.log_execution(
            task_id=execution_id,
            tool_name="web_navigator_agent",
            action_type="navigate_and_extract",
            status="FAILED",
            data={"error": error},
            duration_ms=duration_ms
        )
        
        return {
            "status": "FAILED",
            "error": error,
            "metadata": {
                "execution_id": execution_id,
                "duration_ms": duration_ms
            }
        }

