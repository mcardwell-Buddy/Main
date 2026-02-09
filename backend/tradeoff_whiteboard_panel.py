"""
Phase 8: Whiteboard Economic Panel

Exposes economic tradeoff reasoning in the Whiteboard.

Panels:
- Tradeoff Decision (proceed/pause/reject)
- ROI Analysis (raw vs adjusted)
- Opportunity Cost
- Value Type & Reusability

Read-only, default-visible, non-executing.
"""

from typing import Optional, Dict, Any, List
from backend.tradeoff_evaluator import TradeoffEvaluator, TradeoffScore, TradeoffOpportunity


class EconomicWhiteboardPanel:
    """Renders economic tradeoff intelligence for the Whiteboard."""

    def __init__(self):
        """Initialize economic panel."""
        self._evaluator = TradeoffEvaluator()
        self._latest_score: Optional[TradeoffScore] = None

    def set_tradeoff_score(self, score: TradeoffScore) -> None:
        """Set the latest tradeoff score for rendering."""
        self._latest_score = score

    def evaluate_and_render(self, opportunity: TradeoffOpportunity) -> str:
        """
        Evaluate opportunity and render the economic panel.

        Args:
            opportunity: TradeoffOpportunity to analyze

        Returns:
            Formatted panel string
        """
        score = self._evaluator.evaluate(opportunity)
        self._latest_score = score
        return self.render()

    def render(self) -> str:
        """
        Render the economic panel.

        Returns:
            Formatted multi-line panel string
        """
        if not self._latest_score:
            return "No tradeoff score available"

        score = self._latest_score
        lines = []

        # Header
        lines.append("+" + "-" * 58 + "+")
        lines.append("|" + " ECONOMIC TRADEOFF: IS THIS WORTH DOING?".ljust(58) + "|")
        lines.append("+" + "-" * 58 + "+")

        # Decision with color coding
        decision_icon = self._get_decision_icon(score.decision.value)
        decision_line = f"| {decision_icon} Decision: {score.decision.value:<32} |"
        lines.append(decision_line)

        # Adjusted value (after cognitive load adjustment)
        value_line = f"| Value Score: {score.adjusted_value:.2f}x (after adjustments)".ljust(59) + "|"
        lines.append(value_line)

        # ROI Analysis
        lines.append("|" + " " * 58 + "|")
        lines.append("| ROI Analysis:".ljust(59) + "|")
        roi_raw = f"  Raw ROI: {score.roi_ratio:.2f}x ({score.estimated_payoff_minutes}m payoff / {score.time_cost_minutes}m effort)"
        roi_lines = self._wrap_text(roi_raw, 53)
        for i, line in enumerate(roi_lines):
            if i == 0:
                lines.append(f"|   {line:<54} |")
            else:
                lines.append(f"|   {line:<54} |")

        # Cognitive Load Impact
        lines.append("|" + " " * 58 + "|")
        load_text = f"Cognitive Load: {score.cognitive_load.value}"
        lines.append(f"| {load_text:<57} |")

        # Value Type
        value_text = f"Value Type: {score.value_type.value}"
        lines.append(f"| {value_text:<57} |")

        # Opportunity Cost
        opp_cost_pct = f"{score.opportunity_cost_score * 100:.0f}%"
        opp_text = f"Opportunity Cost: {opp_cost_pct} of available time"
        lines.append(f"| {opp_text:<57} |")

        # Confidence
        conf_pct = f"{score.confidence * 100:.0f}%"
        conf_line = f"| Confidence: {conf_pct}".ljust(59) + "|"
        lines.append(conf_line)

        # Rationale
        lines.append("|" + " " * 58 + "|")
        lines.append("| Reasoning:".ljust(59) + "|")
        rationale_lines = self._wrap_text(score.rationale, 52)
        for line in rationale_lines[:5]:  # Show first 5 lines of rationale
            lines.append(f"|   {line:<54} |")

        # Key Factors
        if score.key_factors:
            lines.append("|" + " " * 58 + "|")
            lines.append("| Key Factors:".ljust(59) + "|")
            for factor in score.key_factors[:4]:  # Show first 4 factors
                factor_line = f"  {factor}"
                factor_lines = self._wrap_text(factor_line, 52)
                for i, fline in enumerate(factor_lines):
                    if i == 0:
                        lines.append(f"|   {fline:<54} |")
                    else:
                        lines.append(f"|   {fline:<54} |")

        # Footer with decision guidance
        lines.append("|" + " " * 58 + "|")
        if score.decision.value == "PROCEED":
            guidance = "Go ahead - value justifies effort"
        elif score.decision.value == "PAUSE":
            guidance = "Consider deferring - marginal value"
        else:  # REJECT
            guidance = "Skip this - insufficient payoff"
        guidance_line = f"| {guidance:<57} |"
        lines.append(guidance_line)

        # Footer
        lines.append("+" + "-" * 58 + "+")

        return "\n".join(lines)

    def render_quick_summary(self) -> str:
        """Render a one-line summary."""
        if not self._latest_score:
            return "No tradeoff score"

        return self._evaluator.get_quick_summary(self._latest_score)

    def render_full_summary(self) -> str:
        """Render full economic summary."""
        if not self._latest_score:
            return "No tradeoff score"

        return self._evaluator.get_full_summary(self._latest_score)

    def render_portfolio_view(self, scores: List[TradeoffScore]) -> str:
        """
        Render comparison of multiple opportunities.

        Shows portfolio of work sorted by value.
        """
        if not scores:
            return "No opportunities to analyze"

        lines = []
        lines.append("=" * 70)
        lines.append("ECONOMIC PORTFOLIO VIEW")
        lines.append("=" * 70)

        # Sort by value descending
        sorted_scores = sorted(scores, key=lambda s: s.adjusted_value, reverse=True)

        for i, score in enumerate(sorted_scores, 1):
            icon = self._get_decision_icon(score.decision.value)
            value_text = f"{score.adjusted_value:.2f}x"
            roi_text = f"({score.roi_ratio:.2f}x ROI)"
            effort_text = f"{score.time_cost_minutes}m effort"

            lines.append(
                f"[{i}] {icon} {value_text:<8} {roi_text:<12} {effort_text:<15}"
            )
            lines.append(f"     Decision: {score.decision.value}")
            lines.append(f"     Load: {score.cognitive_load.value} | Type: {score.value_type.value}")

        lines.append("=" * 70)
        return "\n".join(lines)

    @staticmethod
    def _get_decision_icon(decision: str) -> str:
        """Get icon for decision."""
        if decision == "PROCEED":
            return "[GO]"
        elif decision == "PAUSE":
            return "[WAIT]"
        else:  # REJECT
            return "[SKIP]"

    @staticmethod
    def _wrap_text(text: str, width: int = 50) -> List[str]:
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


