"""
Phase 7: Advanced Analytics Engine
Orchestrates metrics collection, storage, aggregation, and learning profile building.
Integrates with existing budget_tracker, cost_tracker, and human_energy_model systems.
"""

import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from collections import defaultdict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Learning-driven tool confidence levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class ExecutionMetrics:
    """Execution-level metrics for a single task."""
    task_id: str
    agent_id: str
    tool_name: str
    start_time: float
    end_time: float
    duration_seconds: float
    success: bool
    cost_estimate: float = 0.0
    cost_actual: float = 0.0
    human_effort_level: str = "MEDIUM"
    tokens_used: int = 0
    browser_used: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ToolProfile:
    """Learning profile for a single tool."""
    tool_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_duration_seconds: float = 0.0
    avg_cost: float = 0.0
    avg_tokens: int = 0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    success_rate: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    recent_failures: List[Dict] = field(default_factory=list)
    risk_patterns: List[str] = field(default_factory=list)


@dataclass
class AgentStatusSnapshot:
    """Real-time snapshot of an agent's status."""
    agent_id: str
    status: str  # "IDLE", "BUSY", "ERROR"
    current_task_id: Optional[str] = None
    tasks_completed_today: int = 0
    avg_response_time: float = 0.0
    success_rate: float = 0.0
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CapacityForecast:
    """Predicted agent capacity for next time window."""
    agent_id: str
    estimated_available_capacity: int  # percentage
    predicted_completion_time: Optional[str] = None
    current_queue_depth: int = 0
    bottleneck_tools: List[str] = field(default_factory=list)


@dataclass
class HourlySummary:
    """Aggregated hourly summary of execution metrics."""
    hour_timestamp: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    avg_task_duration: float = 0.0
    avg_cost_per_task: float = 0.0
    tool_execution_counts: Dict[str, int] = field(default_factory=dict)


