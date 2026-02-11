"""Buddy Phase 10 Policy Updater.

Derives adaptive policy changes from prior outcomes and confidence metrics.
This module is additive and does not modify Phase 1–9 logic.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class PolicyState:
    high_risk_threshold: float = 0.8
    retry_multiplier: float = 1.0
    priority_bias: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PolicyUpdater:
    def __init__(self, initial_policy: PolicyState | None = None):
        self.policy = initial_policy or PolicyState()

    def update_from_outcomes(self, outcomes: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not outcomes:
            return {
                "policy": self.policy.to_dict(),
                "changes": [],
                "reason": "no outcomes"
            }

        total = len(outcomes)
        completed = sum(1 for o in outcomes if o.get("status") == "completed")
        deferred = sum(1 for o in outcomes if o.get("status") == "deferred")
        failed = sum(1 for o in outcomes if o.get("status") == "failed")

        success_rate = completed / total if total else 0.0
        deferred_rate = deferred / total if total else 0.0
        failed_rate = failed / total if total else 0.0

        changes = []

        if failed_rate > 0.2:
            self.policy.retry_multiplier = min(2.0, self.policy.retry_multiplier + 0.2)
            changes.append("increase_retry_multiplier")

        if deferred_rate > 0.3:
            self.policy.high_risk_threshold = min(0.9, self.policy.high_risk_threshold + 0.05)
            changes.append("tighten_high_risk_threshold")

        if success_rate > 0.85:
            self.policy.priority_bias = min(1.5, self.policy.priority_bias + 0.05)
            changes.append("increase_priority_bias")

        return {
            "policy": self.policy.to_dict(),
            "changes": changes,
            "reason": "adaptive_update",
            "metrics": {
                "success_rate": success_rate,
                "deferred_rate": deferred_rate,
                "failed_rate": failed_rate
            }
        }

