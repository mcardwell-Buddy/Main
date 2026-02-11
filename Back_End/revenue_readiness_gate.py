"""
Phase 12.4: Revenue Readiness Gate

Deterministic, read-only gate to determine if a build is eligible
for economic testing. No execution, no selling.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

from Back_End.build_registry import BuildRegistry
from Back_End.build_review import BuildReviewRegistry, BuildReviewVerdict
from Back_End.build_deliverable import DeliverableRegistry, DeliverableReadiness


@dataclass(frozen=True)
class RevenueReadinessResult:
    """Immutable revenue readiness result."""
    build_id: str
    ready: bool
    blocking_reasons: List[str]
    confidence: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "build_id": self.build_id,
            "ready": self.ready,
            "blocking_reasons": list(self.blocking_reasons),
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


class RevenueReadinessGate:
    """Deterministic revenue readiness evaluator (read-only)."""

    def __init__(
        self,
        build_registry: Optional[BuildRegistry] = None,
        deliverable_registry: Optional[DeliverableRegistry] = None,
        review_registry: Optional[BuildReviewRegistry] = None,
    ) -> None:
        self._build_registry = build_registry or BuildRegistry()
        self._deliverable_registry = deliverable_registry or DeliverableRegistry()
        self._review_registry = review_registry or BuildReviewRegistry()

    def evaluate(self, build_id: str) -> RevenueReadinessResult:
        """Evaluate readiness for a build (no side effects)."""
        builds = self._build_registry.get_latest_builds()
        build = builds.get(build_id)
        if build is None:
            return RevenueReadinessResult(
                build_id=build_id,
                ready=False,
                blocking_reasons=["build_not_found"],
                confidence=0.0,
                timestamp=datetime.utcnow().isoformat(),
            )

        deliverables = self._deliverable_registry.list_by_build(build_id)
        latest_review = self._review_registry.get_latest_review(build_id)

        return RevenueReadinessGate.evaluate_from_records(
            build_record={
                "build_id": build.build_id,
                "status": build.status.value,
                "current_stage": build.current_stage.value,
            },
            deliverable_records=[d.to_dict() for d in deliverables],
            latest_review_record=(latest_review.to_dict() if latest_review else None),
        )

    @staticmethod
    def evaluate_from_records(
        build_record: Dict[str, Any],
        deliverable_records: List[Dict[str, Any]],
        latest_review_record: Optional[Dict[str, Any]],
    ) -> RevenueReadinessResult:
        """Evaluate readiness using existing records (read-only)."""
        build_id = build_record.get("build_id", "")
        blocking: List[str] = []

        status = build_record.get("status")
        stage = build_record.get("current_stage")
        build_completed = status == "completed" or stage == "complete"
        if not build_completed:
            blocking.append("build_not_completed")

        deliverable_exists = len(deliverable_records) > 0
        if not deliverable_exists:
            blocking.append("no_deliverable")

        final_deliverable = False
        if deliverable_records:
            for d in deliverable_records:
                if d.get("readiness_state") == DeliverableReadiness.FINAL.value:
                    final_deliverable = True
                    break
        if not final_deliverable:
            blocking.append("deliverable_not_final")

        verdict_ok = False
        confidence = 0.0
        if latest_review_record:
            verdict_ok = latest_review_record.get("verdict") == BuildReviewVerdict.APPROVED.value
            confidence = float(latest_review_record.get("confidence", 0.0))
        if not verdict_ok:
            blocking.append("review_not_approved")
        if confidence < 0.7:
            blocking.append("review_confidence_below_threshold")

        ready = len(blocking) == 0
        return RevenueReadinessResult(
            build_id=build_id,
            ready=ready,
            blocking_reasons=blocking,
            confidence=confidence,
            timestamp=datetime.utcnow().isoformat(),
        )

    @staticmethod
    def emit_readiness_signal(
        result: RevenueReadinessResult,
        stream_file: Optional[Path] = None,
    ) -> None:
        """Emit readiness signal to learning_signals.jsonl (append-only)."""
        if stream_file is None:
            stream_file = Path("outputs/phase25/learning_signals.jsonl")
        stream_file.parent.mkdir(parents=True, exist_ok=True)

        signal = {
            "signal_type": "revenue_readiness_evaluated",
            "signal_layer": "economic",
            "signal_source": "revenue_gate",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": result.to_dict(),
        }

        with stream_file.open("a", encoding="utf-8") as f:
            json.dump(signal, f)
            f.write("\n")

