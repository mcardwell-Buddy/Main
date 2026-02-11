"""
Phase 7: Capability Boundary Model

Defines three execution classes for tasks/goals:
- AI_EXECUTABLE: Can be done entirely by AI without human intervention
- HUMAN_REQUIRED: Must involve human judgment/action
- COLLABORATIVE: Requires both AI and human contribution

Classification is deterministic and rule-based using keyword analysis.

Hard constraints:
- READ-ONLY (no execution changes)
- NO retries
- NO loops
- NO mission creation
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List


class ExecutionClass(Enum):
    """Three execution classes for capability boundary."""
    AI_EXECUTABLE = "AI_EXECUTABLE"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    COLLABORATIVE = "COLLABORATIVE"


@dataclass(frozen=True)
class CapabilityBoundary:
    """Immutable capability boundary assessment."""
    execution_class: ExecutionClass
    reasoning: str
    confidence: float  # 0.0-1.0
    key_indicators: List[str]


class CapabilityBoundaryModel:
    """
    Deterministic model for classifying tasks into execution classes.
    
    Uses keyword analysis and business logic patterns.
    No machine learning. No external dependencies.
    """

    # Keywords that strongly indicate AI_EXECUTABLE tasks
    AI_EXECUTABLE_KEYWORDS = {
        # Data processing
        "parse", "extract", "analyze", "process", "aggregate", "consolidate",
        "sort", "filter", "deduplicate", "transform", "map", "reduce",
        # Automation
        "automate", "batch", "loop", "iterate", "apply", "perform",
        "schedule", "queue", "enqueue", "trigger", "generate", "create records",
        # Analysis & decision
        "calculate", "compute", "summarize", "report", "classify", "score",
        "rank", "compare", "match", "find", "search", "lookup",
        # Data output
        "export", "import", "serialize", "format", "structure", "compile",
        # System operations
        "validate", "verify", "check", "monitor", "log", "track", "record",
        "debug", "test", "scan", "audit", "inspect"
    }

    # Keywords that strongly indicate HUMAN_REQUIRED tasks
    HUMAN_REQUIRED_KEYWORDS = {
        # Decision making
        "approve", "reject", "decide", "authorize", "consent", "sign off",
        "review", "validate decision", "judgment call", "discretion",
        # Creative/subjective
        "creative", "design", "write", "compose", "brainstorm", "ideate",
        "interpret", "curate", "imagine", "conceptualize",
        # Physical action
        "physical", "manual", "hands-on", "in person", "visit", "inspect physically",
        "photograph", "document on site", "measure", "observe",
        # Relationship/communication
        "negotiate", "communicate", "discuss", "convince", "persuade",
        "present", "pitch", "explain", "feedback", "counsel",
        # Policy/authority
        "policy", "compliance", "legal", "regulatory", "board approval",
        "executive sign off", "budget approval", "exception",
        # Sensitive/confidential
        "sensitive", "confidential", "private", "personal", "secure",
        "disclosure", "nda", "patent"
    }

    # Keywords that indicate COLLABORATIVE tasks
    COLLABORATIVE_KEYWORDS = {
        "coordinate", "collaborate", "partnership", "joint", "combined",
        "handoff", "escalate", "review and approve", "refine", "iterate",
        "implement with oversight", "execute with review", "managed process",
        "phased approach", "staged", "checkpoint", "validation stage",
        "user reviews", "reviews and", "reviews result"
    }

    # Patterns that override basic classification
    AI_EXECUTABLE_PATTERNS = {
        # Simple data operations without approvals
        "extract and store",
        "parse and categorize",
        "format and export",
        "collect and aggregate",
        "scan and report",
        "monitor and log",
        "validate and store"
    }

    HUMAN_REQUIRED_PATTERNS = {
        # Any approval needed
        "await approval",
        "pending approval",
        "requires sign off",
        "needs authorization",
        "must approve",
        "can only approve",
        "decision pending",
        # Contact/outreach
        "contact and ask",
        "reach out and",
        "call and inform",
        "email and request",
        # Physical verification
        "verify in person",
        "inspect on site",
        "photograph and document"
    }

    COLLABORATIVE_PATTERNS = {
        "ai assists with",
        "human coordinates with",
        "buddy provides data then user",
        "user provides then buddy",
        "iterate between",
        "staged process",
        "ai then human then ai",
        "managed handoff"
    }

    def __init__(self):
        """Initialize the capability boundary model."""
        pass

    def classify(self, task_description: str) -> CapabilityBoundary:
        """
        Classify a task into an execution class.

        Args:
            task_description: Natural language description of the task

        Returns:
            CapabilityBoundary with execution_class, reasoning, and indicators
        """
        if not task_description or not isinstance(task_description, str):
            return CapabilityBoundary(
                execution_class=ExecutionClass.HUMAN_REQUIRED,
                reasoning="Invalid task description",
                confidence=0.5,
                key_indicators=["invalid_input"]
            )

        lower_desc = task_description.lower()
        indicators = []
        scores = {
            ExecutionClass.AI_EXECUTABLE: 0.0,
            ExecutionClass.HUMAN_REQUIRED: 0.0,
            ExecutionClass.COLLABORATIVE: 0.0,
        }

        # Check for explicit patterns first (highest priority)
        for pattern in self.HUMAN_REQUIRED_PATTERNS:
            if pattern in lower_desc:
                scores[ExecutionClass.HUMAN_REQUIRED] += 5.0
                indicators.append(f"pattern:{pattern}")

        for pattern in self.AI_EXECUTABLE_PATTERNS:
            if pattern in lower_desc:
                scores[ExecutionClass.AI_EXECUTABLE] += 5.0
                indicators.append(f"pattern:{pattern}")

        for pattern in self.COLLABORATIVE_PATTERNS:
            if pattern in lower_desc:
                scores[ExecutionClass.COLLABORATIVE] += 5.0
                indicators.append(f"pattern:{pattern}")

        # Count keyword matches
        for keyword in self.AI_EXECUTABLE_KEYWORDS:
            if keyword in lower_desc:
                scores[ExecutionClass.AI_EXECUTABLE] += 1.0
                indicators.append(f"ai_keyword:{keyword}")

        for keyword in self.HUMAN_REQUIRED_KEYWORDS:
            if keyword in lower_desc:
                scores[ExecutionClass.HUMAN_REQUIRED] += 1.0
                indicators.append(f"human_keyword:{keyword}")

        for keyword in self.COLLABORATIVE_KEYWORDS:
            if keyword in lower_desc:
                scores[ExecutionClass.COLLABORATIVE] += 1.0
                indicators.append(f"collab_keyword:{keyword}")

        # Determine winner and confidence
        max_score = max(scores.values())
        if max_score == 0:
            # No keywords matched - default to COLLABORATIVE (safest)
            execution_class = ExecutionClass.COLLABORATIVE
            confidence = 0.4
            reasoning = "No specific keywords detected; defaulting to collaborative"
        else:
            # Find the execution class with highest score
            execution_class = max(scores, key=scores.get)
            # Calculate confidence (normalize by max possible score)
            confidence = min(max_score / 10.0, 1.0)
            
            if max_score > scores[ExecutionClass.COLLABORATIVE] + 1 and \
               max_score > scores[ExecutionClass.HUMAN_REQUIRED] + 1:
                # Clear winner
                confidence = min(confidence, 0.95)
            elif max_score == scores[ExecutionClass.COLLABORATIVE] + 1 or \
                 max_score == scores[ExecutionClass.HUMAN_REQUIRED] + 1:
                # Close call
                confidence = min(confidence, 0.65)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            execution_class, 
            scores, 
            indicators
        )

        # Limit indicators for clarity
        unique_indicators = sorted(list(set(indicators)))[:5]

        return CapabilityBoundary(
            execution_class=execution_class,
            reasoning=reasoning,
            confidence=confidence,
            key_indicators=unique_indicators
        )

    def _generate_reasoning(
        self,
        execution_class: ExecutionClass,
        scores: Dict[ExecutionClass, float],
        indicators: List[str]
    ) -> str:
        """Generate human-readable reasoning for classification."""
        if execution_class == ExecutionClass.AI_EXECUTABLE:
            return (
                f"Can be fully automated. No approval or human decision needed. "
                f"Score: {scores[ExecutionClass.AI_EXECUTABLE]:.1f}"
            )
        elif execution_class == ExecutionClass.HUMAN_REQUIRED:
            return (
                f"Requires human judgment, approval, or physical action. "
                f"Score: {scores[ExecutionClass.HUMAN_REQUIRED]:.1f}"
            )
        else:  # COLLABORATIVE
            return (
                f"Requires coordination between AI and human. "
                f"AI will prepare, human will decide or complete. "
                f"Score: {scores[ExecutionClass.COLLABORATIVE]:.1f}"
            )

    def classify_from_dict(self, task_dict: Dict[str, Any]) -> CapabilityBoundary:
        """
        Classify a task from a dictionary (goal, build_intent, mission, etc).

        Args:
            task_dict: Dictionary with 'description', 'goal', 'title', 'intent', etc.

        Returns:
            CapabilityBoundary
        """
        # Extract text from common fields
        text_parts = []
        for key in ["description", "goal", "title", "intent", "task", "objective", "name"]:
            if key in task_dict and task_dict[key]:
                text_parts.append(str(task_dict[key]))

        combined_text = " ".join(text_parts)
        return self.classify(combined_text)

    def get_execution_class_name(self, execution_class: ExecutionClass) -> str:
        """Get human-readable name for execution class."""
        return execution_class.value

