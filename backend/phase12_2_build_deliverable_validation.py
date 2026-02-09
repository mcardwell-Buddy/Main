"""
Phase 12.2: Build Deliverable Validation

Validates:
- Build produces deliverable
- Deliverable persists
- Read-only access works
"""

import unittest
import tempfile
from pathlib import Path

from backend.build_deliverable import (
    BuildDeliverable,
    DeliverableRegistry,
    DeliverableType,
    DeliverableReadiness,
)


class TestBuildDeliverable(unittest.TestCase):
    """Deliverable creation tests."""

    def test_build_produces_deliverable(self):
        deliverable = BuildDeliverable.new(
            build_id="build_1",
            deliverable_type=DeliverableType.REPORT,
            format="pdf",
            description="Monthly performance report",
            completeness_score=0.9,
            readiness_state=DeliverableReadiness.REVIEWABLE,
            mission_id="mission_1",
        )

        self.assertIsNotNone(deliverable.deliverable_id)
        self.assertEqual(deliverable.build_id, "build_1")
        self.assertEqual(deliverable.deliverable_type, DeliverableType.REPORT)
        self.assertEqual(deliverable.readiness_state, DeliverableReadiness.REVIEWABLE)


class TestDeliverableRegistry(unittest.TestCase):
    """Deliverable registry tests."""

    def test_deliverable_persists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "build_deliverables.jsonl"
            registry = DeliverableRegistry(stream_file=path)

            deliverable = BuildDeliverable.new(
                build_id="build_2",
                deliverable_type=DeliverableType.DATASET,
                format="csv",
                description="Aggregated dataset",
                completeness_score=1.0,
                readiness_state=DeliverableReadiness.FINAL,
                mission_id="mission_2",
            )

            registry.register_deliverable(deliverable)
            self.assertTrue(path.exists())

            by_build = registry.list_by_build("build_2")
            self.assertEqual(len(by_build), 1)
            self.assertEqual(by_build[0].deliverable_id, deliverable.deliverable_id)

            by_mission = registry.list_by_mission("mission_2")
            self.assertEqual(len(by_mission), 1)
            self.assertEqual(by_mission[0].build_id, "build_2")

    def test_read_only_access(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "build_deliverables.jsonl"
            registry = DeliverableRegistry(stream_file=path)

            deliverable = BuildDeliverable.new(
                build_id="build_3",
                deliverable_type=DeliverableType.DOCUMENT,
                format="markdown",
                description="Architecture summary",
                completeness_score=0.7,
                readiness_state=DeliverableReadiness.DRAFT,
            )

            registry.register_deliverable(deliverable)

            # Read-only access should not mutate data
            before = registry.list_by_build("build_3")[0].to_dict()
            after = registry.list_by_build("build_3")[0].to_dict()
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
