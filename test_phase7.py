"""
Phase 7: Advanced Analytics Engine - Unit Tests
Comprehensive test suite for metrics collection, storage, and analytics.
"""

import unittest
import tempfile
import shutil
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import time

from analytics_engine import (
    ExecutionMetrics, ToolProfile, AgentStatusSnapshot, CapacityForecast, HourlySummary,
    ConfidenceLevel, MetricsCollector, StorageManager, ToolRegistry, CapacityAnalyzer,
    CostAnalyzer, HourlyAggregator, AnalyticsEngine
)


class TestExecutionMetrics(unittest.TestCase):
    """Test ExecutionMetrics dataclass."""
    
    def test_create_execution_metrics(self):
        """Test creating execution metrics."""
        metrics = ExecutionMetrics(
            task_id="task_1",
            agent_id="agent_1",
            tool_name="web_search",
            start_time=100.0,
            end_time=105.0,
            duration_seconds=5.0,
            success=True,
            cost_actual=0.05,
            tokens_used=150
        )
        
        self.assertEqual(metrics.task_id, "task_1")
        self.assertEqual(metrics.tool_name, "web_search")
        self.assertTrue(metrics.success)
        self.assertEqual(metrics.duration_seconds, 5.0)
    
    def test_execution_metrics_defaults(self):
        """Test default values in metrics."""
        metrics = ExecutionMetrics(
            task_id="task_1",
            agent_id="agent_1",
            tool_name="tool",
            start_time=0,
            end_time=1,
            duration_seconds=1,
            success=False
        )
        
        self.assertEqual(metrics.cost_actual, 0.0)
        self.assertEqual(metrics.human_effort_level, "MEDIUM")
        self.assertFalse(metrics.browser_used)


class TestMetricsCollector(unittest.TestCase):
    """Test MetricsCollector class."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_analytics.db"
        self.collector = MetricsCollector(str(self.db_path))
    
    def tearDown(self):
        """Clean up test database."""
        shutil.rmtree(self.temp_dir)
    
    def test_database_initialization(self):
        """Test database tables are created."""
        self.assertTrue(self.db_path.exists())
    
    def test_record_execution(self):
        """Test recording a single execution."""
        metrics = ExecutionMetrics(
            task_id="task_1",
            agent_id="agent_1",
            tool_name="api_call",
            start_time=100,
            end_time=105,
            duration_seconds=5.0,
            success=True,
            cost_actual=0.10
        )
        
        self.collector.record_execution(metrics)
        
        # Verify in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tier1_raw_metrics")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)
    
    def test_record_multiple_executions(self):
        """Test recording multiple executions."""
        for i in range(5):
            metrics = ExecutionMetrics(
                task_id=f"task_{i}",
                agent_id="agent_1",
                tool_name="api_call",
                start_time=100 + i,
                end_time=105 + i,
                duration_seconds=5.0,
                success=i % 2 == 0  # Alternate success/failure
            )
            self.collector.record_execution(metrics)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tier1_raw_metrics")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 5)
    
    def test_get_recent_metrics(self):
        """Test retrieving recent metrics."""
        metrics = ExecutionMetrics(
            task_id="task_1",
            agent_id="agent_1",
            tool_name="tool",
            start_time=100,
            end_time=105,
            duration_seconds=5.0,
            success=True
        )
        
        self.collector.record_execution(metrics)
        
        recent = self.collector.get_recent_metrics(hours=24)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].task_id, "task_1")
    
    def test_cleanup_old_metrics(self):
        """Test cleanup of old metrics."""
        metrics = ExecutionMetrics(
            task_id="task_1",
            agent_id="agent_1",
            tool_name="tool",
            start_time=100,
            end_time=105,
            duration_seconds=5.0,
            success=True
        )
        
        self.collector.record_execution(metrics)
        
        # Cleanup with 0 hours retention should delete nothing (just recorded)
        deleted = self.collector.cleanup_old_metrics(hours=0)
        self.assertEqual(deleted, 0)


class TestStorageManager(unittest.TestCase):
    """Test StorageManager class."""
    
    def setUp(self):
        """Set up test storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_analytics.db"
        self.storage = StorageManager(str(self.db_path))
    
    def tearDown(self):
        """Clean up test storage."""
        shutil.rmtree(self.temp_dir)
    
    def test_store_hourly_summary(self):
        """Test storing hourly summary (Tier 2)."""
        summary = HourlySummary(
            hour_timestamp="2024-01-01T12:00:00",
            total_tasks=10,
            successful_tasks=8,
            failed_tasks=2,
            total_cost=0.50,
            total_tokens=2000,
            avg_task_duration=5.0,
            tool_execution_counts={"api": 5, "browser": 5}
        )
        
        self.storage.store_hourly_summary(summary)
        
        # Verify in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tier2_hourly_summaries")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)
    
    def test_store_tool_profile(self):
        """Test storing tool profile (Tier 3)."""
        profile = ToolProfile(
            tool_name="web_search",
            total_executions=100,
            successful_executions=95,
            failed_executions=5,
            avg_duration_seconds=2.5,
            avg_cost=0.05,
            success_rate=0.95,
            confidence_level=ConfidenceLevel.HIGH
        )
        
        self.storage.store_tool_profile(profile)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tier3_tool_profiles")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)
    
    def test_get_tool_profile(self):
        """Test retrieving tool profile."""
        profile = ToolProfile(
            tool_name="api_call",
            total_executions=50,
            successful_executions=48,
            success_rate=0.96,
            confidence_level=ConfidenceLevel.HIGH,
            risk_patterns=["timeout", "rate_limit"]
        )
        
        self.storage.store_tool_profile(profile)
        retrieved = self.storage.get_tool_profile("api_call")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.tool_name, "api_call")
        self.assertEqual(retrieved.total_executions, 50)
        self.assertEqual(len(retrieved.risk_patterns), 2)
    
    def test_get_nonexistent_profile(self):
        """Test retrieving non-existent profile."""
        profile = self.storage.get_tool_profile("nonexistent")
        self.assertIsNone(profile)


