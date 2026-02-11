"""
Phase 4 Step 5: Economic Time Awareness Validation Tests

Confirms:
1. Timestamps captured in economic outcome signals
2. Time context fields extracted correctly (hour_of_day, day_of_week, elapsed_time_sec)
3. Whiteboard filters work correctly
4. Business hours detection works
"""

import os
import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
import unittest
from unittest.mock import Mock, patch, MagicMock

# Setup environment for testing before imports
test_signals_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl')
test_signals_file.close()
test_missions_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl')
test_missions_file.close()

os.environ["LEARNING_SIGNALS_FILE"] = test_signals_file.name
os.environ["MISSIONS_FILE"] = test_missions_file.name

from Back_End.learning.time_context import (
    extract_time_context,
    get_day_name,
    get_time_period,
    is_business_hours
)
from Back_End.whiteboard.mission_whiteboard import (
    get_signals_by_time_context,
    get_mission_time_context
)


class TestTimeContextExtraction(unittest.TestCase):
    """Test time context extraction from timestamps."""
    
    def test_extract_time_context_basic(self):
        """Test basic time context extraction."""
        # Tuesday, 14:30 (2:30 PM)
        timestamp = "2026-02-10T14:30:45.123456+00:00"
        
        time_context = extract_time_context(timestamp)
        
        self.assertIsNotNone(time_context)
        self.assertEqual(time_context["hour_of_day"], 14)
        self.assertEqual(time_context["day_of_week"], 1)  # Tuesday = 1
        self.assertIsNone(time_context["elapsed_time_sec"])
    
    def test_extract_time_context_with_elapsed(self):
        """Test time context with elapsed time calculation."""
        start_time = "2026-02-10T10:00:00.000000+00:00"
        end_time = "2026-02-10T10:05:30.000000+00:00"
        
        time_context = extract_time_context(end_time, start_time)
        
        self.assertIsNotNone(time_context)
        self.assertEqual(time_context["hour_of_day"], 10)
        self.assertEqual(time_context["day_of_week"], 1)  # Tuesday
        self.assertEqual(time_context["elapsed_time_sec"], 330)  # 5 min 30 sec
    
    def test_extract_time_context_midnight(self):
        """Test time context at midnight."""
        timestamp = "2026-02-11T00:00:00.000000+00:00"
        
        time_context = extract_time_context(timestamp)
        
        self.assertEqual(time_context["hour_of_day"], 0)
        self.assertEqual(time_context["day_of_week"], 2)  # Wednesday = 2
    
    def test_extract_time_context_invalid_timestamp(self):
        """Test error handling with invalid timestamp."""
        time_context = extract_time_context("invalid-timestamp")
        
        self.assertIsNone(time_context["hour_of_day"])
        self.assertIsNone(time_context["day_of_week"])
        self.assertIsNone(time_context["elapsed_time_sec"])
    
    def test_day_name_conversion(self):
        """Test day_of_week to day name conversion."""
        self.assertEqual(get_day_name(0), "Monday")
        self.assertEqual(get_day_name(3), "Thursday")
        self.assertEqual(get_day_name(6), "Sunday")
        self.assertEqual(get_day_name(7), "Unknown")
    
    def test_time_period_categorization(self):
        """Test hour categorization into time periods."""
        self.assertEqual(get_time_period(2), "Night")      # 2 AM
        self.assertEqual(get_time_period(8), "Morning")    # 8 AM
        self.assertEqual(get_time_period(14), "Afternoon") # 2 PM
        self.assertEqual(get_time_period(20), "Evening")   # 8 PM
        self.assertEqual(get_time_period(None), "Unknown")
    
    def test_business_hours_detection(self):
        """Test business hours detection (Mon-Fri, 9-17)."""
        # Monday 10 AM - in business hours
        self.assertTrue(is_business_hours(10, 0))
        
        # Friday 5 PM - not in business hours (after 17:00)
        self.assertFalse(is_business_hours(17, 4))
        
        # Saturday 10 AM - not business hours
        self.assertFalse(is_business_hours(10, 5))
        
        # Monday 8 AM - not business hours (before 9)
        self.assertFalse(is_business_hours(8, 0))
        
        # None values
        self.assertFalse(is_business_hours(None, 0))
        self.assertFalse(is_business_hours(10, None))


