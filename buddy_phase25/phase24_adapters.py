"""
Phase 24 Integration Adapters

Read-only adapters for consuming Phase 24 autonomous system outputs.
Integrates tool execution, orchestration health, conflicts, and learning signals
into Phase 25 dashboards without triggering or modifying any execution state.

Key Guarantee: All adapters are purely observational. Zero side effects.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum


class ExecutionMode(Enum):
    """Phase 24 execution mode"""
    MOCK = "mock"
    DRY_RUN = "dry_run"
    LIVE = "live"
    LOCKED = "locked"


@dataclass(frozen=True)
class ToolExecution:
    """Single tool execution record from Phase 24"""
    execution_id: str
    tool_name: str
    timestamp: str
    duration_ms: float
    status: str  # success, partial, failed, blocked, rollback
    confidence_score: float  # 0.0-1.0
    risk_level: str  # low, medium, high
    approval_status: str  # approved, pending, rejected
    dry_run_mode: bool
    error_message: Optional[str] = None
    output_summary: Optional[str] = None
    agent_id: Optional[str] = None


@dataclass(frozen=True)
class ExecutionStateTransition:
    """State transition in orchestration"""
    transition_id: str
    timestamp: str
    from_state: str
    to_state: str
    trigger: str  # completion, approval, error, rollback, safety_gate
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SystemHealthSnapshot:
    """System health at a point in time"""
    timestamp: str
    health_score: int  # 0-100
    execution_mode: str
    active_executions: int
    completed_executions: int
    failed_executions: int
    blocked_by_safety: int
    avg_tool_confidence: float
    anomalies_detected: int


@dataclass(frozen=True)
class RollbackEvent:
    """Rollback triggered by safety, error, or conflict"""
    rollback_id: str
    timestamp: str
    trigger: str  # safety_violation, execution_failure, conflict_resolution, manual
    affected_executions: List[str]
    reason: str
    recovery_status: str  # in_progress, completed, failed
    duration_ms: Optional[float] = None


@dataclass(frozen=True)
class ToolConflict:
    """Conflict detected between concurrent tools"""
    conflict_id: str
    timestamp: str
    tools_involved: List[str]
    conflict_type: str  # resource_contention, safety_violation, state_inconsistency
    severity: str  # low, medium, high
    resolution_strategy: str  # rollback, serialize, approval_wait
    resolution_status: str  # resolved, pending, failed
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LearningSignal:
    """Learning signal generated during execution"""
    signal_id: str
    timestamp: str
    signal_type: str  # tool_reliability, timing_pattern, safety_pattern, conflict_pattern
    tool_name: str
    insight: str
    confidence: float  # 0.0-1.0
    recommended_action: str
    affected_future_executions: int


class Phase24Adapter:
    """
    Base adapter for Phase 24 outputs.
    All methods are read-only with exception handling for missing files.
    """

    def __init__(self, phase24_outputs_path: Optional[Path] = None):
        """Initialize adapter with path to Phase 24 outputs"""
        if phase24_outputs_path is None:
            phase24_outputs_path = Path("outputs/phase24")
        self.phase24_path = phase24_outputs_path

    def _read_jsonl(self, filename: str) -> List[Dict[str, Any]]:
        """
        Read JSONL file safely.
        Returns empty list if file not found.
        """
        filepath = self.phase24_path / filename
        records = []

        try:
            if not filepath.exists():
                return records

            with open(filepath, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass

        return records

    def _read_json(self, filename: str) -> Dict[str, Any]:
        """
        Read JSON file safely.
        Returns empty dict if file not found.
        """
        filepath = self.phase24_path / filename
        try:
            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception:
            pass

        return {}


class ExecutionLogAdapter(Phase24Adapter):
    """
    Adapter for tool_execution_log.jsonl.
    Reads all tool executions without modifying any state.
    """

    def get_recent_executions(self, limit: int = 50) -> List[ToolExecution]:
        """Get most recent tool executions"""
        records = self._read_jsonl("tool_execution_log.jsonl")

        executions = []
        for record in records:
            try:
                execution = ToolExecution(
                    execution_id=record.get("execution_id", ""),
                    tool_name=record.get("tool_name", "unknown"),
                    timestamp=record.get("timestamp", ""),
                    duration_ms=record.get("duration_ms", 0.0),
                    status=record.get("status", "unknown"),
                    confidence_score=record.get("confidence_score", 0.0),
                    risk_level=record.get("risk_level", "unknown"),
                    approval_status=record.get("approval_status", "unknown"),
                    dry_run_mode=record.get("dry_run_mode", False),
                    error_message=record.get("error_message"),
                    output_summary=record.get("output_summary"),
                    agent_id=record.get("agent_id")
                )
                executions.append(execution)
            except Exception:
                continue

        # Return most recent (reverse chronological)
        return list(reversed(executions))[:limit]

    def get_executions_by_status(self, status: str) -> List[ToolExecution]:
        """Get all executions with given status (success, failed, blocked, etc)"""
        records = self._read_jsonl("tool_execution_log.jsonl")
        executions = []

        for record in records:
            if record.get("status") == status:
                try:
                    execution = ToolExecution(
                        execution_id=record.get("execution_id", ""),
                        tool_name=record.get("tool_name", "unknown"),
                        timestamp=record.get("timestamp", ""),
                        duration_ms=record.get("duration_ms", 0.0),
                        status=record.get("status", "unknown"),
                        confidence_score=record.get("confidence_score", 0.0),
                        risk_level=record.get("risk_level", "unknown"),
                        approval_status=record.get("approval_status", "unknown"),
                        dry_run_mode=record.get("dry_run_mode", False),
                        error_message=record.get("error_message"),
                        output_summary=record.get("output_summary"),
                        agent_id=record.get("agent_id")
                    )
                    executions.append(execution)
                except Exception:
                    continue

        return executions

    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics by tool"""
        records = self._read_jsonl("tool_execution_log.jsonl")
        stats = {}

        for record in records:
            tool = record.get("tool_name", "unknown")

            if tool not in stats:
                stats[tool] = {
                    "total_calls": 0,
                    "successful": 0,
                    "failed": 0,
                    "blocked": 0,
                    "avg_confidence": 0.0,
                    "avg_duration_ms": 0.0,
                    "confidence_scores": [],
                    "durations": []
                }

            stats[tool]["total_calls"] += 1
            status = record.get("status", "unknown")

            if status == "success":
                stats[tool]["successful"] += 1
            elif status == "failed":
                stats[tool]["failed"] += 1
            elif status == "blocked":
                stats[tool]["blocked"] += 1

            confidence = record.get("confidence_score", 0.0)
            duration = record.get("duration_ms", 0.0)

            stats[tool]["confidence_scores"].append(confidence)
            stats[tool]["durations"].append(duration)

        # Calculate averages
        for tool in stats:
            if stats[tool]["confidence_scores"]:
                stats[tool]["avg_confidence"] = sum(stats[tool]["confidence_scores"]) / len(
                    stats[tool]["confidence_scores"]
                )
            if stats[tool]["durations"]:
                stats[tool]["avg_duration_ms"] = sum(stats[tool]["durations"]) / len(
                    stats[tool]["durations"]
                )

            # Remove intermediate lists
            del stats[tool]["confidence_scores"]
            del stats[tool]["durations"]

        return stats

    def get_execution_success_rate(self) -> float:
        """Calculate overall success rate (0.0-1.0)"""
        records = self._read_jsonl("tool_execution_log.jsonl")

        if not records:
            return 0.0

        successful = sum(1 for r in records if r.get("status") == "success")
        return successful / len(records)


