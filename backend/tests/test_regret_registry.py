"""
Tests for Phase 4 Step 6: Regret Registry

Tests the persistence, querying, and display of irreversible failures
and high-cost mistakes to prevent blind repetition.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

# Setup environment for regret registry tests
# We'll use mocking to override the REGRET_REGISTRY_FILE at function level
from backend.mission_control import regret_registry
from backend.mission_control.regret_registry import (
    RegretEntry,
    log_regret,
    get_regrets,
    get_regrets_by_action,
    get_irreversible_regrets,
    get_regret_summary,
)


class TestRegretEntry(unittest.TestCase):
    """Tests for RegretEntry class and severity calculation"""

    def test_create_regret_entry(self):
        """Test creating a RegretEntry with all fields"""
        entry = RegretEntry(
            mission_id="M001",
            action="navigate_failed",
            failure_reason="navigation_blocked",
            irreversible=True,
            estimated_cost={
                "time_lost": 120,
                "trust_impact": 15,
                "opportunities_lost": 0,
            },
            context={"url": "https://example.com", "max_depth": 3},
        )

        self.assertEqual(entry.mission_id, "M001")
        self.assertEqual(entry.action, "navigate_failed")
        self.assertEqual(entry.failure_reason, "navigation_blocked")
        self.assertTrue(entry.irreversible)
        self.assertEqual(entry.estimated_cost["time_lost"], 120)
        self.assertEqual(entry.context["url"], "https://example.com")

    def test_severity_critical_irreversible(self):
        """Test CRITICAL severity when irreversible=true"""
        entry = RegretEntry(
            mission_id="M001",
            action="navigate_failed",
            failure_reason="navigation_blocked",
            irreversible=True,
            estimated_cost={"time_lost": 10, "trust_impact": 5, "opportunities_lost": 0},
        )

        self.assertEqual(entry.severity, "critical")

    def test_severity_high_cost(self):
        """Test HIGH severity when total cost >= 100"""
        entry = RegretEntry(
            mission_id="M001",
            action="data_lost",
            failure_reason="extraction_failed",
            irreversible=False,
            estimated_cost={"time_lost": 60, "trust_impact": 25, "opportunities_lost": 20},
        )

        total_cost = 60 + 25 + 20
        self.assertGreaterEqual(total_cost, 100)
        self.assertEqual(entry.severity, "high")

    def test_severity_medium_cost(self):
        """Test MEDIUM severity when total cost 50-99"""
        entry = RegretEntry(
            mission_id="M001",
            action="retry_failed",
            failure_reason="timeout",
            irreversible=False,
            estimated_cost={"time_lost": 30, "trust_impact": 15, "opportunities_lost": 5},
        )

        total_cost = 30 + 15 + 5
        self.assertIn(total_cost, range(50, 100))
        self.assertEqual(entry.severity, "medium")

    def test_severity_low_cost(self):
        """Test LOW severity when total cost < 50"""
        entry = RegretEntry(
            mission_id="M001",
            action="minor_delay",
            failure_reason="slow_response",
            irreversible=False,
            estimated_cost={"time_lost": 10, "trust_impact": 5, "opportunities_lost": 0},
        )

        total_cost = 10 + 5 + 0
        self.assertLess(total_cost, 50)
        self.assertEqual(entry.severity, "low")

    def test_regret_entry_to_dict(self):
        """Test RegretEntry serialization to dict"""
        entry = RegretEntry(
            mission_id="M001",
            action="navigate_failed",
            failure_reason="navigation_blocked",
            irreversible=True,
            estimated_cost={"time_lost": 120, "trust_impact": 15, "opportunities_lost": 0},
        )

        entry_dict = entry.to_dict()

        self.assertEqual(entry_dict["mission_id"], "M001")
        self.assertEqual(entry_dict["action"], "navigate_failed")
        self.assertEqual(entry_dict["failure_reason"], "navigation_blocked")
        self.assertTrue(entry_dict["irreversible"])
        self.assertIn("timestamp", entry_dict)
        self.assertIn("severity", entry_dict)


class TestRegretPersistence(unittest.TestCase):
    """Tests for regret registry persistence"""

    def setUp(self):
        """Create a temporary directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.regret_file = Path(self.temp_dir) / "test_regrets.jsonl"

    def tearDown(self):
        """Clean up temporary files"""
        if self.regret_file.exists():
            self.regret_file.unlink()
        self.temp_dir_path = Path(self.temp_dir)
        if self.temp_dir_path.exists():
            self.temp_dir_path.rmdir()

    def test_log_regret_creates_file(self):
        """Test that log_regret creates regret_registry.jsonl"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 120, "trust_impact": 15, "opportunities_lost": 0},
            )

        self.assertTrue(self.regret_file.exists())

    def test_log_regret_appends_entry(self):
        """Test that log_regret appends entries (JSONL format)"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 120, "trust_impact": 15, "opportunities_lost": 0},
            )
            log_regret(
                mission_id="M002",
                action="confidence_collapse",
                failure_reason="low_confidence",
                irreversible=False,
                estimated_cost={"time_lost": 10, "trust_impact": 20, "opportunities_lost": 5},
            )

        with open(self.regret_file, "r") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)

        obj1 = json.loads(lines[0])
        obj2 = json.loads(lines[1])

        self.assertEqual(obj1["mission_id"], "M001")
        self.assertEqual(obj2["mission_id"], "M002")

    def test_log_regret_preserves_history(self):
        """Test that logging new regrets doesn't overwrite existing ones"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            log_regret(
                mission_id="M001",
                action="action1",
                failure_reason="reason1",
                irreversible=True,
                estimated_cost={"time_lost": 100, "trust_impact": 10, "opportunities_lost": 0},
            )
            first_line_count = sum(1 for _ in open(self.regret_file))

            log_regret(
                mission_id="M002",
                action="action2",
                failure_reason="reason2",
                irreversible=False,
                estimated_cost={"time_lost": 50, "trust_impact": 20, "opportunities_lost": 0},
            )
            second_line_count = sum(1 for _ in open(self.regret_file))

        self.assertEqual(first_line_count + 1, second_line_count)


class TestRegretQuerying(unittest.TestCase):
    """Tests for querying regrets"""

    def setUp(self):
        """Set up test regrets in temporary file"""
        self.temp_dir = tempfile.mkdtemp()
        self.regret_file = Path(self.temp_dir) / "test_regrets.jsonl"

    def tearDown(self):
        """Clean up temporary files"""
        if self.regret_file.exists():
            self.regret_file.unlink()
        self.temp_dir_path = Path(self.temp_dir)
        if self.temp_dir_path.exists():
            self.temp_dir_path.rmdir()

    def test_get_all_regrets(self):
        """Test getting all regrets"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 120, "trust_impact": 15, "opportunities_lost": 0},
            )
            log_regret(
                mission_id="M002",
                action="confidence_collapse",
                failure_reason="low_confidence",
                irreversible=False,
                estimated_cost={"time_lost": 10, "trust_impact": 20, "opportunities_lost": 5},
            )
            log_regret(
                mission_id="M001",
                action="extraction_failed",
                failure_reason="no_progress",
                irreversible=True,
                estimated_cost={"time_lost": 90, "trust_impact": 15, "opportunities_lost": 0},
            )
            log_regret(
                mission_id="M003",
                action="timeout_error",
                failure_reason="network_timeout",
                irreversible=False,
                estimated_cost={"time_lost": 60, "trust_impact": 10, "opportunities_lost": 0},
            )
            
            regrets = get_regrets()

        self.assertEqual(len(regrets), 4)

    def test_get_regrets_by_mission(self):
        """Test getting regrets for a specific mission"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 120, "trust_impact": 15, "opportunities_lost": 0},
            )
            log_regret(
                mission_id="M002",
                action="confidence_collapse",
                failure_reason="low_confidence",
                irreversible=False,
                estimated_cost={"time_lost": 10, "trust_impact": 20, "opportunities_lost": 5},
            )
            log_regret(
                mission_id="M001",
                action="extraction_failed",
                failure_reason="no_progress",
                irreversible=True,
                estimated_cost={"time_lost": 90, "trust_impact": 15, "opportunities_lost": 0},
            )
            
            m001_regrets = [r for r in get_regrets() if r.get("mission_id") == "M001"]

        self.assertEqual(len(m001_regrets), 2)

    def test_get_regrets_by_action(self):
        """Test getting regrets by action type"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 120, "trust_impact": 15, "opportunities_lost": 0},
            )
            log_regret(
                mission_id="M002",
                action="confidence_collapse",
                failure_reason="low_confidence",
                irreversible=False,
                estimated_cost={"time_lost": 10, "trust_impact": 20, "opportunities_lost": 5},
            )
            
            navigate_failed = get_regrets_by_action("navigate_failed")

        self.assertEqual(len(navigate_failed), 1)
        self.assertEqual(navigate_failed[0]["action"], "navigate_failed")

    def test_get_irreversible_regrets(self):
        """Test getting only irreversible regrets"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 120, "trust_impact": 15, "opportunities_lost": 0},
            )
            log_regret(
                mission_id="M002",
                action="confidence_collapse",
                failure_reason="low_confidence",
                irreversible=False,
                estimated_cost={"time_lost": 10, "trust_impact": 20, "opportunities_lost": 5},
            )
            log_regret(
                mission_id="M001",
                action="extraction_failed",
                failure_reason="no_progress",
                irreversible=True,
                estimated_cost={"time_lost": 90, "trust_impact": 15, "opportunities_lost": 0},
            )
            
            irreversible = get_irreversible_regrets()

        self.assertEqual(len(irreversible), 2)
        for regret in irreversible:
            self.assertTrue(regret["irreversible"])


class TestRegretSummary(unittest.TestCase):
    """Tests for regret summary aggregation"""

    def setUp(self):
        """Set up test regrets"""
        self.temp_dir = tempfile.mkdtemp()
        self.regret_file = Path(self.temp_dir) / "test_regrets.jsonl"

    def tearDown(self):
        """Clean up"""
        if self.regret_file.exists():
            self.regret_file.unlink()
        self.temp_dir_path = Path(self.temp_dir)
        if self.temp_dir_path.exists():
            self.temp_dir_path.rmdir()

    def test_summary_total_count(self):
        """Test summary counts total regrets"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 120, "trust_impact": 15, "opportunities_lost": 0},
            )
            log_regret(
                mission_id="M002",
                action="confidence_collapse",
                failure_reason="low_confidence",
                irreversible=False,
                estimated_cost={"time_lost": 10, "trust_impact": 20, "opportunities_lost": 5},
            )
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 90, "trust_impact": 15, "opportunities_lost": 0},
            )
            
            summary = get_regret_summary()

        self.assertEqual(summary["total_regrets"], 3)

    def test_summary_irreversible_count(self):
        """Test summary counts irreversible regrets"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 120, "trust_impact": 15, "opportunities_lost": 0},
            )
            log_regret(
                mission_id="M002",
                action="confidence_collapse",
                failure_reason="low_confidence",
                irreversible=False,
                estimated_cost={"time_lost": 10, "trust_impact": 20, "opportunities_lost": 5},
            )
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 90, "trust_impact": 15, "opportunities_lost": 0},
            )
            
            summary = get_regret_summary()

        self.assertEqual(summary["irreversible_count"], 2)

    def test_summary_cost_breakdown(self):
        """Test summary aggregates costs by type"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 120, "trust_impact": 15, "opportunities_lost": 0},
            )
            log_regret(
                mission_id="M002",
                action="confidence_collapse",
                failure_reason="low_confidence",
                irreversible=False,
                estimated_cost={"time_lost": 10, "trust_impact": 20, "opportunities_lost": 5},
            )
            log_regret(
                mission_id="M001",
                action="navigate_failed",
                failure_reason="navigation_blocked",
                irreversible=True,
                estimated_cost={"time_lost": 90, "trust_impact": 15, "opportunities_lost": 0},
            )
            
            summary = get_regret_summary()
            costs = summary["total_cost"]

        # Verify total costs are correct
        expected_time = 120 + 10 + 90  # 220
        expected_trust = 15 + 20 + 15  # 50
        expected_opportunities = 0 + 5 + 0  # 5

        self.assertEqual(costs["time_lost"], expected_time)
        self.assertEqual(costs["trust_impact"], expected_trust)
        self.assertEqual(costs["opportunities_lost"], expected_opportunities)


class TestBackwardCompatibility(unittest.TestCase):
    """Tests for backward compatibility with existing code"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.regret_file = Path(self.temp_dir) / "test_regrets.jsonl"

    def tearDown(self):
        """Clean up"""
        if self.regret_file.exists():
            self.regret_file.unlink()
        self.temp_dir_path = Path(self.temp_dir)
        if self.temp_dir_path.exists():
            self.temp_dir_path.rmdir()

    def test_get_regrets_empty_registry(self):
        """Test that get_regrets returns empty list when no regrets exist"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            regrets = get_regrets()

        self.assertEqual(regrets, [])

    def test_summary_empty_registry(self):
        """Test summary returns valid structure even with no regrets"""
        with mock.patch.object(regret_registry, 'REGRET_REGISTRY_FILE', self.regret_file):
            summary = get_regret_summary()

        self.assertIn("total_regrets", summary)
        self.assertIn("irreversible_count", summary)
        self.assertEqual(summary["total_regrets"], 0)
        self.assertEqual(summary["total_cost"]["time_lost"], 0)


if __name__ == "__main__":
    unittest.main()
