"""
Multi-Step Mission Planner

Orchestrates multi-step mission planning by integrating:
- TaskBreakdownEngine (goal decomposition)
- ToolSelector (per-step tool selection with cost/duration)
- ProposalPresenter (unified proposal generation)

Philosophy:
- Multi-step is DEFAULT (not exception)
- Single cohesive proposal message
- Per-step scheduling support
- Clear cost/duration per step + total
- User sees EXACTLY what Buddy will do

Author: Buddy Multi-Step Architecture Team
Date: February 11, 2026
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional

from Back_End.action_readiness_engine import ReadinessResult, ReadinessDecision
from Back_End.task_breakdown_and_proposal import (
    TaskBreakdownEngine, TaskBreakdown, TaskStep, StepType
)
from Back_End.proposal_presenter import ProposalPresenter, UnifiedProposal
from Back_End.tool_selector import tool_selector
from Back_End.memory_manager import memory

logger = logging.getLogger(__name__)


class MultiStepMissionPlanner:
    """
    Multi-step mission planner with per-step tool selection and cost estimation.
    
    Workflow:
    1. ReadinessResult → Goal description
    2. TaskBreakdownEngine → TaskBreakdown (steps)
    3. Per-step tool selection → Cost + duration estimates
    4. ProposalPresenter → UnifiedProposal (single cohesive message)
    5. Store → Memory
    6. Return UnifiedProposal
    """
    
    def __init__(self):
        self.breakdown_engine = TaskBreakdownEngine()
        self.proposal_presenter = ProposalPresenter()
        self.tool_selector = tool_selector
        self.memory = memory
        
        logger.info("MultiStepMissionPlanner initialized")
    
    def plan_mission(
        self,
        readiness_result: ReadinessResult,
        raw_chat_message: str,
        user_id: str = "default_user"
    ) -> UnifiedProposal:
        """
        Create multi-step mission plan from readiness result.
        
        Args:
            readiness_result: Output from ActionReadinessEngine
            raw_chat_message: Original user message
            user_id: User identifier
            
        Returns:
            UnifiedProposal with complete multi-step breakdown
            
        Raises:
            ValueError: If readiness_result is not READY
        """
        if readiness_result.decision != ReadinessDecision.READY:
            raise ValueError(
                f"Cannot plan non-READY mission: {readiness_result.decision}. "
                f"Clarification needed: {readiness_result.clarification_question}"
            )
        
        # Generate mission ID
        mission_id = f"mission_{uuid.uuid4().hex[:12]}"
        
        # Extract goal description
        objective_desc = readiness_result.action_object or raw_chat_message
        
        logger.info(
            f"[MULTI-STEP PLANNING] Starting for mission {mission_id}: "
            f"{objective_desc[:80]}..."
        )
        
        # STEP 1: Create task breakdown (goal → steps)
        logger.info("[MULTI-STEP PLANNING] Creating task breakdown...")
        task_breakdown = self.breakdown_engine.analyze_task(
            goal=objective_desc,
            context={
                'mission_id': mission_id,
                'user_id': user_id,
                'raw_message': raw_chat_message
            }
        )
        
        logger.info(
            f"[MULTI-STEP PLANNING] Breakdown complete: {len(task_breakdown.steps)} steps"
        )
        
        # STEP 2: Per-step tool selection with cost/duration
        logger.info("[MULTI-STEP PLANNING] Running per-step tool selection...")
        self._enhance_steps_with_tool_selection(task_breakdown)
        
        # STEP 3: Add scheduling to steps
        logger.info("[MULTI-STEP PLANNING] Creating step schedules...")
        self._add_step_scheduling(task_breakdown)
        
        # STEP 4: Detect parallelization opportunities
        logger.info("[MULTI-STEP PLANNING] Analyzing parallelization opportunities...")
        parallelization_opportunities = self._detect_parallelization(task_breakdown)
        
        # STEP 5: Generate unified proposal
        logger.info("[MULTI-STEP PLANNING] Generating unified proposal...")
        unified_proposal = self.proposal_presenter.create_proposal(
            mission_id=mission_id,
            objective=objective_desc,
            task_breakdown=task_breakdown,
            mission_title=self._generate_mission_title(objective_desc)
        )
        
        # STEP 6: Enhance proposal with scheduling and parallelization
        unified_proposal.step_schedules = [
            step.schedule.to_dict() if step.schedule else None
            for step in task_breakdown.steps
        ]
        unified_proposal.parallelization_opportunities = [
            opp.to_dict() for opp in parallelization_opportunities
        ]
        
        # STEP 7: Store in memory
        logger.info(f"[MULTI-STEP PLANNING] Storing mission to memory: {mission_id}")
        self.memory.safe_call(
            'set',
            f"unified_proposal:{mission_id}",
            unified_proposal.to_dict()
        )
        self.memory.safe_call(
            'set',
            f"task_breakdown:{mission_id}",
            task_breakdown.to_dict()
        )
        
        # Log summary
        logger.info(
            f"[MULTI-STEP PLANNING] Mission plan complete: {mission_id}\n"
            f"  - Steps: {len(task_breakdown.steps)}\n"
            f"  - Buddy steps: {task_breakdown.pure_buddy_steps}\n"
            f"  - Human steps: {task_breakdown.pure_human_steps}\n"
            f"  - Hybrid steps: {task_breakdown.hybrid_steps}\n"
            f"  - Total cost: ${task_breakdown.total_cost.total_usd:.4f}\n"
            f"  - Buddy time: {task_breakdown.total_buddy_time_seconds:.1f}s\n"
            f"  - Human time: {task_breakdown.total_human_time_minutes}min\n"
            f"  - Parallelization opportunities: {len(parallelization_opportunities)}"
        )
        
        return unified_proposal
    
    def _add_step_scheduling(self, task_breakdown: TaskBreakdown) -> None:
        """
        Add default cascade scheduling to steps.
        
        Default: Step 1 immediate, subsequent steps cascade from previous.
        """
        try:
            from Back_End.step_scheduler import step_scheduler
            
            for step in task_breakdown.steps:
                if step.step_number == 1:
                    # First step: immediate execution
                    step.schedule = step_scheduler.create_immediate_schedule(step.step_number)
                else:
                    # Subsequent steps: cascade from previous
                    step.schedule = step_scheduler.create_cascade_schedule(
                        step_number=step.step_number,
                        depends_on_step=step.step_number - 1
                    )
                
                logger.debug(
                    f"  Step {step.step_number}: {step.schedule.to_human_readable()}"
                )
        
        except Exception as e:
            logger.error(f"Failed to add scheduling: {e}", exc_info=True)
    
    def _detect_parallelization(
        self,
        task_breakdown: TaskBreakdown
    ) -> List[Any]:
        """
        Detect parallelization opportunities in task breakdown.
        
        Returns:
            List of ParallelizationOpportunity objects
        """
        try:
            from Back_End.parallelization_detector import parallelization_detector
            
            opportunities = parallelization_detector.analyze_steps(
                steps=task_breakdown.steps,
                conservative=True  # Conservative by default
            )
            
            for opp in opportunities:
                logger.info(
                    f"  Parallelization: {opp.to_human_readable()} "
                    f"(saves {opp.time_savings_seconds:.1f}s, risk: {opp.risk_level})"
                )
            
            return opportunities
        
        except Exception as e:
            logger.error(f"Failed to detect parallelization: {e}", exc_info=True)
            return []
    
    def _enhance_steps_with_tool_selection(
        self,
        task_breakdown: TaskBreakdown
    ) -> None:
        """
        Enhance each TaskStep with tool selection, cost, and duration estimates.
        
        Modifies task_breakdown.steps in-place.
        """
        for step in task_breakdown.steps:
            # Skip pure human steps (no tool execution)
            if step.step_type == StepType.PURE_HUMAN:
                logger.debug(
                    f"  Step {step.step_number}: PURE_HUMAN - skipping tool selection"
                )
                continue
            
            # Build constraints for this step
            constraints = {
                'target_count': 50,  # Default
                'max_pages': 5,
                'max_duration_seconds': 300
            }
            
            # Run tool selection for this step
            try:
                tool_plan = self.tool_selector.plan_tool_selection(
                    objective_description=step.description,
                    objective_type=self._infer_step_objective_type(step.description),
                    constraints=constraints,
                    domain="_global"
                )
                
                primary_tool = tool_plan.get('primary_tool')
                
                if primary_tool:
                    # Update step with tool selection results
                    step.tools_used = [primary_tool['tool_name']]
                    
                    # Update cost estimate (prefer tool-specific over heuristic)
                    if primary_tool.get('estimated_cost_usd', 0) > 0:
                        # Tool selector has better cost estimate
                        from Back_End.cost_estimator import MissionCost
                        step.estimated_cost = MissionCost(
                            total_usd=primary_tool['estimated_cost_usd'],
                            service_costs=[],
                            currency="USD"
                        )
                    
                    # Update duration estimate
                    if primary_tool.get('estimated_duration_seconds', 0) > 0:
                        step.estimated_buddy_time = primary_tool['estimated_duration_seconds']
                    
                    # Update confidence
                    step.confidence = primary_tool.get('combined_score', step.confidence)
                    
                    # Add rationale
                    if not step.rationale:
                        step.rationale = primary_tool.get('reasoning', '')
                    
                    logger.info(
                        f"  Step {step.step_number}: {primary_tool['tool_name']} "
                        f"(confidence: {step.confidence:.1%}, "
                        f"cost: ${primary_tool['estimated_cost_usd']:.4f}, "
                        f"duration: {primary_tool['estimated_duration_seconds']:.1f}s)"
                    )
                else:
                    logger.warning(
                        f"  Step {step.step_number}: No tool selected - "
                        f"using defaults"
                    )
            
            except Exception as e:
                logger.error(
                    f"  Step {step.step_number}: Tool selection failed: {e}",
                    exc_info=True
                )
                # Keep existing estimates from TaskBreakdownEngine
    
    def _infer_step_objective_type(self, step_description: str) -> str:
        """Infer objective type from step description"""
        desc_lower = step_description.lower()
        
        if any(word in desc_lower for word in ['extract', 'pull', 'get data', 'scrape']):
            return 'extract'
        elif any(word in desc_lower for word in ['navigate', 'go to', 'visit', 'open']):
            return 'navigate'
        elif any(word in desc_lower for word in ['search', 'find', 'look up', 'research']):
            return 'search'
        elif any(word in desc_lower for word in ['calculate', 'compute', 'solve']):
            return 'calculate'
        elif any(word in desc_lower for word in ['write', 'create', 'generate', 'compose']):
            return 'generate'
        else:
            return 'search'  # Default
    
    def _generate_mission_title(self, objective: str) -> str:
        """Generate concise mission title from objective"""
        # Take first sentence or 60 chars
        if '.' in objective:
            title = objective.split('.')[0]
        else:
            title = objective[:60]
        
        # Capitalize first letter
        title = title.strip().capitalize()
        
        # Remove trailing punctuation
        title = title.rstrip('.,!?')
        
        return title if len(title) > 0 else "Mission"


def plan_multi_step_mission(
    readiness_result: ReadinessResult,
    raw_chat_message: str,
    user_id: str = "default_user"
) -> UnifiedProposal:
    """
    Convenience function to plan a multi-step mission.
    
    Args:
        readiness_result: Output from ActionReadinessEngine
        raw_chat_message: Original user message
        user_id: User identifier
        
    Returns:
        UnifiedProposal with complete breakdown
    """
    planner = MultiStepMissionPlanner()
    return planner.plan_mission(readiness_result, raw_chat_message, user_id)


# Singleton instance
multi_step_planner = MultiStepMissionPlanner()
