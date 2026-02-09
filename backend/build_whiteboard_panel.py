"""
Phase 11: Build Whiteboard Panel

Read-only visualization of Build state.
No autonomy, no execution, no UI redesign.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from backend.build_contract import BuildContract, BuildStage
from backend.build_registry import BuildRegistry
from backend.build_stage_evaluator import BuildStageEvaluation
from backend.artifact_registry import BuildArtifactRegistry


@dataclass
class BuildWhiteboardDisplay:
    """Immutable view of build state."""
    active_builds: List[BuildContract]
    paused_builds: List[BuildContract]
    completed_builds: List[BuildContract]
    evaluations: Dict[str, BuildStageEvaluation]
    last_updated: datetime


class BuildWhiteboardPanel:
    """Renders build intelligence panel."""

    def __init__(self) -> None:
        self._build_registry: Optional[BuildRegistry] = None
        self._artifact_registry: Optional[BuildArtifactRegistry] = None
        self._evaluations: Dict[str, BuildStageEvaluation] = {}
        self._last_updated = datetime.utcnow()

    def set_sources(
        self,
        build_registry: BuildRegistry,
        artifact_registry: Optional[BuildArtifactRegistry] = None,
        evaluations: Optional[Dict[str, BuildStageEvaluation]] = None,
    ) -> None:
        """Set registries and evaluations for rendering."""
        self._build_registry = build_registry
        self._artifact_registry = artifact_registry
        self._evaluations = evaluations or {}
        self._last_updated = datetime.utcnow()

    def render(self) -> str:
        """Render full build panel."""
        if self._build_registry is None:
            return "No build registry available"

        builds = list(self._build_registry.get_latest_builds().values())
        active = [b for b in builds if b.status.value == "active"]
        paused = [b for b in builds if b.status.value == "paused"]
        completed = [b for b in builds if b.status.value == "completed"]

        lines: List[str] = []
        lines.append("═" * 80)
        lines.append("BUILD INTELLIGENCE WHITEBOARD".center(80))
        lines.append("═" * 80)
        lines.append("")

        lines.extend(self._render_summary(active, paused, completed))
        lines.append("")

        lines.extend(self._render_active_builds(active))
        lines.append("")

        if paused:
            lines.extend(self._render_paused_builds(paused))
            lines.append("")

        if completed:
            lines.extend(self._render_completed_builds(completed))
            lines.append("")

        lines.append("═" * 80)
        timestamp = self._last_updated.strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"Updated: {timestamp}".rjust(80))
        return "\n".join(lines)

    def render_quick_summary(self) -> str:
        """Render quick one-line summary."""
        if self._build_registry is None:
            return "[BUILD] No registry"

        builds = list(self._build_registry.get_latest_builds().values())
        active = len([b for b in builds if b.status.value == "active"])
        paused = len([b for b in builds if b.status.value == "paused"])
        completed = len([b for b in builds if b.status.value == "completed"])
        return f"[BUILD] Active: {active} | Paused: {paused} | Completed: {completed}"

    def _render_summary(
        self,
        active: List[BuildContract],
        paused: List[BuildContract],
        completed: List[BuildContract],
    ) -> List[str]:
        total = len(active) + len(paused) + len(completed)
        return [
            "[SUMMARY]",
            f"  Total Builds: {total}",
            f"  Active: {len(active)}  |  Paused: {len(paused)}  |  Completed: {len(completed)}",
        ]

    def _render_active_builds(self, builds: List[BuildContract]) -> List[str]:
        if not builds:
            return ["[ACTIVE] No active builds"]

        lines = ["[ACTIVE] Current Builds"]
        for build in builds:
            evaluation = self._evaluations.get(build.build_id)
            readiness = self._format_readiness(evaluation)
            mission_count = len(build.mission_ids)
            artifact_count = self._artifact_count(build.build_id, build)
            investment = "n/a" if build.investment_score is None else f"{build.investment_score:.2f}"

            lines.append(
                f"  ◆ {build.name} ({build.build_type.value})"
            )
            lines.append(
                f"    ID: {build.build_id} | Stage: {build.current_stage.value} | Status: {build.status.value}"
            )
            lines.append(
                f"    Missions: {mission_count} | Artifacts: {artifact_count} | Investment: {investment}"
            )
            lines.append(
                f"    Readiness: {readiness}"
            )
        return lines

    def _render_paused_builds(self, builds: List[BuildContract]) -> List[str]:
        lines = ["[PAUSED] Builds on Hold"]
        for build in builds:
            lines.append(
                f"  ◇ {build.name} | Stage: {build.current_stage.value} | Status: {build.status.value}"
            )
        return lines

    def _render_completed_builds(self, builds: List[BuildContract]) -> List[str]:
        lines = ["[COMPLETED] Finished Builds"]
        for build in builds:
            lines.append(
                f"  ■ {build.name} | Stage: {build.current_stage.value} | Status: {build.status.value}"
            )
        return lines

    def _artifact_count(self, build_id: str, build: BuildContract) -> int:
        if self._artifact_registry is None:
            return len(build.artifact_ids)
        return len(self._artifact_registry.get_artifacts_for_build(build_id))

    def _format_readiness(self, evaluation: Optional[BuildStageEvaluation]) -> str:
        if evaluation is None:
            return "unknown"
        if evaluation.is_ready:
            next_stage = evaluation.next_stage.value if evaluation.next_stage else "n/a"
            return f"ready → {next_stage} ({evaluation.readiness_score:.2f})"
        if evaluation.blocking_reasons:
            return f"blocked ({', '.join(evaluation.blocking_reasons)})"
        return f"not ready ({evaluation.readiness_score:.2f})"
