import json
import tempfile
import unittest
from pathlib import Path

from buddy_self_driven_harness import SelfDrivenHarness


class TestSelfDrivenHarness(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name) / "phase11"
        self.phase10_dir = Path("outputs/phase10")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _read_jsonl(self, path: Path):
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_learning_insights_generated(self):
        if not self.phase10_dir.exists():
            self.skipTest("Phase 10 outputs not available")
        
        harness = SelfDrivenHarness(output_dir=str(self.output_dir), phase10_dir=str(self.phase10_dir))
        harness.run(waves=2)

        insights = self._read_jsonl(self.output_dir / "learning_insights.jsonl")
        self.assertGreaterEqual(len(insights), 1)

    def test_autonomous_goals_generated(self):
        if not self.phase10_dir.exists():
            self.skipTest("Phase 10 outputs not available")
        
        harness = SelfDrivenHarness(output_dir=str(self.output_dir), phase10_dir=str(self.phase10_dir))
        harness.run(waves=2)

        outcomes = self._read_jsonl(self.output_dir / "task_outcomes.jsonl")
        self.assertGreaterEqual(len(outcomes), 1)

    def test_policy_inherits_from_phase10(self):
        if not self.phase10_dir.exists():
            self.skipTest("Phase 10 outputs not available")
        
        harness = SelfDrivenHarness(output_dir=str(self.output_dir), phase10_dir=str(self.phase10_dir))
        self.assertEqual(harness.policy_updater.policy.high_risk_threshold, 0.8)


if __name__ == "__main__":
    unittest.main()
