"""
Mission Planner

Orchestrates mission planning by integrating:
- Tool selection (with ranking)
- Cost estimation
- Duration estimation
- Feasibility assessment
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional

from Back_End.mission_plan import MissionPlan, ToolOption
from Back_End.action_readiness_engine import ReadinessResult, ReadinessDecision
from Back_End.tool_selector import tool_selector
from Back_End.tool_performance import tracker
from Back_End.memory_manager import memory

logger = logging.getLogger(__name__)


class MissionPlanner:
    """
    Converts a Readiness Result into a complete Mission Plan.
    
    Integrates:
    - Tool selection (with ranking)
    - Cost estimation
    - Duration estimation
    - Feasibility assessment
    """
    
    def __init__(self):
        self.tool_selector = tool_selector
        self.memory = memory
    
    def plan_mission(
        self,
        readiness_result: ReadinessResult,
        raw_chat_message: str
    ) -> MissionPlan:
        """
        Create a complete mission plan from readiness result.
        
        Args:
            readiness_result: Output from ActionReadinessEngine
            raw_chat_message: Original user message
            
        Returns:
            MissionPlan with tool selection + cost/duration estimates
            
        Raises:
            ValueError: If readiness_result is not READY
        """
        if readiness_result.decision != ReadinessDecision.READY:
            raise ValueError(
                f"Cannot plan non-READY mission: {readiness_result.decision}. "
                f"Clarification needed: {readiness_result.clarification_question}"
            )
        
        # Extract readiness data
        mission_id = f"mission_{uuid.uuid4().hex[:12]}"
        objective_desc = readiness_result.action_object or ""
        objective_type = self._determine_objective_type(readiness_result)
        
        logger.info(
            f"[PLANNING] Starting mission plan for: {objective_desc[:60]}... "
            f"(intent: {objective_type})"
        )
        
        # Build constraints dict
        constraints = {
            'target_count': (
                readiness_result.constraints.get('count', 50) 
                if readiness_result.constraints else 50
            ),
            'max_pages': 5,
            'max_duration_seconds': 300,
            'allowed_domains': (
                readiness_result.constraints.get('domains', []) 
                if readiness_result.constraints else []
            )
        }
        
        # TOOL SELECTION WITH COST/DURATION
        logger.info("[PLANNING] Running tool selection...")
        tool_plan = self.tool_selector.plan_tool_selection(
            objective_description=objective_desc,
            objective_type=objective_type,
            constraints=constraints,
            domain="_global"  # Could be domain-specific later
        )
        
        if not tool_plan['primary_tool']:
            logger.error("[PLANNING] No tools available for selection")
            raise ValueError("No tools available for selection")
        
        primary_tool_dict = tool_plan['primary_tool']
        logger.info(
            f"[PLANNING] Selected tool: {primary_tool_dict['tool_name']} "
            f"(confidence: {primary_tool_dict['combined_score']:.1%})"
        )
        
        # FEASIBILITY CHECK
        is_feasible, issues = self._assess_feasibility(
            primary_tool_dict,
            constraints
        )
        
        if not is_feasible:
            logger.warning(f"[PLANNING] Feasibility issues: {issues}")
        
        # Determine risk level
        risk_level = self._assess_risk(primary_tool_dict, is_feasible)
        logger.info(f"[PLANNING] Risk level: {risk_level}")
        
        # BUILD PLAN
        plan = MissionPlan(
            mission_id=mission_id,
            source='chat',
            status='planned',
            objective_description=objective_desc,
            objective_type=objective_type,
            target_count=constraints['target_count'],
            allowed_domains=constraints['allowed_domains'],
            max_pages=constraints['max_pages'],
            max_duration_seconds=constraints['max_duration_seconds'],
            primary_tool=primary_tool_dict,
            alternative_tools=tool_plan['alternatives'],
            total_estimated_cost=primary_tool_dict['estimated_cost_usd'],
            total_cost_rationale=primary_tool_dict['cost_rationale'],
            total_estimated_duration=primary_tool_dict['estimated_duration_seconds'],
            total_duration_rationale=primary_tool_dict['duration_rationale'],
            is_feasible=is_feasible,
            feasibility_issues=issues,
            risk_level=risk_level,
            created_at=datetime.now(timezone.utc).isoformat(),
            raw_chat_message=raw_chat_message,
            intent_keywords=[
                readiness_result.intent_candidates[0].intent 
                if readiness_result.intent_candidates else "unknown"
            ]
        )
        
        # STORE PLAN
        logger.info(f"[PLANNING] Storing plan to memory: {mission_id}")
        self.memory.safe_call('set', f"mission_plan:{mission_id}", plan.to_dict())
        
        logger.info(
            f"[PLANNING] Mission plan complete: {mission_id} | "
            f"Tool: {primary_tool_dict['tool_name']} | "
            f"Cost: ${plan.total_estimated_cost:.4f} | "
            f"Duration: {plan.total_estimated_duration:.0f}s"
        )
        
        return plan
    
    def _determine_objective_type(self, readiness_result: ReadinessResult) -> str:
        """Infer objective type from readiness result"""
        if not readiness_result.intent_candidates:
            return 'search'
        
        intent = readiness_result.intent_candidates[0].intent.lower()
        
        if 'extract' in intent or 'extraction' in intent:
            return 'extract'
        elif 'navigate' in intent or 'navigation' in intent:
            return 'navigate'
        else:
            return 'search'
    
    def _assess_feasibility(
        self,
        primary_tool: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Check if mission is feasible"""
        issues = []
        
        # Check duration
        estimated_duration = primary_tool.get('estimated_duration_seconds', 0)
        max_duration = constraints.get('max_duration_seconds', 300)
        
        if estimated_duration > max_duration:
            issues.append(
                f"Estimated {estimated_duration:.0f}s exceeds "
                f"limit of {max_duration}s"
            )
        
        # Check success rate
        success_rate = primary_tool.get('success_rate', 0.5)
        if success_rate < 0.5:
            issues.append(
                f"Tool {primary_tool.get('tool_name')} has low success rate: "
                f"{success_rate:.1%}"
            )
        
        # Check failure modes
        failure_modes = primary_tool.get('failure_modes', [])
        if 'timeout' in failure_modes:
            issues.append("Tool has timeout failures - may exceed duration limit")
        
        is_feasible = len(issues) == 0
        return is_feasible, issues
    
    def _assess_risk(
        self,
        primary_tool: Dict[str, Any],
        is_feasible: bool
    ) -> str:
        """Assess mission risk level"""
        if not is_feasible:
            return "HIGH"
        
        success_rate = primary_tool.get('success_rate', 0.5)
        if success_rate < 0.7:
            return "HIGH"
        
        estimated_duration = primary_tool.get('estimated_duration_seconds', 0)
        if estimated_duration > 200:
            return "MEDIUM"
        
        estimated_cost = primary_tool.get('estimated_cost_usd', 0.0)
        if estimated_cost > 0.10:
            return "MEDIUM"
        
        return "LOW"


def plan_mission(
    readiness_result: ReadinessResult,
    raw_chat_message: str
) -> MissionPlan:
    """Convenience function to plan a mission"""
    planner = MissionPlanner()
    return planner.plan_mission(readiness_result, raw_chat_message)
