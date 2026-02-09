"""
Phase 9: Fatigue Model

Models human cognitive fatigue and energy availability.

Hard constraints:
- NO autonomy (advisory only)
- NO learning loops
- NO mission killing
- NO external APIs
- READ-ONLY analysis

Fatigue States:
  FRESH (0-20%): Full capacity, accept complex missions
  NORMAL (20-60%): Reduced capacity, prefer medium complexity
  TIRED (60-85%): Significantly reduced, only small tasks
  EXHAUSTED (85-100%): Hard stop, no new missions

Daily Budget Model:
  - Total minutes available per day (configurable, default 480 = 8 hours)
  - Per-mission effort estimates
  - Cumulative tracking
  - Hard budget enforcement
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
from datetime import datetime, timedelta
import math


class FatigueState(Enum):
    """Human fatigue levels."""
    FRESH = "FRESH"           # 0-20% exhausted
    NORMAL = "NORMAL"         # 20-60% exhausted
    TIRED = "TIRED"           # 60-85% exhausted
    EXHAUSTED = "EXHAUSTED"   # 85-100% exhausted


@dataclass(frozen=True)
class DailyBudget:
    """Daily effort budget (immutable)."""
    total_minutes: int = 480          # Default: 8 hour day
    used_minutes: int = 0
    mission_efforts: List[int] = field(default_factory=list)
    
    def remaining_minutes(self) -> int:
        """Minutes remaining in budget."""
        return max(0, self.total_minutes - self.used_minutes)
    
    def exhaustion_ratio(self) -> float:
        """0.0 (fresh) to 1.0 (exhausted)."""
        if self.total_minutes == 0:
            return 0.0
        return min(1.0, self.used_minutes / self.total_minutes)
    
    def can_afford_mission(self, effort_minutes: int) -> bool:
        """Can we afford this mission without exceeding budget?"""
        return self.used_minutes + effort_minutes <= self.total_minutes
    
    def update_used(self, added_minutes: int) -> 'DailyBudget':
        """Create new budget with updated used minutes."""
        new_efforts = self.mission_efforts + [added_minutes]
        return DailyBudget(
            total_minutes=self.total_minutes,
            used_minutes=self.used_minutes + added_minutes,
            mission_efforts=new_efforts
        )
    
    def add_mission_effort(self, effort_minutes: int) -> 'DailyBudget':
        """Add mission effort without updating used (for planning)."""
        new_efforts = self.mission_efforts + [effort_minutes]
        return DailyBudget(
            total_minutes=self.total_minutes,
            used_minutes=self.used_minutes,
            mission_efforts=new_efforts
        )


@dataclass(frozen=True)
class FatigueScore:
    """Immutable fatigue assessment."""
    state: FatigueState
    exhaustion_ratio: float          # 0.0-1.0
    remaining_budget_minutes: int
    capacity_multiplier: float        # 0.3 (exhausted) to 1.0 (fresh)
    complexity_threshold: str          # SIMPLE, MEDIUM, COMPLEX
    recommendation: str                # e.g., "Accept only simple tasks"
    reasoning: List[str] = field(default_factory=list)
    
    def is_budget_exhausted(self) -> bool:
        """Is daily budget completely spent?"""
        return self.state == FatigueState.EXHAUSTED
    
    def can_accept_new_mission(self) -> bool:
        """Should we accept new missions at this fatigue level?"""
        return self.state not in [FatigueState.EXHAUSTED]


class FatigueCalculator:
    """Calculates human fatigue state from effort budget."""
    
    # Thresholds for fatigue states
    FRESH_THRESHOLD = 0.20           # 0-20% of budget used
    NORMAL_THRESHOLD = 0.60          # 20-60%
    TIRED_THRESHOLD = 0.85           # 60-85%
    # Anything above 85% is EXHAUSTED
    
    # Capacity multipliers per fatigue state
    # These adjust how much work we recommend
    CAPACITY_MULTIPLIERS = {
        FatigueState.FRESH: 1.0,       # Full capacity
        FatigueState.NORMAL: 0.85,     # 85% capacity (slight decline)
        FatigueState.TIRED: 0.6,       # 60% capacity (significant decline)
        FatigueState.EXHAUSTED: 0.3,   # 30% capacity (hard stop mode)
    }
    
    # Complexity thresholds per fatigue state
    COMPLEXITY_THRESHOLDS = {
        FatigueState.FRESH: "COMPLEX",
        FatigueState.NORMAL: "MEDIUM",
        FatigueState.TIRED: "SIMPLE",
        FatigueState.EXHAUSTED: "NONE",
    }
    
    @staticmethod
    def calculate_fatigue_state(budget: DailyBudget) -> FatigueState:
        """Determine fatigue state from exhaustion ratio."""
        ratio = budget.exhaustion_ratio()
        
        if ratio < FatigueCalculator.FRESH_THRESHOLD:
            return FatigueState.FRESH
        elif ratio < FatigueCalculator.NORMAL_THRESHOLD:
            return FatigueState.NORMAL
        elif ratio < FatigueCalculator.TIRED_THRESHOLD:
            return FatigueState.TIRED
        else:
            return FatigueState.EXHAUSTED
    
    @staticmethod
    def calculate_capacity_multiplier(state: FatigueState) -> float:
        """Get capacity multiplier for fatigue state."""
        return FatigueCalculator.CAPACITY_MULTIPLIERS.get(state, 1.0)
    
    @staticmethod
    def calculate_complexity_threshold(state: FatigueState) -> str:
        """Get complexity threshold for fatigue state."""
        return FatigueCalculator.COMPLEXITY_THRESHOLDS.get(state, "NONE")
    
    @staticmethod
    def calculate_fatigue_score(
        budget: DailyBudget,
        detailed_reasoning: bool = False
    ) -> FatigueScore:
        """Calculate complete fatigue assessment."""
        state = FatigueCalculator.calculate_fatigue_state(budget)
        ratio = budget.exhaustion_ratio()
        capacity = FatigueCalculator.calculate_capacity_multiplier(state)
        complexity = FatigueCalculator.calculate_complexity_threshold(state)
        
        # Generate recommendation
        recommendation = FatigueCalculator._get_recommendation(state, ratio)
        
        # Generate reasoning
        reasoning = FatigueCalculator._generate_reasoning(
            state, ratio, budget, detailed_reasoning
        )
        
        return FatigueScore(
            state=state,
            exhaustion_ratio=ratio,
            remaining_budget_minutes=budget.remaining_minutes(),
            capacity_multiplier=capacity,
            complexity_threshold=complexity,
            recommendation=recommendation,
            reasoning=reasoning
        )
    
    @staticmethod
    def _get_recommendation(state: FatigueState, ratio: float) -> str:
        """Get recommendation based on fatigue state."""
        recommendations = {
            FatigueState.FRESH: "Accept challenging missions; full capacity",
            FatigueState.NORMAL: "Accept medium-complexity missions; normal pace",
            FatigueState.TIRED: "Accept only simple, quick missions; consider break",
            FatigueState.EXHAUSTED: "HARD STOP: No new missions; take substantial break",
        }
        return recommendations.get(state, "Unknown state")
    
    @staticmethod
    def _generate_reasoning(
        state: FatigueState,
        ratio: float,
        budget: DailyBudget,
        detailed: bool = False
    ) -> List[str]:
        """Generate reasoning for fatigue score."""
        reasons = []
        
        # Budget status
        used_pct = int(ratio * 100)
        remaining = budget.remaining_minutes()
        reasons.append(f"Used {used_pct}% of daily budget ({budget.used_minutes}/{budget.total_minutes} min)")
        
        if remaining > 0:
            reasons.append(f"{remaining} minutes remaining in budget")
        else:
            reasons.append("Budget exhausted; no remaining capacity")
        
        # State-specific reasoning
        if state == FatigueState.FRESH:
            reasons.append("Fresh start: accept complex, high-value work")
        elif state == FatigueState.NORMAL:
            reasons.append("Normal pace: balance complexity and capability")
        elif state == FatigueState.TIRED:
            reasons.append("Fatigue setting in: focus on high-ROI simple tasks")
        elif state == FatigueState.EXHAUSTED:
            reasons.append("Severe fatigue: human needs substantial break")
            reasons.append("Risk of poor decisions and errors if work continues")
        
        # Capacity impact
        capacity_pct = int(FatigueCalculator.CAPACITY_MULTIPLIERS[state] * 100)
        if detailed:
            reasons.append(f"Effective capacity at {capacity_pct}% of normal")
        
        return reasons
    
    @staticmethod
    def adjust_roi_for_fatigue(
        base_roi: float,
        fatigue_score: FatigueScore
    ) -> float:
        """Adjust ROI based on fatigue state (lower ROI when fatigued)."""
        return base_roi * fatigue_score.capacity_multiplier
    
    @staticmethod
    def get_quality_impact(state: FatigueState) -> Dict[str, float]:
        """Get quality degradation factors for fatigue state."""
        impacts = {
            FatigueState.FRESH: {
                "error_rate": 0.02,        # 2% error rate
                "decision_quality": 1.0,   # Full quality
                "focus": 1.0,              # Full focus
            },
            FatigueState.NORMAL: {
                "error_rate": 0.05,        # 5% error rate
                "decision_quality": 0.95,
                "focus": 0.90,
            },
            FatigueState.TIRED: {
                "error_rate": 0.15,        # 15% error rate
                "decision_quality": 0.80,
                "focus": 0.70,
            },
            FatigueState.EXHAUSTED: {
                "error_rate": 0.40,        # 40% error rate (very high!)
                "decision_quality": 0.50,
                "focus": 0.30,
            },
        }
        return impacts.get(state, impacts[FatigueState.NORMAL])
    
    @staticmethod
    def estimate_recovery_time(state: FatigueState) -> Tuple[int, str]:
        """Estimate time needed to recover from fatigue state (in minutes)."""
        recovery_times = {
            FatigueState.FRESH: (0, "No recovery needed"),
            FatigueState.NORMAL: (15, "Short break recommended (15 min)"),
            FatigueState.TIRED: (45, "Substantial break needed (30-45 min)"),
            FatigueState.EXHAUSTED: (180, "Extended break required (3+ hours or end of day)"),
        }
        minutes, message = recovery_times.get(state, (0, "Unknown"))
        return minutes, message
