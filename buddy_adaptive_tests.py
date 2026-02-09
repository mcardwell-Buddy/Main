import json
import tempfile
import unittest
from pathlib import Path

from buddy_adaptive_harness import AdaptiveHarness


class TestAdaptiveHarness(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _read_jsonl(self, path: Path):
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_wave_execution_generates_outputs(self):
        harness = AdaptiveHarness(output_dir=str(self.output_dir))
        harness.run(waves=2)

        self.assertTrue((self.output_dir / "self_questions.jsonl").exists())
        self.assertTrue((self.output_dir / "task_outcomes.jsonl").exists())
        self.assertTrue((self.output_dir / "confidence_updates.jsonl").exists())
        self.assertTrue((self.output_dir / "policy_updates.jsonl").exists())

        questions = self._read_jsonl(self.output_dir / "self_questions.jsonl")
        outcomes = self._read_jsonl(self.output_dir / "task_outcomes.jsonl")
        updates = self._read_jsonl(self.output_dir / "confidence_updates.jsonl")

        self.assertGreaterEqual(len(outcomes), 1)
        self.assertGreaterEqual(len(questions), 4)
        self.assertEqual(len(outcomes), len(updates))

    def test_high_risk_deferred(self):
        harness = AdaptiveHarness(output_dir=str(self.output_dir))
        harness.run(waves=4)

        outcomes = self._read_jsonl(self.output_dir / "task_outcomes.jsonl")
        high_risk = [o for o in outcomes if o.get("risk_level") == "HIGH"]
        if high_risk:
            for outcome in high_risk:
                if outcome.get("confidence_score", 1.0) < 0.8:
                    self.assertEqual(outcome.get("status"), "deferred")

    def test_wave_metrics_written(self):
        harness = AdaptiveHarness(output_dir=str(self.output_dir))
        harness.run(waves=3)

        for wave in range(1, 4):
            wave_dir = self.output_dir / f"wave_{wave}"
            self.assertTrue((wave_dir / "wave_metrics.json").exists())


if __name__ == "__main__":
    unittest.main()
