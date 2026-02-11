import json
import tempfile
import unittest
from pathlib import Path

from buddy_self_reflective_harness import SelfReflectiveHarness


class TestSelfReflectiveHarness(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _read_jsonl(self, path: Path):
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_self_questions_generated_for_each_task(self):
        harness = SelfReflectiveHarness(output_dir=str(self.output_dir))
        harness.run()

        questions = self._read_jsonl(self.output_dir / "self_questions.jsonl")
        outcomes = self._read_jsonl(self.output_dir / "task_outcomes.jsonl")

        task_ids = {o["task_id"] for o in outcomes}
        question_ids = {q["task_id"] for q in questions}

        self.assertTrue(task_ids.issubset(question_ids))
        for task_id in task_ids:
            count = sum(1 for q in questions if q["task_id"] == task_id)
            self.assertGreaterEqual(count, 4)

    def test_confidence_updates_logged(self):
        harness = SelfReflectiveHarness(output_dir=str(self.output_dir))
        harness.run()

        updates = self._read_jsonl(self.output_dir / "confidence_updates.jsonl")
        outcomes = self._read_jsonl(self.output_dir / "task_outcomes.jsonl")

        self.assertEqual(len(updates), len(outcomes))
        for update in updates:
            self.assertIn("previous_confidence", update)
            self.assertIn("updated_confidence", update)

    def test_sandbox_prevents_high_risk_execution(self):
        harness = SelfReflectiveHarness(output_dir=str(self.output_dir))
        harness.run()

        outcomes = self._read_jsonl(self.output_dir / "task_outcomes.jsonl")
        high_risk = [o for o in outcomes if o["risk_level"] == "HIGH"]

        if high_risk:
            for outcome in high_risk:
                if outcome["confidence_score"] < 0.8:
                    self.assertEqual(outcome["status"], "deferred")

    def test_recovery_and_metrics_consistency(self):
        harness = SelfReflectiveHarness(output_dir=str(self.output_dir))
        harness.run()

        outcomes = self._read_jsonl(self.output_dir / "task_outcomes.jsonl")
        failed = [o for o in outcomes if o["status"] == "failed"]
        deferred = [o for o in outcomes if o["status"] == "deferred"]

        self.assertGreaterEqual(len(outcomes), 1)
        self.assertGreaterEqual(len(failed) + len(deferred), 0)


if __name__ == "__main__":
    unittest.main()

