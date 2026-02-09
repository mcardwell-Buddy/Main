"""
Phase 8: Tradeoff Evaluator

Determines whether work is worth doing based on economic reasoning:
- Time cost vs potential payoff
- Cognitive load vs expected value
- Reusability / compounding value
- Opportunity cost

Output: proceed / pause / reject decision with justification

Hard constraints:
- NO autonomy (advisory only)
- NO auto-escalation
- NO mission killing (suggest, don't enforce)
- NO learning loops
- READ-ONLY analysis
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


class TradeoffDecision(Enum):
    """Tradeoff decision recommendations."""
    PROCEED = "PROCEED"
    PAUSE = "PAUSE"
    REJECT = "REJECT"


class CognitiveLoad(Enum):
    """Cognitive load levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ValueType(Enum):
    """Types of value from work."""
    ONE_TIME = "ONE_TIME"
    REUSABLE = "REUSABLE"
    COMPOUNDING = "COMPOUNDING"


@dataclass(frozen=True)
class TradeoffScore:
    """Immutable tradeoff scoring."""
    # Cost factors
    time_cost_minutes: int
    cognitive_load: CognitiveLoad
    
    # Benefit factors
    estimated_payoff_minutes: int  # Time saved or value created
    value_type: ValueType
    
    # Calculations
    roi_ratio: float  # payoff / cost
    opportunity_cost_score: float  # 0.0 - 1.0 (how much is being given up)
    reuse_multiplier: float  # 1.0x to 3.0x based on compounding
    
    # Final
    adjusted_value: float  # Final calculated value
    decision: TradeoffDecision
    confidence: float
    
    # Reasoning
    rationale: str
    key_factors: List[str] = field(default_factory=list)


@dataclass
class TradeoffOpportunity:
    """Work opportunity for tradeoff analysis."""
    name: str
    description: str
    estimated_effort_minutes: int
    estimated_payoff_minutes: int  # Or relative value
    cognitive_load: CognitiveLoad
    value_type: ValueType = ValueType.ONE_TIME
    urgency: str = "normal"  # low, normal, high, critical
    depends_on: Optional[List[str]] = None
    blocked_by: Optional[List[str]] = None
    repeatable: bool = False
    learning_value: bool = False


class TradeoffScoringRubric:
    """
    Deterministic scoring rubric for economic tradeoff analysis.
    
    Factors considered:
    1. Time Investment vs Payoff (ROI)
    2. Cognitive Load Impact
    3. Value Type (one-time vs compounding)
    4. Opportunity Cost (what else could be done?)
    5. Strategic Value (learning, reusability)
    
    Decision Thresholds:
    - PROCEED: ROI >= 1.5 AND cognitive load acceptable
    - PAUSE: 0.5 <= ROI < 1.5 OR high cognitive load
    - REJECT: ROI < 0.5 OR critical cognitive load
    """

    # Cognitive load cost multipliers
    COGNITIVE_LOAD_MULTIPLIER = {
        CognitiveLoad.LOW: 0.8,      # Pleasant, energizing
        CognitiveLoad.MEDIUM: 1.0,   # Normal baseline
        CognitiveLoad.HIGH: 1.5,     # Draining, need recovery
        CognitiveLoad.CRITICAL: 3.0, # Unsustainable
    }

    # Value type reuse multipliers
    VALUE_TYPE_MULTIPLIER = {
        ValueType.ONE_TIME: 1.0,         # Single use only
        ValueType.REUSABLE: 1.5,         # Can be reused
        ValueType.COMPOUNDING: 2.0,      # Creates momentum, future value
    }

    # Urgency multipliers (time pressure effect)
    URGENCY_MULTIPLIER = {
        "low": 0.7,
        "normal": 1.0,
        "high": 1.2,
        "critical": 1.5,
    }

    # Decision thresholds
    PROCEED_THRESHOLD = 1.5
    PAUSE_THRESHOLD_MIN = 0.5
    PAUSE_THRESHOLD_MAX = 1.5
    REJECT_THRESHOLD = 0.5

    @staticmethod
    def calculate_roi(payoff: int, cost: int) -> float:
        """
        Calculate ROI ratio.
        
        ROI = (Payoff - Cost) / Cost
        Or simplified: Payoff / Cost (ratio)
        
        Examples:
        - 100 min payoff, 50 min cost = 2.0 ROI (great)
        - 100 min payoff, 100 min cost = 1.0 ROI (break-even)
        - 100 min payoff, 200 min cost = 0.5 ROI (poor)
        """
        if cost <= 0:
            return 0.0
        return payoff / cost

    @staticmethod
    def calculate_opportunity_cost_score(
        time_cost: int,
        total_available_time: int = 480  # 8-hour workday
    ) -> float:
        """
        Calculate opportunity cost (0.0 - 1.0).
        
        What % of available time is this consuming?
        
        Args:
            time_cost: Minutes for this task
            total_available_time: Total available (default 8 hours)
        
        Returns:
            Score 0.0 (none) to 1.0 (all time)
        """
        if total_available_time <= 0:
            return 0.0
        ratio = time_cost / total_available_time
        return min(ratio, 1.0)

    @staticmethod
    def is_worth_the_effort(
        roi_ratio: float,
        cognitive_load: CognitiveLoad,
        urgency: str = "normal"
    ) -> bool:
        """Simple decision: worth it or not?"""
        # Critical cognitive load = automatic no
        if cognitive_load == CognitiveLoad.CRITICAL:
            return False
        
        # High cognitive load requires higher ROI
        if cognitive_load == CognitiveLoad.HIGH:
            return roi_ratio >= 2.0
        
        # Normal threshold
        return roi_ratio >= TradeoffScoringRubric.PROCEED_THRESHOLD