class TestToolRegistry(unittest.TestCase):
    """Test ToolRegistry class."""
    
    def setUp(self):
        """Set up test registry."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_analytics.db"
        self.storage = StorageManager(str(self.db_path))
        self.registry = ToolRegistry(self.storage)
    
    def tearDown(self):
        """Clean up test registry."""
        shutil.rmtree(self.temp_dir)
    
    def test_register_tool(self):
        """Test registering a tool."""
        self.registry.register_tool("web_search")
        
        self.assertIn("web_search", self.registry.tools)
        self.assertEqual(self.registry.tools["web_search"].tool_name, "web_search")
    
    def test_update_tool_from_execution(self):
        """Test updating tool profile from execution."""
        self.registry.register_tool("api")
        
        self.registry.update_tool_from_execution(
            "api", success=True, duration=2.0, cost=0.05, tokens=100
        )
        
        profile = self.registry.tools["api"]
        self.assertEqual(profile.total_executions, 1)
        self.assertEqual(profile.successful_executions, 1)
        self.assertEqual(profile.avg_duration_seconds, 2.0)
    
    def test_confidence_level_high(self):
        """Test confidence level becomes HIGH."""
        self.registry.register_tool("reliable_tool")
        
        # Record 10 successful executions
        for _ in range(10):
            self.registry.update_tool_from_execution(
                "reliable_tool", success=True, duration=1.0, cost=0.01, tokens=50
            )
        
        confidence = self.registry.get_tool_confidence("reliable_tool")
        self.assertEqual(confidence, ConfidenceLevel.HIGH)
    
    def test_confidence_level_low(self):
        """Test confidence level becomes LOW."""
        self.registry.register_tool("unreliable_tool")
        
        # Record 10 failed executions (0% success rate)
        for _ in range(10):
            self.registry.update_tool_from_execution(
                "unreliable_tool", success=False, duration=5.0, cost=0.50, tokens=0
            )
        
        confidence = self.registry.get_tool_confidence("unreliable_tool")
        self.assertEqual(confidence, ConfidenceLevel.LOW)
    
    def test_get_tools_by_confidence(self):
        """Test getting tools by confidence level."""
        # Create high confidence tools
        for i in range(3):
            self.registry.register_tool(f"high_{i}")
            for _ in range(10):
                self.registry.update_tool_from_execution(
                    f"high_{i}", success=True, duration=1.0, cost=0.01, tokens=50
                )
        
        high_tools = self.registry.get_tools_by_confidence(ConfidenceLevel.HIGH)
        self.assertEqual(len(high_tools), 3)


class TestCapacityAnalyzer(unittest.TestCase):
    """Test CapacityAnalyzer class."""
    
    def setUp(self):
        """Set up test analyzer."""
        self.analyzer = CapacityAnalyzer()
    
    def test_predict_capacity_default(self):
        """Test capacity prediction for unknown agent."""
        forecast = self.analyzer.predict_capacity("unknown_agent")
        
        self.assertEqual(forecast.agent_id, "unknown_agent")
        self.assertEqual(forecast.estimated_available_capacity, 100)
    
    def test_predict_capacity_high_response_time(self):
        """Test capacity based on response time."""
        metrics = [
            ExecutionMetrics(
                task_id=f"task_{i}",
                agent_id="agent_1",
                tool_name="tool",
                start_time=100 + i*15,
                end_time=115 + i*15,
                duration_seconds=15.0,
                success=True
            )
            for i in range(3)
        ]
        
        self.analyzer.update_agent_metrics("agent_1", metrics)
        forecast = self.analyzer.predict_capacity("agent_1")
        
        self.assertLess(forecast.estimated_available_capacity, 100)


class TestCostAnalyzer(unittest.TestCase):
    """Test CostAnalyzer class."""
    
    def setUp(self):
        """Set up test analyzer."""
        self.analyzer = CostAnalyzer()
    
    def test_calculate_storage_cost(self):
        """Test storage cost calculation."""
        # 1000 Tier 1 records + 100 Tier 2 summaries
        cost = self.analyzer.calculate_storage_cost(tier1_records=1000, tier2_summaries=100)
        
        self.assertGreater(cost, 0)
        self.assertLess(cost, 0.01)  # Should be less than 1 cent per day
    
    def test_update_hourly_costs(self):
        """Test updating hourly costs."""
        self.analyzer.update_hourly_costs("2024-01-01T12:00:00", 10.50)
        
        cost = self.analyzer.get_hourly_cost_summary("2024-01-01T12:00:00")
        self.assertEqual(cost, 10.50)


class TestHourlyAggregator(unittest.TestCase):
    """Test HourlyAggregator class."""
    
    def setUp(self):
        """Set up test aggregator."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_analytics.db"
        self.collector = MetricsCollector(str(self.db_path))
        self.storage = StorageManager(str(self.db_path))
        self.aggregator = HourlyAggregator(self.collector, self.storage)
    
    def tearDown(self):
        """Clean up test aggregator."""
        shutil.rmtree(self.temp_dir)
    
    def test_aggregate_empty(self):
        """Test aggregation with no metrics."""
        summary = self.aggregator.aggregate_last_hour()
        self.assertIsNone(summary)
    
    def test_aggregate_last_hour(self):
        """Test aggregating last hour metrics."""
        # Record some metrics
        for i in range(5):
            metrics = ExecutionMetrics(
                task_id=f"task_{i}",
                agent_id="agent_1",
                tool_name="api" if i % 2 == 0 else "browser",
                start_time=time.time() - 1000,
                end_time=time.time() - 995 + i,
                duration_seconds=5.0,
                success=i < 4,
                cost_actual=0.10
            )
            self.collector.record_execution(metrics)
        
        summary = self.aggregator.aggregate_last_hour()
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary.total_tasks, 5)
        self.assertEqual(summary.successful_tasks, 4)
        self.assertEqual(summary.failed_tasks, 1)