class StateTransitionAdapter(Phase24Adapter):
    """
    Adapter for execution_state_transitions.jsonl.
    Reads orchestration state changes without modifying them.
    """

    def get_recent_transitions(self, limit: int = 50) -> List[ExecutionStateTransition]:
        """Get most recent state transitions"""
        records = self._read_jsonl("execution_state_transitions.jsonl")
        transitions = []

        for record in records:
            try:
                transition = ExecutionStateTransition(
                    transition_id=record.get("transition_id", ""),
                    timestamp=record.get("timestamp", ""),
                    from_state=record.get("from_state", ""),
                    to_state=record.get("to_state", ""),
                    trigger=record.get("trigger", ""),
                    details=record.get("details", {})
                )
                transitions.append(transition)
            except Exception:
                continue

        return list(reversed(transitions))[:limit]

    def get_state_timeline(self) -> List[Tuple[str, str, str]]:
        """Get timeline of state transitions as (timestamp, from_state, to_state)"""
        records = self._read_jsonl("execution_state_transitions.jsonl")
        timeline = []

        for record in records:
            timeline.append((
                record.get("timestamp", ""),
                record.get("from_state", "unknown"),
                record.get("to_state", "unknown")
            ))

        return timeline

    def get_transitions_by_trigger(self, trigger: str) -> List[ExecutionStateTransition]:
        """Get all transitions triggered by specific event"""
        records = self._read_jsonl("execution_state_transitions.jsonl")
        transitions = []

        for record in records:
            if record.get("trigger") == trigger:
                try:
                    transition = ExecutionStateTransition(
                        transition_id=record.get("transition_id", ""),
                        timestamp=record.get("timestamp", ""),
                        from_state=record.get("from_state", ""),
                        to_state=record.get("to_state", ""),
                        trigger=record.get("trigger", ""),
                        details=record.get("details", {})
                    )
                    transitions.append(transition)
                except Exception:
                    continue

        return transitions


