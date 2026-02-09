"""
Buddy's Discovery - Ask for unknowns and propose improvement ideas.
Generates clarifying questions and idea seeds aligned with Buddy's Soul.
"""

from typing import Dict, List, Optional
from backend.buddys_soul import evaluate_alignment


DEFAULT_QUESTION_THEMES = [
    "current pain points",
    "workflow bottlenecks",
    "data quality issues",
    "manual steps",
    "error-prone areas",
    "slow response times",
    "cost drivers",
    "user drop-off points",
    "compliance or audit needs",
    "integration gaps",
    "reporting blind spots",
    "scaling constraints",
]

DEFAULT_IDEA_SEEDS = [
    "Automate repetitive steps with clear checkpoints and user approval",
    "Add lightweight validation to prevent downstream errors",
    "Introduce a simple dashboard with key metrics and alerts",
    "Cache expensive operations to reduce cost and latency",
    "Add retry and fallback logic for critical workflows",
    "Create a guided onboarding flow with autofill and confirmation",
    "Standardize data fields to improve matching and reporting",
    "Add a feedback loop to measure outcomes and refine rules",
    "Reduce steps in high-frequency tasks to improve efficiency",
    "Centralize credentials and profile data with least-privilege access",
]


def discover_unknowns(goal: str = "", domain: str = "", context: Optional[Dict] = None) -> Dict:
    """
    Generate clarifying questions and idea seeds to surface unknowns.
    Returns an alignment score based on Buddy's Soul.
    """
    context = context or {}

    questions = [
        f"What is the single biggest pain point in {domain or 'this workflow'} right now?",
        "Which step is most error-prone or frequently reworked?",
        "Where are we losing time, money, or leads?",
        "What data is missing or unreliable for decisions?",
        "What should never happen (safety, privacy, compliance)?",
        "Which outcomes matter most: speed, cost, accuracy, or conversions?",
        "What would a 10x improvement look like in measurable terms?",
    ]

    # Add theme-based questions
    questions.extend([f"Do we have visibility into {theme}?" for theme in DEFAULT_QUESTION_THEMES[:6]])

    # Create idea seeds, then score alignment
    ideas = []
    for seed in DEFAULT_IDEA_SEEDS:
        alignment = evaluate_alignment(seed)
        ideas.append({
            "idea": seed,
            "soul_alignment": alignment,
        })

    # Optional: tailor to goal keywords
    if goal:
        alignment = evaluate_alignment(goal)
    else:
        alignment = {"score": 0.0, "matched_values": [], "reasons": []}

    return {
        "questions": questions,
        "idea_seeds": ideas,
        "goal_alignment": alignment,
        "note": "These are hypothesis prompts. Confirm relevance before building.",
    }
