"""
Investment Connector: Link investment/ROI signals to tool selection.

PHASE 5: Integrates investment cost tracking with tool selection confidence.

Balances:
- Tool Reliability: Success rate (from Phase 3 feedback)
- Tool Cost: Expected execution cost (from investment_core)
- ROI: (success_rate * result_value) - expected_cost

Example:
- Tool A: 90% success, $0.50 cost, 4.5/5 satisfaction → ROI: 0.90*4.5-0.50 = 3.55
- Tool B: 95% success, $2.00 cost, 4.8/5 satisfaction → ROI: 0.95*4.8-2.00 = 2.56
→ Tool A selected based on better ROI despite slightly lower success rate
"""

from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ToolInvestmentProfile:
    """Financial profile of a tool's usage."""
    
    def __init__(
        self,
        tool_name: str,
        mission_type: str,
        usage_count: int = 0,
        success_count: int = 0,
        total_cost: float = 0.0,
        avg_satisfaction: float = 3.0
    ):
        self.tool_name = tool_name
        self.mission_type = mission_type
        self.usage_count = usage_count
        self.success_count = success_count
        self.total_cost = total_cost
        self.avg_satisfaction = avg_satisfaction
    
    def success_rate(self) -> float:
        """Calculate success rate (0-1)."""
        if self.usage_count == 0:
            return 0.5  # Neutral default
        return self.success_count / self.usage_count
    
    def avg_cost_per_execution(self) -> float:
        """Average cost per execution."""
        if self.usage_count == 0:
            return 0.0
        return self.total_cost / self.usage_count
    
    def roi_score(self) -> float:
        """
        Calculate ROI score (revenue - cost).
        
        Formula:
        ROI = (success_rate * satisfaction_score) - avg_cost
        
        Higher = better (more value per dollar spent)
        """
        return (self.success_rate() * self.avg_satisfaction) - self.avg_cost_per_execution()
    
    def cost_efficiency_ratio(self) -> float:
        """
        Cost efficiency: value per dollar.
        
        Formula:
        efficiency = (success_rate * satisfaction) / (cost + 0.01)
        
        Dividing by cost shows how much value you get per dollar spent.
        """
        denominator = max(self.avg_cost_per_execution(), 0.01)  # Avoid division by zero
        return (self.success_rate() * self.avg_satisfaction) / denominator
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tool_name': self.tool_name,
            'mission_type': self.mission_type,
            'usage_count': self.usage_count,
            'success_count': self.success_count,
            'total_cost': self.total_cost,
            'avg_satisfaction': self.avg_satisfaction,
            'success_rate': self.success_rate(),
            'avg_cost_per_execution': self.avg_cost_per_execution(),
            'roi_score': self.roi_score(),
            'cost_efficiency_ratio': self.cost_efficiency_ratio()
        }


