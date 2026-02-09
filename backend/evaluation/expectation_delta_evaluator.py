"""
Phase 4 Step 2: Expectation Delta Evaluation

Read-only evaluator that captures whether mission outcomes matched user expectations.
This provides human-alignment feedback without modifying execution behavior.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, Literal
from datetime import datetime, timezone
import json
from pathlib import Path

from backend.learning.signal_priority import apply_signal_priority


AlignmentType = Literal["aligned", "misaligned", "unclear"]


class ExpectationDeltaEvaluator:
    """
    Evaluates alignment between mission outcomes and user expectations.
    
    This is a read-only observational system that:
    - Analyzes mission objectives vs actual outcomes
    - Detects expectation mismatches
    - Provides alignment signals for learning
    
    Does NOT:
    - Trigger retries or corrective actions
    - Modify mission execution
    - Make autonomous decisions
    """
    
    def __init__(self, signals_file: Optional[Path] = None):
        """Initialize evaluator with signal output file."""
        if signals_file is None:
            output_dir = Path(__file__).parent.parent.parent / "outputs" / "phase25"
            output_dir.mkdir(parents=True, exist_ok=True)
            signals_file = output_dir / "learning_signals.jsonl"
        
        self.signals_file = signals_file
    
    def evaluate(
        self,
        mission_id: str,
        objective: Dict[str, Any],
        outcome_summary: Dict[str, Any],
        mission_thread_id: Optional[str] = None,
        user_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate expectation alignment for a completed mission.
        
        Args:
            mission_id: Unique mission identifier
            objective: Mission objective dict with type, description, target, etc.
            outcome_summary: Mission outcome with status, items_collected, reason
            mission_thread_id: Optional thread linking related missions
            user_feedback: Optional explicit user feedback (future extension)
        
        Returns:
            Expectation delta signal dict
        """
        # Determine alignment based on objective vs outcome
        alignment, confidence, reason = self._analyze_alignment(
            objective, outcome_summary
        )
        
        # Build signal
        signal = {
            "signal_type": "expectation_delta",
            "signal_layer": "evaluation",
            "signal_source": "expectation_delta_evaluator",
            "mission_id": mission_id,
            "alignment": alignment,
            "confidence": confidence,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Include thread_id if present
        if mission_thread_id:
            signal["mission_thread_id"] = mission_thread_id
        
        # Include user feedback if provided
        if user_feedback:
            signal["user_feedback"] = user_feedback
        
        # Persist signal
        self._emit_signal(apply_signal_priority(signal))
        
        return signal
    
    def _analyze_alignment(
        self,
        objective: Dict[str, Any],
        outcome: Dict[str, Any]
    ) -> tuple[AlignmentType, float, str]:
        """
        Analyze alignment between objective and outcome.
        
        Returns:
            (alignment_type, confidence, reason)
        """
        status = outcome.get("status", "unknown")
        items_collected = outcome.get("items_collected", 0)
        reason = outcome.get("reason", "")
        
        objective_type = objective.get("type", "")
        target = objective.get("target")
        description = objective.get("description", "")
        
        # Case 1: Mission completed with items collected
        if status == "completed" and items_collected > 0:
            if target and items_collected >= target:
                return (
                    "aligned",
                    0.9,
                    f"Collected {items_collected} items, met target of {target}"
                )
            elif target and items_collected < target:
                return (
                    "misaligned",
                    0.7,
                    f"Collected {items_collected} items, below target of {target}"
                )
            else:
                # No explicit target, but items collected
                return (
                    "aligned",
                    0.7,
                    f"Collected {items_collected} items, no specific target set"
                )
        
        # Case 2: Mission completed but zero items
        if status == "completed" and items_collected == 0:
            if objective_type == "data_collection":
                return (
                    "misaligned",
                    0.8,
                    "Mission completed but no data collected (expected data collection)"
                )
            else:
                # Non-data-collection mission
                return (
                    "unclear",
                    0.5,
                    "Mission completed with zero items, objective unclear"
                )
        
        # Case 3: Mission failed
        if status == "failed":
            if "no_progress" in reason:
                return (
                    "misaligned",
                    0.9,
                    "Mission failed: no progress made"
                )
            elif "navigation_blocked" in reason:
                return (
                    "misaligned",
                    0.8,
                    "Mission failed: navigation blocked"
                )
            elif "required_fields_missing" in reason:
                return (
                    "misaligned",
                    0.8,
                    "Mission failed: required fields missing"
                )
            else:
                return (
                    "misaligned",
                    0.7,
                    f"Mission failed: {reason}"
                )
        
        # Case 4: Mission aborted
        if status == "aborted":
            if "max_duration_exceeded" in reason:
                return (
                    "misaligned",
                    0.6,
                    "Mission aborted: timeout (may have been progressing)"
                )
            else:
                return (
                    "misaligned",
                    0.8,
                    f"Mission aborted: {reason}"
                )
        
        # Case 5: Mission still active (shouldn't evaluate yet)
        if status == "active" or status == "created":
            return (
                "unclear",
                0.3,
                f"Mission status: {status} (evaluation premature)"
            )
        
        # Default: unclear
        return (
            "unclear",
            0.4,
            f"Unable to determine alignment (status: {status})"
        )
    
    def _emit_signal(self, signal: Dict[str, Any]) -> None:
        """Write signal to learning_signals.jsonl."""
        with open(self.signals_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(signal) + "\n")