class TradeoffEvaluator:
    """
    Evaluates whether work is worth doing based on economic reasoning.
    
    Advisory only - does not make decisions, provides analysis.
    """

    def __init__(self):
        """Initialize tradeoff evaluator."""
        self._rubric = TradeoffScoringRubric()

    def evaluate(self, opportunity: TradeoffOpportunity) -> TradeoffScore:
        """
        Evaluate a work opportunity.

        Args:
            opportunity: TradeoffOpportunity with effort/payoff estimates

        Returns:
            TradeoffScore with decision and reasoning
        """
        # Calculate base ROI
        roi_ratio = self._rubric.calculate_roi(
            opportunity.estimated_payoff_minutes,
            opportunity.estimated_effort_minutes
        )

        # Calculate opportunity cost
        opp_cost = self._rubric.calculate_opportunity_cost_score(
            opportunity.estimated_effort_minutes
        )

        # Apply cognitive load multiplier to cost
        cognitive_multiplier = self._rubric.COGNITIVE_LOAD_MULTIPLIER[
            opportunity.cognitive_load
        ]

        # Apply value type multiplier
        value_multiplier = self._rubric.VALUE_TYPE_MULTIPLIER[
            opportunity.value_type
        ]

        # Apply urgency multiplier
        urgency_mult = self._rubric.URGENCY_MULTIPLIER.get(
            opportunity.urgency.lower(),
            1.0
        )

        # Calculate adjusted ROI (accounting for cognitive load)
        adjusted_roi = roi_ratio / cognitive_multiplier

        # Apply reuse/compounding multiplier
        reuse_multiplier = value_multiplier

        # Final adjusted value (accounts for all factors)
        final_value = adjusted_roi * reuse_multiplier * urgency_mult

        # Determine decision
        decision = self._make_decision(
            adjusted_roi,
            cognitive_multiplier,
            opportunity.cognitive_load,
            final_value
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            roi_ratio,
            opportunity.estimated_effort_minutes,
            opportunity.estimated_payoff_minutes
        )

        # Generate reasoning
        rationale, key_factors = self._generate_reasoning(
            opportunity,
            roi_ratio,
            adjusted_roi,
            final_value,
            decision,
            cognitive_multiplier,
            reuse_multiplier
        )

        return TradeoffScore(
            time_cost_minutes=opportunity.estimated_effort_minutes,
            cognitive_load=opportunity.cognitive_load,
            estimated_payoff_minutes=opportunity.estimated_payoff_minutes,
            value_type=opportunity.value_type,
            roi_ratio=roi_ratio,
            opportunity_cost_score=opp_cost,
            reuse_multiplier=reuse_multiplier,
            adjusted_value=final_value,
            decision=decision,
            confidence=confidence,
            rationale=rationale,
            key_factors=key_factors
        )

    def _make_decision(
        self,
        adjusted_roi: float,
        cognitive_multiplier: float,
        cognitive_load: CognitiveLoad,
        final_value: float
    ) -> TradeoffDecision:
        """Determine proceed/pause/reject."""
        # Automatic reject for critical cognitive load
        if cognitive_load == CognitiveLoad.CRITICAL:
            return TradeoffDecision.REJECT

        # Check final adjusted value
        if final_value >= self._rubric.PROCEED_THRESHOLD:
            return TradeoffDecision.PROCEED
        elif final_value >= self._rubric.PAUSE_THRESHOLD_MIN:
            return TradeoffDecision.PAUSE
        else:
            return TradeoffDecision.REJECT

    def _calculate_confidence(
        self,
        roi_ratio: float,
        effort_estimate: int,
        payoff_estimate: int
    ) -> float:
        """
        Calculate confidence in the decision (0.0 - 1.0).
        
        Higher confidence when:
        - Both estimates are moderate (not extreme)
        - ROI is far from decision boundaries
        - Estimates are reasonable scale
        """
        # Estimates too extreme = low confidence
        if effort_estimate < 5 or payoff_estimate < 5:
            confidence_penalty = 0.3  # Very rough estimates
        elif effort_estimate > 480 or payoff_estimate > 480:
            confidence_penalty = 0.2  # Estimates beyond normal workday
        else:
            confidence_penalty = 0.0

        # ROI far from boundaries = high confidence
        if roi_ratio < 0.3 or roi_ratio > 3.0:
            confidence_boost = 0.2  # Clear-cut decision
        elif roi_ratio > 1.0:
            confidence_boost = 0.1  # Good ROI
        else:
            confidence_boost = -0.1  # Marginal

        base_confidence = 0.7
        return max(0.4, min(0.95, base_confidence + confidence_boost - confidence_penalty))

    def _generate_reasoning(
        self,
        opportunity: TradeoffOpportunity,
        roi_ratio: float,
        adjusted_roi: float,
        final_value: float,
        decision: TradeoffDecision,
        cognitive_multiplier: float,
        reuse_multiplier: float
    ) -> tuple:
        """Generate human-readable reasoning."""
        lines = []
        key_factors = []

        # Decision statement
        if decision == TradeoffDecision.PROCEED:
            lines.append(f"Worth doing: ROI {adjusted_roi:.2f}x after cognitive load adjustment")
            lines.append("Net payoff justifies time investment.")
        elif decision == TradeoffDecision.PAUSE:
            lines.append(f"Marginal value: ROI {adjusted_roi:.2f}x is borderline")
            lines.append("Consider deferring until higher-value opportunities complete.")
        else:  # REJECT
            if opportunity.cognitive_load == CognitiveLoad.CRITICAL:
                lines.append("CRITICAL cognitive load: Not recommended for current context")
                key_factors.append("excessive_cognitive_load")
            else:
                lines.append(f"Poor ROI: {adjusted_roi:.2f}x adjusted ({roi_ratio:.2f}x raw)")
                lines.append("Payoff insufficient to justify time investment.")

        # Key factors
        lines.append("\nFactors:")
        
        raw_roi_text = f"Raw ROI {roi_ratio:.2f}x ({opportunity.estimated_payoff_minutes}m payoff / {opportunity.estimated_effort_minutes}m cost)"
        lines.append(f"  • {raw_roi_text}")
        key_factors.append(f"raw_roi_{roi_ratio:.1f}")

        cognitive_text = f"Cognitive load: {opportunity.cognitive_load.value} (×{cognitive_multiplier:.1f})"
        lines.append(f"  • {cognitive_text}")
        key_factors.append(f"cognitive_{opportunity.cognitive_load.value}")

        value_text = f"Value type: {opportunity.value_type.value} (×{reuse_multiplier:.1f})"
        lines.append(f"  • {value_text}")
        key_factors.append(f"value_{opportunity.value_type.value}")

        urgency_mult = self._rubric.URGENCY_MULTIPLIER.get(
            opportunity.urgency.lower(), 1.0
        )
        urgency_text = f"Urgency: {opportunity.urgency}"
        lines.append(f"  • {urgency_text}")
        key_factors.append(f"urgency_{opportunity.urgency}")

        # Dependencies
        if opportunity.depends_on or opportunity.blocked_by:
            lines.append("\nConstraints:")
            if opportunity.depends_on:
                lines.append(f"  • Depends on: {', '.join(opportunity.depends_on)}")
                key_factors.append("has_dependencies")
            if opportunity.blocked_by:
                lines.append(f"  • Blocked by: {', '.join(opportunity.blocked_by)}")
                key_factors.append("has_blockers")

        rationale = "\n".join(lines)
        return rationale, key_factors

    def evaluate_multiple(
        self,
        opportunities: List[TradeoffOpportunity]
    ) -> List[TradeoffScore]:
        """Evaluate multiple opportunities and sort by value."""
        scores = [self.evaluate(opp) for opp in opportunities]
        # Sort by adjusted_value (descending)
        return sorted(scores, key=lambda s: s.adjusted_value, reverse=True)

    def get_quick_summary(self, score: TradeoffScore) -> str:
        """One-line summary."""
        if score.decision == TradeoffDecision.PROCEED:
            return f"PROCEED (ROI {score.adjusted_value:.2f}x)"
        elif score.decision == TradeoffDecision.PAUSE:
            return f"PAUSE (ROI {score.adjusted_value:.2f}x - marginal)"
        else:
            return f"REJECT (ROI {score.adjusted_value:.2f}x - insufficient value)"

    def get_full_summary(self, score: TradeoffScore) -> str:
        """Multi-line summary with details."""
        lines = [
            f"Decision: {score.decision.value}",
            f"Adjusted Value: {score.adjusted_value:.2f}x",
            f"ROI: {score.roi_ratio:.2f}x (raw) -> {score.roi_ratio / self._cognitive_multiplier_for_load(score.cognitive_load):.2f}x (adjusted)",
            f"Opportunity Cost: {score.opportunity_cost_score:.1%}",
            f"Confidence: {score.confidence:.0%}",
            f"\n{score.rationale}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _cognitive_multiplier_for_load(load: CognitiveLoad) -> float:
        """Get cognitive load multiplier."""
        return TradeoffScoringRubric.COGNITIVE_LOAD_MULTIPLIER[load]
