"""
Phase 7: Delegation Evaluator

Analyzes missions, goals, and build intents to determine:
- Who does what (execution class)
- What humans must do
- Estimated human effort
- Blocking conditions

Input: mission, goal, or build_intent description
Output: DelegationDecision with:
  - execution_class (AI_EXECUTABLE | HUMAN_REQUIRED | COLLABORATIVE)
  - rationale (human-readable reasoning)
  - required_human_actions (list of actions if HUMAN_REQUIRED or COLLABORATIVE)
  - estimated_human_effort (minutes)
  - is_blocked (true if human action needed first)
  - blocking_reason (why blocked, if applicable)

Hard constraints:
- READ-ONLY analysis only
- NO retries
- NO loops
- NO mission creation
- NO execution
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime

from backend.capability_boundary import CapabilityBoundaryModel, ExecutionClass


@dataclass
class HumanAction:
    """A required human action."""
    action: str  # e.g., "provide approval", "enter data", "confirm details"
    description: str
    estimated_minutes: int
    is_blocking: bool = False  # true if blocks AI execution


@dataclass
class DelegationDecision:
    """Result of delegation evaluation."""
    execution_class: ExecutionClass
    rationale: str
    required_human_actions: List[HumanAction] = field(default_factory=list)
    estimated_human_effort: int = 0  # minutes
    is_blocked: bool = False  # true if waiting for human
    blocking_reason: Optional[str] = None
    conditions: List[str] = field(default_factory=list)
    confidence: float = 0.8  # 0.0-1.0


class DelegationEvaluator:
    """
    Evaluates task delegation and handoff requirements.

    Uses CapabilityBoundaryModel for classification.
    Adds domain-specific logic for human action detection.
    """

    # Tasks that always require human involvement
    ALWAYS_HUMAN_REQUIRED = {
        "budget approval", "executive sign off", "legal review",
        "compliance check", "privacy review", "security clearance",
        "board decision", "policy exception", "discretionary approval"
    }

    # Tasks that indicate blocking conditions
    BLOCKING_INDICATORS = {
        "awaiting", "pending", "waiting for", "requires approval first",
        "cannot proceed until", "blocked on", "depends on"
    }

    # Effort estimates (minutes) for common human actions
    EFFORT_ESTIMATES = {
        "review": 15,
        "approval": 10,
        "feedback": 20,
        "decision": 30,
        "input": 25,
        "validation": 20,
        "sign off": 10,
        "authorize": 5,
        "contact": 15,
        "meeting": 60,
        "inspection": 30,
        "interview": 45,
    }

    def __init__(self):
        """Initialize the delegation evaluator."""
        self._capability_model = CapabilityBoundaryModel()

    def evaluate(self, task_description: str) -> DelegationDecision:
        """
        Evaluate delegation requirements for a task.

        Args:
            task_description: Natural language description of task/goal

        Returns:
            DelegationDecision with execution class and human actions
        """
        if not task_description or not isinstance(task_description, str):
            return DelegationDecision(
                execution_class=ExecutionClass.HUMAN_REQUIRED,
                rationale="Invalid task description provided",
                is_blocked=True,
                blocking_reason="Cannot evaluate without task description",
                confidence=0.3
            )

        # Classify using capability boundary model
        capability = self._capability_model.classify(task_description)

        # Build delegation decision
        decision = DelegationDecision(
            execution_class=capability.execution_class,
            rationale=capability.reasoning,
            confidence=capability.confidence
        )

        # Determine human actions based on execution class
        if capability.execution_class == ExecutionClass.AI_EXECUTABLE:
            # No human actions required
            decision.required_human_actions = []
            decision.estimated_human_effort = 0
            decision.is_blocked = False

        elif capability.execution_class == ExecutionClass.HUMAN_REQUIRED:
            # Extract human actions from description
            actions = self._extract_human_actions(task_description)
            decision.required_human_actions = actions
            decision.estimated_human_effort = sum(a.estimated_minutes for a in actions)
            decision.is_blocked = any(a.is_blocking for a in actions)
            
            if decision.is_blocked:
                blocking_action = next(
                    (a for a in actions if a.is_blocking), 
                    None
                )
                if blocking_action:
                    decision.blocking_reason = f"Blocked waiting on: {blocking_action.action}"

        else:  # COLLABORATIVE
            # Both AI and human contribute
            actions = self._extract_human_actions(task_description)
            decision.required_human_actions = actions
            decision.estimated_human_effort = sum(a.estimated_minutes for a in actions) if actions else 15

            # Check if blocking
            blocking_actions = [a for a in actions if a.is_blocking]
            if blocking_actions:
                decision.is_blocked = True
                decision.blocking_reason = f"Initial human input needed: {blocking_actions[0].action}"

        # Add conditions
        decision.conditions = self._extract_conditions(task_description)

        return decision

    def evaluate_from_dict(self, task_dict: Dict[str, Any]) -> DelegationDecision:
        """
        Evaluate delegation from a dictionary (mission, goal, build_intent).

        Args:
            task_dict: Dictionary with task description fields

        Returns:
            DelegationDecision
        """
        # Extract text from common fields
        text_parts = []
        for key in ["description", "goal", "title", "intent", "task", "objective", "name"]:
            if key in task_dict and task_dict[key]:
                text_parts.append(str(task_dict[key]))

        combined_text = " ".join(text_parts)
        return self.evaluate(combined_text)

    def _extract_human_actions(self, task_description: str) -> List[HumanAction]:
        """Extract required human actions from task description."""
        actions = []
        lower_desc = task_description.lower()

        # Look for human action keywords
        human_action_keywords = {
            "review": ("review the results", 15, False),
            "approve": ("approve the action", 10, True),
            "feedback": ("provide feedback", 20, False),
            "contact": ("contact stakeholder", 15, True),
            "sign off": ("sign off on completion", 10, True),
            "authorize": ("authorize the execution", 5, True),
            "decision": ("make final decision", 30, True),
            "interview": ("conduct interview", 45, False),
            "validate": ("validate results", 20, False),
            "input": ("provide required input", 25, True),
            "approval": ("receive approval", 10, True),
            "meeting": ("attend meeting", 60, False),
        }

        for keyword, (action, minutes, blocking) in human_action_keywords.items():
            if keyword in lower_desc:
                actions.append(HumanAction(
                    action=action,
                    description=f"Human action: {action}",
                    estimated_minutes=minutes,
                    is_blocking=blocking
                ))

        # Remove duplicates
        unique_actions = {}
        for action in actions:
            if action.action not in unique_actions:
                unique_actions[action.action] = action

        return list(unique_actions.values())

    def _extract_conditions(self, task_description: str) -> List[str]:
        """Extract execution conditions from task description."""
        conditions = []
        lower_desc = task_description.lower()

        # Check for blocking conditions
        for indicator in self.BLOCKING_INDICATORS:
            if indicator in lower_desc:
                conditions.append(f"Depends on: {indicator}")

        # Check for required approvals
        if any(req in lower_desc for req in self.ALWAYS_HUMAN_REQUIRED):
            conditions.append("Requires formal approval")

        # Time-based conditions
        if "after" in lower_desc or "before" in lower_desc or "on" in lower_desc:
            conditions.append("Time-dependent execution")

        # Data conditions
        if "if" in lower_desc or "when" in lower_desc:
            conditions.append("Conditional execution")

        return conditions

    def get_handoff_summary(self, decision: DelegationDecision) -> str:
        """
        Generate a human-readable summary of the delegation decision.

        Args:
            decision: DelegationDecision

        Returns:
            Multi-line summary string
        """
        summary_lines = [
            f"Execution Class: {decision.execution_class.value}",
            f"Rationale: {decision.rationale}",
        ]

        if decision.required_human_actions:
            summary_lines.append("\nRequired Human Actions:")
            for action in decision.required_human_actions:
                blocking_marker = "[BLOCKING] " if action.is_blocking else ""
                summary_lines.append(
                    f"  • {blocking_marker}{action.action} "
                    f"(~{action.estimated_minutes} min)"
                )

        if decision.estimated_human_effort > 0:
            summary_lines.append(
                f"\nEstimated Human Effort: {decision.estimated_human_effort} minutes"
            )

        if decision.is_blocked:
            summary_lines.append(f"\n⚠️  BLOCKED: {decision.blocking_reason}")

        if decision.conditions:
            summary_lines.append("\nExecution Conditions:")
            for condition in decision.conditions:
                summary_lines.append(f"  • {condition}")

        return "\n".join(summary_lines)

    def get_quick_summary(self, decision: DelegationDecision) -> str:
        """Get a one-line summary."""
        if decision.execution_class == ExecutionClass.AI_EXECUTABLE:
            return f"✓ Fully automated ({decision.execution_class.value})"
        elif decision.execution_class == ExecutionClass.HUMAN_REQUIRED:
            blocked_marker = "🔴 BLOCKED" if decision.is_blocked else "⏳ Waiting"
            return f"{blocked_marker} - Requires: {', '.join(a.action for a in decision.required_human_actions[:2])}"
        else:  # COLLABORATIVE
            return (
                f"🤝 Collaborative - "
                f"AI handles data, human provides {decision.estimated_human_effort} min effort"
            )