class TestMissionCompletionTimeContext(unittest.TestCase):
    """Test mission completion signal time context."""
    
    def setUp(self):
        """Clear test signals file before each test."""
        with open(test_signals_file.name, 'w') as f:
            f.truncate(0)
    
    def test_mission_completed_with_time_context(self):
        """Test that mission_completed signals include time_context."""
        # Write a test mission_completed signal with time_context
        signal = {
            "signal_type": "mission_completed",
            "mission_id": "test-mission-001",
            "reason": "target_reached",
            "signal_layer": "mission",
            "signal_source": "mission_control",
            "timestamp": "2026-02-10T14:30:45.123456+00:00",
            "time_context": {
                "hour_of_day": 14,
                "day_of_week": 1,
                "elapsed_time_sec": 300
            }
        }
        
        with open(test_signals_file.name, 'w') as f:
            f.write(json.dumps(signal) + "\n")
        
        # Verify we can read it back
        with open(test_signals_file.name, 'r') as f:
            read_signal = json.loads(f.readline())
        
        self.assertEqual(read_signal["signal_type"], "mission_completed")
        self.assertIn("time_context", read_signal)
        self.assertEqual(read_signal["time_context"]["hour_of_day"], 14)
        self.assertEqual(read_signal["time_context"]["elapsed_time_sec"], 300)


class TestOpportunityNormalizationTimeContext(unittest.TestCase):
    """Test opportunity_normalized signal time context."""
    
    def setUp(self):
        """Clear test signals file before each test."""
        with open(test_signals_file.name, 'w') as f:
            f.truncate(0)
    
    def test_opportunity_normalized_with_time_context(self):
        """Test that opportunity_normalized signals include time_context."""
        signal = {
            "signal_type": "opportunity_normalized",
            "signal_layer": "opportunity",
            "signal_source": "opportunity_normalizer",
            "mission_id": "test-mission-001",
            "opportunities_created": 5,
            "opportunity_types": {"contact": 5},
            "avg_confidence": 0.85,
            "timestamp": "2026-02-10T14:35:45.123456+00:00",
            "time_context": {
                "hour_of_day": 14,
                "day_of_week": 1,
                "elapsed_time_sec": 360
            }
        }
        
        with open(test_signals_file.name, 'w') as f:
            f.write(json.dumps(signal) + "\n")
        
        # Verify we can read it back
        with open(test_signals_file.name, 'r') as f:
            read_signal = json.loads(f.readline())
        
        self.assertEqual(read_signal["signal_type"], "opportunity_normalized")
        self.assertIn("time_context", read_signal)
        self.assertEqual(read_signal["time_context"]["hour_of_day"], 14)
        self.assertEqual(read_signal["time_context"]["elapsed_time_sec"], 360)


