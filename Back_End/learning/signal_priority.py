"""
Signal Prioritization

Adds priority tiers to learning signals to prevent saturation.
Defaults are determined by signal_type.
"""

from __future__ import annotations

from typing import Dict, Any


SIGNAL_PRIORITY_DEFAULTS: Dict[str, str] = {
    # Critical alerts
    "drift_warning": "CRITICAL",
    "mission_failed": "CRITICAL",

    # Economic signals
    "opportunity_normalized": "ECONOMIC",
    "mission_cost_report": "ECONOMIC",

    # Important mission outcomes
    "mission_status_update": "IMPORTANT",
    "mission_completed": "IMPORTANT",
    "mission_progress_update": "IMPORTANT",
    "mission_ambiguous": "IMPORTANT",
    "goal_evaluation": "IMPORTANT",
    "expectation_delta": "IMPORTANT",

    # Goal/program registry
    "goal_created": "IMPORTANT",
    "goal_updated": "IMPORTANT",
    "program_created": "IMPORTANT",
    "program_updated": "IMPORTANT",
    "mission_linked": "IMPORTANT",

    # Informational instrumentation
    "selector_outcome": "INFO",
    "selector_aggregate": "INFO",
    "navigation_intent_ranked": "INFO",
    "intent_action_taken": "INFO",
    "decision_rationale": "INFO"
}


def apply_signal_priority(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Attach signal_priority to signal if missing."""
    if "signal_priority" in signal:
        return signal

    signal_type = signal.get("signal_type")
    signal["signal_priority"] = SIGNAL_PRIORITY_DEFAULTS.get(signal_type, "INFO")
    return signal

