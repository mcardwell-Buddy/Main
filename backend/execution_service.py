"""
Execution Service: Safely executes approved missions.

Contract:
- Input: mission_id (string)
- Precondition: Mission exists AND status == "approved"
- Action: Select tools, execute exactly once, write result
- Output: Execution summary (success/failure)
- Side effects: ONE event written to Firebase missions collection

This is synchronous, explicit, and non-retryable by design.
No auto-execution, no background jobs, no re-runs.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4
from backend.tool_registry import tool_registry
from backend.tool_selector import tool_selector
from backend.execution_learning_emitter import get_learning_emitter
from backend.artifact_writer import get_artifact_writer
from backend.mission_evaluator import MissionEvaluator
from backend.mission_store import get_mission_store, Mission
from backend.streaming_events import (
    get_event_emitter,
    MissionStatus,
    IntentDecisionType,
)
from backend.artifact_preview_generator import ArtifactPreviewGenerator
from backend.budget_enforcer import get_budget_enforcer
from backend.budget_tracker import get_budget_tracker
from backend.cost_tracker import get_cost_tracker
from backend.cost_estimator import ServiceTier, ModelType
import re

logger = logging.getLogger(__name__)

# Tool Selection Invariant: Intent → Allowed Tools Mapping
# This enforces that execution ONLY proceeds with valid tools for detected intents
INTENT_TOOL_RULES = {
    'extraction': ['web_extract', 'web_search'],  # Data extraction from web
    'calculation': ['calculate'],                  # Math operations
    'navigation': ['web_navigate'],                # Web navigation
    'search': ['web_search'],                      # General search
    'research': ['web_research'],                  # Multi-engine research
    'time': ['get_time'],                          # Time/date queries
    'file': ['read_file', 'list_directory'],      # File operations
    'introspection': ['learning_query', 'understanding_metrics'],  # Self-knowledge
    'learning': ['store_knowledge'],               # Active learning
    'reflection': ['reflect'],                     # Self-reflection
    'repository': ['repo_index', 'file_summary', 'dependency_map'],  # Repo analysis
    'mployer': ['mployer_login', 'mployer_search_employers']  # Mployer operations
}


class ExecutionService:
    """
    Synchronous execution service for approved missions.
    
    Invariant: A mission executes if and only if its current state is "approved".
    Tool Selection Invariant: Execution ONLY proceeds with allowed tool for detected intent.
    """

    def _classify_intent(self, objective: str) -> str:
        """
        Classify the intent of an objective to determine allowed tools.
        
        Args:
            objective: Mission objective description
            
        Returns:
            Intent category string (extraction, calculation, search, etc.)
        """
        try:
            from backend.llm_client import llm_client
            
            prompt = f"""Classify the intent of this objective into ONE category. Return ONLY the category name.

Categories: extraction, calculation, search, navigation, research, file, introspection, learning, reflection, repository, mployer, time

Objective: {objective}

