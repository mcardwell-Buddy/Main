"""
Phase 12.1: Revenue Signal Validation Tests

Validates:
- Schema validation
- File persistence
- Mission attribution if present
"""

import unittest
import tempfile
from pathlib import Path
import json

from Back_End.revenue_signal import (
    RevenueSignal,
    RevenueSignalEmitter,
    RevenueSignalType,
    RevenueSignalSource,
)


class TestRevenueSignalSchema(unittest.TestCase):
    """Schema validation tests."""

    def test_valid_signal(self):
        signal = RevenueSignal.new(
            signal_type=RevenueSignalType.OFFER_SENT,
            confidence=0.8,
            source=RevenueSignalSource.CHAT,
            mission_id="m1",
            build_id="b1",
            opportunity_id="o1",
            amount=199.0,
            currency="USD",
        )
        self.assertIsNotNone(signal.revenue_signal_id)
        self.assertEqual(signal.signal_type, RevenueSignalType.OFFER_SENT)
        self.assertEqual(signal.source, RevenueSignalSource.CHAT)

    def test_invalid_confidence(self):
        signal = RevenueSignal.new(
            signal_type=RevenueSignalType.PRICE_VIEWED,
            confidence=1.2,
            source=RevenueSignalSource.WEB,
        )
        emitter = RevenueSignalEmitter(stream_file=Path(tempfile.gettempdir()) / "signals.jsonl")
        with self.assertRaises(ValueError):
            emitter.emit(signal)


class TestRevenueSignalPersistence(unittest.TestCase):
    """Persistence tests."""

    def test_persistence_to_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "revenue_signals.jsonl"
            emitter = RevenueSignalEmitter(stream_file=path)

            signal = RevenueSignal.new(
                signal_type=RevenueSignalType.RESPONSE_RECEIVED,
                confidence=0.7,
                source=RevenueSignalSource.MANUAL,
                mission_id="m2",
            )
            emitter.emit(signal)

            self.assertTrue(path.exists())
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)

            data = json.loads(lines[0])
            self.assertEqual(data["signal_type"], "response_received")
            self.assertEqual(data["mission_id"], "m2")


class TestMissionAttribution(unittest.TestCase):
    """Mission attribution tests."""

    def test_mission_attribution_present(self):
        signal = RevenueSignal.new(
            signal_type=RevenueSignalType.INTENT_DETECTED,
            confidence=0.6,
            source=RevenueSignalSource.CHAT,
            mission_id="mission_123",
        )
        self.assertEqual(signal.mission_id, "mission_123")


if __name__ == "__main__":
    unittest.main()

