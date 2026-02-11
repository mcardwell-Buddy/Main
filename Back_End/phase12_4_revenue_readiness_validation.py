"""
Phase 12.4: Revenue Readiness Gate Validation

Validates:
- Gate conditions
- Signal emission
- Read-only evaluation
"""

import unittest
import tempfile
from pathlib import Path
import json

from Back_End.build_contract import BuildContract, BuildType, BuildStage, BuildStatus
from Back_End.build_registry import BuildRegistry
from Back_End.build_deliverable import (
    BuildDeliverable,
    DeliverableRegistry,
    DeliverableReadiness,
    DeliverableType,
)
from Back_End.build_review import BuildReview, BuildReviewRegistry, BuildReviewVerdict, BuildReviewer
from Back_End.revenue_readiness_gate import RevenueReadinessGate


class TestRevenueReadinessGate(unittest.TestCase):
    """Revenue readiness gate tests."""

    def test_gate_ready(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            build_registry = BuildRegistry(output_dir=Path(tmpdir))
            deliverable_registry = DeliverableRegistry(stream_file=Path(tmpdir) / "build_deliverables.jsonl")
            review_registry = BuildReviewRegistry(stream_file=Path(tmpdir) / "build_reviews.jsonl")

            build = BuildContract.new(
                name="Revenue Build",
                objective="Ship deliverable",
                build_type=BuildType.SOFTWARE,
                current_stage=BuildStage.COMPLETE,
                status=BuildStatus.COMPLETED,
            )
            build_registry.register_build(build)

            deliverable = BuildDeliverable.new(
                build_id=build.build_id,
                deliverable_type=DeliverableType.REPORT,
                format="pdf",
                description="Final report",
                completeness_score=1.0,
                readiness_state=DeliverableReadiness.FINAL,
            )
            deliverable_registry.register_deliverable(deliverable)

            review = BuildReview.new(
                build_id=build.build_id,
                reviewer=BuildReviewer.USER,
                verdict=BuildReviewVerdict.APPROVED,
                rationale="Approved",
                confidence=0.8,
            )
            review_registry.register_review(review)

            gate = RevenueReadinessGate(
                build_registry=build_registry,
                deliverable_registry=deliverable_registry,
                review_registry=review_registry,
            )
            result = gate.evaluate(build.build_id)

            self.assertTrue(result.ready)
            self.assertEqual(result.blocking_reasons, [])
            self.assertGreaterEqual(result.confidence, 0.7)

    def test_gate_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            build_registry = BuildRegistry(output_dir=Path(tmpdir))
            deliverable_registry = DeliverableRegistry(stream_file=Path(tmpdir) / "build_deliverables.jsonl")
            review_registry = BuildReviewRegistry(stream_file=Path(tmpdir) / "build_reviews.jsonl")

            build = BuildContract.new(
                name="Blocked Build",
                objective="Not ready",
                build_type=BuildType.SOFTWARE,
                current_stage=BuildStage.IMPLEMENTATION,
                status=BuildStatus.ACTIVE,
            )
            build_registry.register_build(build)

            gate = RevenueReadinessGate(
                build_registry=build_registry,
                deliverable_registry=deliverable_registry,
                review_registry=review_registry,
            )
            result = gate.evaluate(build.build_id)

            self.assertFalse(result.ready)
            self.assertIn("build_not_completed", result.blocking_reasons)

    def test_signal_emission(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stream_file = Path(tmpdir) / "learning_signals.jsonl"

            build_registry = BuildRegistry(output_dir=Path(tmpdir))
            deliverable_registry = DeliverableRegistry(stream_file=Path(tmpdir) / "build_deliverables.jsonl")
            review_registry = BuildReviewRegistry(stream_file=Path(tmpdir) / "build_reviews.jsonl")

            build = BuildContract.new(
                name="Signal Build",
                objective="Emit signal",
                build_type=BuildType.SOFTWARE,
                current_stage=BuildStage.COMPLETE,
                status=BuildStatus.COMPLETED,
            )
            build_registry.register_build(build)

            deliverable_registry.register_deliverable(BuildDeliverable.new(
                build_id=build.build_id,
                deliverable_type=DeliverableType.DOCUMENT,
                format="markdown",
                description="Final doc",
                completeness_score=1.0,
                readiness_state=DeliverableReadiness.FINAL,
            ))

            review_registry.register_review(BuildReview.new(
                build_id=build.build_id,
                reviewer=BuildReviewer.BUDDY,
                verdict=BuildReviewVerdict.APPROVED,
                rationale="Approved",
                confidence=0.9,
            ))

            gate = RevenueReadinessGate(
                build_registry=build_registry,
                deliverable_registry=deliverable_registry,
                review_registry=review_registry,
            )
            result = gate.evaluate(build.build_id)
            gate.emit_readiness_signal(result, stream_file=stream_file)

            data = json.loads(stream_file.read_text(encoding="utf-8").strip())
            self.assertEqual(data["signal_type"], "revenue_readiness_evaluated")
            self.assertEqual(data["signal_layer"], "economic")
            self.assertEqual(data["signal_source"], "revenue_gate")


if __name__ == "__main__":
    unittest.main()