Category:"""
            
            intent = llm_client.complete(prompt, max_tokens=50, temperature=0.2).strip().lower()
            
            # Validate the intent is in our allowed list
            valid_intents = ['extraction', 'calculation', 'search', 'navigation', 'research', 'file', 
                           'introspection', 'learning', 'reflection', 'repository', 'mployer', 'time']
            
            if intent in valid_intents:
                logger.info(f"[INTENT_CLASSIFY] {objective[:60]}... → {intent}")
                return intent
            else:
                logger.warning(f"[INTENT_CLASSIFY] LLM returned invalid intent '{intent}', defaulting to 'search'")
                return 'search'
        except Exception as e:
            logger.error(f"[INTENT_CLASSIFY_ERROR] Failed to classify intent: {e}")
            # Fallback: assume search if LLM fails
            return 'search'
    
    def _validate_tool_for_intent(self, tool_name: str, intent: str, objective: str) -> Dict[str, Any]:
        """
        Validate that the selected tool is allowed for the classified intent.
        This enforces the Tool Selection Invariant.
        
        Args:
            tool_name: The tool selected by tool_selector
            intent: The classified intent category
            objective: The mission objective (for logging)
            
        Returns:
            {'valid': bool, 'error': str (if invalid)}
        """
        allowed_tools = INTENT_TOOL_RULES.get(intent, [])
        
        if tool_name not in allowed_tools:
            return {
                'valid': False,
                'error': f'Tool selection invariant violated: tool "{tool_name}" not allowed for intent "{intent}". Allowed tools: {allowed_tools}'
            }
        
        logger.info(f"[TOOL VALIDATION] ✓ Tool '{tool_name}' is valid for intent '{intent}'")
        return {'valid': True}

    def _extract_source_url(self, objective: str, raw_chat_message: Optional[str] = None, allowed_domains: Optional[List[str]] = None) -> str:
        """Extract a source URL using LLM from available mission fields."""
        try:
            from backend.llm_client import llm_client
            
            # Combine all text sources
            combined_text = f"{raw_chat_message or ''} {objective}".strip()
            
            prompt = f"""Extract the URL or website from this text. Return ONLY the URL (starting with http:// or https://).

Text: {combined_text}

URL:"""
            
            url = llm_client.complete(prompt, max_tokens=100, temperature=0.2).strip()
            
            # Validate it looks like a URL
            if url.startswith(('http://', 'https://')):
                return url
            
            # Fallback to allowed_domains
            if allowed_domains and allowed_domains[0]:
                return f"https://{allowed_domains[0]}"
            
            return ""
        except Exception as e:
            logger.warning(f"[URL_EXTRACT_ERROR] Failed to extract URL: {e}")
            if allowed_domains and allowed_domains[0]:
                return f"https://{allowed_domains[0]}"
            return ""

    def _build_web_extraction_artifact(
        self,
        mission_id: str,
        execution_result: Dict[str, Any],
        objective_description: str,
        execution_trace_id: str,
        raw_chat_message: Optional[str] = None,
        allowed_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Build a web_extraction_result artifact from execution output."""
        source_url = self._extract_source_url(objective_description, raw_chat_message, allowed_domains)
        
        # Handle new semantic extraction format (sections + content)
        sections = execution_result.get('sections', []) if isinstance(execution_result, dict) else []
        content = execution_result.get('content', '') if isinstance(execution_result, dict) else ''
        
        if sections:
            # New format: extract from sections
            title = sections[0].get('title', '') if sections else ''
            section_texts = [s.get('text', '')[:500] for s in sections[:5]]
            summary = content[:500] if content else '\n'.join(section_texts[:3])
            
            extracted_data = {
                "title": title,
                "sections": [
                    {
                        "title": s.get('title', ''),
                        "text": s.get('text', '')[:1000]
                    }
                    for s in sections
                ],
                "summary": summary,
                "full_content": content
            }
        else:
            # Fallback to old format (elements)
            elements = execution_result.get('elements', []) if isinstance(execution_result, dict) else []
            title = ""
            headings: List[str] = []
            summary = ""
            
            if elements:
                first_text = None
                for element in elements:
                    text = element.get('text') if isinstance(element, dict) else None
                    if text:
                        if first_text is None:
                            first_text = text
                        headings.append(text)
                
                title = first_text or ""
                headings = headings[:5]
                summary = (first_text or "")[:200]
            
            extracted_data = {
                "title": title,
                "headings": headings,
                "summary": summary
            }

        artifact = {
            "artifact_id": f"artifact_{uuid4().hex}",
            "artifact_type": "web_extraction_result",
            "mission_id": mission_id,
            "source_url": source_url,
            "extracted_data": extracted_data,
            "tool_used": "web_extract",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "execution_trace_id": execution_trace_id
        }

        return artifact

    def _build_web_search_artifact(
        self,
        mission_id: str,
        execution_result: Dict[str, Any],
        query: str,
        execution_trace_id: str
    ) -> Dict[str, Any]:
        """Build a web_search_result artifact from execution output."""
        results = []
        if isinstance(execution_result, dict):
            results = execution_result.get('results', [])

        artifact = {
            "artifact_id": f"artifact_{uuid4().hex}",
            "artifact_type": "web_search_result",
            "mission_id": mission_id,
            "query": query,
            "results": results,
            "tool_used": "web_search",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "execution_trace_id": execution_trace_id
        }

        return artifact

    def _build_web_navigation_artifact(
        self,
        mission_id: str,
        execution_result: Dict[str, Any],
        objective_description: str,
        execution_trace_id: str,
        raw_chat_message: Optional[str] = None,
        allowed_domains: Optional[List[str]] = None,
        starting_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build a web_navigation_result artifact from execution output."""
        resolved_start = starting_url or self._extract_source_url(
            objective_description,
            raw_chat_message=raw_chat_message,
            allowed_domains=allowed_domains
        )
        final_url = ""
        page_title = ""
        if isinstance(execution_result, dict):
            final_url = execution_result.get("final_url") or execution_result.get("url") or ""
            page_title = execution_result.get("title") or ""

        artifact = {
            "artifact_id": f"artifact_{uuid4().hex}",
            "artifact_type": "web_navigation_result",
            "mission_id": mission_id,
            "starting_url": resolved_start,
            "final_url": final_url,
            "navigation_reason": objective_description,
            "page_title": page_title,
            "links_found": [],
            "tool_used": "web_navigate",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "execution_trace_id": execution_trace_id
        }

        return artifact

    def _build_calculation_artifact(
        self,
        mission_id: str,
        execution_result: Dict[str, Any],
        tool_input: str,
        execution_trace_id: str
    ) -> Dict[str, Any]:
        """Build a calculation_result artifact from execution output."""
        result = execution_result.get('result')

        artifact = {
            "artifact_id": f"artifact_{uuid4().hex}",
            "artifact_type": "calculation_result",
            "mission_id": mission_id,
            "expression": tool_input,
            "result": result,
            "tool_used": "calculate",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "execution_trace_id": execution_trace_id
        }

        return artifact

    def execute_mission(self, mission_id: str) -> Dict[str, Any]:
        """
        Execute an approved mission.

        Steps:
        1. Load mission from missions.jsonl
        2. Verify status == "approved"
        3. Validate mission data
        4. Select tool using tool_selector
        5. Execute tool once
        6. Write execution result record
        7. Return summary

        Args:
            mission_id: Mission identifier

        Returns:
            {
                'success': bool,
                'mission_id': str,
                'status': 'completed' | 'failed',
                'tool_used': str,
                'tool_confidence': float,
                'execution_result': Dict,
                'error': str (if failed)
            }
        """
        try:
            emitter = get_event_emitter()
            preview_generator = ArtifactPreviewGenerator()
            total_steps = 5

            emitter.emit_mission_start(mission_id, "Mission execution started")
            emitter.emit_execution_step(
                mission_id,
                step_name="verification",
                step_status="started",
                step_index=1,
                total_steps=total_steps,
                progress_percent=5,
                message="Verifying mission eligibility",
            )
            # STEP 1: Load mission
            mission_record = self._find_mission_record(mission_id)
            if not mission_record:
                emitter.emit_execution_step(
                    mission_id,
                    step_name="verification",
                    step_status="failed",
                    step_index=1,
                    total_steps=total_steps,
                    progress_percent=5,
                    message="Mission not found",
                )
                emitter.emit_mission_stop(
                    mission_id,
                    reason="mission_not_found",
                    final_status=MissionStatus.FAILED,
                )
                return {
                    'success': False,
                    'mission_id': mission_id,
                    'error': f'Mission {mission_id} not found'
                }

            # STEP 2: Verify status == "approved"
            current_status = self._get_current_status(mission_id)
            if current_status != "approved":
                emitter.emit_execution_step(
                    mission_id,
                    step_name="verification",
                    step_status="failed",
                    step_index=1,
                    total_steps=total_steps,
                    progress_percent=5,
                    message=f"Mission status is {current_status}",
                )
                emitter.emit_mission_stop(
                    mission_id,
                    reason="mission_not_approved",
                    final_status=MissionStatus.FAILED,
                )
                return {
                    'success': False,
                    'mission_id': mission_id,
                    'current_status': current_status,
                    'error': f'Mission status is "{current_status}", not "approved". Cannot execute.'
                }

            logger.info(f"[EXECUTION] Mission {mission_id} verified as approved. Starting execution...")

            # STEP 2.5: Verify mission hasn't already been executed (idempotency check)
            existing_executions = self._count_execution_records(mission_id)
            if existing_executions > 0:
                emitter.emit_execution_step(
                    mission_id,
                    step_name="verification",
                    step_status="failed",
                    step_index=1,
                    total_steps=total_steps,
                    progress_percent=5,
                    message="Mission already executed",
                )
                emitter.emit_mission_stop(
                    mission_id,
                    reason="mission_already_executed",
                    final_status=MissionStatus.FAILED,
                )
                return {
                    'success': False,
                    'mission_id': mission_id,
                    'error': f'Mission has already been executed ({existing_executions} execution record(s) found). Cannot re-execute.'
                }

            # STEP 3: Extract mission objective
            # Handle both nested mission_data structure and flat objective structure
            mission_data = mission_record.get('mission', mission_record)  # Try nested first, fall back to record itself
            objective = mission_data.get('objective', {})
            
            # objective might be a dict with 'description' key, or a string directly
            if isinstance(objective, dict):
                objective_description = objective.get('description', '')
            else:
                objective_description = str(objective) if objective else ''
            
            # Fallback to objective_description key if it exists
            if not objective_description:
                objective_description = mission_data.get('objective_description', '')

            metadata = mission_data.get('metadata', {}) if isinstance(mission_data, dict) else {}
            raw_chat_message = metadata.get('raw_chat_message') if isinstance(metadata, dict) else None
            scope = mission_data.get('scope', {}) if isinstance(mission_data, dict) else {}
            allowed_domains = scope.get('allowed_domains') if isinstance(scope, dict) else None

            if not objective_description:
                emitter.emit_execution_step(
                    mission_id,
                    step_name="verification",
                    step_status="failed",
                    step_index=1,
                    total_steps=total_steps,
                    progress_percent=5,
                    message="No objective found",
                )
                emitter.emit_mission_stop(
                    mission_id,
                    reason="objective_missing",
                    final_status=MissionStatus.FAILED,
                )
                return {
                    'success': False,
                    'mission_id': mission_id,
                    'error': 'No objective found in mission'
                }

            logger.info(f"[EXECUTION] Mission objective: {objective_description[:100]}")

            # Execution trace ID for artifact linkage
            execution_trace_id = f"trace_{uuid4().hex}"

            # STEP 4: Classify intent for tool validation
            emitter.emit_execution_step(
                mission_id,
                step_name="intent_classification",
                step_status="started",
                step_index=2,
                total_steps=total_steps,
                progress_percent=20,
                message="Classifying intent",
            )
            intent = self._classify_intent(objective_description)
            logger.info(f"[EXECUTION] Classified intent: {intent}")

            intent_map = {
                "navigation": IntentDecisionType.NAVIGATE,
                "extraction": IntentDecisionType.EXTRACT,
                "search": IntentDecisionType.ANALYZE,
                "research": IntentDecisionType.ANALYZE,
                "calculation": IntentDecisionType.SYNTHESIZE,
                "file": IntentDecisionType.OTHER,
                "introspection": IntentDecisionType.OTHER,
                "learning": IntentDecisionType.OTHER,
                "reflection": IntentDecisionType.OTHER,
                "repository": IntentDecisionType.OTHER,
                "mployer": IntentDecisionType.OTHER,
                "time": IntentDecisionType.OTHER,
            }
            emitter.emit_intent_decision(
                mission_id=mission_id,
                intent_type=intent_map.get(intent, IntentDecisionType.OTHER),
                reasoning=f"Classified intent as {intent}",
                confidence=0.7,
            )
            emitter.emit_execution_step(
                mission_id,
                step_name="intent_classification",
                step_status="completed",
                step_index=2,
                total_steps=total_steps,
                progress_percent=30,
                message=f"Intent classified as {intent}",
            )

            # STEP 4.5: BUDGET CHECK (CRITICAL - Check before tool selection)
            logger.info(f"[EXECUTION] Checking budget limits...")
            emitter.emit_execution_step(
                mission_id,
                step_name="budget_check",
                step_status="started",
                step_index=3,
                total_steps=total_steps + 1,  # Added budget check step
                progress_percent=35,
                message="Checking budget limits",
            )
            
            try:
                # Get budget enforcer and estimated cost from mission metadata
                budget_enforcer = get_budget_enforcer()
                
                # For now, use current tier - in production, get from mission metadata
                current_tier = ServiceTier.FREE
                
                # Create a minimal cost estimate for budget checking
                # In full implementation, this would come from the proposal
                from backend.cost_estimator import MissionCost, ServiceCost
                
                # Estimate based on tool types expected
                estimated_searches = 1 if 'search' in intent or 'research' in intent else 0
                estimated_cost = MissionCost(
                    total_usd=0.01,  # Minimal estimate
                    service_costs=[
                        ServiceCost(
                            service='serpapi',
                            operation_count=estimated_searches,
                            unit_cost=0.0,
                            total_cost=0.0,
                            tier=current_tier.value
                        )
                    ]
                )
                
                # Create minimal task breakdown for budget check
                from backend.task_breakdown_and_proposal import TaskBreakdown
                task_breakdown = TaskBreakdown(
                    goal=objective_description,
                    steps=[],
                    total_cost=estimated_cost,
                    total_buddy_time_seconds=10,
                    total_human_time_minutes=0,
                    pure_buddy_steps=1,
                    pure_human_steps=0,
                    hybrid_steps=0,
                    has_blocking_steps=False,
                    requires_human_approval=False
                )
                
                budget_check = budget_enforcer.check_mission_budget(
                    mission_cost=estimated_cost,
                    task_breakdown=task_breakdown,
                    serpapi_tier=current_tier
                )
                
                if not budget_check['can_execute']:
                    logger.error(f"[EXECUTION] Budget check failed: {budget_check['reason']}")
                    emitter.emit_execution_step(
                        mission_id,
                        step_name="budget_check",
                        step_status="failed",
                        step_index=3,
                        total_steps=total_steps + 1,
                        progress_percent=35,
                        message=f"Budget exceeded: {budget_check['reason']}",
                    )
                    emitter.emit_mission_stop(
                        mission_id,
                        reason="budget_exceeded",
                        final_status=MissionStatus.FAILED,
                    )
                    return {
                        'success': False,
                        'mission_id': mission_id,
                        'error': budget_check['reason'],
                        'budget_status': budget_check,
                        'recommended_action': budget_check.get('recommended_action'),
                        'action_detail': budget_check.get('action_detail')
                    }
                
                logger.info(f"[EXECUTION] Budget check passed ✓")
                emitter.emit_execution_step(
                    mission_id,
                    step_name="budget_check",
                    step_status="completed",
                    step_index=3,
                    total_steps=total_steps + 1,
                    progress_percent=38,
                    message="Budget check passed",
                )
            except Exception as budget_error:
                logger.error(f"[EXECUTION] Budget check error: {budget_error}")
                # Continue execution if budget check fails (failsafe)

            # STEP 5: Select tool
            emitter.emit_execution_step(
                mission_id,
                step_name="tool_selection",
                step_status="started",
                step_index=4,
                total_steps=total_steps + 1,
                progress_percent=40,
                message="Selecting best tool",
            )
            tool_name, tool_input, confidence = tool_selector.select_tool(objective_description)

            if not tool_name or confidence < 0.15:
                emitter.emit_execution_step(
                    mission_id,
                    step_name="tool_selection",
                    step_status="failed",
                    step_index=3,
                    total_steps=total_steps,
                    progress_percent=40,
                    message="Tool selection failed",
                )
                emitter.emit_mission_stop(
                    mission_id,
                    reason="tool_selection_failed",
                    final_status=MissionStatus.FAILED,
                )
                return {
                    'success': False,
                    'mission_id': mission_id,
                    'error': f'Tool selection failed (confidence: {confidence:.2f})',
                    'tool_confidence': confidence
                }

            logger.info(f"[EXECUTION] Selected tool: {tool_name} (confidence: {confidence:.2f})")
            logger.info(f"[EXECUTION] Tool input: {tool_input[:100]}")

            emitter.emit_tool_invoked(
                mission_id=mission_id,
                tool_name=tool_name,
                tool_input=tool_input,
                message="Tool selected for execution",
            )
            emitter.emit_execution_step(
                mission_id,
                step_name="tool_selection",
                step_status="completed",
                step_index=3,
                total_steps=total_steps,
                progress_percent=55,
                message=f"Selected {tool_name}",
            )

            # STEP 5.5: Validate tool selection against intent (TOOL SELECTION INVARIANT)
            validation = self._validate_tool_for_intent(tool_name, intent, objective_description)
            if not validation['valid']:
                # Write failed execution record with invariant violation
                failed_record = {
                    'event_type': 'mission_executed',
                    'mission_id': mission_id,
                    'status': 'failed',
                    'tool_used': tool_name,
                    'tool_confidence': confidence,
                    'intent': intent,
                    'error': validation['error'],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                self._write_execution_record(failed_record)
                logger.error(f"[EXECUTION] {validation['error']}")
                
                # Emit learning signal for tool validation failure (OBSERVE-ONLY)
                try:
                    learning_emitter = get_learning_emitter()
                    learning_emitter.emit_execution_outcome(
                        mission_id=mission_id,
                        intent=intent,
                        tool_used=tool_name,
                        tool_confidence=confidence,
                        success=False,
                        execution_result={'error': validation['error']},
                        objective=objective_description,
                        error=validation['error']
                    )
                except Exception as learning_error:
                    logger.warning(f"[LEARNING] Failed to emit learning signal: {learning_error}")
                
                return {
                    'success': False,
                    'mission_id': mission_id,
                    'error': validation['error'],
                    'tool_used': tool_name,
                    'intent': intent,
                    'allowed_tools': INTENT_TOOL_RULES.get(intent, [])
                }

            # STEP 5.6: Normalize web_navigate input to a URL
            if tool_name == 'web_navigate':
                if not re.search(r'^https?://', str(tool_input)):
                    source_url = self._extract_source_url(
                        objective_description,
                        raw_chat_message=raw_chat_message,
                        allowed_domains=allowed_domains
                    )
                    if source_url:
                        tool_input = source_url
                        logger.info(f"[EXECUTION] Normalized web_navigate input to URL: {tool_input}")
                    else:
                        return {
                            'success': False,
                            'mission_id': mission_id,
                            'error': 'No valid URL found for web_navigate input',
                            'tool_used': tool_name,
                            'intent': intent
                        }

            # STEP 5.7: For web_extract, navigate to the URL first
            if tool_name == 'web_extract':
                # Extract URL from objective
                source_url = self._extract_source_url(
                    objective_description,
                    raw_chat_message=raw_chat_message,
                    allowed_domains=allowed_domains
                )
                if source_url:
                    logger.info(f"[EXECUTION] web_extract: Navigating to {source_url} before extraction")
                    try:
                        nav_result = tool_registry.call('web_navigate', source_url)
                        if nav_result.get('error'):
                            logger.warning(f"[EXECUTION] Failed to navigate to {source_url}: {nav_result.get('error')}")
                        else:
                            logger.info(f"[EXECUTION] Successfully navigated to {source_url}")
                    except Exception as nav_error:
                        logger.warning(f"[EXECUTION] Navigation error: {nav_error}")
                else:
                    logger.warning(f"[EXECUTION] web_extract: No URL found in objective for pre-navigation")

            # STEP 6: Execute tool (synchronous, no retry)
            emitter.emit_execution_step(
                mission_id,
                step_name="tool_execution",
                step_status="started",
                step_index=4,
                total_steps=total_steps,
                progress_percent=65,
                message=f"Executing {tool_name}",
            )
            try:
                execution_result = tool_registry.call(tool_name, tool_input)
                logger.info(f"[EXECUTION] Tool execution succeeded")
            except Exception as e:
                logger.error(f"[EXECUTION] Tool execution failed: {e}")
                execution_result = {
                    'error': str(e),
                    'success': False
                }

            # Determine if execution succeeded
            execution_success = execution_result.get('success', True) and 'error' not in execution_result

            preview_details = None
            if execution_success:
                if tool_name == 'web_extract':
                    preview_details = {
                        "type": "web_extraction",
                        "sections": execution_result.get("sections", []),
                        "count": execution_result.get("count"),
                    }
                elif tool_name == 'web_search':
                    preview_details = {
                        "type": "web_search",
                        "results": execution_result.get("results", [])[:5],
                    }
                elif tool_name == 'calculate':
                    preview_details = {
                        "type": "calculation",
                        "expression": execution_result.get("expression"),
                        "result": execution_result.get("result"),
                    }
                elif tool_name == 'web_navigate':
                    preview_details = {
                        "type": "web_navigation",
                        "url": execution_result.get("final_url") or execution_result.get("url"),
                        "title": execution_result.get("title"),
                    }

            emitter.emit_tool_result(
                mission_id=mission_id,
                tool_name=tool_name,
                success=execution_success,
                summary="Execution completed" if execution_success else "Execution failed",
                details={"error": execution_result.get("error")} if not execution_success else preview_details,
            )
            emitter.emit_execution_step(
                mission_id,
                step_name="tool_execution",
                step_status="completed" if execution_success else "failed",
                step_index=4,
                total_steps=total_steps,
                progress_percent=80,
                message="Tool execution complete" if execution_success else "Tool execution failed",
            )

            # STEP 7: Write ONE execution result record
            result_record = {
                'event_type': 'mission_executed',
                'mission_id': mission_id,
                'status': 'completed' if execution_success else 'failed',
                'tool_used': tool_name,
                'tool_confidence': confidence,
                'intent': intent,  # Include intent for auditability
                'tool_input': tool_input,
                'execution_result': execution_result,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            self._write_execution_record(result_record)
            logger.info(f"[EXECUTION] Execution record written to Firebase")

            # STEP 8: Generate human-readable summary
            result_summary = self._generate_result_summary(tool_name, execution_result)
            
            # STEP 9: Log execution complete in human-readable format
            self._log_execution_complete(mission_id, tool_name, execution_success, result_summary)

            # STEP 9.2: Persist artifact for successful web extract/search (append-only)
            artifact_reference = None
            artifact_message = None
            if execution_success and tool_name == 'web_extract':
                artifact = self._build_web_extraction_artifact(
                    mission_id=mission_id,
                    execution_result=execution_result,
                    objective_description=objective_description,
                    execution_trace_id=execution_trace_id,
                    raw_chat_message=raw_chat_message,
                    allowed_domains=allowed_domains
                )
                get_artifact_writer().write_artifact(artifact)
                artifact_reference = {
                    "artifact_id": artifact.get("artifact_id"),
                    "artifact_type": artifact.get("artifact_type")
                }
                preview = preview_generator.generate_preview(artifact)
                emitter.emit_artifact_preview(
                    mission_id=mission_id,
                    artifact_type=artifact.get("artifact_type", "unknown"),
                    preview=preview,
                    message="Artifact preview ready",
                )
                source_url = artifact.get("source_url")
                if source_url:
                    artifact_message = f"I extracted data from {source_url} and saved the result."
                else:
                    artifact_message = "I extracted data and saved the result."

            if execution_success and tool_name == 'web_search':
                artifact = self._build_web_search_artifact(
                    mission_id=mission_id,
                    execution_result=execution_result,
                    query=tool_input,
                    execution_trace_id=execution_trace_id
                )
                get_artifact_writer().write_artifact(artifact)
                artifact_reference = {
                    "artifact_id": artifact.get("artifact_id"),
                    "artifact_type": artifact.get("artifact_type")
                }
                preview = preview_generator.generate_preview(artifact)
                emitter.emit_artifact_preview(
                    mission_id=mission_id,
                    artifact_type=artifact.get("artifact_type", "unknown"),
                    preview=preview,
                    message="Artifact preview ready",
                )
                artifact_message = f"I searched for '{tool_input}' and saved the results."

            if execution_success and tool_name == 'web_navigate':
                artifact = self._build_web_navigation_artifact(
                    mission_id=mission_id,
                    execution_result=execution_result,
                    objective_description=objective_description,
                    execution_trace_id=execution_trace_id,
                    raw_chat_message=raw_chat_message,
                    allowed_domains=allowed_domains,
                    starting_url=tool_input
                )
                get_artifact_writer().write_artifact(artifact)
                artifact_reference = {
                    "artifact_id": artifact.get("artifact_id"),
                    "artifact_type": artifact.get("artifact_type")
                }
                preview = preview_generator.generate_preview(artifact)
                emitter.emit_artifact_preview(
                    mission_id=mission_id,
                    artifact_type=artifact.get("artifact_type", "unknown"),
                    preview=preview,
                    message="Artifact preview ready",
                )
                final_url = artifact.get("final_url") or artifact.get("starting_url")
                if final_url:
                    artifact_message = f"I navigated to {final_url} and saved the navigation result."
                else:
                    artifact_message = "I completed the navigation and saved the result."

            if execution_success and tool_name == 'calculate':
                artifact = self._build_calculation_artifact(
                    mission_id=mission_id,
                    execution_result=execution_result,
                    tool_input=tool_input,
                    execution_trace_id=execution_trace_id
                )
                get_artifact_writer().write_artifact(artifact)
                artifact_reference = {
                    "artifact_id": artifact.get("artifact_id"),
                    "artifact_type": artifact.get("artifact_type")
                }
                preview = preview_generator.generate_preview(artifact)
                emitter.emit_artifact_preview(
                    mission_id=mission_id,
                    artifact_type=artifact.get("artifact_type", "unknown"),
                    preview=preview,
                    message="Artifact preview ready",
                )
                result_value = execution_result.get('result', 'N/A')
                artifact_message = f"Calculated {tool_input} = {result_value}"

            # STEP 9.5: Emit learning signal (OBSERVE-ONLY, non-blocking)
            # This happens AFTER execution completes and does NOT affect behavior
            try:
                learning_emitter = get_learning_emitter()
                learning_emitter.emit_execution_outcome(
                    mission_id=mission_id,
                    intent=intent,
                    tool_used=tool_name,
                    tool_confidence=confidence,
                    success=execution_success,
                    execution_result=execution_result,
                    objective=objective_description,
                    error=None
                )
                logger.info(f"[LEARNING] Learning signal emitted for mission {mission_id}")
            except Exception as learning_error:
                # Learning failures are non-critical - log but continue
                logger.warning(f"[LEARNING] Failed to emit learning signal: {learning_error}")

            # STEP 9.6: Mission-level evaluation (observe-only, feature-flagged)
            try:
                evaluator = MissionEvaluator()

                # Build items_collected and context from execution result
                items_collected: List[Dict[str, Any]] = []
                context: Dict[str, Any] = {
                    "page_title": execution_result.get("title") if isinstance(execution_result, dict) else None,
                    "page_url": execution_result.get("final_url") if isinstance(execution_result, dict) else None,
                    "page_type": "unknown",
                    "items_count": 0,
                }

                if tool_name == "web_extract":
                    items_collected = execution_result.get("elements", []) if isinstance(execution_result, dict) else []
                    context["items_count"] = len(items_collected)
                    context["page_url"] = context.get("page_url") or self._extract_source_url(
                        objective_description,
                        raw_chat_message=raw_chat_message,
                        allowed_domains=allowed_domains
                    )

                if tool_name == "web_search":
                    items_collected = execution_result.get("results", []) if isinstance(execution_result, dict) else []
                    context["items_count"] = len(items_collected)

                if tool_name == "web_navigate":
                    context["page_url"] = execution_result.get("final_url") if isinstance(execution_result, dict) else None
                    context["page_title"] = execution_result.get("title") if isinstance(execution_result, dict) else None

                # Build mission objective object if available
                objective_obj = None
                if isinstance(objective, dict):
                    try:
                        from types import SimpleNamespace
                        objective_obj = SimpleNamespace(**objective)
                    except Exception:
                        objective_obj = None

                evaluator.evaluate_after_execution(
                    mission_id=mission_id,
                    objective_description=objective_description,
                    items_collected=items_collected,
                    context=context,
                    outcome_summary={
                        "status": "completed" if execution_success else "failed",
                        "items_collected": len(items_collected),
                        "reason": "execution_completed" if execution_success else "execution_failed",
                    },
                    objective=objective_obj,
                    mission_thread_id=mission_data.get("mission_thread_id") if isinstance(mission_data, dict) else None,
                    mission_created_at=mission_data.get("created_at") if isinstance(mission_data, dict) else None,
                )

                evaluator.emit_mission_outcome(
                    mission_id=mission_id,
                    status="completed" if execution_success else "failed",
                    reason="execution_completed" if execution_success else "execution_failed",
                    mission_thread_id=mission_data.get("mission_thread_id") if isinstance(mission_data, dict) else None,
                    mission_created_at=mission_data.get("created_at") if isinstance(mission_data, dict) else None,
                )
            except Exception as eval_error:
                logger.warning(f"[MISSION_EVAL] Failed to run mission evaluation: {eval_error}")

            # STEP 9.7: TRACK ACTUAL COSTS (after successful execution)
            if execution_success:
                try:
                    cost_tracker = get_cost_tracker()
                    budget_tracker = get_budget_tracker()
                    
                    # Extract actual usage from API response
                    actual_usage = cost_tracker.extract_api_usage(tool_name, execution_result)
                    logger.info(f"[COST_TRACKER] Extracted usage: {actual_usage}")
                    
                    # Record usage in budgets
                    if actual_usage.get('serpapi_searches'):
                        budget_tracker.record_serpapi_usage(
                            actual_usage['serpapi_searches'],
                            mission_id=mission_id
                        )
                    
                    if actual_usage.get('openai_input_tokens') or actual_usage.get('openai_output_tokens'):
                        actual_cost = cost_tracker.calculate_actual_cost(
                            actual_usage,
                            tier=ServiceTier.FREE,  # Would get from mission metadata in production
                            model=ModelType.GPT_4O_MINI
                        )
                        budget_tracker.record_openai_usage(
                            actual_cost['openai_cost_usd'],
                            mission_id=mission_id,
                            tokens={
                                'input': actual_usage.get('openai_input_tokens', 0),
                                'output': actual_usage.get('openai_output_tokens', 0)
                            }
                        )
                    
                    # Create reconciliation record (if we had estimated cost)
                    # For now, just log that we tracked actual usage
                    logger.info(
                        f"[COST_TRACKER] Tracked actual costs for mission {mission_id}: "
                        f"{actual_usage.get('serpapi_searches', 0)} searches, "
                        f"${actual_cost.get('total_dollar_cost', 0):.4f} spent"
                    )
                    
                except Exception as cost_error:
                    # Cost tracking failures are non-critical
                    logger.warning(f"[COST_TRACKER] Failed to track costs: {cost_error}")

            # STEP 10: Return summary with human-readable result
            emitter.emit_execution_step(
                mission_id,
                step_name="finalize",
                step_status="completed" if execution_success else "failed",
                step_index=5,
                total_steps=total_steps,
                progress_percent=100,
                message="Execution complete" if execution_success else "Execution failed",
            )
            emitter.emit_mission_stop(
                mission_id,
                reason="execution_completed" if execution_success else "execution_failed",
                final_status=MissionStatus.COMPLETED if execution_success else MissionStatus.FAILED,
            )
            return {
                'success': execution_success,
                'mission_id': mission_id,
                'status': 'completed' if execution_success else 'failed',
                'tool_used': tool_name,
                'tool_confidence': confidence,
                'intent': intent,  # Include for visibility
                'result_summary': result_summary,
                'execution_result': execution_result,
                'artifact_reference': artifact_reference,
                'artifact_message': artifact_message,
                'artifact_preview': preview if execution_success and artifact_reference else None
            }

        except Exception as e:
            logger.error(f"[EXECUTION] Unexpected error during execution: {e}", exc_info=True)
            try:
                emitter = get_event_emitter()
                emitter.emit_execution_step(
                    mission_id,
                    step_name="finalize",
                    step_status="failed",
                    step_index=5,
                    total_steps=total_steps,
                    progress_percent=100,
                    message="Unexpected error",
                )
                emitter.emit_mission_stop(
                    mission_id,
                    reason="unexpected_error",
                    final_status=MissionStatus.FAILED,
                )
            except Exception:
                pass
            return {
                'success': False,
                'mission_id': mission_id,
                'error': f'Unexpected error: {str(e)}'
            }

    def _find_mission_record(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Find the original mission creation record."""
        store = get_mission_store()
        mission = store.find_mission(mission_id)
        if mission:
            return mission.to_dict()
        return None

    def _get_current_status(self, mission_id: str) -> Optional[str]:
        """Get the current status of a mission by reading the latest status update."""
        store = get_mission_store()
        return store.get_current_status(mission_id)

    def _count_execution_records(self, mission_id: str) -> int:
        """Count how many execution records exist for a mission (idempotency check)."""
        store = get_mission_store()
        return store.count_execution_records(mission_id)

    def _write_execution_record(self, record: Dict[str, Any]) -> None:
        """Write ONE execution result event to Firebase missions collection."""
        store = get_mission_store()
        
        # Convert record dict to Mission object
        mission = Mission(
            mission_id=record['mission_id'],
            event_type=record['event_type'],
            status=record['status'],
            objective={},  # Execution records don't need full objective
            metadata={},
            scope={},
            timestamp=record.get('timestamp', datetime.now(timezone.utc).isoformat()),
            tool_used=record.get('tool_used'),
            tool_confidence=record.get('tool_confidence'),
            intent=record.get('intent'),
            execution_result=record.get('execution_result'),
            error=record.get('error')
        )
        
        store.write_mission_event(mission)
        logger.info(f"Execution record written to Firebase: {record.get('mission_id')} → {record.get('status')}")

    def _generate_result_summary(self, tool_name: str, execution_result: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the execution result."""
        if not execution_result:
            return "No result available"
        
        if execution_result.get('error'):
            return f"Error: {execution_result.get('error')}"
        
        # Tool-specific summaries
        if tool_name == 'web_extract':
            # New semantic extraction returns sections and content
            sections = execution_result.get('sections', [])
            content = execution_result.get('content', '')
            
            if sections:
                # Show section titles and preview
                section_titles = [s.get('title', 'Section') for s in sections[:3]]
                preview_text = sections[0].get('text', '')[:150] if sections else ''
                return f"Found {len(sections)} sections: {', '.join(section_titles)}. Preview: {preview_text}..."
            elif content:
                # Show content preview
                preview = content[:200] if len(content) > 200 else content
                return f"Extracted content: {preview}..."
            
            # Fallback for old format (elements)
            elements = execution_result.get('elements', []) if isinstance(execution_result, dict) else []
            texts = []
            for element in elements:
                if isinstance(element, dict) and element.get('text'):
                    texts.append(element.get('text'))
            title = texts[0] if texts else ""
            heading_text = ", ".join(texts[:3]) if texts else ""
            if title or heading_text:
                return f"Title: {title if title else '(not available)'} | Headings: {heading_text if heading_text else '(none found)'}"
            return execution_result.get('message', 'Extraction complete')
        
        elif tool_name == 'web_search':
            results = execution_result.get('results', [])
            if results:
                if isinstance(results, list):
                    # Show first 2 results
                    result_summaries = [str(r)[:100] for r in results[:2]]
                    return " | ".join(result_summaries)
                else:
                    return str(results)[:150]
            return "No search results"
        
        elif tool_name == 'calculate':
            result = execution_result.get('result', 'N/A')
            expr = execution_result.get('expression', '')
            return f"Calculated: {expr} = {result}"
        
        elif tool_name == 'math_eval':
            result = execution_result.get('result', 'N/A')
            return f"Result: {result}"
        
        # Generic fallback
        if isinstance(execution_result, dict):
            # Try to extract a meaningful field
            if 'result' in execution_result:
                result = execution_result['result']
                if isinstance(result, str) and len(result) > 100:
                    return result[:100] + "..."
                return str(result)
            elif 'data' in execution_result:
                data = execution_result['data']
                if isinstance(data, str) and len(data) > 100:
                    return data[:100] + "..."
                return str(data)
            elif 'results' in execution_result:
                # Generic results field
                results = execution_result['results']
                if isinstance(results, list) and results:
                    return str(results[0])[:150]
        
        return str(execution_result)[:150]

    def _log_execution_complete(self, mission_id: str, tool_name: str, success: bool, result_summary: str) -> None:
        """Log execution completion in human-readable format."""
        status_badge = "✅" if success else "❌"
        
        log_block = f"""
╔════════════════════════════════════════════════════════════╗
║                  BUDDY EXECUTION COMPLETE                  ║
╠════════════════════════════════════════════════════════════╣
║ Mission: {mission_id:<48} ║
║ Tool Used: {tool_name:<44} ║
║ Status: {status_badge} {"SUCCESS" if success else "FAILED":<44} ║
╠════════════════════════════════════════════════════════════╣
║ Result:                                                    ║
║ {result_summary:<56} ║
╚════════════════════════════════════════════════════════════╝
"""
        logger.info(log_block)



# Singleton instance
_execution_service = ExecutionService()


def execute_mission(mission_id: str) -> Dict[str, Any]:
    """
    Convenience function to execute an approved mission.
    
    This is the primary entry point for execution.
    """
    return _execution_service.execute_mission(mission_id)