class InvestmentConnector:
    """
    Link investment/cost signals to tool selection decisions.
    
    Applies investment scores as multipliers to tool confidence:
    - High ROI (>3.0): +20% confidence boost
    - Medium ROI (1.0-3.0): +5% confidence boost
    - Low ROI (<1.0): -15% confidence penalty
    
    Can operate in two modes:
    1. RELIABILITY_FIRST: Use feedback confidence, apply small investment adjustment
    2. ROI_OPTIMIZED: Use ROI score as primary factor
    """
    
    def __init__(self, mission_store, feedback_integrator):
        self.mission_store = mission_store
        self.feedback_integrator = feedback_integrator
        self._profile_cache: Dict[str, ToolInvestmentProfile] = {}
    
    def get_tool_investment_multiplier(
        self,
        tool_name: str,
        mission_type: str,
        optimization_mode: str = 'reliability_first'
    ) -> float:
        """
        Get multiplier for tool confidence based on investment/ROI.
        
        Args:
            tool_name: Tool to evaluate
            mission_type: Type of mission
            optimization_mode: 'reliability_first' or 'roi_optimized'
        
        Returns:
            Multiplier (1.0 = no change, >1.0 = boost, <1.0 = penalty)
        
        In RELIABILITY_FIRST mode (default):
        - Tool confidence from feedback is primary
        - Investment score modifies it slightly
        - Formula: 1.0 + (0.2 * roi_signal)
        
        In ROI_OPTIMIZED mode:
        - ROI score is primary
        - Higher ROI = higher confidence boost
        - Use only if cost matters more than reliability
        """
        try:
            profile = self.get_tool_investment_profile(tool_name, mission_type)
            
            roi = profile.roi_score()
            efficiency = profile.cost_efficiency_ratio()
            
            if optimization_mode == 'roi_optimized':
                # Pure ROI optimization
                if roi >= 3.0:
                    return 1.30  # Strong boost for excellent ROI
                elif roi >= 1.0:
                    return 1.15  # Moderate boost for good ROI
                elif roi > 0:
                    return 1.0   # Neutral for barely positive ROI
                else:
                    return 0.70  # Penalty for negative ROI
            
            else:  # reliability_first (default)
                # Reliability primary, investment as secondary factor
                if efficiency >= 4.0:
                    return 1.15  # Good efficiency boost
                elif efficiency >= 2.0:
                    return 1.05  # Small efficiency boost
                elif efficiency >= 1.0:
                    return 1.0   # Neutral
                else:
                    return 0.85  # Penalty for poor efficiency
        
        except Exception as e:
            logger.warning(f"Failed to calculate investment multiplier: {e}")
            return 1.0  # Default: no adjustment
    
    def get_tool_investment_profile(
        self,
        tool_name: str,
        mission_type: str,
        days: int = 30
    ) -> ToolInvestmentProfile:
        """
        Get investment profile (cost/ROI metrics) for a tool.
        
        Returns:
            ToolInvestmentProfile with financials and ROI
        """
        cache_key = f"{tool_name}:{mission_type}"
        if cache_key in self._profile_cache:
            return self._profile_cache[cache_key]
        
        try:
            # Get performance data from feedback system
            stats = self.feedback_integrator.get_tool_stats(tool_name, mission_type, days)
            
            # Get cost data from mission_store
            costs = self.mission_store.get_tool_costs(tool_name, mission_type, days)
            
            # Build profile
            profile = ToolInvestmentProfile(
                tool_name=tool_name,
                mission_type=mission_type,
                usage_count=stats['count'],
                success_count=stats['success_count'],
                total_cost=costs['total_cost'],
                avg_satisfaction=costs['avg_satisfaction'] or stats.get('avg_satisfaction', 3.0)
            )
            
            # Cache it
            self._profile_cache[cache_key] = profile
            
            logger.debug(
                f"[INVESTMENT] Profile for {tool_name}/{mission_type}: "
                f"ROI={profile.roi_score():.2f}, efficiency={profile.cost_efficiency_ratio():.2f}"
            )
            
            return profile
        except Exception as e:
            logger.error(f"Failed to get investment profile: {e}")
            # Return neutral profile
            return ToolInvestmentProfile(tool_name, mission_type, 0, 0, 0, 3.0)
    
    def get_best_roi_tool(
        self,
        candidate_tools: List[Tuple[str, float]],
        mission_type: str
    ) -> Tuple[str, float]:
        """
        Select tool with best ROI from candidates.
        
        Args:
            candidate_tools: List of (tool_name, base_confidence)
            mission_type: Type of mission
        
        Returns:
            (best_tool_name, adjusted_confidence)
        """
        if not candidate_tools:
            return ('unknown', 0.0)
        
        try:
            best_tool = None
            best_roi = float('-inf')
            
            for tool_name, base_confidence in candidate_tools:
                profile = self.get_tool_investment_profile(tool_name, mission_type)
                roi = profile.roi_score()
                
                # Factor in base confidence to avoid picking untrustworthy tools
                adjusted_roi = roi * (1 + base_confidence)
                
                if adjusted_roi > best_roi:
                    best_roi = adjusted_roi
                    best_tool = tool_name
            
            if best_tool:
                profile = self.get_tool_investment_profile(best_tool, mission_type)
                adjusted_confidence = min(0.95, max(0.5, profile.roi_score()))  # Cap 0.5-0.95
                
                logger.info(
                    f"[INVESTMENT] Best ROI tool for '{mission_type}': "
                    f"{best_tool} (roi={profile.roi_score():.2f})"
                )
                
                return (best_tool, adjusted_confidence)
            
            return candidate_tools[0]  # Fallback to first candidate
        except Exception as e:
            logger.error(f"Failed to select best ROI tool: {e}")
            return candidate_tools[0] if candidate_tools else ('unknown', 0.0)
    
    def get_cost_benefit_analysis(
        self,
        mission_type: str
    ) -> Dict[str, Any]:
        """
        Get cost-benefit analysis for all tools on a mission type.
        
        Returns:
        {
            'mission_type': 'web_search_tutorial',
            'tools': [
                {
                    'tool': 'web_search',
                    'usage_count': 50,
                    'success_rate': 0.92,
                    'avg_cost': 0.15,
                    'avg_satisfaction': 4.2,
                    'roi_score': 3.63,
                    'efficiency_ratio': 28.8,
                    'recommendation': 'Excellent value'
                },
                ...
            ]
        }
        """
        try:
            tools_analysis = []
            
            # Get all tools used for this mission type
            feedbacks = self.mission_store.get_mission_feedbacks(mission_type=mission_type)
            
            if not feedbacks:
                return {
                    'mission_type': mission_type,
                    'tools': [],
                    'message': 'No data available for this mission type'
                }
            
            # Collect unique tools
            tools_set = set(f.get('tool_used') for f in feedbacks if f.get('tool_used'))
            
            for tool in sorted(tools_set):
                profile = self.get_tool_investment_profile(tool, mission_type)
                
                # Determine recommendation
                roi = profile.roi_score()
                if roi >= 3.0:
                    recommendation = 'Excellent value'
                elif roi >= 1.5:
                    recommendation = 'Good value'
                elif roi > 0:
                    recommendation = 'Acceptable'
                else:
                    recommendation = 'Poor value'
                
                tools_analysis.append({
                    'tool': tool,
                    'usage_count': profile.usage_count,
                    'success_rate': round(profile.success_rate(), 3),
                    'avg_cost': round(profile.avg_cost_per_execution(), 4),
                    'avg_satisfaction': round(profile.avg_satisfaction, 2),
                    'roi_score': round(profile.roi_score(), 2),
                    'efficiency_ratio': round(profile.cost_efficiency_ratio(), 2),
                    'recommendation': recommendation
                })
            
            # Sort by ROI descending
            tools_analysis.sort(key=lambda x: x['roi_score'], reverse=True)
            
            return {
                'mission_type': mission_type,
                'tools': tools_analysis,
                'message': f'Analysis of {len(tools_analysis)} tools'
            }
        except Exception as e:
            logger.error(f"Failed to get cost-benefit analysis: {e}")
            return {'error': str(e)}
    
    def clear_cache(self) -> None:
        """Clear profile cache (useful for testing)."""
        self._profile_cache.clear()
        logger.debug("[INVESTMENT] Cleared cache")


def get_investment_connector():
    """Get singleton InvestmentConnector instance."""
    from Back_End.mission_store import get_mission_store
    from Back_End.feedback_integrator import get_feedback_integrator
    
    if not hasattr(get_investment_connector, '_instance'):
        get_investment_connector._instance = InvestmentConnector(
            mission_store=get_mission_store(),
            feedback_integrator=get_feedback_integrator()
        )
    
    return get_investment_connector._instance
