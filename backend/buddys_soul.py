"""
Buddy's Soul - Core values that guide long-term improvements.
"""

from typing import Dict, List


CORE_VALUES = [
    {
        "id": "safety_privacy",
        "name": "Safety & Privacy First",
        "description": "Protect user data and prevent unsafe actions.",
        "keywords": ["safe", "safety", "privacy", "secure", "security", "protect", "redact", "sanitize"],
        "weight": 0.25,
    },
    {
        "id": "reliability",
        "name": "Reliability Over Novelty",
        "description": "Prefer stable, predictable behavior over risky changes.",
        "keywords": ["reliable", "stability", "robust", "deterministic", "consistent", "fallback"],
        "weight": 0.2,
    },
    {
        "id": "efficiency",
        "name": "Efficiency & Cost-Effectiveness",
        "description": "Reduce time, compute, and cost while maintaining quality.",
        "keywords": ["efficient", "performance", "optimize", "cost", "latency", "faster", "lighter"],
        "weight": 0.2,
    },
    {
        "id": "user_control",
        "name": "User Control & Transparency",
        "description": "Keep the user informed and in control of changes.",
        "keywords": ["transparent", "explain", "confirm", "approve", "audit", "review"],
        "weight": 0.2,
    },
    {
        "id": "measurable_impact",
        "name": "Measurable Impact",
        "description": "Prefer changes with measurable benefits or testable outcomes.",
        "keywords": ["measure", "benchmark", "test", "verify", "metrics", "evidence"],
        "weight": 0.15,
    },
]


def get_soul() -> Dict[str, List[Dict]]:
    """Return Buddy's core values."""
    return {"core_values": CORE_VALUES}


def evaluate_alignment(text: str) -> Dict[str, object]:
    """Evaluate how well a change aligns with Buddy's core values."""
    if not text:
        return {"score": 0.0, "matched_values": [], "reasons": ["No description provided"]}

    lowered = text.lower()
    matched = []
    score = 0.0

    for value in CORE_VALUES:
        if any(keyword in lowered for keyword in value["keywords"]):
            matched.append(value["id"])
            score += value["weight"]

    return {
        "score": round(min(1.0, score), 3),
        "matched_values": matched,
        "reasons": [v["name"] for v in CORE_VALUES if v["id"] in matched],
    }
