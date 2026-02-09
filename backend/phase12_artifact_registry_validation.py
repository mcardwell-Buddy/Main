"""
Phase 12: Artifact Registry Validation

Validates:
- JSONL persistence
- Mission attribution
- Whiteboard artifacts summary
- No behavior changes
"""

import unittest
import tempfile
import os
import json
import importlib
from pathlib import Path

from backend.artifact_registry import Artifact, ArtifactType, PresentationHint, ArtifactStatus
from backend.artifact_registry_store import ArtifactRegistryStore


class TestArtifactRegistry(unittest.TestCase):
    def test_registry_and_whiteboard_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_file = Path(tmpdir) / "artifacts.jsonl"
            missions_file = Path(tmpdir) / "missions.jsonl"
            signals_file = Path(tmpdir) / "learning_signals.jsonl"

            # Ensure empty mission/signal files exist
            missions_file.write_text("", encoding="utf-8")
            signals_file.write_text("", encoding="utf-8")

            os.environ["ARTIFACTS_FILE"] = str(artifacts_file)
            os.environ["MISSIONS_FILE"] = str(missions_file)
            os.environ["LEARNING_SIGNALS_FILE"] = str(signals_file)

            registry = ArtifactRegistryStore(stream_file=artifacts_file)

            # Register 3 artifacts, 2 tied to mission_id
            artifact1 = Artifact.new(
                artifact_type=ArtifactType.REPORT,
                title="Mission Report",
                description="Summary report",
                created_by="mission_123",
                source_module="test",
                presentation_hint=PresentationHint.DOCUMENT,
                confidence=0.9,
                tags=["mission"],
                status=ArtifactStatus.FINAL,
            )
            artifact2 = Artifact.new(
                artifact_type=ArtifactType.DATASET,
                title="Mission Dataset",
                description="Collected dataset",
                created_by="mission_123",
                source_module="test",
                presentation_hint=PresentationHint.TABLE,
                confidence=0.8,
                tags=["mission"],
                status=ArtifactStatus.DRAFT,
            )
            artifact3 = Artifact.new(
                artifact_type=ArtifactType.LOG,
                title="System Log",
                description="System log",
                created_by="manual",
                source_module="test",
                presentation_hint=PresentationHint.TEXT,
                status=ArtifactStatus.FINAL,
            )

            registry.register_artifact(artifact1)
            registry.register_artifact(artifact2)
            registry.register_artifact(artifact3)

            # Confirm persistence
            lines = artifacts_file.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 3)
            data = json.loads(lines[0])
            self.assertIn("artifact_id", data)

            # Reload whiteboard to pick env vars
            import backend.whiteboard.mission_whiteboard as mission_whiteboard
            importlib.reload(mission_whiteboard)

            summary = mission_whiteboard.get_mission_whiteboard("mission_123")
            artifacts_summary = summary.get("artifacts_summary", {})
            self.assertEqual(artifacts_summary.get("artifact_count"), 2)
            self.assertIn("report", artifacts_summary.get("artifact_types", []))
            self.assertIn("dataset", artifacts_summary.get("artifact_types", []))


if __name__ == "__main__":
    unittest.main()