class TestAnalyticsEngine(unittest.TestCase):
    """Test AnalyticsEngine integration."""
    
    def setUp(self):
        """Set up test engine."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_analytics.db"
        self.engine = AnalyticsEngine()
        self.engine.metrics_collector.db_path = str(self.db_path)
        self.engine.storage_manager.db_path = str(self.db_path)
    
    def tearDown(self):
        """Clean up test engine."""
        shutil.rmtree(self.temp_dir)
    
    def test_record_execution(self):
        """Test recording execution through engine."""
        self.engine.record_execution(
            task_id="task_1",
            agent_id="agent_1",
            tool_name="web_search",
            duration_seconds=3.0,
            success=True,
            cost_actual=0.05,
            tokens_used=150
        )
        
        # Verify tool is registered and updated
        confidence = self.engine.tool_registry.get_tool_confidence("web_search")
        self.assertEqual(confidence, ConfidenceLevel.MEDIUM)
    
    def test_api_get_agents_status(self):
        """Test agents status API endpoint."""
        self.engine.record_execution(
            task_id="task_1",
            agent_id="agent_1",
            tool_name="api",
            duration_seconds=2.0,
            success=True
        )
        
        status = self.engine.get_agents_status()
        
        self.assertIn("timestamp", status)
        self.assertIn("agents", status)
        self.assertEqual(status["total_agents"], 1)
    
    def test_api_get_predictive_capacity(self):
        """Test capacity prediction API."""
        self.engine.record_execution(
            task_id="task_1",
            agent_id="agent_1",
            tool_name="api",
            duration_seconds=2.0,
            success=True
        )
        
        capacity = self.engine.get_predictive_capacity()
        
        self.assertIn("timestamp", capacity)
        self.assertIn("forecasts", capacity)
    
    def test_api_get_task_pipeline(self):
        """Test task pipeline API."""
        self.engine.record_execution(
            task_id="task_1",
            agent_id="agent_1",
            tool_name="api",
            duration_seconds=2.0,
            success=True
        )
        
        self.engine.record_execution(
            task_id="task_2",
            agent_id="agent_2",
            tool_name="browser",
            duration_seconds=5.0,
            success=False
        )
        
        pipeline = self.engine.get_task_pipeline()
        
        self.assertIn("last_24_hours", pipeline)
        self.assertEqual(pipeline["last_24_hours"]["total_tasks"], 2)
        self.assertEqual(pipeline["last_24_hours"]["successful_tasks"], 1)
    
    def test_api_get_api_usage_and_costing(self):
        """Test API usage and costing endpoint."""
        self.engine.record_execution(
            task_id="task_1",
            agent_id="agent_1",
            tool_name="api",
            duration_seconds=2.0,
            success=True,
            tokens_used=500,
            cost_actual=0.10
        )
        
        costing = self.engine.get_api_usage_and_costing()
        
        self.assertIn("api_usage", costing)
        self.assertIn("costing", costing)
        self.assertIn("storage", costing)
        self.assertEqual(costing["api_usage"]["total_tasks_24h"], 1)
    
    def test_api_get_system_learning(self):
        """Test system learning API."""
        # Record successful executions
        for i in range(5):
            self.engine.record_execution(
                task_id=f"task_{i}",
                agent_id="agent_1",
                tool_name="reliable_api",
                duration_seconds=2.0,
                success=True
            )
        
        learning = self.engine.get_system_learning()
        
        self.assertIn("confidence_distribution", learning)
        self.assertIn("tool_profiles", learning)
    
    def test_api_get_risk_patterns(self):
        """Test risk patterns API (internal)."""
        # Record failures
        for i in range(3):
            self.engine.record_execution(
                task_id=f"task_{i}",
                agent_id="agent_1",
                tool_name="flaky_api",
                duration_seconds=2.0,
                success=False
            )
        
        risks = self.engine.get_risk_patterns()
        
        self.assertIn("failure_patterns", risks)
        self.assertIn("flaky_api", risks["failure_patterns"])
    
    def test_api_get_tool_recommendations(self):
        """Test tool recommendations API (internal)."""
        # Record all failures
        for i in range(5):
            self.engine.record_execution(
                task_id=f"task_{i}",
                agent_id="agent_1",
                tool_name="broken_api",
                duration_seconds=2.0,
                success=False
            )
        
        recommendations = self.engine.get_tool_recommendations()
        
        self.assertIn("recommendations", recommendations)
        self.assertGreater(recommendations["total_recommendations"], 0)
    
    def test_cleanup_old_data(self):
        """Test cleanup of old data."""
        self.engine.record_execution(
            task_id="task_1",
            agent_id="agent_1",
            tool_name="api",
            duration_seconds=2.0,
            success=True
        )
        
        # Should not delete recently added data
        self.engine.cleanup_old_data()
        
        metrics = self.engine.metrics_collector.get_recent_metrics(hours=24)
        self.assertEqual(len(metrics), 1)


class TestAnalyticsIntegration(unittest.TestCase):
    """Integration tests for full analytics workflow."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_analytics.db"
        self.engine = AnalyticsEngine()
        self.engine.metrics_collector.db_path = str(self.db_path)
        self.engine.storage_manager.db_path = str(self.db_path)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow(self):
        """Test complete analytics workflow."""
        # Simulate task executions
        tasks = [
            ("task_1", "agent_1", "web_search", 2.5, True, 0.08),
            ("task_2", "agent_1", "api_call", 1.5, True, 0.05),
            ("task_3", "agent_2", "browser_action", 4.0, False, 0.15),
            ("task_4", "agent_2", "web_search", 2.0, True, 0.07),
            ("task_5", "agent_1", "api_call", 1.8, True, 0.05),
        ]
        
        for task_id, agent_id, tool, duration, success, cost in tasks:
            self.engine.record_execution(
                task_id=task_id,
                agent_id=agent_id,
                tool_name=tool,
                duration_seconds=duration,
                success=success,
                cost_actual=cost,
                tokens_used=int(duration * 100)
            )
        
        # Verify all data collected
        metrics = self.engine.metrics_collector.get_recent_metrics(hours=24)
        self.assertEqual(len(metrics), 5)
        
        # Run aggregation
        self.engine.run_hourly_aggregation()
        
        # Check all APIs work
        agents = self.engine.get_agents_status()
        pipeline = self.engine.get_task_pipeline()
        costing = self.engine.get_api_usage_and_costing()
        learning = self.engine.get_system_learning()
        
        self.assertEqual(agents["total_agents"], 2)
        self.assertEqual(pipeline["last_24_hours"]["total_tasks"], 5)
        self.assertGreater(costing["api_usage"]["total_tokens_24h"], 0)
        self.assertGreater(len(learning["tool_profiles"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
