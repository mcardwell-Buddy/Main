"""
Ambiguity Evaluator: Detects unclear mission outcomes requiring human judgment.
Purely deterministic rules - no LLM, no autonomy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class AmbiguityEvaluation:
    """Result of ambiguity evaluation."""
    ambiguous: bool
    reason: str
    recommended_next_mission: Optional[str]
    confidence_gap: float
    opportunity_weakness: float
    evidence_sufficiency: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ambiguous": self.ambiguous,
            "reason": self.reason,
            "recommended_next_mission": self.recommended_next_mission,
            "confidence_gap": self.confidence_gap,
            "opportunity_weakness": self.opportunity_weakness,
            "evidence_sufficiency": self.evidence_sufficiency,
            "timestamp": self.timestamp
        }

    def to_signal(self, mission_id: str) -> Dict[str, Any]:
        """Convert to learning signal format."""
        return {
            "signal_type": "mission_ambiguous",
            "signal_layer": "mission",
            "signal_source": "ambiguity_evaluator",
            "mission_id": mission_id,
            "ambiguous": self.ambiguous,
            "reason": self.reason,
            "recommended_next_mission": self.recommended_next_mission,
            "confidence_gap": self.confidence_gap,
            "opportunity_weakness": self.opportunity_weakness,
            "evidence_sufficiency": self.evidence_sufficiency,
            "timestamp": self.timestamp
        }


class AmbiguityEvaluator:
    """
    Evaluates whether mission outcomes are ambiguous.
    
    Ambiguity occurs when:
    - Goal confidence is below threshold
    - Opportunities exist but are weak (low confidence)
    - Evidence is insufficient to make clear decision
    
    Purely deterministic - no LLM, no autonomy.
    """

    def __init__(
        self,
        goal_confidence_threshold: float = 0.6,
        opportunity_confidence_threshold: float = 0.65,
        evidence_minimum_items: int = 3
    ):
        """
        Initialize ambiguity evaluator with thresholds.
        
        Args:
            goal_confidence_threshold: Below this, goal satisfaction is unclear
            opportunity_confidence_threshold: Below this, opportunities are weak
            evidence_minimum_items: Minimum items for sufficient evidence
        """
        self.goal_confidence_threshold = goal_confidence_threshold
        self.opportunity_confidence_threshold = opportunity_confidence_threshold
        self.evidence_minimum_items = evidence_minimum_items

    def evaluate(
        self,
        mission_id: str,
        goal_evaluation: Optional[Dict[str, Any]],
        opportunity_summary: Optional[Dict[str, Any]],
        items_collected: int,
        mission_status: str
    ) -> AmbiguityEvaluation:
        """
        Evaluate whether mission outcome is ambiguous.
        
        Args:
            mission_id: Mission identifier
            goal_evaluation: Goal satisfaction evaluation result
            opportunity_summary: Opportunity normalization summary
            items_collected: Number of items collected
            mission_status: Mission final status (completed, failed, etc)
        
        Returns:
            AmbiguityEvaluation with ambiguity determination
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Extract metrics
        goal_confidence = (goal_evaluation or {}).get("confidence", 0.0)
        goal_satisfied = (goal_evaluation or {}).get("goal_satisfied", False)
        
        opportunities_created = (opportunity_summary or {}).get("opportunities_created", 0)
        avg_opportunity_confidence = (opportunity_summary or {}).get("avg_confidence", 0.0)
        
        # Calculate gaps
        confidence_gap = self.goal_confidence_threshold - goal_confidence
        opportunity_weakness = self.opportunity_confidence_threshold - avg_opportunity_confidence
        evidence_sufficiency = items_collected / self.evidence_minimum_items if self.evidence_minimum_items > 0 else 0.0
        
        # Ambiguity detection rules (deterministic - ordered by specificity)
        ambiguous = False
        reason = "clear_outcome"
        recommended_next_mission = None
        
        # Rule 1: Insufficient/no evidence (highest priority - most specific)
        if items_collected < self.evidence_minimum_items and mission_status == "completed":
            if items_collected == 0:
                ambiguous = True
                reason = "no_evidence_collected"
                recommended_next_mission = "retry_with_different_approach"
            else:
                ambiguous = True
                reason = "insufficient_evidence"
                recommended_next_mission = "continuation_mission"
        
        # Rule 2: Low goal confidence but mission succeeded (only if not already ambiguous)
        if not ambiguous and mission_status == "completed" and goal_confidence < self.goal_confidence_threshold:
            if not goal_satisfied:
                ambiguous = True
                reason = "low_goal_confidence_despite_completion"
                recommended_next_mission = "retry_with_refined_objective"
            elif goal_confidence < 0.3:
                ambiguous = True
                reason = "very_low_confidence_needs_verification"
                recommended_next_mission = "verification_mission"
        
        # Rule 3: Opportunities created but all are weak (only if not already ambiguous)
        if not ambiguous and opportunities_created > 0 and avg_opportunity_confidence < self.opportunity_confidence_threshold:
            if opportunities_created >= 5:
                ambiguous = True
                reason = "many_weak_opportunities_need_filtering"
                recommended_next_mission = "enrichment_mission"
            else:
                ambiguous = True
                reason = "weak_opportunities_low_quality"
                recommended_next_mission = "quality_verification_mission"
        
        # Rule 4: Mixed signals - goal satisfied but no opportunities (only if not already ambiguous)
        if not ambiguous and goal_satisfied and opportunities_created == 0 and items_collected > 0:
            ambiguous = True
            reason = "goal_satisfied_but_no_opportunities_identified"
            recommended_next_mission = "opportunity_identification_mission"
        
        # Rule 5: Mission failed but some opportunities found (only if not already ambiguous)
        if not ambiguous and mission_status == "failed" and opportunities_created > 0:
            ambiguous = True
            reason = "mission_failed_but_opportunities_exist"
            recommended_next_mission = "salvage_mission"
        
        # Rule 6: Goal unsatisfied but high confidence (only if not already ambiguous)
        if not ambiguous and not goal_satisfied and goal_confidence >= 0.8 and items_collected > 0:
            ambiguous = True
            reason = "high_confidence_but_goal_unsatisfied"
            recommended_next_mission = "objective_refinement_needed"
        
        return AmbiguityEvaluation(
            ambiguous=ambiguous,
            reason=reason,
            recommended_next_mission=recommended_next_mission,
            confidence_gap=max(0.0, confidence_gap),
            opportunity_weakness=max(0.0, opportunity_weakness),
            evidence_sufficiency=evidence_sufficiency,
            timestamp=timestamp
        )

    def should_emit_signal(self, evaluation: AmbiguityEvaluation) -> bool:
        """Determine if ambiguity signal should be emitted."""
        return evaluation.ambiguous

