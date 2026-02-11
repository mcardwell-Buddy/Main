"""
Phase 7: Whiteboard Delegation Panel

Exposes delegation intelligence in the Whiteboard.

Panels:
- Execution Class (AI_EXECUTABLE | HUMAN_REQUIRED | COLLABORATIVE)
- Human Actions (list of required actions if not fully automated)
- Effort Estimate (human effort in minutes)
- Blocking Status (is execution blocked on human action?)

Read-only, default-visible, non-executing.
"""

from typing import Optional, Dict, Any, List
from Back_End.delegation_evaluator import DelegationEvaluator, DelegationDecision, ExecutionClass


class DelegationWhiteboardPanel:
    """Renders delegation intelligence for the Whiteboard."""

    def __init__(self):
        """Initialize delegation panel."""
        self._evaluator = DelegationEvaluator()
        self._latest_decision: Optional[DelegationDecision] = None

    def set_delegation_decision(self, decision: DelegationDecision) -> None:
        """Set the latest delegation decision for rendering."""
        self._latest_decision = decision

    def evaluate_and_render(self, task_description: str) -> str:
        """
        Evaluate a task and render the delegation panel.

        Args:
            task_description: Task/goal/intent description

        Returns:
            Formatted panel string
        """
        decision = self._evaluator.evaluate(task_description)
        self._latest_decision = decision
        return self.render()

    def render(self) -> str:
        """
        Render the delegation panel.

        Returns:
            Formatted multi-line panel string
        """
        if not self._latest_decision:
            return "No delegation decision available"

        decision = self._latest_decision
        lines = []

        # Header
        lines.append("+" + "-" * 58 + "+")
        lines.append("| DELEGATION: WHO DOES WHAT                           |")
        lines.append("+" + "-" * 58 + "+")

        # Execution class with icon
        icon = self._get_execution_icon(decision.execution_class)
        class_line = f"| {icon} Execution: {decision.execution_class.value:<30} |"
        lines.append(class_line)

        # Rationale
        rationale_wrapped = self._wrap_text(decision.rationale, 50)
        for i, line in enumerate(rationale_wrapped):
            if i == 0:
                lines.append(f"| Reason: {line:<49} |")
            else:
                lines.append(f"|         {line:<49} |")

        # Human actions (if any)
        if decision.required_human_actions:
            lines.append("|                                                    |")
            lines.append("| Required Human Actions:                            |")
            for action in decision.required_human_actions[:3]:  # Show first 3
                blocking = "[BLOCKED] " if action.is_blocking else "[PENDING] "
                action_line = f"|   {blocking}{action.action} (~{action.estimated_minutes}m)"
                action_line = action_line.ljust(59) + "|"
                lines.append(action_line)

        # Blocking status
        if decision.is_blocked:
            lines.append("|                                                    |")
            lines.append("| WARNING: BLOCKED - Cannot proceed without human    |")
            if decision.blocking_reason:
                reason_wrapped = self._wrap_text(decision.blocking_reason, 48)
                for i, line in enumerate(reason_wrapped):
                    if i == 0:
                        lines.append(f"|    {line:<49} |")
                    else:
                        lines.append(f"|    {line:<49} |")

        # Effort estimate
        if decision.estimated_human_effort > 0:
            effort_line = f"| Human Effort: {decision.estimated_human_effort} minutes".ljust(59) + "|"
            lines.append(effort_line)

        # Conditions
        if decision.conditions:
            lines.append("|                                                    |")
            lines.append("| Conditions:                                        |")
            for condition in decision.conditions[:2]:  # Show first 2
                cond_wrapped = self._wrap_text(condition, 46)
                for i, line in enumerate(cond_wrapped):
                    if i == 0:
                        lines.append(f"|   * {line:<46} |")
                    else:
                        lines.append(f"|     {line:<46} |")

        # Footer
        lines.append("+" + "-" * 58 + "+")

        return "\n".join(lines)

    def render_quick_summary(self) -> str:
        """Render a one-line delegation summary."""
        if not self._latest_decision:
            return "No delegation decision"

        return self._evaluator.get_quick_summary(self._latest_decision)

    def render_full_summary(self) -> str:
        """Render full delegation summary with all details."""
        if not self._latest_decision:
            return "No delegation decision"

        return self._evaluator.get_handoff_summary(self._latest_decision)

    def _get_execution_icon(self, execution_class: ExecutionClass) -> str:
        """Get icon for execution class."""
        if execution_class == ExecutionClass.AI_EXECUTABLE:
            return "[AUTO]"
        elif execution_class == ExecutionClass.HUMAN_REQUIRED:
            return "[HUMAN]"
        else:  # COLLABORATIVE
            return "[TEAM]"

    def _wrap_text(self, text: str, width: int = 50) -> List[str]:
        """
        Wrap text to specified width.

        Args:
            text: Text to wrap
            width: Target line width

        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            if sum(len(w) for w in current_line) + len(current_line) + len(word) <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines if lines else [""]


class DelegationPanelManager:
    """Manager for delegation panel integration with whiteboard."""

    def __init__(self):
        """Initialize panel manager."""
        self._panel = DelegationWhiteboardPanel()
        self._decisions: Dict[str, DelegationDecision] = {}

    def evaluate_and_store(self, task_id: str, task_description: str) -> DelegationDecision:
        """
        Evaluate task and store decision.

        Args:
            task_id: Unique task identifier
            task_description: Task description

        Returns:
            DelegationDecision
        """
        decision = self._panel._evaluator.evaluate(task_description)
        self._decisions[task_id] = decision
        self._panel.set_delegation_decision(decision)
        return decision

    def get_decision(self, task_id: str) -> Optional[DelegationDecision]:
        """Get stored decision."""
        return self._decisions.get(task_id)

    def render_for_task(self, task_id: str) -> str:
        """Render panel for specific task."""
        decision = self.get_decision(task_id)
        if decision:
            self._panel.set_delegation_decision(decision)
            return self._panel.render()
        return f"No decision for task {task_id}"

    def render_comparison(self, task_ids: List[str]) -> str:
        """
        Render comparison of multiple delegation decisions.

        Args:
            task_ids: List of task IDs to compare

        Returns:
            Formatted comparison string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("DELEGATION COMPARISON")
        lines.append("=" * 60)

        for task_id in task_ids:
            decision = self.get_decision(task_id)
            if decision:
                lines.append("")
                lines.append(f"Task: {task_id}")
                lines.append(f"  Execution: {decision.execution_class.value}")
                lines.append(f"  Blocked: {'Yes' if decision.is_blocked else 'No'}")
                lines.append(f"  Human Effort: {decision.estimated_human_effort} min")
                lines.append(f"  Actions: {len(decision.required_human_actions)}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

