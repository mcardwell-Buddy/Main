"""
Phase 9: Orchestration Whiteboard Panel

Visualizes mission queue, priorities, and deferred-but-good ideas.

Display elements:
  - Current mission (if any)
  - Mission queue (ranked by priority)
  - Paused good ideas (clearly labeled as "deferred")
  - Fatigue state and remaining budget
  - Recommendations

Hard constraints:
- NO autonomy (display only)
- NO execution instructions
- READ-ONLY visualization
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from backend.mission_orchestrator import (
    MissionOrchestrator, MissionEntry, MissionStatus, MissionPriority
)
from backend.fatigue_model import FatigueScore, FatigueState, DailyBudget


@dataclass
class OrchestrationDisplay:
    """Immutable orchestration view."""
    fatigue_state: FatigueState
    budget_used_pct: int
    active_mission: Optional[MissionEntry]
    queued_missions: List[MissionEntry]
    paused_missions: List[MissionEntry]
    priorities: List[MissionPriority]
    deferred_good_ideas: List[MissionEntry]
    recommendation: str
    reasoning: List[str]


class OrchestrationWhiteboardPanel:
    """Renders mission orchestration state to formatted display."""
    
    def __init__(self):
        """Initialize empty display."""
        self._fatigue_score: Optional[FatigueScore] = None
        self._orchestrator: Optional[MissionOrchestrator] = None
        self._budget: Optional[DailyBudget] = None
        self._priorities: List[MissionPriority] = []
        self._last_updated: datetime = datetime.utcnow()
    
    def set_orchestration_state(
        self,
        orchestrator: MissionOrchestrator,
        fatigue_score: FatigueScore,
        budget: DailyBudget,
        priorities: List[MissionPriority]
    ) -> None:
        """Update orchestration state for rendering."""
        self._orchestrator = orchestrator
        self._fatigue_score = fatigue_score
        self._budget = budget
        self._priorities = priorities
        self._last_updated = datetime.utcnow()
    
    def render(self) -> str:
        """Render complete orchestration panel."""
        if self._orchestrator is None or self._fatigue_score is None:
            return "No orchestration data available"
        
        lines = []
        lines.append("═" * 80)
        lines.append("MISSION ORCHESTRATION WHITEBOARD".center(80))
        lines.append("═" * 80)
        lines.append("")
        
        # Fatigue status
        lines.extend(self._render_fatigue_section())
        lines.append("")
        
        # Budget status
        lines.extend(self._render_budget_section())
        lines.append("")
        
        # Active mission
        lines.extend(self._render_active_section())
        lines.append("")
        
        # Queued missions
        lines.extend(self._render_queued_section())
        lines.append("")
        
        # Paused good ideas
        lines.extend(self._render_paused_section())
        lines.append("")
        
        # Recommendation
        lines.extend(self._render_recommendation_section())
        lines.append("")
        
        lines.append("═" * 80)
        timestamp = self._last_updated.strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"Updated: {timestamp}".rjust(80))
        
        return "\n".join(lines)
    
    def _render_fatigue_section(self) -> List[str]:
        """Render fatigue state section."""
        if self._fatigue_score is None:
            return ["[FATIGUE] Unknown state"]
        
        state = self._fatigue_score.state
        state_icon = self._get_state_icon(state)
        ratio_pct = int(self._fatigue_score.exhaustion_ratio * 100)
        
        lines = [
            f"[FATIGUE] {state_icon} {state.value}",
            f"          Exhaustion: {ratio_pct}%  |  Capacity: {int(self._fatigue_score.capacity_multiplier * 100)}%",
            f"          Max Complexity: {self._fatigue_score.complexity_threshold}",
            f"          Status: {self._fatigue_score.recommendation}"
        ]
        
        return lines
    
    def _render_budget_section(self) -> List[str]:
        """Render budget and effort section."""
        if self._budget is None:
            return ["[BUDGET] Unknown"]
        
        remaining = self._budget.remaining_minutes()
        total = self._budget.total_minutes
        used = self._budget.used_minutes
        
        # Draw budget bar
        bar_width = 40
        used_chars = int((used / total) * bar_width)
        bar = "█" * used_chars + "░" * (bar_width - used_chars)
        
        lines = [
            f"[BUDGET] Daily Effort Budget",
            f"         Progress: [{bar}]",
            f"         Used: {used}/{total} min  |  Remaining: {remaining} min"
        ]
        
        if remaining == 0:
            lines.append("         ⚠ Budget exhausted - new missions cannot start")
        
        return lines
    
    def _render_active_section(self) -> List[str]:
        """Render active mission section."""
        if self._orchestrator is None:
            return ["[ACTIVE] No active mission"]
        
        active = self._orchestrator.get_active_mission()
        if active is None:
            return ["[ACTIVE] No mission currently running"]
        
        roi = active.roi_ratio()
        lines = [
            f"[ACTIVE] ▶ {active.description}",
            f"         ID: {active.mission_id}",
            f"         Effort: {active.estimated_effort_minutes} min  |  Value: {active.estimated_payoff_minutes} min  |  ROI: {roi:.1f}x"
        ]
        
        if active.tradeoff_score:
            lines.append(f"         Decision: {active.tradeoff_score.decision.value}")
        
        return lines
    
    def _render_queued_section(self) -> List[str]:
        """Render mission queue section."""
        if self._orchestrator is None or not self._priorities:
            return ["[QUEUE] Empty"]
        
        lines = ["[QUEUE] Prioritized Missions"]
        
        for priority in self._priorities[:5]:  # Show top 5
            mission = self._orchestrator.get_mission(priority.mission_id)
            if mission is None:
                continue
            
            rank_str = f"#{priority.rank}".ljust(4)
            roi_str = f"{mission.roi_ratio():.1f}x ROI".ljust(12)
            effort_str = f"{mission.estimated_effort_minutes}m"
            
            # Truncate description to fit
            desc = mission.description[:45]
            if len(mission.description) > 45:
                desc += "..."
            
            lines.append(f"       {rank_str} {roi_str} {effort_str.rjust(6)}  {desc}")
            lines.append(f"              → {priority.reason}")
        
        queued_count = len(self._orchestrator.get_missions_by_status(MissionStatus.QUEUED))
        if queued_count > 5:
            lines.append(f"       ... and {queued_count - 5} more in queue")
        
        return lines
    
    def _render_paused_section(self) -> List[str]:
        """Render paused/deferred good ideas section."""
        if self._orchestrator is None:
            return []
        
        deferred = self._orchestrator.get_deferred_good_ideas()
        if not deferred:
            return []
        
        lines = ["[DEFERRED] Good Ideas Being Paused (High ROI, But Not Now)"]
        
        for mission in deferred[:3]:  # Show top 3 deferred
            roi = mission.roi_ratio()
            reason = mission.paused_reason or "Budget constraint"
            desc = mission.description[:50]
            if len(mission.description) > 50:
                desc += "..."
            
            lines.append(f"       ◆ {desc}")
            lines.append(f"         ROI: {roi:.1f}x | Effort: {mission.estimated_effort_minutes}m | Reason: {reason}")
        
        paused_count = len(self._orchestrator.get_missions_by_status(MissionStatus.PAUSED))
        if paused_count > 3:
            lines.append(f"       ... and {paused_count - 3} more deferred")
        
        return lines
    
    def _render_recommendation_section(self) -> List[str]:
        """Render recommendation section."""
        if self._fatigue_score is None:
            return []
        
        lines = ["[RECOMMENDATION]", ""]
        
        # Main recommendation
        lines.append(f"  {self._fatigue_score.recommendation}")
        lines.append("")
        
        # Key reasoning points
        if self._fatigue_score.reasoning:
            lines.append("  Key Factors:")
            for reason in self._fatigue_score.reasoning[:3]:
                lines.append(f"    • {reason}")
        
        return lines
    
    def render_quick_summary(self) -> str:
        """Render one-line orchestration summary."""
        if self._orchestrator is None or self._fatigue_score is None:
            return "No orchestration data"
        
        active_count = 1 if self._orchestrator.get_active_mission() else 0
        queued_count = len(self._orchestrator.get_missions_by_status(MissionStatus.QUEUED))
        paused_count = len(self._orchestrator.get_missions_by_status(MissionStatus.PAUSED))
        budget_pct = int(self._fatigue_score.exhaustion_ratio * 100)
        
        return (
            f"[{self._fatigue_score.state.value}] "
            f"Active: {active_count} | Queue: {queued_count} | "
            f"Deferred: {paused_count} | Budget: {budget_pct}%"
        )
    
    def render_portfolio_view(self) -> str:
        """Render portfolio analysis view."""
        if self._orchestrator is None:
            return "No portfolio data"
        
        lines = []
        lines.append("MISSION PORTFOLIO ANALYSIS".center(60))
        lines.append("=" * 60)
        
        total_missions = len(self._orchestrator._missions)
        active, queued, paused = self._orchestrator.get_queue_summary()
        
        lines.append(f"Total Missions: {total_missions}")
        lines.append(f"  Active:  {active}")
        lines.append(f"  Queued:  {queued}")
        lines.append(f"  Paused:  {paused}")
        lines.append("")
        
        # Effort analysis
        total_effort = self._orchestrator.get_total_effort()
        total_payoff = self._orchestrator.get_total_payoff()
        portfolio_roi = self._orchestrator.get_portfolio_roi()
        
        lines.append("Effort Analysis:")
        lines.append(f"  Total Effort:  {total_effort} minutes")
        lines.append(f"  Total Payoff:  {total_payoff} minutes")
        lines.append(f"  Portfolio ROI: {portfolio_roi:.1f}x")
        lines.append("")
        
        # Deferred good ideas
        deferred_good = self._orchestrator.get_deferred_good_ideas()
        if deferred_good:
            lines.append(f"Deferred Good Ideas: {len(deferred_good)}")
            total_deferred_roi = sum(m.roi_ratio() for m in deferred_good)
            avg_deferred_roi = total_deferred_roi / len(deferred_good)
            lines.append(f"  Average ROI: {avg_deferred_roi:.1f}x (being paused due to fatigue/budget)")
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_state_icon(state: FatigueState) -> str:
        """Get icon for fatigue state."""
        icons = {
            FatigueState.FRESH: "🟢",      # Green - go
            FatigueState.NORMAL: "🟡",     # Yellow - normal
            FatigueState.TIRED: "🟠",      # Orange - tired
            FatigueState.EXHAUSTED: "🔴",  # Red - stop
        }
        return icons.get(state, "⚪")
    
    @staticmethod
    def _wrap_text(text: str, width: int = 80) -> List[str]:
        """Wrap text to specified width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines


