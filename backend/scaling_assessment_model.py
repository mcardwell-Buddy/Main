"""
Scaling Assessment Model - Phase 6 Step 3

Detects whether tasks are:
- SCALABLE: Parallelizable digitally (no human bottleneck)
- NON_SCALABLE: Human or system bottleneck
- CONDITIONAL: Can be scalable with conditions

SCALABILITY ANALYSIS:
- Input dependency: Task requires single input point
- Output aggregation: Results combine easily
- Atomicity: Tasks are independent units
- Concurrency constraints: No sequential dependencies

NO EXECUTION LOGIC:
- Assessment only, no agent spawning
- No concurrency added
- No parallelization attempted
- Read-only analysis

SIGNALS:
- signal_type: scalability_assessed
- signal_layer: cognition
- signal_source: scaling_model
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Tuple
from uuid import uuid4


class ScalabilityLevel(Enum):
    """Task scalability classification."""
    SCALABLE = "SCALABLE"          # Parallelizable, no bottleneck
    NON_SCALABLE = "NON_SCALABLE"  # Human or system bottleneck
    CONDITIONAL = "CONDITIONAL"    # Scalable with conditions


@dataclass
class ScalabilityAssessment:
    """Scalability assessment result."""
    task_description: str
    scalability_level: ScalabilityLevel
    confidence: float  # 0.0-1.0
    bottleneck_type: str  # human, system, temporal, sequential, data_dependency, none
    parallelizable_units: int  # Estimated number of parallel units
    reasoning: str
    evidence_factors: List[str]  # Factors influencing decision
    conditions_for_scale: List[str]  # What would make it scalable (for CONDITIONAL)
    session_id: str
    timestamp: str


class ScalingAssessmentModel:
    """Deterministic scalability assessment engine."""

    # SCALABLE indicators (parallelizable, no human bottleneck)
    SCALABLE_KEYWORDS: Set[str] = {
        "batch", "bulk", "multiple", "many", "repetitive", "loop",
        "process", "scan", "crawl", "collect", "gather", "aggregate",
        "compile", "analyze", "extract", "transform", "convert",
        "generate", "create", "build", "calculate", "compute",
        "search", "query", "filter", "map", "reduce", "distribute",
        "replicate", "copy", "sync", "push", "pull", "broadcast",
        "email batch", "send emails", "export data",
        "run reports", "analyze records", "process files", "import data",
        "parallel", "concurrent", "parallel processing", "parallelizable",
        "map reduce", "fork join", "divide and conquer", "decomposable",
        "independent", "idempotent", "stateless", "pure", "function",
        "each", "all items", "all records", "per record", "per item",
        "array", "list", "collection", "set", "batch job",
        "automated", "automatic", "background", "async", "offline",
        "export", "to csv", "records"
    }

    # NON_SCALABLE indicators (human bottleneck, sequential, dependent)
    NON_SCALABLE_KEYWORDS: Set[str] = {
        "call", "interview", "meeting", "discuss", "negotiate",
        "decision", "judgment call", "approval", "approval workflow",
        "one by one", "sequential", "order dependent", "sequential dependency",
        "handoff", "hand off", "escalate", "escalation", "approval chain",
        "sign", "signature", "authorization", "authorize", "verify identity",
        "human approval", "human decision", "human intervention", "human driven",
        "person to person", "direct", "personal", "individualized", "custom",
        "exception", "edge case", "special case", "unique", "one off",
        "manual", "manually", "hands on",
        "sync", "synchronous", "real time", "realtime", "live",
        "data privacy", "pii", "sensitive data", "confidential", "encrypted",
        "depends on", "prerequisite", "requires approval",
        "blocking", "blocked by", "wait for", "hold",
        "high context", "contextual", "nuanced", "subjective", "interpretation",
        "safety critical", "mission critical", "critical system", "critical",
        "feedback loop", "iterative", "back and forth", "by priority"
    }

    # CONDITIONAL indicators (scalable with conditions)
    CONDITIONAL_KEYWORDS: Set[str] = {
        "if", "when", "provided", "given", "assume",
        "after", "before", "subject to", "contingent on",
        "with approval", "with permission", "authorized",
        "staged", "phased", "incremental", "rollout", "pilot",
        "on condition", "conditional", "scenario", "case by case",
        "depending on approval", "pending decision", "pending review",
        "breakable into", "split into", "divide into", "segments",
        "optional", "discretionary", "best effort", "may be", "could be",
        "partly", "partially", "some of", "portion",
        "once approved", "after decision", "post approval", "when ready",
        "once", "depending on initial", "depending on"
    }

    # BOTTLENECK PATTERNS
    HUMAN_BOTTLENECK_PATTERNS: List[Tuple[str, float]] = [
        (r"call.*customer", 2.0),
        (r"negotiate.*terms", 2.0),
        (r"approve.*request", 1.5),
        (r"review.*application", 1.5),
        (r"sign.*document", 1.5),
        (r"decision.*make", 2.0),
        (r"hand.*off.*to", 1.5),
        (r"escalate.*issue", 1.5),
    ]

    SYSTEM_BOTTLENECK_PATTERNS: List[Tuple[str, float]] = [
        (r"third.*party.*api", 1.5),
        (r"external.*system", 1.5),
        (r"rate.*limit", 2.0),
        (r"quota", 1.5),
        (r"sequence.*required", 2.0),
        (r"order.*depend", 2.0),
        (r"state.*machine", 1.5),
    ]

    SCALABLE_PATTERNS: List[Tuple[str, float]] = [
        (r"process.*batch", 2.0),
        (r"process.*all.*records", 2.0),
        (r"export.*data", 1.5),
        (r"send.*bulk", 1.5),
        (r"analyze.*dataset", 1.5),
        (r"map.*each", 2.0),
        (r"for.*each.*item", 2.0),
        (r"parallel.*processing", 2.0),
    ]

    def __init__(self):
        """Initialize Scaling Assessment Model."""
        self.session_id = str(uuid4())

    def assess_scalability(
        self, task_description: str
    ) -> ScalabilityAssessment:
        """
        Assess whether a task is scalable.

        Args:
            task_description: Description of the task

        Returns:
            ScalabilityAssessment with level, confidence, bottleneck type, and reasoning
        """
        # Score indicators
        scalable_score, scalable_factors = self._score_keywords(
            task_description, self.SCALABLE_KEYWORDS
        )
        non_scalable_score, non_scalable_factors = self._score_keywords(
            task_description, self.NON_SCALABLE_KEYWORDS
        )
        conditional_score, conditional_factors = self._score_keywords(
            task_description, self.CONDITIONAL_KEYWORDS
        )

        # Score patterns
        human_bottleneck_score = self._score_patterns(
            task_description, self.HUMAN_BOTTLENECK_PATTERNS
        )
        system_bottleneck_score = self._score_patterns(
            task_description, self.SYSTEM_BOTTLENECK_PATTERNS
        )
        scalable_pattern_score = self._score_patterns(
            task_description, self.SCALABLE_PATTERNS
        )

        scalable_score += scalable_pattern_score
        non_scalable_score += human_bottleneck_score + system_bottleneck_score

        # Determine scalability level
        scalability_level, confidence = self._determine_scalability(
            scalable_score, non_scalable_score, conditional_score
        )

        # Identify bottleneck type
        bottleneck_type = self._identify_bottleneck(
            task_description,
            human_bottleneck_score,
            system_bottleneck_score,
            scalability_level
        )

        # Estimate parallelizable units
        parallelizable_units = self._estimate_parallelizable_units(
            task_description, scalability_level
        )

        # Collect evidence factors
        evidence = list(set(
            scalable_factors + non_scalable_factors + conditional_factors
        ))

        # Generate conditions for scaling (if CONDITIONAL)
        conditions = self._generate_conditions_for_scale(
            task_description, scalability_level
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            scalability_level, confidence, bottleneck_type, parallelizable_units
        )

        return ScalabilityAssessment(
            task_description=task_description,
            scalability_level=scalability_level,
            confidence=confidence,
            bottleneck_type=bottleneck_type,
            parallelizable_units=parallelizable_units,
            reasoning=reasoning,
            evidence_factors=evidence,
            conditions_for_scale=conditions,
            session_id=self.session_id,
            timestamp=datetime.now().isoformat()
        )

    def _score_keywords(
        self, text: str, keywords: Set[str]
    ) -> Tuple[float, List[str]]:
        """Score keywords in text."""
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
        """Score regex patterns in text."""
        text_lower = text.lower()
        score = 0.0

        for pattern, pattern_score in patterns:
            if re.search(pattern, text_lower):
                score += pattern_score

        return score

    def _determine_scalability(
        self,
        scalable_score: float,
        non_scalable_score: float,
        conditional_score: float
    ) -> Tuple[ScalabilityLevel, float]:
        """Determine scalability level from scores."""
        total_score = scalable_score + non_scalable_score + conditional_score

        # Handle no matches
        if total_score == 0.0:
            return ScalabilityLevel.NON_SCALABLE, 0.33  # Default to non-scalable

        # Determine primary level
        if scalable_score >= non_scalable_score and scalable_score >= conditional_score:
            level = ScalabilityLevel.SCALABLE
            confidence = scalable_score / total_score
        elif non_scalable_score >= conditional_score:
            level = ScalabilityLevel.NON_SCALABLE
            confidence = non_scalable_score / total_score
        else:
            level = ScalabilityLevel.CONDITIONAL
            confidence = conditional_score / total_score

        return level, confidence

    def _identify_bottleneck(
        self,
        task_description: str,
        human_score: float,
        system_score: float,
        scalability_level: ScalabilityLevel
    ) -> str:
        """Identify the type of bottleneck."""
        if scalability_level == ScalabilityLevel.SCALABLE:
            return "none"

        text_lower = task_description.lower()

        # Check for sequential dependencies
        if any(word in text_lower for word in ["sequential", "one by one", "order dependent", "prerequisite"]):
            return "sequential"

        # Check for data dependencies
        if any(word in text_lower for word in ["depends on", "dependent on", "prerequisite", "requires"]):
            return "data_dependency"

        # Check for temporal constraints
        if any(word in text_lower for word in ["sync", "synchronous", "real time", "live", "blocking"]):
            return "temporal"

        # Compare scores
        if human_score > system_score:
            return "human"
        elif system_score > human_score:
            return "system"

        return "unknown"

    def _estimate_parallelizable_units(
        self, task_description: str, scalability_level: ScalabilityLevel
    ) -> int:
        """Estimate number of parallelizable units."""
        if scalability_level == ScalabilityLevel.NON_SCALABLE:
            return 1

        text_lower = task_description.lower()

        # Extract numeric hints
        numbers = re.findall(r'\d+', text_lower)
        if numbers:
            try:
                max_num = max(int(n) for n in numbers)
                if 2 <= max_num <= 1000:
                    return max_num
                elif max_num > 1000:
                    return 100  # Cap at 100
            except (ValueError, TypeError):
                pass

        # Estimate based on keywords
        if any(word in text_lower for word in ["batch", "bulk", "all", "multiple", "many"]):
            return 10

        if scalability_level == ScalabilityLevel.CONDITIONAL:
            return 3

        return 2

    def _generate_conditions_for_scale(
        self, task_description: str, scalability_level: ScalabilityLevel
    ) -> List[str]:
        """Generate conditions needed for scalability (for CONDITIONAL)."""
        if scalability_level != ScalabilityLevel.CONDITIONAL:
            return []

        conditions = []
        text_lower = task_description.lower()

        # Approval-based conditions
        if "approval" in text_lower or "authorize" in text_lower or "approved" in text_lower:
            conditions.append("Requires initial approval")

        # Staging conditions
        if "pilot" in text_lower or "phased" in text_lower or "staged" in text_lower:
            conditions.append("Can be deployed in phases")

        # Data conditions
        if "subject to" in text_lower or "depending on" in text_lower or "initial" in text_lower:
            conditions.append("Dependent on initial setup")

        # Default conditions if none found
        if not conditions:
            conditions = [
                "Batch mode processing enabled",
                "No blocking dependencies"
            ]

        return conditions

    def _generate_reasoning(
        self,
        scalability_level: ScalabilityLevel,
        confidence: float,
        bottleneck_type: str,
        parallelizable_units: int
    ) -> str:
        """Generate human-readable reasoning."""
        conf_pct = confidence * 100

        level_desc = {
            ScalabilityLevel.SCALABLE: "highly parallelizable",
            ScalabilityLevel.NON_SCALABLE: "requires sequential processing",
            ScalabilityLevel.CONDITIONAL: "parallelizable with conditions"
        }

        bottleneck_desc = {
            "human": "human bottleneck",
            "system": "system/API bottleneck",
            "temporal": "temporal/synchronization constraint",
            "sequential": "sequential dependency",
            "data_dependency": "data flow dependency",
            "none": "no bottleneck",
            "unknown": "unknown bottleneck type"
        }

        base_desc = level_desc.get(scalability_level, "UNKNOWN")
        bottleneck_desc_str = bottleneck_desc.get(bottleneck_type, "unknown")

        return (
            f"{scalability_level.value} ({conf_pct:.0f}% confidence). "
            f"Classification: {base_desc}. "
            f"Bottleneck: {bottleneck_desc_str}. "
            f"Estimated parallelizable units: {parallelizable_units}"
        )

    def get_scalability_summary(self) -> Dict[str, int | str]:
        """Get session summary."""
        return {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat()
        }


def get_scaling_assessment_model() -> ScalingAssessmentModel:
    """Get singleton-like instance of ScalingAssessmentModel."""
    return ScalingAssessmentModel()


def assess_scalability(task_description: str) -> ScalabilityAssessment:
    """
    Convenience function to assess task scalability.

    Args:
        task_description: Description of the task

    Returns:
        ScalabilityAssessment
    """
    model = ScalingAssessmentModel()
    return model.assess_scalability(task_description)