class MetricsCollector:
    """Collects execution metrics from task execution pipeline."""
    
    def __init__(self, db_path: str = "data/analytics.db"):
        self.db_path = db_path
        self.metrics_buffer = []
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize Tier 1 raw metrics table."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tier1_raw_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                duration_seconds FLOAT NOT NULL,
                success INTEGER NOT NULL,
                cost_actual FLOAT DEFAULT 0.0,
                human_effort_level TEXT DEFAULT 'MEDIUM',
                tokens_used INTEGER DEFAULT 0,
                browser_used INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tier1_timestamp ON tier1_raw_metrics(created_at)
        """)
        
        conn.commit()
        conn.close()
    
    def record_execution(self, metrics: ExecutionMetrics) -> None:
        """Record a single execution metric."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tier1_raw_metrics 
                (task_id, agent_id, tool_name, duration_seconds, success, 
                 cost_actual, human_effort_level, tokens_used, browser_used, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.task_id,
                metrics.agent_id,
                metrics.tool_name,
                metrics.duration_seconds,
                1 if metrics.success else 0,
                metrics.cost_actual,
                metrics.human_effort_level,
                metrics.tokens_used,
                1 if metrics.browser_used else 0,
                metrics.timestamp
            ))
            
            conn.commit()
            conn.close()
            self.metrics_buffer.append(metrics)
    
    def get_recent_metrics(self, hours: int = 24) -> List[ExecutionMetrics]:
        """Retrieve recent metrics from Tier 1 storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT task_id, agent_id, tool_name, duration_seconds, success,
                   cost_actual, human_effort_level, tokens_used, browser_used, timestamp
            FROM tier1_raw_metrics
            WHERE created_at > ?
            ORDER BY created_at DESC
        """, (cutoff_time,))
        
        metrics = []
        for row in cursor.fetchall():
            metrics.append(ExecutionMetrics(
                task_id=row[0],
                agent_id=row[1],
                tool_name=row[2],
                duration_seconds=row[3],
                success=bool(row[4]),
                cost_actual=row[5],
                human_effort_level=row[6],
                tokens_used=row[7],
                browser_used=bool(row[8]),
                timestamp=row[9],
                start_time=0,  # Not tracked in Tier 1
                end_time=0
            ))
        
        conn.close()
        return metrics
    
    def cleanup_old_metrics(self, hours: int = 24) -> int:
        """Remove metrics older than specified hours (Tier 1 retention)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            DELETE FROM tier1_raw_metrics WHERE created_at < ?
        """, (cutoff_time,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted


class StorageManager:
    """Manages three-tier storage: Tier 1 (raw), Tier 2 (summaries), Tier 3 (profiles)."""
    
    def __init__(self, db_path: str = "data/analytics.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_tier2_tier3()
    
    def _init_tier2_tier3(self):
        """Initialize Tier 2 and Tier 3 tables."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tier 2: Hourly Summaries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tier2_hourly_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hour_timestamp TEXT NOT NULL UNIQUE,
                    total_tasks INTEGER DEFAULT 0,
                    successful_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    total_cost FLOAT DEFAULT 0.0,
                    total_tokens INTEGER DEFAULT 0,
                    avg_task_duration FLOAT DEFAULT 0.0,
                    tool_counts TEXT,  -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tier 3: Tool Performance Profiles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tier3_tool_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL UNIQUE,
                    total_executions INTEGER DEFAULT 0,
                    successful_executions INTEGER DEFAULT 0,
                    failed_executions INTEGER DEFAULT 0,
                    avg_duration_seconds FLOAT DEFAULT 0.0,
                    avg_cost FLOAT DEFAULT 0.0,
                    avg_tokens INTEGER DEFAULT 0,
                    success_rate FLOAT DEFAULT 0.0,
                    confidence_level TEXT DEFAULT 'MEDIUM',
                    risk_patterns TEXT,  -- JSON string
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
    
    def store_hourly_summary(self, summary: HourlySummary) -> None:
        """Store hourly summary in Tier 2."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            tool_counts_json = json.dumps(summary.tool_execution_counts)
            
            cursor.execute("""
                INSERT OR REPLACE INTO tier2_hourly_summaries
                (hour_timestamp, total_tasks, successful_tasks, failed_tasks, 
                 total_cost, total_tokens, avg_task_duration, tool_counts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                summary.hour_timestamp,
                summary.total_tasks,
                summary.successful_tasks,
                summary.failed_tasks,
                summary.total_cost,
                summary.total_tokens,
                summary.avg_task_duration,
                tool_counts_json
            ))
            
            conn.commit()
            conn.close()
    
    def store_tool_profile(self, profile: ToolProfile) -> None:
        """Store/update tool profile in Tier 3."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            risk_patterns_json = json.dumps(profile.risk_patterns)
            
            cursor.execute("""
                INSERT OR REPLACE INTO tier3_tool_profiles
                (tool_name, total_executions, successful_executions, failed_executions,
                 avg_duration_seconds, avg_cost, avg_tokens, success_rate, confidence_level, risk_patterns)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.tool_name,
                profile.total_executions,
                profile.successful_executions,
                profile.failed_executions,
                profile.avg_duration_seconds,
                profile.avg_cost,
                profile.avg_tokens,
                profile.success_rate,
                profile.confidence_level.value,
                risk_patterns_json
            ))
            
            conn.commit()
            conn.close()
    
    def get_tool_profile(self, tool_name: str) -> Optional[ToolProfile]:
        """Retrieve tool profile from Tier 3."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT tool_name, total_executions, successful_executions, failed_executions,
                       avg_duration_seconds, avg_cost, avg_tokens, success_rate, confidence_level, risk_patterns
                FROM tier3_tool_profiles
                WHERE tool_name = ?
            """, (tool_name,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            risk_patterns = json.loads(row[9]) if row[9] else []
            
            return ToolProfile(
                tool_name=row[0],
                total_executions=row[1],
                successful_executions=row[2],
                failed_executions=row[3],
                avg_duration_seconds=row[4],
                avg_cost=row[5],
                avg_tokens=row[6],
                success_rate=row[7],
                confidence_level=ConfidenceLevel(row[8]),
                risk_patterns=risk_patterns
            )
    
    def cleanup_tier2(self, days: int = 30) -> int:
        """Remove Tier 2 summaries older than specified days."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(days=days)
            cursor.execute("""
                DELETE FROM tier2_hourly_summaries WHERE created_at < ?
            """, (cutoff_time,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted


class ToolRegistry:
    """Registry for tools with learning-driven confidence tracking."""
    
    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager
        self.tools: Dict[str, ToolProfile] = {}
        self.lock = threading.Lock()
    
    def register_tool(self, tool_name: str) -> None:
        """Register a new tool."""
        with self.lock:
            if tool_name not in self.tools:
                self.tools[tool_name] = ToolProfile(tool_name=tool_name)
    
    def update_tool_from_execution(self, tool_name: str, success: bool, 
                                  duration: float, cost: float, tokens: int) -> None:
        """Update tool profile based on execution results."""
        with self.lock:
            if tool_name not in self.tools:
                self.register_tool(tool_name)
            
            profile = self.tools[tool_name]
            profile.total_executions += 1
            
            if success:
                profile.successful_executions += 1
            else:
                profile.failed_executions += 1
            
            # Update averages
            old_avg_duration = profile.avg_duration_seconds
            profile.avg_duration_seconds = (
                (old_avg_duration * (profile.total_executions - 1) + duration) / 
                profile.total_executions
            )
            
            old_avg_cost = profile.avg_cost
            profile.avg_cost = (
                (old_avg_cost * (profile.total_executions - 1) + cost) / 
                profile.total_executions
            )
            
            old_avg_tokens = profile.avg_tokens
            profile.avg_tokens = int(
                (old_avg_tokens * (profile.total_executions - 1) + tokens) / 
                profile.total_executions
            )
            
            # Update success rate
            profile.success_rate = (
                profile.successful_executions / profile.total_executions
            )
            
            # Update confidence level based on executions and success rate
            self._update_confidence_level(profile)
            
            # Store to Tier 3
            self.storage.store_tool_profile(profile)
    
    def _update_confidence_level(self, profile: ToolProfile) -> None:
        """Determine confidence level based on execution history."""
        if profile.total_executions < 3:
            profile.confidence_level = ConfidenceLevel.MEDIUM
        elif profile.success_rate >= 0.95:
            profile.confidence_level = ConfidenceLevel.HIGH
        elif profile.success_rate >= 0.80:
            profile.confidence_level = ConfidenceLevel.MEDIUM
        else:
            profile.confidence_level = ConfidenceLevel.LOW
    
    def get_tool_confidence(self, tool_name: str) -> ConfidenceLevel:
        """Get confidence level for a tool."""
        with self.lock:
            if tool_name in self.tools:
                return self.tools[tool_name].confidence_level
            return ConfidenceLevel.MEDIUM
    
    def get_tools_by_confidence(self, level: ConfidenceLevel) -> List[str]:
        """Get all tools with a specific confidence level."""
        with self.lock:
            return [
                tool_name for tool_name, profile in self.tools.items()
                if profile.confidence_level == level
            ]


class CapacityAnalyzer:
    """Analyzes agent capacity and predicts availability."""
    
    def __init__(self):
        self.agent_metrics = defaultdict(lambda: {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "avg_response_time": 0.0,
            "current_queue": [],
            "status": "IDLE"
        })
    
    def update_agent_metrics(self, agent_id: str, metrics: List[ExecutionMetrics]) -> None:
        """Update metrics for an agent."""
        if not metrics:
            return
        
        agent_data = self.agent_metrics[agent_id]
        agent_data["total_tasks"] = len(metrics)
        
        successful = [m for m in metrics if m.success]
        agent_data["completed_tasks"] = len(successful)
        agent_data["failed_tasks"] = len(metrics) - len(successful)
        
        if successful:
            avg_duration = sum(m.duration_seconds for m in successful) / len(successful)
            agent_data["avg_response_time"] = avg_duration
    
    def predict_capacity(self, agent_id: str) -> CapacityForecast:
        """Predict agent capacity for next time window."""
        agent_data = self.agent_metrics.get(agent_id)
        
        if not agent_data:
            return CapacityForecast(
                agent_id=agent_id,
                estimated_available_capacity=100
            )
        
        # Estimate capacity based on response time and queue depth
        if agent_data["avg_response_time"] > 10:  # seconds
            capacity = 50
        elif agent_data["avg_response_time"] > 5:
            capacity = 75
        else:
            capacity = 100
        
        # Identify bottleneck tools
        bottlenecks = self._identify_bottlenecks(agent_id)
        
        return CapacityForecast(
            agent_id=agent_id,
            estimated_available_capacity=capacity,
            current_queue_depth=len(agent_data.get("current_queue", [])),
            bottleneck_tools=bottlenecks
        )
    
    def _identify_bottlenecks(self, agent_id: str) -> List[str]:
        """Identify tools that are bottlenecks for an agent."""
        # Implementation would analyze tool performance for this agent
        return []


class CostAnalyzer:
    """Analyzes costs and integrates with cost_tracker system."""
    
    def __init__(self, cost_tracker_module=None):
        self.cost_tracker = cost_tracker_module
        self.hourly_costs = defaultdict(float)
    
    def calculate_storage_cost(self, tier1_records: int, tier2_summaries: int) -> float:
        """Calculate storage cost for analytics data."""
        # Tier 1: ~500 bytes per record
        # Tier 2: ~200 bytes per summary
        # Estimate: $0.023 per GB per month (Firestore pricing)
        
        tier1_size_mb = (tier1_records * 500) / (1024 * 1024)
        tier2_size_mb = (tier2_summaries * 200) / (1024 * 1024)
        
        total_size_mb = tier1_size_mb + tier2_size_mb
        storage_cost = (total_size_mb / 1024) * 0.023 / 30  # Daily cost
        
        return storage_cost
    
    def get_hourly_cost_summary(self, hour_timestamp: str) -> float:
        """Get total cost for a specific hour."""
        return self.hourly_costs.get(hour_timestamp, 0.0)
    
    def update_hourly_costs(self, hour_timestamp: str, total_cost: float) -> None:
        """Update hourly cost totals."""
        self.hourly_costs[hour_timestamp] = total_cost


class HourlyAggregator:
    """Aggregates metrics into hourly summaries (Tier 2)."""
    
    def __init__(self, metrics_collector: MetricsCollector, storage_manager: StorageManager):
        self.collector = metrics_collector
        self.storage = storage_manager
    
    def aggregate_last_hour(self) -> Optional[HourlySummary]:
        """Aggregate metrics from the last hour."""
        now = datetime.now()
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        hour_timestamp = hour_start.isoformat()
        
        # Get metrics from last hour
        metrics = self.collector.get_recent_metrics(hours=1)
        
        if not metrics:
            return None
        
        # Calculate aggregations
        total_tasks = len(metrics)
        successful = len([m for m in metrics if m.success])
        failed = total_tasks - successful
        
        total_cost = sum(m.cost_actual for m in metrics)
        total_tokens = sum(m.tokens_used for m in metrics)
        avg_duration = sum(m.duration_seconds for m in metrics) / total_tasks if total_tasks > 0 else 0.0
        
        # Count executions by tool
        tool_counts = defaultdict(int)
        for m in metrics:
            tool_counts[m.tool_name] += 1
        
        summary = HourlySummary(
            hour_timestamp=hour_timestamp,
            total_tasks=total_tasks,
            successful_tasks=successful,
            failed_tasks=failed,
            total_cost=total_cost,
            total_tokens=total_tokens,
            avg_task_duration=avg_duration,
            tool_execution_counts=dict(tool_counts)
        )
        
        # Store to Tier 2
        self.storage.store_hourly_summary(summary)
        return summary


class AnalyticsEngine:
    """Main orchestrator for Phase 7 analytics system."""
    
    def __init__(self, cost_tracker_module=None):
        self.metrics_collector = MetricsCollector()
        self.storage_manager = StorageManager()
        self.tool_registry = ToolRegistry(self.storage_manager)
        self.capacity_analyzer = CapacityAnalyzer()
        self.cost_analyzer = CostAnalyzer(cost_tracker_module)
        self.hourly_aggregator = HourlyAggregator(self.metrics_collector, self.storage_manager)
        
        self.agents = {}  # agent_id -> AgentStatusSnapshot
        self.lock = threading.Lock()
        self.running = False
    
    def record_execution(self, task_id: str, agent_id: str, tool_name: str,
                        duration_seconds: float, success: bool,
                        cost_actual: float = 0.0, tokens_used: int = 0,
                        human_effort_level: str = "MEDIUM", browser_used: bool = False) -> None:
        """Record a single execution (integration point with task execution pipeline)."""
        
        # Ensure tool is registered
        self.tool_registry.register_tool(tool_name)
        
        # Create metrics record
        metrics = ExecutionMetrics(
            task_id=task_id,
            agent_id=agent_id,
            tool_name=tool_name,
            start_time=time.time() - duration_seconds,
            end_time=time.time(),
            duration_seconds=duration_seconds,
            success=success,
            cost_actual=cost_actual,
            tokens_used=tokens_used,
            human_effort_level=human_effort_level,
            browser_used=browser_used
        )
        
        # Record to Tier 1
        self.metrics_collector.record_execution(metrics)
        
        # Update tool profile
        self.tool_registry.update_tool_from_execution(
            tool_name, success, duration_seconds, cost_actual, tokens_used
        )
        
        # Update agent status
        self._update_agent_status(agent_id, success)
    
    def _update_agent_status(self, agent_id: str, success: bool) -> None:
        """Update agent status snapshot."""
        with self.lock:
            if agent_id not in self.agents:
                self.agents[agent_id] = AgentStatusSnapshot(
                    agent_id=agent_id,
                    status="IDLE"
                )
            
            agent = self.agents[agent_id]
            agent.tasks_completed_today += 1
            agent.status = "IDLE"
            agent.last_activity = datetime.now().isoformat()
    
    def run_hourly_aggregation(self) -> None:
        """Run hourly aggregation job."""
        summary = self.hourly_aggregator.aggregate_last_hour()
        if summary:
            self.cost_analyzer.update_hourly_costs(
                summary.hour_timestamp,
                summary.total_cost
            )
    
    def cleanup_old_data(self) -> None:
        """Cleanup old data from Tier 1 and Tier 2."""
        deleted_tier1 = self.metrics_collector.cleanup_old_metrics(hours=24)
        deleted_tier2 = self.storage_manager.cleanup_tier2(days=30)
        
        logger.info(f"Cleanup: Deleted {deleted_tier1} Tier 1 records, {deleted_tier2} Tier 2 summaries")
    
    # ============ PUBLIC API ENDPOINTS ============
    
    def get_agents_status(self) -> Dict[str, Any]:
        """API: Get current status of all agents."""
        with self.lock:
            agents_list = []
            for agent_id, agent in self.agents.items():
                agents_list.append({
                    "agent_id": agent_id,
                    "status": agent.status,
                    "tasks_completed_today": agent.tasks_completed_today,
                    "avg_response_time": agent.avg_response_time,
                    "success_rate": agent.success_rate,
                    "last_activity": agent.last_activity
                })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(agents_list),
            "agents": agents_list
        }
    
    def get_predictive_capacity(self) -> Dict[str, Any]:
        """API: Get predicted capacity for all agents."""
        forecasts = []
        for agent_id in list(self.agents.keys()):
            forecast = self.capacity_analyzer.predict_capacity(agent_id)
            forecasts.append({
                "agent_id": forecast.agent_id,
                "estimated_available_capacity": forecast.estimated_available_capacity,
                "current_queue_depth": forecast.current_queue_depth,
                "bottleneck_tools": forecast.bottleneck_tools
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "forecasts": forecasts
        }
    
    def get_task_pipeline(self) -> Dict[str, Any]:
        """API: Get current task pipeline status."""
        metrics = self.metrics_collector.get_recent_metrics(hours=24)
        
        total_tasks = len(metrics)
        successful = len([m for m in metrics if m.success])
        failed = total_tasks - successful
        
        # Tool breakdown
        tool_stats = defaultdict(lambda: {"total": 0, "successful": 0})
        for m in metrics:
            tool_stats[m.tool_name]["total"] += 1
            if m.success:
                tool_stats[m.tool_name]["successful"] += 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "last_24_hours": {
                "total_tasks": total_tasks,
                "successful_tasks": successful,
                "failed_tasks": failed,
                "success_rate": successful / total_tasks if total_tasks > 0 else 0.0,
                "tool_breakdown": dict(tool_stats)
            }
        }
    
    def get_api_usage_and_costing(self) -> Dict[str, Any]:
        """API: Get API usage and real-time storage costing."""
        metrics = self.metrics_collector.get_recent_metrics(hours=24)
        
        total_tokens = sum(m.tokens_used for m in metrics)
        total_cost = sum(m.cost_actual for m in metrics)
        
        # Get raw metric count for storage cost calculation
        conn = sqlite3.connect(self.metrics_collector.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tier1_raw_metrics")
        tier1_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tier2_hourly_summaries")
        tier2_count = cursor.fetchone()[0]
        conn.close()
        
        storage_cost = self.cost_analyzer.calculate_storage_cost(tier1_count, tier2_count)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "api_usage": {
                "total_tasks_24h": len(metrics),
                "total_tokens_24h": total_tokens,
                "avg_tokens_per_task": total_tokens / len(metrics) if metrics else 0
            },
            "costing": {
                "execution_costs_24h": total_cost,
                "storage_costs_daily": storage_cost,
                "total_daily_cost": total_cost + storage_cost
            },
            "storage": {
                "tier1_raw_records": tier1_count,
                "tier2_hourly_summaries": tier2_count,
                "estimated_size_mb": ((tier1_count * 500) + (tier2_count * 200)) / (1024 * 1024)
            }
        }
    
    def get_system_learning(self) -> Dict[str, Any]:
        """API: Get system learning profiles and confidence metrics."""
        high_confidence_tools = self.tool_registry.get_tools_by_confidence(ConfidenceLevel.HIGH)
        medium_confidence_tools = self.tool_registry.get_tools_by_confidence(ConfidenceLevel.MEDIUM)
        low_confidence_tools = self.tool_registry.get_tools_by_confidence(ConfidenceLevel.LOW)
        
        tool_profiles = []
        for tool_name in self.tool_registry.tools.keys():
            profile = self.tool_registry.tools[tool_name]
            tool_profiles.append({
                "tool_name": profile.tool_name,
                "total_executions": profile.total_executions,
                "success_rate": profile.success_rate,
                "avg_cost": profile.avg_cost,
                "avg_duration": profile.avg_duration_seconds,
                "confidence_level": profile.confidence_level.value
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "confidence_distribution": {
                "high_confidence": len(high_confidence_tools),
                "medium_confidence": len(medium_confidence_tools),
                "low_confidence": len(low_confidence_tools)
            },
            "tool_profiles": sorted(tool_profiles, 
                                   key=lambda x: x["total_executions"], 
                                   reverse=True)
        }
    
    def get_risk_patterns(self) -> Dict[str, Any]:
        """API (Internal): Get risk patterns and recommendations."""
        metrics = self.metrics_collector.get_recent_metrics(hours=24)
        
        risk_patterns = defaultdict(list)
        
        # Identify failure patterns by tool
        for m in metrics:
            if not m.success:
                risk_patterns[m.tool_name].append({
                    "task_id": m.task_id,
                    "timestamp": m.timestamp,
                    "duration": m.duration_seconds
                })
        
        # Identify cost anomalies
        high_cost_threshold = sum(m.cost_actual for m in metrics) / len(metrics) * 2 if metrics else 0
        cost_anomalies = [
            {
                "task_id": m.task_id,
                "cost": m.cost_actual,
                "tool": m.tool_name
            }
            for m in metrics if m.cost_actual > high_cost_threshold
        ]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "failure_patterns": dict(risk_patterns),
            "cost_anomalies": cost_anomalies
        }
    
    def get_tool_recommendations(self) -> Dict[str, Any]:
        """API (Internal): Get tool optimization recommendations."""
        low_confidence = self.tool_registry.get_tools_by_confidence(ConfidenceLevel.LOW)
        
        recommendations = []
        for tool_name in low_confidence:
            profile = self.tool_registry.tools[tool_name]
            recommendations.append({
                "tool": tool_name,
                "reason": f"Low success rate: {profile.success_rate:.1%}",
                "executions": profile.total_executions,
                "failed": profile.failed_executions,
                "recommendation": "Review tool configuration or fallback strategies"
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_recommendations": len(recommendations),
            "recommendations": recommendations
        }