class EconomicPanelManager:
    """Manager for economic panel integration with whiteboard."""

    def __init__(self):
        """Initialize panel manager."""
        self._panel = EconomicWhiteboardPanel()
        self._scores: Dict[str, TradeoffScore] = {}

    def evaluate_and_store(
        self,
        work_id: str,
        opportunity: TradeoffOpportunity
    ) -> TradeoffScore:
        """
        Evaluate opportunity and store score.

        Args:
            work_id: Unique work identifier
            opportunity: TradeoffOpportunity to evaluate

        Returns:
            TradeoffScore
        """
        score = self._panel._evaluator.evaluate(opportunity)
        self._scores[work_id] = score
        self._panel.set_tradeoff_score(score)
        return score

    def get_score(self, work_id: str) -> Optional[TradeoffScore]:
        """Get stored score."""
        return self._scores.get(work_id)

    def render_for_work(self, work_id: str) -> str:
        """Render panel for specific work."""
        score = self.get_score(work_id)
        if score:
            self._panel.set_tradeoff_score(score)
            return self._panel.render()
        return f"No score for work {work_id}"

    def get_proceed_work(self) -> List[tuple]:
        """Get all work recommended to proceed."""
        return [
            (wid, score) for wid, score in self._scores.items()
            if score.decision.value == "PROCEED"
        ]

    def get_pause_work(self) -> List[tuple]:
        """Get all work recommended to pause."""
        return [
            (wid, score) for wid, score in self._scores.items()
            if score.decision.value == "PAUSE"
        ]

    def get_reject_work(self) -> List[tuple]:
        """Get all work recommended to reject."""
        return [
            (wid, score) for wid, score in self._scores.items()
            if score.decision.value == "REJECT"
        ]

    def get_portfolio_summary(self) -> str:
        """Get portfolio view of all work."""
        if not self._scores:
            return "No work analyzed yet"

        scores = list(self._scores.values())
        return self._panel.render_portfolio_view(scores)

    def get_total_recommended_effort(self) -> int:
        """Total minutes recommended to proceed."""
        proceed_work = self.get_proceed_work()
        return sum(score.time_cost_minutes for _, score in proceed_work)