class SystemHealthAdapter(Phase24Adapter):
    """
    Adapter for system_health.json.
    Reads current system health snapshot without modification.
    """

    def get_health_snapshot(self) -> Optional[SystemHealthSnapshot]:
        """Get current system health"""
        data = self._read_json("system_health.json")

        if not data:
            return None

        try:
            return SystemHealthSnapshot(
                timestamp=data.get("timestamp", ""),
                health_score=data.get("health_score", 0),
                execution_mode=data.get("execution_mode", "unknown"),
                active_executions=data.get("active_executions", 0),
                completed_executions=data.get("completed_executions", 0),
                failed_executions=data.get("failed_executions", 0),
                blocked_by_safety=data.get("blocked_by_safety", 0),
                avg_tool_confidence=data.get("avg_tool_confidence", 0.0),
                anomalies_detected=data.get("anomalies_detected", 0)
            )
        except Exception:
            return None

    def get_health_tier(self, score: int) -> str:
        """Convert health score to tier label"""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 75:
            return "GOOD"
        elif score >= 60:
            return "WARNING"
        elif score >= 40:
            return "CRITICAL"
        else:
            return "FAILURE"

    def get_health_indicators(self) -> Dict[str, Any]:
        """Get detailed health indicators"""
        data = self._read_json("system_health.json")

        return {
            "current_mode": data.get("execution_mode", "unknown"),
            "active_tools": data.get("active_executions", 0),
            "success_rate": data.get("success_rate", 0.0),
            "safety_blocks": data.get("blocked_by_safety", 0),
            "rollbacks_triggered": data.get("rollbacks_triggered", 0),
            "conflicts_detected": data.get("conflicts_detected", 0),
            "avg_execution_time_ms": data.get("avg_execution_time_ms", 0.0)
        }


class RollbackAdapter(Phase24Adapter):
    """
    Adapter for rollback_events.jsonl.
    Reads rollback history without triggering new rollbacks.
    """

    def get_recent_rollbacks(self, limit: int = 20) -> List[RollbackEvent]:
        """Get most recent rollback events"""
        records = self._read_jsonl("rollback_events.jsonl")
        rollbacks = []

        for record in records:
            try:
                rollback = RollbackEvent(
                    rollback_id=record.get("rollback_id", ""),
                    timestamp=record.get("timestamp", ""),
                    trigger=record.get("trigger", "unknown"),
                    affected_executions=record.get("affected_executions", []),
                    reason=record.get("reason", ""),
                    recovery_status=record.get("recovery_status", "pending"),
                    duration_ms=record.get("duration_ms")
                )
                rollbacks.append(rollback)
            except Exception:
                continue

        return list(reversed(rollbacks))[:limit]

    def get_rollback_summary(self) -> Dict[str, Any]:
        """Get aggregate rollback statistics"""
        records = self._read_jsonl("rollback_events.jsonl")

        summary = {
            "total_rollbacks": len(records),
            "by_trigger": {},
            "successful": 0,
            "failed": 0,
            "in_progress": 0
        }

        for record in records:
            trigger = record.get("trigger", "unknown")
            status = record.get("recovery_status", "unknown")

            if trigger not in summary["by_trigger"]:
                summary["by_trigger"][trigger] = 0

            summary["by_trigger"][trigger] += 1

            if status == "completed":
                summary["successful"] += 1
            elif status == "failed":
                summary["failed"] += 1
            elif status == "in_progress":
                summary["in_progress"] += 1

        return summary

    def get_rollbacks_by_trigger(self, trigger: str) -> List[RollbackEvent]:
        """Get all rollbacks triggered by specific event"""
        records = self._read_jsonl("rollback_events.jsonl")
        rollbacks = []

        for record in records:
            if record.get("trigger") == trigger:
                try:
                    rollback = RollbackEvent(
                        rollback_id=record.get("rollback_id", ""),
                        timestamp=record.get("timestamp", ""),
                        trigger=record.get("trigger", "unknown"),
                        affected_executions=record.get("affected_executions", []),
                        reason=record.get("reason", ""),
                        recovery_status=record.get("recovery_status", "pending"),
                        duration_ms=record.get("duration_ms")
                    )
                    rollbacks.append(rollback)
                except Exception:
                    continue

        return rollbacks


