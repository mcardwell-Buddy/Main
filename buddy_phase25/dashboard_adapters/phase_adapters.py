"""
Phase 25: Dashboard Adapters

Read-only adapters that map phase outputs to dashboard views.
Deterministic, testable, no side effects.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from .dashboard_state_models import (
    LearningSignal, ToolExecution, SafetyDecision, ActiveAgent,
    SystemHealthMetrics, ConfidenceTrajectory, MetricPoint,
    ExecutionEnvironment, LearningDashboardState, OperationsDashboardState,
    InteractionDashboardState, TaskRequest, ApprovalPrompt
)


class PhaseOutputAdapter:
    """Base adapter for reading phase outputs"""
    
    def __init__(self, outputs_base_path: Path = Path("outputs")):
        self.outputs_base = outputs_base_path
    
    def read_phase_output(self, phase: int, filename: str) -> Optional[Dict[str, Any]]:
        """Read JSON output from phase"""
        try:
            phase_dir = self.outputs_base / f"phase{phase}"
            output_file = phase_dir / filename
            if output_file.exists():
                with open(output_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error reading phase {phase} output: {e}")
        return None
    
    def read_jsonl_stream(self, phase: int, filename: str) -> List[Dict[str, Any]]:
        """Read JSONL stream from phase"""
        records = []
        try:
            phase_dir = self.outputs_base / f"phase{phase}"
            stream_file = phase_dir / filename
            if stream_file.exists():
                with open(stream_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line))
        except Exception as e:
            print(f"Error reading JSONL stream: {e}")
        return records


class LearningDashboardAdapter(PhaseOutputAdapter):
    """Adapter for Learning Dashboard - maps Phase 16, 19, 24 outputs"""
    
    def build_learning_signals(self) -> List[LearningSignal]:
        """Build learning signals from Phase 16, 19, 24"""
        signals = []
        
        # Phase 24 learning signals
        phase24_signals = self.read_jsonl_stream(24, "learning_signals.jsonl")
        for signal_data in phase24_signals:
            signals.append(LearningSignal(
                signal_id=f"phase24_{len(signals)}",
                signal_type=signal_data.get("signal_type", "UNKNOWN"),
                source_phase=24,
                tool_name=signal_data.get("tool_name"),
                insight=signal_data.get("insight", ""),
                recommended_action=signal_data.get("recommended_action", ""),
                confidence=signal_data.get("confidence", 0.5),
                timestamp=signal_data.get("timestamp", datetime.now(timezone.utc).isoformat())
            ))
        
        # Phase 16 signals (if available)
        phase16_output = self.read_phase_output(16, "learning_metrics.json")
        if phase16_output:
            for tool, metrics in phase16_output.items():
                signals.append(LearningSignal(
                    signal_id=f"phase16_{len(signals)}",
                    signal_type="TOOL_PERFORMANCE",
                    source_phase=16,
                    tool_name=tool,
                    insight=f"Tool {tool} performance metrics updated",
                    recommended_action="Review performance trends",
                    confidence=0.85,
                    timestamp=datetime.now(timezone.utc).isoformat()
                ))
        
        return sorted(signals, key=lambda s: s.timestamp, reverse=True)
    
    def build_confidence_trajectory(self) -> ConfidenceTrajectory:
        """Build confidence trajectory from Phase 2 metrics"""
        trajectory = ConfidenceTrajectory()
        
        # Read Phase 2 confidence history
        phase2_metrics = self.read_jsonl_stream(2, "confidence_metrics.jsonl")
        
        for metric_data in phase2_metrics[-100:]:  # Last 100 points
            trajectory.metric_points.append(MetricPoint(
                timestamp=metric_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                value=metric_data.get("confidence", 0.5),
                unit="confidence_score",
                source_phase=2
            ))
        
        # Calculate statistics
        if trajectory.metric_points:
            values = [p.value for p in trajectory.metric_points]
            trajectory.current_confidence = values[-1]
            trajectory.average_confidence = sum(values) / len(values)
            
            # Determine trend
            if len(values) > 1:
                recent_avg = sum(values[-10:]) / min(10, len(values))
                older_avg = sum(values[:10]) / min(10, len(values))
                if recent_avg > older_avg * 1.05:
                    trajectory.confidence_trend = "increasing"
                elif recent_avg < older_avg * 0.95:
                    trajectory.confidence_trend = "decreasing"
        
        return trajectory
    
    def build_tool_metrics(self) -> Dict[str, Dict[str, float]]:
        """Build tool performance metrics from Phase 24"""
        metrics = {}
        
        orchestration_output = self.read_phase_output(24, "orchestration_summary.json")
        if orchestration_output:
            # Extract tool metrics from orchestration
            for result in orchestration_output.get("orchestration_results", []):
                for tool_result in result.get("tool_results", []):
                    tool_name = tool_result.get("tool_name", "unknown")
                    metrics[tool_name] = {
                        "execution_time_ms": tool_result.get("result", {}).get("duration_ms", 0),
                        "confidence_score": tool_result.get("result", {}).get("confidence", 0.5),
                        "success": tool_result.get("status") == "executed"
                    }
        
        return metrics
    
    def build_failure_to_insight_chains(self) -> List[Dict[str, Any]]:
        """Build failure → insight → improvement chains"""
        chains = []
        
        # Read Phase 19 optimization outputs
        phase19_output = self.read_phase_output(19, "optimization_report.json")
        if phase19_output:
            for optimization in phase19_output.get("optimizations", []):
                chains.append({
                    "failure_pattern": optimization.get("issue", ""),
                    "insight_gained": optimization.get("analysis", ""),
                    "improvement_action": optimization.get("recommendation", ""),
                    "timestamp": optimization.get("timestamp", datetime.now(timezone.utc).isoformat())
                })
        
        return chains
    
    def build_state(self) -> LearningDashboardState:
        """Build complete learning dashboard state"""
        state = LearningDashboardState(
            dashboard_id=f"learning_{datetime.now(timezone.utc).isoformat()}",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Build components
        signals = self.build_learning_signals()
        state.recent_signals = signals[:20]  # Last 20
        
        # Group by phase and type
        for signal in signals:
            if signal.source_phase not in state.signals_by_phase:
                state.signals_by_phase[signal.source_phase] = []
            state.signals_by_phase[signal.source_phase].append(signal)
            
            if signal.signal_type not in state.signals_by_type:
                state.signals_by_type[signal.signal_type] = []
            state.signals_by_type[signal.signal_type].append(signal)
        
        state.confidence_trajectory = self.build_confidence_trajectory()
        state.tool_metrics = self.build_tool_metrics()
        state.strategy_updates = []  # From Phase 19
        state.failure_to_insight_chains = self.build_failure_to_insight_chains()
        
        # Build summary
        state.learning_summary = f"Processed {len(signals)} learning signals. Confidence trend: {state.confidence_trajectory.confidence_trend}"
        
        return state


class OperationsDashboardAdapter(PhaseOutputAdapter):
    """Adapter for Operations Dashboard - maps Phase 13, 18, 19, 24 outputs"""
    
    def build_active_agents(self) -> List[ActiveAgent]:
        """Build active agent list from Phase 18"""
        agents = []
        
        # Read Phase 18 agent status
        phase18_output = self.read_phase_output(18, "agent_status.json")
        if phase18_output:
            for agent_data in phase18_output.get("agents", []):
                agents.append(ActiveAgent(
                    agent_id=agent_data.get("id", "unknown"),
                    role=agent_data.get("role", "executor"),
                    status=agent_data.get("status", "idle"),
                    current_task=agent_data.get("current_task"),
                    tasks_completed=agent_data.get("tasks_completed", 0),
                    success_rate=agent_data.get("success_rate", 0.5),
                    last_activity=agent_data.get("last_activity", datetime.now(timezone.utc).isoformat())
                ))
        
        return agents
    
    def build_tool_executions(self) -> tuple[List[ToolExecution], List[ToolExecution]]:
        """Build active and recent tool executions from Phase 24"""
        active = []
        recent = []
        
        # Read Phase 24 execution log
        executions = self.read_jsonl_stream(24, "tool_execution_log.jsonl")
        
        for exec_data in executions[-50:]:  # Last 50
            tool_exec = ToolExecution(
                execution_id=exec_data.get("execution_id", f"exec_{len(recent)}"),
                tool_name=exec_data.get("tool_name", "unknown"),
                agent_id=exec_data.get("agent_id", "unknown"),
                environment=ExecutionEnvironment[exec_data.get("environment", "MOCK")],
                status=exec_data.get("status", "completed"),
                confidence_score=exec_data.get("confidence", 0.5),
                start_time=exec_data.get("start_time", datetime.now(timezone.utc).isoformat()),
                end_time=exec_data.get("end_time"),
                duration_ms=exec_data.get("duration_ms")
            )
            recent.append(tool_exec)
            if tool_exec.status == "executing":
                active.append(tool_exec)
        
        return active, recent
    
    def build_safety_decisions(self) -> tuple[List[SafetyDecision], List[SafetyDecision]]:
        """Build safety decisions from Phase 13"""
        recent = []
        
        # Read Phase 13 safety events
        safety_events = self.read_jsonl_stream(13, "safety_decisions.jsonl")
        
        for event_data in safety_events[-20:]:  # Last 20
            safety_dec = SafetyDecision(
                decision_id=event_data.get("id", f"decision_{len(recent)}"),
                timestamp=event_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                tool_name=event_data.get("tool_name", "unknown"),
                risk_level=event_data.get("risk_level", "LOW"),
                decision=event_data.get("decision", "APPROVED"),
                reasoning=event_data.get("reasoning", ""),
                approver_phase=13
            )
            recent.append(safety_dec)
        
        return recent[-10:], recent  # Last 10 active, all recent
    
    def build_system_health(self) -> SystemHealthMetrics:
        """Build system health from Phase 24"""
        health_output = self.read_phase_output(24, "system_health.json")
        
        if health_output:
            return SystemHealthMetrics(
                health_score=health_output.get("health_score", 75),
                health_status=health_output.get("health_assessment", "GOOD"),
                timestamp=health_output.get("timestamp", datetime.now(timezone.utc).isoformat()),
                metrics=health_output.get("metrics", {}),
                anomalies=health_output.get("anomalies", [])
            )
        
        return SystemHealthMetrics(
            health_score=75,
            health_status="GOOD",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def build_state(self, environment: ExecutionEnvironment = ExecutionEnvironment.MOCK) -> OperationsDashboardState:
        """Build complete operations dashboard state"""
        state = OperationsDashboardState(
            dashboard_id=f"operations_{datetime.now(timezone.utc).isoformat()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            current_environment=environment
        )
        
        # Build components
        state.active_agents = self.build_active_agents()
        active_execs, recent_execs = self.build_tool_executions()
        state.active_executions = active_execs
        state.recent_executions = recent_execs[:10]
        
        recent_safety, all_safety = self.build_safety_decisions()
        state.recent_safety_events = recent_safety
        state.safety_decisions = all_safety
        
        state.system_health = self.build_system_health()
        state.environment = environment
        
        # Build execution summary
        state.execution_summary = {
            "total_executions": len(recent_execs),
            "active_executions": len(active_execs),
            "success_rate": sum(1 for e in recent_execs if e.status == "succeeded") / max(1, len(recent_execs)),
            "environment": environment.value
        }
        
        return state


class InteractionDashboardAdapter(PhaseOutputAdapter):
    """Adapter for Interaction Dashboard - maps Phase 2, 13, 15 outputs"""
    
    def build_pending_approvals(self) -> List[ApprovalPrompt]:
        """Build pending approval prompts from Phase 13"""
        approvals = []
        
        # Read Phase 13 pending approvals
        pending = self.read_phase_output(13, "pending_approvals.json")
        if pending:
            for approval_data in pending.get("approvals", []):
                approvals.append(ApprovalPrompt(
                    prompt_id=approval_data.get("id", f"approval_{len(approvals)}"),
                    timestamp=approval_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    tool_name=approval_data.get("tool_name", "unknown"),
                    risk_level=approval_data.get("risk_level", "MEDIUM"),
                    context=approval_data.get("context", ""),
                    recommended_action=approval_data.get("recommended_action", ""),
                    requires_confirmation=approval_data.get("requires_confirmation", True)
                ))
        
        return approvals
    
    def build_pending_clarifications(self) -> List[str]:
        """Build pending clarifications from Phase 2"""
        clarifications = []
        
        # Read Phase 2 clarification requests
        phase2_output = self.read_phase_output(2, "clarification_requests.json")
        if phase2_output:
            clarifications = phase2_output.get("pending_clarifications", [])
        
        return clarifications
    
    def build_state(self) -> InteractionDashboardState:
        """Build complete interaction dashboard state"""
        state = InteractionDashboardState(
            dashboard_id=f"interaction_{datetime.now(timezone.utc).isoformat()}",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Build components
        state.pending_approvals = self.build_pending_approvals()
        state.pending_clarifications = self.build_pending_clarifications()
        
        # Build task list (placeholder)
        state.task_requests = []
        state.active_tasks = []
        state.completed_tasks = []
        
        # Last action explanation
        state.last_action_explanation = "Awaiting interaction..."
        
        # Recent feedback (from Phase 15)
        phase15_output = self.read_phase_output(15, "execution_feedback.json")
        if phase15_output:
            state.recent_feedback = phase15_output.get("feedback", [])
        
        return state


class DeveloperModeAdapter(PhaseOutputAdapter):
    """Adapter for Developer/Audit Mode"""
    
    def build_phase_tabs(self) -> Dict[int, Dict[str, Any]]:
        """Build phase data for tabs 1-24"""
        tabs = {}
        
        for phase_num in range(1, 25):
            phase_data = self.read_phase_output(phase_num, "summary.json")
            if phase_data:
                tabs[phase_num] = phase_data
        
        return tabs
    
    def build_audit_timeline(self) -> List[Dict[str, Any]]:
        """Build audit timeline from all phase outputs"""
        timeline = []
        
        for phase_num in range(1, 25):
            phase_dir = self.outputs_base / f"phase{phase_num}"
            if phase_dir.exists():
                # Find most recent output file
                files = list(phase_dir.glob("*.json"))
                if files:
                    latest = max(files, key=lambda f: f.stat().st_mtime)
                    timeline.append({
                        "phase": phase_num,
                        "timestamp": datetime.fromtimestamp(latest.stat().st_mtime).isoformat(),
                        "output_file": latest.name
                    })
        
        return sorted(timeline, key=lambda t: t["timestamp"])
