"""
Budget Enforcer: Checks budgets BEFORE execution

Prevents:
- Exceeding SerpAPI monthly quota
- Exceeding OpenAI spending limits
- Executing when out of credits

Returns actionable decisions with clear reasons for blocking.
"""

import logging
from typing import Dict, Any
from Back_End.budget_tracker import get_budget_tracker, CreditBudget, DollarBudget
from Back_End.cost_estimator import MissionCost, ServiceTier
from Back_End.task_breakdown_and_proposal import TaskBreakdown

logger = logging.getLogger(__name__)


class BudgetEnforcer:
    """
    Enforces budget limits before mission execution.
    
    Checks both credit-based (SerpAPI) and dollar-based (OpenAI, Firestore) budgets.
    """
    
    def __init__(self):
        self.budget_tracker = get_budget_tracker()
    
    def check_mission_budget(
        self,
        mission_cost: MissionCost,
        task_breakdown: TaskBreakdown,
        serpapi_tier: ServiceTier = ServiceTier.FREE
    ) -> Dict[str, Any]:
        """
        Check if mission is within ALL budgets.
        
        Args:
            mission_cost: Estimated mission cost
            task_breakdown: Task breakdown with steps
            serpapi_tier: Current SerpAPI tier
            
        Returns:
            {
                'can_execute': bool,
                'reason': str (if blocked),
                'credit_check': {...},
                'dollar_check': {...},
                'recommended_action': str (if blocked)
            }
        """
        logger.info("[BUDGET_ENFORCER] Checking mission budget...")
        
        # Check SerpAPI credits
        serpapi_searches = self._count_serpapi_searches(mission_cost)
        credit_budget = self.budget_tracker.get_serpapi_budget(serpapi_tier)
        
        if serpapi_searches > 0 and not credit_budget.can_afford(serpapi_searches):
            logger.warning(
                f"[BUDGET_ENFORCER] Insufficient SerpAPI credits: "
                f"{credit_budget.credits_remaining} available, {serpapi_searches} needed"
            )
            
            # Determine recommended action
            if credit_budget.days_remaining_in_month <= 5:
                recommended_action = 'wait_for_reset'
                action_detail = f'Reset in {credit_budget.days_remaining_in_month} days'
            else:
                recommended_action = 'upgrade_tier'
                action_detail = 'Consider upgrading to STARTER tier (1,000 searches/month)'
            
            return {
                'can_execute': False,
                'reason': (
                    f'Insufficient SerpAPI credits: {credit_budget.credits_remaining} available, '
                    f'{serpapi_searches} needed'
                ),
                'service': 'serpapi',
                'credit_check': {
                    'credits_available': credit_budget.credits_remaining,
                    'credits_needed': serpapi_searches,
                    'tier': serpapi_tier.value,
                    'monthly_quota': credit_budget.monthly_quota,
                    'days_until_reset': credit_budget.days_remaining_in_month
                },
                'recommended_action': recommended_action,
                'action_detail': action_detail
            }
        
        # Check OpenAI dollars
        openai_cost = self._extract_openai_cost(mission_cost)
        dollar_budget = self.budget_tracker.get_openai_budget()
        
        if openai_cost > 0 and not dollar_budget.can_afford(openai_cost):
            logger.warning(
                f"[BUDGET_ENFORCER] Insufficient OpenAI budget: "
                f"${dollar_budget.dollars_remaining:.2f} available, ${openai_cost:.2f} needed"
            )
            
            return {
                'can_execute': False,
                'reason': (
                    f'Insufficient OpenAI budget: ${dollar_budget.dollars_remaining:.2f} available, '
                    f'${openai_cost:.2f} needed'
                ),
                'service': 'openai',
                'dollar_check': {
                    'budget_remaining': dollar_budget.dollars_remaining,
                    'cost_needed': openai_cost,
                    'monthly_limit': dollar_budget.monthly_limit_usd
                },
                'recommended_action': 'increase_budget',
                'action_detail': 'Consider increasing monthly OpenAI budget limit'
            }
        
        # Check Firestore dollars
        firestore_cost = self._extract_firestore_cost(mission_cost)
        firestore_budget = self.budget_tracker.get_firestore_budget()
        
        if firestore_cost > 0 and not firestore_budget.can_afford(firestore_cost):
            logger.warning(
                f"[BUDGET_ENFORCER] Insufficient Firestore budget: "
                f"${firestore_budget.dollars_remaining:.2f} available, ${firestore_cost:.2f} needed"
            )
            
            return {
                'can_execute': False,
                'reason': (
                    f'Insufficient Firestore budget: ${firestore_budget.dollars_remaining:.2f} available, '
                    f'${firestore_cost:.2f} needed'
                ),
                'service': 'firestore',
                'dollar_check': {
                    'budget_remaining': firestore_budget.dollars_remaining,
                    'cost_needed': firestore_cost,
                    'monthly_limit': firestore_budget.monthly_limit_usd
                },
                'recommended_action': 'increase_budget',
                'action_detail': 'Consider increasing monthly Firestore budget limit'
            }
        
        # All checks passed
        logger.info("[BUDGET_ENFORCER] Mission within budget limits ✓")
        
        return {
            'can_execute': True,
            'credit_check': {
                'serpapi_searches': serpapi_searches,
                'credits_before': credit_budget.credits_remaining,
                'credits_after': credit_budget.credits_remaining - serpapi_searches,
                'tier': serpapi_tier.value,
                'todays_budget': credit_budget.calculate_todays_budget(),
                'pace': credit_budget.pace_status()
            },
            'dollar_check': {
                'openai_cost': openai_cost,
                'openai_budget_before': dollar_budget.dollars_remaining,
                'openai_budget_after': dollar_budget.dollars_remaining - openai_cost,
                'firestore_cost': firestore_cost,
                'firestore_budget_before': firestore_budget.dollars_remaining,
                'firestore_budget_after': firestore_budget.dollars_remaining - firestore_cost
            }
        }
    
    def _count_serpapi_searches(self, mission_cost: MissionCost) -> int:
        """Extract number of SerpAPI searches from mission cost"""
        for service_cost in mission_cost.service_costs:
            if service_cost.service == 'serpapi':
                return service_cost.operation_count
        return 0
    
    def _extract_openai_cost(self, mission_cost: MissionCost) -> float:
        """Extract OpenAI dollar cost from mission cost"""
        total = 0.0
        for service_cost in mission_cost.service_costs:
            if service_cost.service == 'openai':
                total += service_cost.total_cost
        return total
    
    def _extract_firestore_cost(self, mission_cost: MissionCost) -> float:
        """Extract Firestore dollar cost from mission cost"""
        total = 0.0
        for service_cost in mission_cost.service_costs:
            if service_cost.service == 'firestore':
                total += service_cost.total_cost
        return total
    
    def get_budget_status_summary(self, serpapi_tier: ServiceTier = ServiceTier.FREE) -> Dict[str, Any]:
        """
        Get summary of all budget statuses.
        
        Returns:
            {
                'serpapi': {...},
                'openai': {...},
                'firestore': {...}
            }
        """
        serpapi = self.budget_tracker.get_serpapi_budget(serpapi_tier)
        openai = self.budget_tracker.get_openai_budget()
        firestore = self.budget_tracker.get_firestore_budget()
        
        return {
            'serpapi': {
                'type': 'credits',
                'tier': serpapi.tier,
                'monthly_quota': serpapi.monthly_quota,
                'credits_used': serpapi.credits_used,
                'credits_remaining': serpapi.credits_remaining,
                'todays_budget': serpapi.calculate_todays_budget(),
                'daily_rollover': serpapi.daily_rollover,
                'pace': serpapi.pace_status(),
                'days_until_reset': serpapi.days_remaining_in_month
            },
            'openai': {
                'type': 'dollars',
                'monthly_limit': openai.monthly_limit_usd,
                'spent': openai.dollars_spent,
                'remaining': openai.dollars_remaining,
                'billing_period_end': openai.billing_period_end
            },
            'firestore': {
                'type': 'dollars',
                'monthly_limit': firestore.monthly_limit_usd,
                'spent': firestore.dollars_spent,
                'remaining': firestore.dollars_remaining,
                'billing_period_end': firestore.billing_period_end
            }
        }


# Singleton instance
_budget_enforcer = None


def get_budget_enforcer() -> BudgetEnforcer:
    """Get or create budget enforcer singleton"""
    global _budget_enforcer
    if _budget_enforcer is None:
        _budget_enforcer = BudgetEnforcer()
    return _budget_enforcer

