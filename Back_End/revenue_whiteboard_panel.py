"""
Phase 12.5: Whiteboard Revenue Panels

Read-only economic observability panels (no actions, no execution).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

from Back_End.build_registry import BuildRegistry
from Back_End.build_deliverable import DeliverableRegistry
from Back_End.build_review import BuildReviewRegistry
from Back_End.revenue_readiness_gate import RevenueReadinessGate
from Back_End.economic_scenario import EconomicScenarioRegistry


REVENUE_SIGNALS_FILE = Path("outputs/phase25/revenue_signals.jsonl")


@dataclass
class RevenueWhiteboardDisplay:
    """Immutable revenue whiteboard view."""
    build_outputs_panel: str
    revenue_signals_panel: str
    readiness_funnel_panel: str
    last_updated: datetime


class RevenueWhiteboardPanel:
    """Renders revenue observability panels."""

    def __init__(self) -> None:
        self._build_registry = BuildRegistry()
        self._deliverable_registry = DeliverableRegistry()
        self._review_registry = BuildReviewRegistry()
        self._readiness_gate = RevenueReadinessGate(
            build_registry=self._build_registry,
            deliverable_registry=self._deliverable_registry,
            review_registry=self._review_registry,
        )
        self._scenario_registry = EconomicScenarioRegistry()
        self._last_updated = datetime.utcnow()

    def render(self) -> str:
        """Render all revenue panels as a single display."""
        self._last_updated = datetime.utcnow()

        sections = [
            "═" * 80,
            "REVENUE WHITEBOARD PANELS".center(80),
            "═" * 80,
            "",
            self.render_build_outputs_panel(),
            "",
            self.render_revenue_signals_panel(),
            "",
            self.render_simulation_panel(),
            "",
            self.render_readiness_funnel(),
            "",
            "═" * 80,
            f"Updated: {self._last_updated.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]
        return "\n".join(sections)

    def render_build_outputs_panel(self) -> str:
        """Panel: Builds, Deliverables, Readiness, Review verdicts."""
        builds = self._build_registry.get_latest_builds()
        deliverables = self._deliverable_registry
        reviews = self._review_registry

        lines: List[str] = ["[BUILD OUTPUTS PANEL]"]
        if not builds:
            lines.append("  No builds available")
            return "\n".join(lines)

        for build in builds.values():
            build_deliverables = deliverables.list_by_build(build.build_id)
            latest_review = reviews.get_latest_review(build.build_id)
            readiness = self._readiness_gate.evaluate(build.build_id)

            deliverable_summary = "none" if not build_deliverables else f"{len(build_deliverables)}"
            verdict = latest_review.verdict.value if latest_review else "none"
            confidence = latest_review.confidence if latest_review else None
            readiness_state = "ready" if readiness.ready else "blocked"

            lines.append(
                f"  ◆ {build.name} | Stage: {build.current_stage.value} | Status: {build.status.value}"
            )
            lines.append(
                f"    Deliverables: {deliverable_summary} | Readiness: {readiness_state}"
            )
            if latest_review:
                lines.append(
                    f"    Review: {verdict} (confidence={confidence:.2f})"
                )
            else:
                lines.append("    Review: none")

        return "\n".join(lines)

    def render_revenue_signals_panel(self) -> str:
        """Panel: Revenue signal counts and timeline summary."""
        records = self._read_revenue_signals()
        lines: List[str] = ["[REVENUE SIGNALS PANEL]"]

        if not records:
            lines.append("  No revenue signals recorded")
            return "\n".join(lines)

        # Count by type
        counts: Dict[str, int] = {}
        for r in records:
            sig_type = r.get("signal_type") or r.get("signal_type", "unknown")
            counts[sig_type] = counts.get(sig_type, 0) + 1

        lines.append("  Signal counts by type:")
        for sig_type, count in sorted(counts.items()):
            lines.append(f"    - {sig_type}: {count}")

        # Confidence timeline (latest 5)
        timeline = []
        for r in records[-5:]:
            timeline.append({
                "timestamp": r.get("timestamp"),
                "confidence": r.get("confidence") or r.get("payload", {}).get("confidence"),
                "mission_id": r.get("mission_id") or r.get("payload", {}).get("mission_id"),
                "build_id": r.get("build_id") or r.get("payload", {}).get("build_id"),
            })

        lines.append("  Confidence timeline (latest 5):")
        for t in timeline:
            lines.append(
                f"    - {t.get('timestamp')} | confidence={t.get('confidence')} | "
                f"mission={t.get('mission_id')} | build={t.get('build_id')}"
            )

        # Attribution summary
        mission_count = len({r.get("mission_id") for r in records if r.get("mission_id")})
        build_count = len({r.get("build_id") for r in records if r.get("build_id")})
        lines.append(f"  Mission attribution: {mission_count}")
        lines.append(f"  Build attribution: {build_count}")

        return "\n".join(lines)

    def render_readiness_funnel(self) -> str:
        """Panel: Readiness funnel across builds."""
        builds = list(self._build_registry.get_latest_builds().values())
        deliverables = self._deliverable_registry
        reviews = self._review_registry

        builds_started = len(builds)
        deliverables_produced = 0
        approved_builds = 0
        revenue_ready_builds = 0

        for build in builds:
            if deliverables.list_by_build(build.build_id):
                deliverables_produced += 1
            latest_review = reviews.get_latest_review(build.build_id)
            if latest_review and latest_review.verdict.value == "approved":
                approved_builds += 1
            readiness = self._readiness_gate.evaluate(build.build_id)
            if readiness.ready:
                revenue_ready_builds += 1

        lines = ["[READINESS FUNNEL]"]
        lines.append(f"  Builds started: {builds_started}")
        lines.append(f"  Deliverables produced: {deliverables_produced}")
        lines.append(f"  Approved builds: {approved_builds}")
        lines.append(f"  Revenue-ready builds: {revenue_ready_builds}")
        return "\n".join(lines)

    def render_simulation_panel(self) -> str:
        """Panel: Economic scenarios (simulation-only)."""
        scenarios = self._scenario_registry.list_all()
        lines = ["[ECONOMIC SCENARIOS]", "  SIMULATION - NO MONEY MOVED"]

        if not scenarios:
            lines.append("  No scenarios recorded")
            return "\n".join(lines)

        lines.append(f"  Total scenarios: {len(scenarios)}")
        for scenario in scenarios[-5:]:
            lines.append(
                "  ◆ "
                f"build={scenario.build_id} | price={scenario.hypothetical_price} | "
                f"response_rate={scenario.hypothetical_response_rate} | risk={scenario.risk_level} | "
                f"confidence={scenario.confidence}"
            )
        return "\n".join(lines)

    @staticmethod
    def _read_revenue_signals() -> List[Dict[str, Any]]:
        if not REVENUE_SIGNALS_FILE.exists():
            return []
        records: List[Dict[str, Any]] = []
        with REVENUE_SIGNALS_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

