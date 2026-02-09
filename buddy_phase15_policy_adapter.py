"""
Phase 15: Policy Adapter

Continuously monitors execution outcomes and adapts policies dynamically
based on real-time performance metrics and meta-learning insights.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple
from pathlib import Path
from collections import defaultdict
import statistics


@dataclass
class PolicyUpdate:
    """Policy state change."""
    wave: int
    timestamp: str
    old_policy: Dict[str, float]
    new_policy: Dict[str, float]
    trigger: str  # Reason for change
    metrics: Dict[str, float]  # Supporting metrics


class PolicyAdapter:
    """Adapts policies based on execution outcomes."""

    def __init__(self, initial_policy: Dict[str, float], output_dir: str = "outputs/phase15"):
        self.current_policy = initial_policy.copy()
        self.initial_policy = initial_policy.copy()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.policy_history: List[PolicyUpdate] = []
        self.execution_metrics: Dict[str, List[float]] = defaultdict(list)

    def record_wave_metrics(self, wave: int, outcomes: List[Any], insights: List[Any]) -> None:
        """Record metrics from wave execution for policy adaptation."""
        if not outcomes:
            return

        # Calculate metrics
        completed = sum(1 for o in outcomes if o.status.value == "completed") if outcomes else 0
        failed = sum(1 for o in outcomes if o.status.value == "failed") if outcomes else 0
        deferred = sum(1 for o in outcomes if o.status.value == "deferred") if outcomes else 0
        rolled_back = sum(1 for o in outcomes if o.status.value == "rolled_back") if outcomes else 0

        total = len(outcomes) if outcomes else 1
        success_rate = completed / total if total > 0 else 0.0
        failure_rate = (failed + rolled_back) / total if total > 0 else 0.0
        deferral_rate = deferred / total if total > 0 else 0.0

        # Store metrics
        self.execution_metrics[f"wave_{wave}_success"] = success_rate
        self.execution_metrics[f"wave_{wave}_failure"] = failure_rate
        self.execution_metrics[f"wave_{wave}_deferral"] = deferral_rate

        # Evaluate policy adaptation needs
        self._adapt_policy_from_metrics(wave, success_rate, failure_rate, deferral_rate)

    def _adapt_policy_from_metrics(self, wave: int, success_rate: float, failure_rate: float, deferral_rate: float) -> None:
        """Adapt policy based on execution metrics."""
        old_policy = self.current_policy.copy()
        trigger_reasons = []
        metrics = {
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "deferral_rate": deferral_rate,
        }

        # Adaptation Rule 1: High failure rate → increase retry_multiplier
        if failure_rate > 0.20:
            self.current_policy["retry_multiplier"] = min(
                self.current_policy.get("retry_multiplier", 1.0) + 0.1, 2.0
            )
            trigger_reasons.append(f"High failure rate ({failure_rate*100:.1f}%)")

        # Adaptation Rule 2: High deferral rate → increase high_risk_threshold
        if deferral_rate > 0.30:
            self.current_policy["high_risk_threshold"] = min(
                self.current_policy.get("high_risk_threshold", 0.8) + 0.05, 0.95
            )
            trigger_reasons.append(f"High deferral rate ({deferral_rate*100:.1f}%)")

        # Adaptation Rule 3: High success rate → increase priority_bias (optimize for speed)
        if success_rate > 0.85:
            self.current_policy["priority_bias"] = min(
                self.current_policy.get("priority_bias", 1.0) + 0.05, 2.0
            )
            trigger_reasons.append(f"High success rate ({success_rate*100:.1f}%)")

        # Adaptation Rule 4: Low success rate → decrease priority_bias (be more conservative)
        if success_rate < 0.60:
            self.current_policy["priority_bias"] = max(
                self.current_policy.get("priority_bias", 1.0) - 0.1, 0.5
            )
            trigger_reasons.append(f"Low success rate ({success_rate*100:.1f}%)")

        # Log policy update if any changes made
        if trigger_reasons and old_policy != self.current_policy:
            update = PolicyUpdate(
                wave=wave,
                timestamp=str(wave),
                old_policy=old_policy,
                new_policy=self.current_policy.copy(),
                trigger=" | ".join(trigger_reasons),
                metrics=metrics,
            )
            self.policy_history.append(update)

    def apply_meta_insights(self, insights: List[Any]) -> None:
        """Apply meta-learning insights to policy."""
        for insight in insights:
            if not hasattr(insight, 'insight_type'):
                continue

            # Apply confidence-boosting insights
            if insight.insight_type == "success_pattern" and insight.confidence > 0.8:
                self.current_policy["priority_bias"] = min(
                    self.current_policy.get("priority_bias", 1.0) + 0.02, 2.0
                )

    def get_current_policy(self) -> Dict[str, float]:
        """Return current policy state."""
        return self.current_policy.copy()

    def get_policy_history(self) -> List[PolicyUpdate]:
        """Return all policy updates."""
        return self.policy_history

    def write_policy_updates(self) -> None:
        """Write policy update history."""
        with open(self.output_dir / "policy_updates.jsonl", "w") as f:
            for update in self.policy_history:
                f.write(json.dumps(asdict(update)) + "\n")

    def get_summary(self) -> Dict[str, Any]:
        """Get policy adaptation summary."""
        return {
            "initial_policy": self.initial_policy,
            "current_policy": self.current_policy,
            "updates_count": len(self.policy_history),
            "policy_changes": {
                "high_risk_threshold": self.current_policy.get("high_risk_threshold", 0.8)
                - self.initial_policy.get("high_risk_threshold", 0.8),
                "retry_multiplier": self.current_policy.get("retry_multiplier", 1.0)
                - self.initial_policy.get("retry_multiplier", 1.0),
                "priority_bias": self.current_policy.get("priority_bias", 1.0)
                - self.initial_policy.get("priority_bias", 1.0),
            },
        }