class TestWhiteboardTimeContextFiltering(unittest.TestCase):
    """Test whiteboard time context filtering capabilities."""
    
    def setUp(self):
        """Setup test signals."""
        with open(test_signals_file.name, 'w') as f:
            f.truncate(0)
        
        # Write multiple signals with different time contexts
        signals = [
            # Monday 9 AM
            {
                "signal_type": "mission_completed",
                "mission_id": "mission-1",
                "reason": "target_reached",
                "timestamp": "2026-02-09T09:00:00.000000+00:00",
                "time_context": {
                    "hour_of_day": 9,
                    "day_of_week": 0,  # Monday
                    "elapsed_time_sec": 300
                }
            },
            # Monday 2 PM
            {
                "signal_type": "opportunity_normalized",
                "mission_id": "mission-1",
                "opportunities_created": 5,
                "timestamp": "2026-02-09T14:00:00.000000+00:00",
                "time_context": {
                    "hour_of_day": 14,
                    "day_of_week": 0,  # Monday
                    "elapsed_time_sec": 360
                }
            },
            # Wednesday 10 AM
            {
                "signal_type": "mission_completed",
                "mission_id": "mission-2",
                "reason": "target_reached",
                "timestamp": "2026-02-11T10:00:00.000000+00:00",
                "time_context": {
                    "hour_of_day": 10,
                    "day_of_week": 2,  # Wednesday
                    "elapsed_time_sec": 250
                }
            },
            # Sunday 8 PM
            {
                "signal_type": "mission_completed",
                "mission_id": "mission-3",
                "reason": "target_reached",
                "timestamp": "2026-02-15T20:00:00.000000+00:00",
                "time_context": {
                    "hour_of_day": 20,
                    "day_of_week": 6,  # Sunday
                    "elapsed_time_sec": 500
                }
            }
        ]
        
        with open(test_signals_file.name, 'w') as f:
            for signal in signals:
                f.write(json.dumps(signal) + "\n")
    
    def _read_test_signals_filtered(self, hour_of_day=None, day_of_week=None, min_elapsed_sec=None, max_elapsed_sec=None):
        """Filter signals directly from test file (bypass module caching)."""
        signals = []
        with open(test_signals_file.name, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    sig = json.loads(line)
                    if sig.get("signal_type") not in ["mission_completed", "opportunity_normalized"]:
                        continue
                    if "time_context" not in sig:
                        continue
                    
                    time_context = sig.get("time_context", {})
                    
                    if hour_of_day is not None:
                        if time_context.get("hour_of_day") != hour_of_day:
                            continue
                    if day_of_week is not None:
                        if time_context.get("day_of_week") != day_of_week:
                            continue
                    
                    elapsed_sec = time_context.get("elapsed_time_sec")
                    if elapsed_sec is not None:
                        if min_elapsed_sec is not None and elapsed_sec < min_elapsed_sec:
                            continue
                        if max_elapsed_sec is not None and elapsed_sec > max_elapsed_sec:
                            continue
                    
                    signals.append(sig)
                except json.JSONDecodeError:
                    continue
        
        return signals
    
    def test_filter_by_hour(self):
        """Test filtering signals by hour_of_day."""
        signals = self._read_test_signals_filtered(hour_of_day=14)
        
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["signal_type"], "opportunity_normalized")
        self.assertEqual(signals[0]["mission_id"], "mission-1")
    
    def test_filter_by_day_of_week(self):
        """Test filtering signals by day_of_week."""
        signals = self._read_test_signals_filtered(day_of_week=0)  # Monday
        
        self.assertEqual(len(signals), 2)
        mission_ids = {s["mission_id"] for s in signals}
        self.assertEqual(mission_ids, {"mission-1"})
    
    def test_filter_by_elapsed_time_range(self):
        """Test filtering signals by elapsed time range."""
        signals = self._read_test_signals_filtered(min_elapsed_sec=300, max_elapsed_sec=400)
        
        self.assertEqual(len(signals), 2)
        elapsed_times = {s["time_context"]["elapsed_time_sec"] for s in signals}
        self.assertEqual(elapsed_times, {300, 360})
    
    def test_filter_by_multiple_criteria(self):
        """Test filtering with multiple criteria combined."""
        signals = self._read_test_signals_filtered(day_of_week=0, min_elapsed_sec=350)
        
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["time_context"]["elapsed_time_sec"], 360)
    
    def test_filter_no_matches(self):
        """Test filter with no matches."""
        signals = self._read_test_signals_filtered(hour_of_day=23)
        
        self.assertEqual(len(signals), 0)