class OrchestrationPanelManager:
    """Manages orchestration panel for multiple mission sets."""
    
    def __init__(self):
        """Initialize panel store."""
        self._panels: Dict[str, OrchestrationWhiteboardPanel] = {}
        self._orchestrators: Dict[str, MissionOrchestrator] = {}
        self._fatigue_scores: Dict[str, FatigueScore] = {}
        self._budgets: Dict[str, DailyBudget] = {}
    
    def set_orchestration_panel(
        self,
        work_id: str,
        orchestrator: MissionOrchestrator,
        fatigue_score: FatigueScore,
        budget: DailyBudget,
        priorities: List[MissionPriority]
    ) -> None:
        """Set or update orchestration panel for work ID."""
        if work_id not in self._panels:
            self._panels[work_id] = OrchestrationWhiteboardPanel()
        
        panel = self._panels[work_id]
        panel.set_orchestration_state(orchestrator, fatigue_score, budget, priorities)
        
        self._orchestrators[work_id] = orchestrator
        self._fatigue_scores[work_id] = fatigue_score
        self._budgets[work_id] = budget
    
    def render_orchestration_panel(self, work_id: str) -> str:
        """Render orchestration panel for work ID."""
        panel = self._panels.get(work_id)
        if panel is None:
            return f"No orchestration panel for {work_id}"
        return panel.render()
    
    def get_panel_summary(self, work_id: str) -> str:
        """Get one-line summary for work ID."""
        panel = self._panels.get(work_id)
        if panel is None:
            return f"No panel for {work_id}"
        return panel.render_quick_summary()
    
    def get_portfolio_view(self, work_id: str) -> str:
        """Get portfolio analysis view for work ID."""
        panel = self._panels.get(work_id)
        if panel is None:
            return f"No portfolio data for {work_id}"
        return panel.render_portfolio_view()
    
    def get_all_panels_summary(self) -> str:
        """Get summary of all panels."""
        if not self._panels:
            return "No panels available"
        
        lines = ["=== ORCHESTRATION PANELS SUMMARY ===", ""]
        for work_id, panel in self._panels.items():
            summary = panel.render_quick_summary()
            lines.append(f"{work_id}: {summary}")
        
        return "\n".join(lines)
    
    def get_critical_alerts(self) -> List[str]:
        """Get list of critical alerts across all orchestrations."""
        alerts = []
        
        for work_id, fatigue in self._fatigue_scores.items():
            if fatigue.is_budget_exhausted():
                alerts.append(f"[ALERT] {work_id}: Daily budget exhausted!")
            elif fatigue.state == FatigueState.EXHAUSTED:
                recovery_time, msg = 180, "3+ hours or end of day break"
                alerts.append(f"[ALERT] {work_id}: Severe fatigue - {msg} needed")
        
        return alerts
