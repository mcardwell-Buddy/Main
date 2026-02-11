"""
Human Energy Model - Phase 6 Step 2

Estimates human effort cost and rest constraints for tasks.
Deterministic, heuristic-based classification (NO LLM).
Emits learning signals for observability.

Effort Levels:
- LOW: Reply, approve, skim (< 5 min, low cognitive load)
- MEDIUM: Review doc, make decision (5-30 min, moderate cognitive load)
- HIGH: Calls, meetings, physical tasks (> 30 min, high cognitive/physical load)

REST AWARENESS:
- Max continuous effort window (default 120 min)
- Tracks cumulative effort
- Soft warnings only (no enforcement)

SIGNALS:
- signal_type: human_effort_estimated
- signal_layer: cognition
- signal_source: human_energy_model
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Tuple
from uuid import uuid4


class EffortLevel(Enum):
    """Human effort classification."""
    LOW = "LOW"          # < 5 min, low cognitive load (reply, approve, skim)
    MEDIUM = "MEDIUM"    # 5-30 min, moderate cognitive load (review doc, decide)
    HIGH = "HIGH"        # > 30 min, high cognitive/physical load (calls, meetings, physical)


@dataclass
class HumanEnergyEstimate:
    """Human effort estimation result."""
    task_description: str
    effort_level: EffortLevel
    estimated_minutes: float  # Point estimate (mid-range)
    min_minutes: float        # Optimistic estimate
    max_minutes: float        # Pessimistic estimate
    evidence_keywords: List[str]  # Keywords that influenced classification
    reasoning: str            # Human-readable explanation
    rest_warning: bool        # Whether this exceeds current window
    rest_recommendation: str  # "OK", "NEAR_LIMIT", "EXCEEDS_LIMIT"
    session_id: str           # For tracking across signals
    timestamp: str


class HumanEnergyModel:
    """Deterministic human effort estimation engine."""

    # LOW effort keywords (reply, approve, skim, <5 min)
    LOW_EFFORT_KEYWORDS: Set[str] = {
        "reply", "respond", "acknowledge", "approve", "reject", "accept",
        "decline", "confirm", "skim", "glance", "quick", "brief", "quick review",
        "yes or no", "simple answer", "straightforward", "click", "select",
        "checkbox", "radio button", "button click", "ok", "authorize", "sign off",
        "thumbs up", "emoji", "react", "like", "upvote", "downvote",
        "quick decision", "simple choice", "two options", "either or",
        "memo", "email reply", "instant message", "chat", "slack", "teams",
        "notification", "alert", "popup", "toast", "hint", "tip",
        "simple form", "one field", "fill in", "name", "email", "phone",
        "password", "pin", "code", "confirm code", "otp", "two factor",
        "glance at", "scan", "preview", "summary", "headline", "bullet points",
        "quick scan", "fast review", "cursory", "superficial"
    }

    # MEDIUM effort keywords (review doc, make decision, 5-30 min)
    MEDIUM_EFFORT_KEYWORDS: Set[str] = {
        "review", "analyze", "evaluate", "assess", "decide", "decide on",
        "make decision", "judgment call", "recommend", "suggestion",
        "consider", "weigh options", "compare", "contrast", "pros and cons",
        "document review", "read document", "peruse", "scan document",
        "moderate review", "thorough review", "detailed check", "verification",
        "moderate decision", "important choice", "significant decision",
        "moderate effort", "standard effort", "typical task", "normal task",
        "discussion", "talk", "conversation", "exchange ideas", "brainstorm",
        "light meeting", "standup", "sync", "quick sync", "check in",
        "feedback", "critique", "comment", "annotation", "note taking",
        "outline", "plan", "sketch", "design", "wireframe", "mockup",
        "write email", "draft", "compose", "write message", "write brief",
        "coordinate", "schedule", "arrange", "organize", "plan meeting",
        "research", "lookup", "search", "find information", "investigate",
        "moderate coding", "code review", "debug", "test", "qa check",
        "moderate form", "multi field form", "questionnaire", "survey",
        "read guidelines", "understand requirements", "clarify", "ask question",
        "30 minute", "20 minute", "15 minute", "10 minute", "moderate time",
        "after meeting", "post call", "follow up review", "decision", "make",
        "decision on", "decision making", "judgment"
    }

    # HIGH effort keywords (calls, meetings, physical tasks, >30 min)
    HIGH_EFFORT_KEYWORDS: Set[str] = {
        "call", "phone call", "conference call", "zoom call", "video call",
        "meeting", "in person meeting", "face to face", "all hands", "town hall",
        "presentation", "demo", "pitch", "keynote", "talk", "seminar",
        "workshop", "training", "coaching", "mentoring", "interview",
        "lengthy meeting", "long meeting", "extended meeting", "all day",
        "physical task", "site visit", "on site", "in person", "travel",
        "inspection", "audit", "walkthrough", "facility", "office visit",
        "installation", "setup", "deployment", "implementation", "rollout",
        "complex task", "involved project", "complicated task", "challenging",
        "extensive", "comprehensive", "detailed", "thorough analysis",
        "deep dive", "research project", "investigation", "study", "survey",
        "extensive coding", "development", "build", "refactor", "major changes",
        "complex decision", "critical decision", "strategic decision",
        "multi person", "group meeting", "team meeting", "stakeholder meeting",
        "board meeting", "executive meeting", "leadership meeting",
        "negotiation", "discussion", "alignment", "alignment meeting",
        "conflict resolution", "mediation", "difficult conversation",
        "performance review", "career conversation", "one on one",
        "project kickoff", "project review", "project close", "retrospective",
        "incident response", "emergency", "crisis", "fire drill",
        "more than hour", "hour long", "two hour", "three hour", "full day",
        "multiple hours", "extended effort", "high effort", "intense",
        "physical inspection", "hands on", "get your hands dirty",
        "travel required", "location required", "scheduled event",
        "calendar block", "reserved time", "time commitment", "visit",
        "site", "warehouse", "facility visit", "attend"
    }

    # HYBRID keywords (could be MEDIUM or HIGH depending on context)
    HYBRID_KEYWORDS: Set[str] = {
        "decision", "complex", "investigation", "project", "implementation",
        "coordination", "management", "leadership", "facilitation"
    }

    # Regex patterns for effort detection
    MEDIUM_EFFORT_PATTERNS: List[Tuple[str, float]] = [
        (r"read.*document", 1.5),
        (r"review.*document", 1.5),
        (r"make.*decision", 2.0),
        (r"discuss.*with", 1.5),
        (r"write.*email", 1.5),
        (r"draft.*\w+", 1.5),
        (r"analyze.*data", 2.0),
        (r"research.*topic", 2.0),
        (r"code.*review", 1.5),
    ]

    HIGH_EFFORT_PATTERNS: List[Tuple[str, float]] = [
        (r"attend.*meeting", 3.0),
        (r"conduct.*meeting", 3.0),
        (r"phone.*call", 3.0),
        (r"video.*call", 3.0),
        (r"presentation", 3.0),
        (r"travel.*to", 3.0),
        (r"site.*visit", 3.0),
        (r"implementation", 3.0),
        (r"deployment", 3.0),
        (r"installation", 3.0),
        (r"training.*session", 3.0),
        (r"workshop", 3.0),
        (r"interview", 3.0),
        (r"negotiation", 3.0),
    ]

    def __init__(self, max_continuous_minutes: float = 120.0):
        """
        Initialize Human Energy Model.

        Args:
            max_continuous_minutes: Max continuous effort before soft warning (default 120 min)
        """
        self.max_continuous_minutes = max_continuous_minutes
        self.cumulative_effort_minutes = 0.0
        self.effort_window_start: datetime | None = None
        self.session_id = str(uuid4())

    def estimate_human_cost(
        self,
        task_description: str,
        current_cumulative_minutes: float = 0.0
    ) -> HumanEnergyEstimate:
        """
        Estimate human effort cost for a task.

        Deterministic classification based on keywords and patterns.
        Returns effort level, time estimates, and rest warning.

        Args:
            task_description: Description of the task
            current_cumulative_minutes: Current accumulated effort in this window

        Returns:
            HumanEnergyEstimate with effort level, time ranges, evidence, and rest warning
        """
        self.cumulative_effort_minutes = current_cumulative_minutes

        # Score keywords and patterns
        low_score, low_keywords = self._score_keywords(
            task_description, self.LOW_EFFORT_KEYWORDS
        )
        medium_score, medium_keywords = self._score_keywords(
            task_description, self.MEDIUM_EFFORT_KEYWORDS
        )
        high_score, high_keywords = self._score_keywords(
            task_description, self.HIGH_EFFORT_KEYWORDS
        )

        # Score patterns
        low_score += self._score_patterns(task_description, [])
        medium_score += self._score_patterns(task_description, self.MEDIUM_EFFORT_PATTERNS)
        high_score += self._score_patterns(task_description, self.HIGH_EFFORT_PATTERNS)

        # Determine effort level and estimates
        effort_level, confidence = self._determine_effort_level(
            (low_score, medium_score, high_score)
        )

        # Generate time estimates based on effort level
        min_minutes, est_minutes, max_minutes = self._estimate_time_range(
            effort_level, task_description
        )

        # Check rest constraints
        rest_warning, rest_rec = self._check_rest_constraints(
            est_minutes, self.cumulative_effort_minutes
        )

        # Collect evidence keywords
        evidence = low_keywords + medium_keywords + high_keywords
        evidence = list(set(evidence))  # Deduplicate

        # Generate reasoning
        reasoning = self._generate_reasoning(
            effort_level, confidence, min_minutes, est_minutes, max_minutes
        )

        return HumanEnergyEstimate(
            task_description=task_description,
            effort_level=effort_level,
            estimated_minutes=est_minutes,
            min_minutes=min_minutes,
            max_minutes=max_minutes,
            evidence_keywords=evidence,
            reasoning=reasoning,
            rest_warning=rest_warning,
            rest_recommendation=rest_rec,
            session_id=self.session_id,
            timestamp=datetime.now().isoformat()
        )

    def _score_keywords(self, text: str, keywords: Set[str]) -> Tuple[float, List[str]]:
        """
        Score keywords in text.

        Args:
            text: Text to search
            keywords: Set of keywords to match

        Returns:
            Tuple of (score, found_keywords)
        """
        text_lower = text.lower()
        found = []
        score = 0.0

        for keyword in keywords:
            if keyword in text_lower:
                found.append(keyword)
                score += 0.5

        return score, found

    def _score_patterns(
        self, text: str, patterns: List[Tuple[str, float]]
    ) -> float:
        """
        Score regex patterns in text.

        Args:
            text: Text to search
            patterns: List of (regex, score) tuples

        Returns:
            Total pattern score
        """
        text_lower = text.lower()
        score = 0.0

        for pattern, pattern_score in patterns:
            if re.search(pattern, text_lower):
                score += pattern_score

        return score

    def _determine_effort_level(
        self, scores: Tuple[float, float, float]
    ) -> Tuple[EffortLevel, float]:
        """
        Determine effort level from scores.

        Args:
            scores: (low_score, medium_score, high_score)

        Returns:
            Tuple of (EffortLevel, confidence 0.0-1.0)
        """
        low_score, medium_score, high_score = scores
        total_score = low_score + medium_score + high_score

        # Handle empty/no match
        if total_score == 0.0:
            return EffortLevel.MEDIUM, 0.33  # Default to MEDIUM if no matches

        # Determine primary effort level
        if high_score >= medium_score and high_score >= low_score:
            effort = EffortLevel.HIGH
            confidence = high_score / total_score
        elif medium_score >= low_score:
            effort = EffortLevel.MEDIUM
            confidence = medium_score / total_score
        else:
            effort = EffortLevel.LOW
            confidence = low_score / total_score

        return effort, confidence

    def _estimate_time_range(
        self, effort_level: EffortLevel, task_description: str
    ) -> Tuple[float, float, float]:
        """
        Estimate time range for effort level.

        Returns:
            Tuple of (min_minutes, estimated_minutes, max_minutes)
        """
        # Base ranges by effort level
        if effort_level == EffortLevel.LOW:
            min_min, est_min, max_min = 1.0, 3.0, 5.0
        elif effort_level == EffortLevel.MEDIUM:
            min_min, est_min, max_min = 5.0, 15.0, 30.0
        else:  # HIGH
            min_min, est_min, max_min = 30.0, 60.0, 120.0

        # Adjust based on specific keywords
        text_lower = task_description.lower()

        # Check for duration hints
        if any(word in text_lower for word in ["quick", "brief", "fast", "short"]):
            min_min *= 0.5
            est_min *= 0.7
            max_min *= 0.8

        if any(word in text_lower for word in ["extensive", "comprehensive", "thorough", "detailed"]):
            min_min *= 1.2
            est_min *= 1.5
            max_min *= 1.8

        if any(word in text_lower for word in ["two hour", "3 hour", "full day", "all day", "multiple hours"]):
            est_min = max(est_min, 120.0)
            max_min = max(max_min, 180.0)

        return min_min, est_min, max_min

    def _check_rest_constraints(
        self, estimated_minutes: float, cumulative_minutes: float
    ) -> Tuple[bool, str]:
        """
        Check if task fits within rest window.

        Returns:
            Tuple of (rest_warning, recommendation)
        """
        projected_effort = cumulative_minutes + estimated_minutes

        if projected_effort > self.max_continuous_minutes * 1.2:
            return True, "EXCEEDS_LIMIT"
        elif projected_effort > self.max_continuous_minutes * 0.85:
            return True, "NEAR_LIMIT"
        else:
            return False, "OK"

    def _generate_reasoning(
        self,
        effort_level: EffortLevel,
        confidence: float,
        min_min: float,
        est_min: float,
        max_min: float
    ) -> str:
        """Generate human-readable reasoning."""
        conf_pct = confidence * 100

        effort_desc = {
            EffortLevel.LOW: "low cognitive load (<5 min)",
            EffortLevel.MEDIUM: "moderate cognitive load (5-30 min)",
            EffortLevel.HIGH: "high cognitive/physical load (>30 min)"
        }

        return (
            f"{effort_level.value} effort ({conf_pct:.0f}% confidence). "
            f"Estimated {est_min:.0f} minutes ({min_min:.0f}-{max_min:.0f} range). "
            f"Classification: {effort_desc.get(effort_level, 'UNKNOWN')}"
        )

    def get_rest_status(self) -> Dict[str, float | str]:
        """Get current rest window status."""
        return {
            "cumulative_minutes": self.cumulative_effort_minutes,
            "max_continuous_minutes": self.max_continuous_minutes,
            "remaining_minutes": max(
                0.0,
                self.max_continuous_minutes - self.cumulative_effort_minutes
            ),
            "status": (
                "OK" if self.cumulative_effort_minutes < self.max_continuous_minutes * 0.85
                else "NEAR_LIMIT" if self.cumulative_effort_minutes < self.max_continuous_minutes
                else "EXCEEDED"
            )
        }


def get_human_energy_model(max_continuous_minutes: float = 120.0) -> HumanEnergyModel:
    """Get singleton-like instance of HumanEnergyModel."""
    return HumanEnergyModel(max_continuous_minutes=max_continuous_minutes)


def estimate_human_cost(
    task_description: str,
    max_continuous_minutes: float = 120.0
) -> HumanEnergyEstimate:
    """
    Convenience function to estimate human cost for a task.

    Args:
        task_description: Description of the task
        max_continuous_minutes: Max continuous effort window

    Returns:
        HumanEnergyEstimate
    """
    model = HumanEnergyModel(max_continuous_minutes=max_continuous_minutes)
    return model.estimate_human_cost(task_description)