class ConflictAdapter(Phase24Adapter):
    """
    Adapter for tool_conflicts.json.
    Reads detected conflicts and resolutions without modifying them.
    """

    def get_conflicts(self) -> List[ToolConflict]:
        """Get all detected conflicts"""
        records = self._read_jsonl("tool_conflicts.json")
        conflicts = []

        for record in records:
            try:
                conflict = ToolConflict(
                    conflict_id=record.get("conflict_id", ""),
                    timestamp=record.get("timestamp", ""),
                    tools_involved=record.get("tools_involved", []),
                    conflict_type=record.get("conflict_type", "unknown"),
                    severity=record.get("severity", "unknown"),
                    resolution_strategy=record.get("resolution_strategy", "unknown"),
                    resolution_status=record.get("resolution_status", "pending"),
                    details=record.get("details", {})
                )
                conflicts.append(conflict)
            except Exception:
                continue

        return conflicts

    def get_unresolved_conflicts(self) -> List[ToolConflict]:
        """Get conflicts still pending resolution"""
        all_conflicts = self.get_conflicts()
        return [c for c in all_conflicts if c.resolution_status != "resolved"]

    def get_conflict_summary(self) -> Dict[str, Any]:
        """Get aggregate conflict statistics"""
        conflicts = self.get_conflicts()

        summary = {
            "total_detected": len(conflicts),
            "unresolved": 0,
            "by_type": {},
            "by_severity": {},
            "resolution_strategies": {}
        }

        for conflict in conflicts:
            if conflict.resolution_status != "resolved":
                summary["unresolved"] += 1

            conflict_type = conflict.conflict_type
            if conflict_type not in summary["by_type"]:
                summary["by_type"][conflict_type] = 0
            summary["by_type"][conflict_type] += 1

            severity = conflict.severity
            if severity not in summary["by_severity"]:
                summary["by_severity"][severity] = 0
            summary["by_severity"][severity] += 1

            strategy = conflict.resolution_strategy
            if strategy not in summary["resolution_strategies"]:
                summary["resolution_strategies"][strategy] = 0
            summary["resolution_strategies"][strategy] += 1

        return summary

    def get_high_severity_conflicts(self) -> List[ToolConflict]:
        """Get all high-severity conflicts for immediate attention"""
        conflicts = self.get_conflicts()
        return [c for c in conflicts if c.severity == "high"]


