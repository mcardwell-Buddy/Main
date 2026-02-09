"""
Phase 11: Build Module Validation

Validates:
- Build persistence
- Deterministic stage evaluation
- Artifact attachment
- Build signals
- Whiteboard display
- No autonomy introduced
"""

import unittest
import tempfile
from pathlib import Path

from backend.build_contract import BuildContract, BuildType, BuildStage, BuildStatus
from backend.build_registry import BuildRegistry
from backend.build_stage_evaluator import BuildStageEvaluator
from backend.build_signal_emitter import BuildSignalEmitter
from backend.artifact_registry import BuildArtifactRegistry
from backend.build_whiteboard_panel import BuildWhiteboardPanel


class TestBuildContract(unittest.TestCase):
    """Test BuildContract serialization."""

    def test_build_contract_serialization(self):
        build = BuildContract.new(
            name="Test Build",
            objective="Create a reporting system",
            build_type=BuildType.SOFTWARE,
            current_stage=BuildStage.DESIGN,
            mission_ids=["m1", "m2"],
            artifact_ids=["a1"],
            investment_score=0.72,
            status=BuildStatus.ACTIVE,
        )

        data = build.to_dict()
        restored = BuildContract.from_dict(data)

        self.assertEqual(build.build_id, restored.build_id)
        self.assertEqual(build.name, restored.name)
        self.assertEqual(build.current_stage, restored.current_stage)
        self.assertEqual(build.status, restored.status)
        self.assertEqual(build.investment_score, restored.investment_score)


class TestBuildRegistry(unittest.TestCase):
    """Test BuildRegistry persistence."""

    def test_register_and_reconstruct(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = BuildRegistry(output_dir=Path(tmpdir))

            build = BuildContract.new(
                name="Alpha",
                objective="Build dashboard",
                build_type=BuildType.SOFTWARE,
                mission_ids=["m1"],
            )

            registry.register_build(build)
            registry.update_stage(build.build_id, BuildStage.IMPLEMENTATION, "design_ready")
            registry.update_status(build.build_id, BuildStatus.ACTIVE, "status_check")
            registry.attach_artifact(build.build_id, "artifact_1", "report", "first_output")
            registry.update_investment_score(build.build_id, 0.66, "investment_eval")

            builds = registry.get_latest_builds()
            self.assertIn(build.build_id, builds)
            latest = builds[build.build_id]
            self.assertEqual(latest.current_stage, BuildStage.IMPLEMENTATION)
            self.assertEqual(latest.status, BuildStatus.ACTIVE)
            self.assertEqual(latest.investment_score, 0.66)
            self.assertIn("artifact_1", latest.artifact_ids)


class TestBuildStageEvaluator(unittest.TestCase):
    """Test stage evaluation determinism."""

    def test_deterministic_evaluation(self):
        build = BuildContract.new(
            name="Beta",
            objective="Build forecasting",
            build_type=BuildType.MODEL,
            mission_ids=["m1"],
        )

        mission_statuses = {"m1": "completed"}
        artifacts = ["a1"]
        goals = [{"goal_satisfied": True}]

        eval1 = BuildStageEvaluator.evaluate(
            build,
            mission_statuses=mission_statuses,
            artifact_ids=artifacts,
            goal_evaluations=goals,
            investment_score=0.8,
        )
        eval2 = BuildStageEvaluator.evaluate(
            build,
            mission_statuses=mission_statuses,
            artifact_ids=artifacts,
            goal_evaluations=goals,
            investment_score=0.8,
        )

        self.assertEqual(eval1.is_ready, eval2.is_ready)
        self.assertEqual(eval1.readiness_score, eval2.readiness_score)
        self.assertEqual(eval1.blocking_reasons, eval2.blocking_reasons)

    def test_stage_blocking(self):
        build = BuildContract.new(
            name="Gamma",
            objective="Build content",
            build_type=BuildType.CONTENT,
            mission_ids=[],
        )

        evaluation = BuildStageEvaluator.evaluate(build)
        self.assertFalse(evaluation.is_ready)
        self.assertIn("no_missions_planned", evaluation.blocking_reasons)


class TestArtifactRegistry(unittest.TestCase):
    """Test build artifact registry."""

    def test_register_artifact(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = BuildArtifactRegistry(output_dir=Path(tmpdir))

            record = registry.register_artifact(
                artifact_id="artifact_1",
                build_id="build_1",
                artifact_type="report",
                description="Build report",
                created_from_mission="m1",
            )

            self.assertEqual(record.build_id, "build_1")
            artifacts = registry.get_artifacts_for_build("build_1")
            self.assertEqual(len(artifacts), 1)
            self.assertEqual(artifacts[0].artifact_id, "artifact_1")


class TestBuildSignals(unittest.TestCase):
    """Test build signal emission."""

    def test_build_signals_emit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            signals_file = Path(tmpdir) / "learning_signals.jsonl"

            build = BuildContract.new(
                name="Delta",
                objective="Build system",
                build_type=BuildType.SYSTEM,
            )

            BuildSignalEmitter.emit_build_created(build, stream_file=signals_file)

            evaluation = BuildStageEvaluator.evaluate(build)
            BuildSignalEmitter.emit_build_stage_evaluated(evaluation, stream_file=signals_file)

            signals = BuildSignalEmitter.get_signals_from_file(signals_file)
            self.assertEqual(len(signals), 2)
            self.assertEqual(signals[0]["signal_type"], "build_created")
            self.assertEqual(signals[1]["signal_type"], "build_stage_evaluated")


class TestBuildWhiteboardPanel(unittest.TestCase):
    """Test build whiteboard rendering."""

    def test_render_panel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = BuildRegistry(output_dir=Path(tmpdir))
            artifact_registry = BuildArtifactRegistry(output_dir=Path(tmpdir))

            build = BuildContract.new(
                name="Epsilon",
                objective="Build research system",
                build_type=BuildType.RESEARCH,
                mission_ids=["m1"],
            )
            registry.register_build(build)

            evaluation = BuildStageEvaluator.evaluate(build)

            panel = BuildWhiteboardPanel()
            panel.set_sources(
                build_registry=registry,
                artifact_registry=artifact_registry,
                evaluations={build.build_id: evaluation},
            )

            rendered = panel.render()
            self.assertIn("BUILD INTELLIGENCE WHITEBOARD", rendered)
            self.assertIn(build.name, rendered)


class TestNoAutonomy(unittest.TestCase):
    """Verify read-only behavior."""

    def test_evaluator_does_not_mutate(self):
        build = BuildContract.new(
            name="Zeta",
            objective="Build tool",
            build_type=BuildType.SOFTWARE,
            mission_ids=["m1"],
        )

        original = build.to_dict()
        BuildStageEvaluator.evaluate(build)
        self.assertEqual(build.to_dict(), original)


if __name__ == "__main__":
    unittest.main()