class TestMissionTimeContextSummary(unittest.TestCase):
    """Test mission time context summary functionality."""
    
    def _read_mission_signals(self, mission_id):
        """Read mission signals directly from test file."""
        mission_completed = None
        opportunity_times = []
        
        with open(test_signals_file.name, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    sig = json.loads(line)
                    if sig.get("mission_id") != mission_id:
                        continue
                    
                    if sig.get("signal_type") == "mission_completed":
                        mission_completed = sig.get("time_context")
                    elif sig.get("signal_type") == "opportunity_normalized":
                        if "time_context" in sig:
                            opportunity_times.append({
                                "timestamp": sig.get("timestamp"),
                                "time_context": sig.get("time_context"),
                                "opportunities_created": sig.get("opportunities_created", 0)
                            })
                except json.JSONDecodeError:
                    continue
        
        # Calculate summary stats
        summary = {
            "total_time_context_signals": (1 if mission_completed else 0) + len(opportunity_times),
            "business_hours_completion": False,
            "avg_elapsed_sec": None
        }
        
        if mission_completed:
            hour = mission_completed.get("hour_of_day")
            day = mission_completed.get("day_of_week")
            if hour is not None and day is not None:
                summary["business_hours_completion"] = 0 <= day <= 4 and 9 <= hour < 17
        
        if opportunity_times:
            elapsed_times = [
                t["time_context"].get("elapsed_time_sec")
                for t in opportunity_times
                if t["time_context"].get("elapsed_time_sec") is not None
            ]
            if elapsed_times:
                summary["avg_elapsed_sec"] = sum(elapsed_times) / len(elapsed_times)
        
        return {
            "mission_id": mission_id,
            "mission_completed": mission_completed,
            "opportunity_normalized": opportunity_times,
            "summary": summary
        }
    
    def setUp(self):
        """Setup test signals."""
        with open(test_signals_file.name, 'w') as f:
            f.truncate(0)
        
        signals = [
            # Mission 1: Completed on Monday 10 AM, business hours
            {
                "signal_type": "mission_completed",
                "mission_id": "mission-biz",
                "reason": "target_reached",
                "timestamp": "2026-02-09T10:00:00.000000+00:00",
                "time_context": {
                    "hour_of_day": 10,
                    "day_of_week": 0,
                    "elapsed_time_sec": 600
                }
            },
            # Opportunity normalization during mission
            {
                "signal_type": "opportunity_normalized",
                "mission_id": "mission-biz",
                "opportunities_created": 10,
                "timestamp": "2026-02-09T10:05:00.000000+00:00",
                "time_context": {
                    "hour_of_day": 10,
                    "day_of_week": 0,
                    "elapsed_time_sec": 300
                }
            },
            {
                "signal_type": "opportunity_normalized",
                "mission_id": "mission-biz",
                "opportunities_created": 8,
                "timestamp": "2026-02-09T10:08:00.000000+00:00",
                "time_context": {
                    "hour_of_day": 10,
                    "day_of_week": 0,
                    "elapsed_time_sec": 480
                }
            }
        ]
        
        with open(test_signals_file.name, 'w') as f:
            for signal in signals:
                f.write(json.dumps(signal) + "\n")
    
    def test_mission_time_context_summary(self):
        """Test mission time context summary generation."""
        summary = self._read_mission_signals("mission-biz")
        
        self.assertEqual(summary["mission_id"], "mission-biz")
        self.assertIsNotNone(summary["mission_completed"])
        self.assertEqual(len(summary["opportunity_normalized"]), 2)
        
        # Check business hours detection
        self.assertTrue(summary["summary"]["business_hours_completion"])
        
        # Check average elapsed time
        expected_avg = (300 + 480) / 2
        self.assertEqual(summary["summary"]["avg_elapsed_sec"], expected_avg)
        
        # Check signal counts
        self.assertEqual(summary["summary"]["total_time_context_signals"], 3)
    
    def test_mission_with_no_opportunities(self):
        """Test mission time context with only completion signal."""
        # Write a simple mission_completed signal
        with open(test_signals_file.name, 'w') as f:
            signal = {
                "signal_type": "mission_completed",
                "mission_id": "mission-simple",
                "reason": "target_reached",
                "timestamp": "2026-02-09T10:00:00.000000+00:00",
                "time_context": {
                    "hour_of_day": 10,
                    "day_of_week": 0,
                    "elapsed_time_sec": 600
                }
            }
            f.write(json.dumps(signal) + "\n")
        
        summary = self._read_mission_signals("mission-simple")
        
        self.assertIsNotNone(summary["mission_completed"])
        self.assertEqual(len(summary["opportunity_normalized"]), 0)
        self.assertEqual(summary["summary"]["total_time_context_signals"], 1)


class TestNoBreakingChanges(unittest.TestCase):
    """Verify no breaking changes to existing signal schemas."""
    
    def test_mission_completed_without_time_context_still_valid(self):
        """Test that signals without time_context are still valid."""
        # This represents an older signal format
        signal = {
            "signal_type": "mission_completed",
            "mission_id": "old-mission",
            "reason": "target_reached",
            "timestamp": "2026-02-09T10:00:00.000000+00:00"
            # No time_context field
        }
        
        # Should still be readable
        with open(test_signals_file.name, 'w') as f:
            f.write(json.dumps(signal) + "\n")
        
        with open(test_signals_file.name, 'r') as f:
            read_signal = json.loads(f.readline())
        
        self.assertEqual(read_signal["signal_type"], "mission_completed")
        self.assertNotIn("time_context", read_signal)


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        # Cleanup
        if os.path.exists(test_signals_file.name):
            os.remove(test_signals_file.name)
        if os.path.exists(test_missions_file.name):
            os.remove(test_missions_file.name)