class LearningSignalAdapter(Phase24Adapter):
    """
    Adapter for learning_signals.jsonl.
    Reads generated learning signals without modifying them.
    """

    def get_recent_signals(self, limit: int = 20) -> List[LearningSignal]:
        """Get most recent learning signals"""
        records = self._read_jsonl("learning_signals.jsonl")
        signals = []

        for record in records:
            try:
                signal = LearningSignal(
                    signal_id=record.get("signal_id", ""),
                    timestamp=record.get("timestamp", ""),
                    signal_type=record.get("signal_type", "unknown"),
                    tool_name=record.get("tool_name", "unknown"),
                    insight=record.get("insight", ""),
                    confidence=record.get("confidence", 0.0),
                    recommended_action=record.get("recommended_action", ""),
                    affected_future_executions=record.get("affected_future_executions", 0)
                )
                signals.append(signal)
            except Exception:
                continue

        return list(reversed(signals))[:limit]

    def get_signals_by_type(self, signal_type: str) -> List[LearningSignal]:
        """Get all signals of given type"""
        records = self._read_jsonl("learning_signals.jsonl")
        signals = []

        for record in records:
            if record.get("signal_type") == signal_type:
                try:
                    signal = LearningSignal(
                        signal_id=record.get("signal_id", ""),
                        timestamp=record.get("timestamp", ""),
                        signal_type=record.get("signal_type", "unknown"),
                        tool_name=record.get("tool_name", "unknown"),
                        insight=record.get("insight", ""),
                        confidence=record.get("confidence", 0.0),
                        recommended_action=record.get("recommended_action", ""),
                        affected_future_executions=record.get("affected_future_executions", 0)
                    )
                    signals.append(signal)
                except Exception:
                    continue

        return signals

    def get_high_confidence_signals(self, threshold: float = 0.8) -> List[LearningSignal]:
        """Get all signals above confidence threshold"""
        all_signals = self.get_recent_signals(limit=1000)
        return [s for s in all_signals if s.confidence >= threshold]

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get aggregate learning statistics"""
        records = self._read_jsonl("learning_signals.jsonl")

        summary = {
            "total_signals": len(records),
            "by_type": {},
            "by_tool": {},
            "avg_confidence": 0.0,
            "high_confidence_count": 0
        }

        confidences = []
        for record in records:
            signal_type = record.get("signal_type", "unknown")
            tool = record.get("tool_name", "unknown")
            confidence = record.get("confidence", 0.0)

            if signal_type not in summary["by_type"]:
                summary["by_type"][signal_type] = 0
            summary["by_type"][signal_type] += 1

            if tool not in summary["by_tool"]:
                summary["by_tool"][tool] = 0
            summary["by_tool"][tool] += 1

            confidences.append(confidence)

            if confidence >= 0.8:
                summary["high_confidence_count"] += 1

        if confidences:
            summary["avg_confidence"] = sum(confidences) / len(confidences)

        return summary


class Phase24AggregateAdapter:
    """
    High-level adapter that combines all Phase 24 data sources
    for dashboard consumption.
    """

    def __init__(self, phase24_outputs_path: Optional[Path] = None):
        """Initialize all sub-adapters"""
        self.execution_log = ExecutionLogAdapter(phase24_outputs_path)
        self.state_transitions = StateTransitionAdapter(phase24_outputs_path)
        self.health = SystemHealthAdapter(phase24_outputs_path)
        self.rollbacks = RollbackAdapter(phase24_outputs_path)
        self.conflicts = ConflictAdapter(phase24_outputs_path)
        self.learning_signals = LearningSignalAdapter(phase24_outputs_path)

    def get_operations_summary(self) -> Dict[str, Any]:
        """
        Aggregated operations dashboard data.
        Combines execution, health, conflicts, and rollbacks.
        """
        health_snap = self.health.get_health_snapshot()
        exec_stats = self.execution_log.get_tool_statistics()
        conflict_summary = self.conflicts.get_conflict_summary()
        rollback_summary = self.rollbacks.get_rollback_summary()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_mode": health_snap.execution_mode if health_snap else "unknown",
            "health_score": health_snap.health_score if health_snap else 0,
            "health_tier": self.health.get_health_tier(health_snap.health_score) if health_snap else "unknown",
            "success_rate": self.execution_log.get_execution_success_rate(),
            "tool_statistics": exec_stats,
            "conflicts": conflict_summary,
            "rollbacks": rollback_summary,
            "recent_executions": [
                {
                    "tool": e.tool_name,
                    "status": e.status,
                    "confidence": e.confidence_score,
                    "duration_ms": e.duration_ms
                }
                for e in self.execution_log.get_recent_executions(limit=10)
            ]
        }

    def get_learning_summary(self) -> Dict[str, Any]:
        """
        Aggregated learning dashboard data.
        Combines learning signals and execution patterns.
        """
        signal_summary = self.learning_signals.get_learning_summary()
        high_confidence = self.learning_signals.get_high_confidence_signals()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_signals": signal_summary["total_signals"],
            "by_type": signal_summary["by_type"],
            "by_tool": signal_summary["by_tool"],
            "avg_confidence": signal_summary["avg_confidence"],
            "high_confidence_signals": len(high_confidence),
            "recent_insights": [
                {
                    "tool": s.tool_name,
                    "type": s.signal_type,
                    "insight": s.insight,
                    "confidence": s.confidence,
                    "timestamp": s.timestamp
                }
                for s in self.learning_signals.get_recent_signals(limit=10)
            ]
        }

    def get_interaction_summary(self) -> Dict[str, Any]:
        """
        Aggregated interaction dashboard data.
        Combines safety decisions, approvals, and execution previews.
        """
        recent_execs = self.execution_log.get_recent_executions(limit=20)
        unresolved_conflicts = self.conflicts.get_unresolved_conflicts()
        recent_rollbacks = self.rollbacks.get_recent_rollbacks(limit=5)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pending_approvals": sum(1 for e in recent_execs if e.approval_status == "pending"),
            "recent_executions": [
                {
                    "tool": e.tool_name,
                    "status": e.status,
                    "risk_level": e.risk_level,
                    "approval_status": e.approval_status,
                    "dry_run": e.dry_run_mode
                }
                for e in recent_execs
            ],
            "unresolved_conflicts": len(unresolved_conflicts),
            "conflict_details": [
                {
                    "tools": ", ".join(c.tools_involved),
                    "type": c.conflict_type,
                    "severity": c.severity,
                    "strategy": c.resolution_strategy
                }
                for c in unresolved_conflicts[:5]
            ],
            "recent_rollbacks": [
                {
                    "trigger": r.trigger,
                    "reason": r.reason,
                    "status": r.recovery_status
                }
                for r in recent_rollbacks
            ]
        }
