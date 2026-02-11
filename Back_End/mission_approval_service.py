"""
Mission Approval Service

Evaluates mission plans and makes informed approval decisions.
Uses plan data (cost, duration, tool, risk) to assess vs user constraints.
"""

import logging
from typing import Dict, Any

from Back_End.mission_plan import MissionPlan
from Back_End.mission_store import get_mission_store, Mission

logger = logging.getLogger(__name__)


class MissionApprovalService:
    """
    Makes informed approval decisions using mission plans.
    Evaluates plan against user budget, constraints, risk tolerance.
    """
    
    def __init__(self):
        self.mission_store = get_mission_store()
    
    def evaluate_approval(
        self,
        mission_plan: MissionPlan,
        user_id: str,
        user_budget_remaining: float,
        service_tier: str = "FREE"
    ) -> Dict[str, Any]:
        """
        Evaluate if mission should be approved.
        Returns decision + rationale + checks.
        
        Args:
            mission_plan: MissionPlan to evaluate
            user_id: User ID (for logging)
            user_budget_remaining: Budget available for this user
            service_tier: User's service tier (FREE, BASIC, PRO, etc.)
            
        Returns:
            {
                'mission_id': str,
                'approved': bool,
                'checks': [{'check': str, 'passed': bool, 'reason': str}],
                'recommendation': 'APPROVE' | 'REVIEW' | 'DENY',
                'alternative_options': int,
                'budget_remaining_after': float
            }
        """
        checks = []
        
        logger.info(
            f"[APPROVAL] Evaluating mission {mission_plan.mission_id} "
            f"for user {user_id} (tier: {service_tier})"
        )
        
        # Budget check
        estimated_cost = mission_plan.total_estimated_cost
        if estimated_cost > user_budget_remaining:
            checks.append({
                'check': 'budget',
                'passed': False,
                'reason': (
                    f"Cost ${estimated_cost:.4f} exceeds remaining budget "
                    f"${user_budget_remaining:.4f}"
                )
            })
            logger.warning(
                f"[APPROVAL] Budget check FAILED: "
                f"cost ${estimated_cost:.4f} > budget ${user_budget_remaining:.4f}"
            )
        else:
            checks.append({
                'check': 'budget',
                'passed': True,
                'reason': (
                    f"Cost ${estimated_cost:.4f} within budget "
                    f"(${user_budget_remaining:.4f} remaining)"
                )
            })
            logger.info(
                f"[APPROVAL] Budget check PASSED: "
                f"${estimated_cost:.4f} <= ${user_budget_remaining:.4f}"
            )
        
        # Feasibility check
        if mission_plan.is_feasible:
            checks.append({
                'check': 'feasibility',
                'passed': True,
                'reason': "Mission parameters within constraints"
            })
            logger.info("[APPROVAL] Feasibility check PASSED")
        else:
            checks.append({
                'check': 'feasibility',
                'passed': False,
                'reason': (
                    mission_plan.feasibility_issues[0] 
                    if mission_plan.feasibility_issues else "Unknown constraint violated"
                )
            })
            logger.warning(
                f"[APPROVAL] Feasibility check FAILED: "
                f"{mission_plan.feasibility_issues}"
            )
        
        # Tool viability check
        success_rate = mission_plan.primary_tool['success_rate']
        if success_rate > 0.7:
            checks.append({
                'check': 'tool_viability',
                'passed': True,
                'reason': (
                    f"Tool {mission_plan.primary_tool['tool_name']} "
                    f"has {success_rate:.1%} success rate"
                )
            })
            logger.info(
                f"[APPROVAL] Tool viability check PASSED: "
                f"{success_rate:.1%} success rate"
            )
        else:
            checks.append({
                'check': 'tool_viability',
                'passed': False,
                'reason': (
                    f"Tool {mission_plan.primary_tool['tool_name']} "
                    f"has low success: {success_rate:.1%}"
                )
            })
            logger.warning(
                f"[APPROVAL] Tool viability check FAILED: "
                f"only {success_rate:.1%} success rate"
            )
        
        # Risk assessment
        risk_level = mission_plan.risk_level
        if risk_level == "HIGH":
            checks.append({
                'check': 'risk_level',
                'passed': False,
                'reason': f"Mission risk level is HIGH - review before approval"
            })
            logger.warning(f"[APPROVAL] Risk level check: HIGH RISK")
        else:
            checks.append({
                'check': 'risk_level',
                'passed': True,
                'reason': f"Mission risk level is {risk_level}"
            })
            logger.info(f"[APPROVAL] Risk level check: {risk_level}")
        
        # Overall decision
        all_passed = all(c['passed'] for c in checks)
        
        if all_passed:
            recommendation = 'APPROVE'
            logger.info(
                f"[APPROVAL] RECOMMENDATION: APPROVE "
                f"(all checks passed)"
            )
        elif checks[0]['passed'] and checks[1]['passed']:
            # Budget and feasibility pass, but other issues
            recommendation = 'REVIEW'
            logger.warning(
                f"[APPROVAL] RECOMMENDATION: REVIEW "
                f"(budget/feasibility OK but other concerns)"
            )
        else:
            recommendation = 'DENY'
            logger.warning(
                f"[APPROVAL] RECOMMENDATION: DENY "
                f"(critical checks failed)"
            )
        
        return {
            'mission_id': mission_plan.mission_id,
            'approved': all_passed,
            'recommendation': recommendation,
            'checks': checks,
            'alternative_options': len(mission_plan.alternative_tools),
            'budget_remaining_after': max(0.0, user_budget_remaining - estimated_cost)
        }
    
    def approve_mission(
        self,
        mission_plan: MissionPlan,
        approval_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert approved MissionPlan → Mission (ready for execution).
        Writes mission with pre-selected tool to mission store.
        
        Args:
            mission_plan: The MissionPlan to approve
            approval_decision: Decision from evaluate_approval()
            
        Returns:
            {
                'success': bool,
                'mission_id': str,
                'status': str,
                'tool': str,
                'estimated_cost': float,
                'estimated_duration': float
            }
        """
        if not approval_decision.get('approved'):
            logger.warning(
                f"[APPROVAL] Cannot approve mission {mission_plan.mission_id}: "
                f"Recommendation is {approval_decision.get('recommendation')}"
            )
            return {
                'success': False,
                'mission_id': mission_plan.mission_id,
                'reason': f"Recommendation: {approval_decision['recommendation']}"
            }
        
        logger.info(
            f"[APPROVAL] Approving mission {mission_plan.mission_id} "
            f"with tool {mission_plan.primary_tool['tool_name']}"
        )
        
        # Create Mission object with tool pre-selected
        mission = Mission(
            mission_id=mission_plan.mission_id,
            event_type='mission_approved',
            status='approved',
            objective={
                'type': mission_plan.objective_type,
                'description': mission_plan.objective_description,
                'target_count': mission_plan.target_count,
            },
            scope={
                'allowed_domains': mission_plan.allowed_domains,
                'max_pages': mission_plan.max_pages,
                'max_duration_seconds': mission_plan.max_duration_seconds,
            },
            metadata={
                'created_at': mission_plan.created_at,
                'raw_chat_message': mission_plan.raw_chat_message,
                'intent_keywords': mission_plan.intent_keywords,
                # NEW: Pre-selected tool info from planning phase
                'tool_selected': mission_plan.primary_tool['tool_name'],
                'tool_confidence': mission_plan.primary_tool['combined_score'],
                'tool_performance_score': mission_plan.primary_tool['performance_score'],
                'estimated_cost': mission_plan.total_estimated_cost,
                'estimated_duration': mission_plan.total_estimated_duration,
                'risk_level': mission_plan.risk_level,
                'feasibility_issues': mission_plan.feasibility_issues,
            }
        )
        
        # Write to mission store
        self.mission_store.write_mission_event(mission)
        
        logger.info(
            f"[APPROVAL] Mission approved and written to store: "
            f"{mission_plan.mission_id}"
        )
        
        return {
            'success': True,
            'mission_id': mission.mission_id,
            'status': 'approved',
            'tool': mission_plan.primary_tool['tool_name'],
            'estimated_cost': mission_plan.total_estimated_cost,
            'estimated_duration': mission_plan.total_estimated_duration,
            'message': f"Mission approved for execution with "
                      f"{mission_plan.primary_tool['tool_name']}"
        }


# Singleton instance
_approval_service = None


def get_approval_service():
    """Get or create approval service singleton."""
    global _approval_service
    if _approval_service is None:
        _approval_service = MissionApprovalService()
    return _approval_service


def evaluate_mission_approval(
    mission_plan: MissionPlan,
    user_id: str,
    user_budget_remaining: float,
    service_tier: str = "FREE"
) -> Dict[str, Any]:
    """Convenience function to evaluate mission approval"""
    service = get_approval_service()
    return service.evaluate_approval(
        mission_plan, user_id, user_budget_remaining, service_tier
    )


def approve_mission(
    mission_plan: MissionPlan,
    approval_decision: Dict[str, Any]
) -> Dict[str, Any]:
    """Convenience function to approve a mission"""
    service = get_approval_service()
    return service.approve_mission(mission_plan, approval_decision)

