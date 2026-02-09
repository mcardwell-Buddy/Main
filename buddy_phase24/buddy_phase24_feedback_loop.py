"""
Phase 24: Feedback Loop - Learn from tool outcomes and generate signals

Tracks success/failure per tool, updates metrics, and emits learning signals
to Phase 16 (reward modeling) and Phase 19 (meta-learning).
"""

import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum


class SignalType(Enum):
    """Types of learning signals"""
    TOOL_RELIABILITY = "TOOL_RELIABILITY"
    TOOL_PERFORMANCE = "TOOL_PERFORMANCE"
    EXECUTION_MODE_ANALYSIS = "EXECUTION_MODE_ANALYSIS"
    CONFLICT_PATTERN = "CONFLICT_PATTERN"
    APPROVAL_MISMATCH = "APPROVAL_MISMATCH"


@dataclass
class ToolOutcome:
    """Outcome of a single tool execution"""
    tool_name: str
    agent_id: str
    execution_mode: str
    success: bool
    confidence_predicted: float
    execution_time_seconds: float
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class LearningSignal:
    """Signal emitted for learning systems"""
    signal_type: SignalType
    tool_name: str
    insight: str
    recommended_action: str
    confidence: float  # 0.0-1.0
    target_phase: int  # 16, 19, etc.
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FeedbackLoop:
    """
    Learn from tool outcomes and emit learning signals
    
    Tracks:
    - Tool success/failure rates
    - Execution mode appropriateness
    - Confidence calibration
    - Conflict patterns
    """
    
    def __init__(self):
        self.tool_outcomes: List[ToolOutcome] = []
        self.learning_signals: List[LearningSignal] = []
        self.tool_metrics: Dict[str, Dict] = {}  # tool_name -> metrics
        self.execution_mode_analysis: Dict[str, Dict] = {}
    
    def record_outcome(self, outcome: ToolOutcome):
        """Record a tool execution outcome"""
        self.tool_outcomes.append(outcome)
        self._update_tool_metrics(outcome)
    
    def _update_tool_metrics(self, outcome: ToolOutcome):
        """Update metrics for a tool"""
        if outcome.tool_name not in self.tool_metrics:
            self.tool_metrics[outcome.tool_name] = {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "total_execution_time": 0.0,
                "by_mode": {}
            }
        
        metrics = self.tool_metrics[outcome.tool_name]
        metrics["total_executions"] += 1
        
        if outcome.success:
            metrics["successful"] += 1
        else:
            metrics["failed"] += 1
        
        metrics["success_rate"] = metrics["successful"] / metrics["total_executions"]
        metrics["total_execution_time"] += outcome.execution_time_seconds
        metrics["avg_execution_time"] = metrics["total_execution_time"] / metrics["total_executions"]
        
        # Track by execution mode
        if outcome.execution_mode not in metrics["by_mode"]:
            metrics["by_mode"][outcome.execution_mode] = {
                "count": 0,
                "success_count": 0,
                "success_rate": 0.0
            }
        
        mode_metrics = metrics["by_mode"][outcome.execution_mode]
        mode_metrics["count"] += 1
        if outcome.success:
            mode_metrics["success_count"] += 1
        mode_metrics["success_rate"] = mode_metrics["success_count"] / mode_metrics["count"]
    
    def analyze_tool_reliability(self) -> List[LearningSignal]:
        """
        Analyze tool reliability and emit signals
        
        Returns: List of learning signals
        """
        signals = []
        
        for tool_name, metrics in self.tool_metrics.items():
            success_rate = metrics.get("success_rate", 0.0)
            
            # HIGH reliability (90%+) - can escalate to live
            if success_rate >= 0.9:
                signals.append(LearningSignal(
                    signal_type=SignalType.TOOL_RELIABILITY,
                    tool_name=tool_name,
                    insight=f"Tool has high reliability ({success_rate:.1%})",
                    recommended_action="Consider escalating to LIVE execution mode",
                    confidence=success_rate,
                    target_phase=19
                ))
            
            # LOW reliability (<70%) - needs investigation
            elif success_rate < 0.7:
                signals.append(LearningSignal(
                    signal_type=SignalType.TOOL_RELIABILITY,
                    tool_name=tool_name,
                    insight=f"Tool has low reliability ({success_rate:.1%})",
                    recommended_action="Investigate failures and consider reverting to DRY_RUN",
                    confidence=1.0 - success_rate,
                    target_phase=16
                ))
        
        self.learning_signals.extend(signals)
        return signals
    
    def analyze_execution_modes(self) -> List[LearningSignal]:
        """
        Analyze appropriateness of execution modes
        
        Returns: List of learning signals
        """
        signals = []
        
        for tool_name, metrics in self.tool_metrics.items():
            by_mode = metrics.get("by_mode", {})
            
            # Check if tool succeeds better in one mode
            mode_success_rates = {
                mode: mode_metrics["success_rate"]
                for mode, mode_metrics in by_mode.items()
            }
            
            if mode_success_rates:
                best_mode = max(mode_success_rates, key=mode_success_rates.get)
                best_rate = mode_success_rates[best_mode]
                
                # All other modes perform significantly worse
                worse_modes = [m for m in mode_success_rates if m != best_mode and 
                              mode_success_rates[m] < best_rate - 0.15]
                
                if worse_modes and best_rate > 0.8:
                    signals.append(LearningSignal(
                        signal_type=SignalType.EXECUTION_MODE_ANALYSIS,
                        tool_name=tool_name,
                        insight=f"Tool performs best in {best_mode} mode ({best_rate:.1%})",
                        recommended_action=f"Prefer {best_mode} mode, avoid {', '.join(worse_modes)}",
                        confidence=best_rate,
                        target_phase=19
                    ))
        
        self.learning_signals.extend(signals)
        return signals
    
    def detect_conflict_patterns(self, conflict_history: List[Dict]) -> List[LearningSignal]:
        """
        Detect patterns in conflicts
        
        Returns: List of learning signals
        """
        signals = []
        
        if not conflict_history:
            return signals
        
        # Count conflict types
        conflict_types = {}
        for conflict in conflict_history:
            ctype = conflict.get("conflict_type", "UNKNOWN")
            conflict_types[ctype] = conflict_types.get(ctype, 0) + 1
        
        # Identify recurring patterns
        for ctype, count in conflict_types.items():
            if count >= 3:  # Recurring pattern
                signals.append(LearningSignal(
                    signal_type=SignalType.CONFLICT_PATTERN,
                    tool_name="*",
                    insight=f"Recurring conflict pattern: {ctype} ({count} occurrences)",
                    recommended_action=f"Review tool dependencies and agent allocation for {ctype}",
                    confidence=min(count / 10.0, 1.0),  # Max 1.0
                    target_phase=16
                ))
        
        self.learning_signals.extend(signals)
        return signals
    
    def analyze_confidence_calibration(self) -> List[LearningSignal]:
        """
        Analyze if predicted confidence matches actual outcomes
        
        Returns: List of learning signals
        """
        signals = []
        
        if not self.tool_outcomes:
            return signals
        
        # Group by confidence buckets
        confidence_buckets = {
            "high": {"total": 0, "success": 0},
            "medium": {"total": 0, "success": 0},
            "low": {"total": 0, "success": 0}
        }
        
        for outcome in self.tool_outcomes:
            conf = outcome.confidence_predicted
            if conf >= 0.7:
                bucket = "high"
            elif conf >= 0.4:
                bucket = "medium"
            else:
                bucket = "low"
            
            confidence_buckets[bucket]["total"] += 1
            if outcome.success:
                confidence_buckets[bucket]["success"] += 1
        
        # Check calibration
        for bucket, data in confidence_buckets.items():
            if data["total"] == 0:
                continue
            
            actual_rate = data["success"] / data["total"]
            
            # Expected rates: high=80%+, medium=60%+, low=40%+
            expected_rates = {"high": 0.8, "medium": 0.6, "low": 0.4}
            expected = expected_rates[bucket]
            
            if actual_rate < expected - 0.15:
                signals.append(LearningSignal(
                    signal_type=SignalType.APPROVAL_MISMATCH,
                    tool_name="*",
                    insight=f"Confidence miscalibration in {bucket} confidence bucket: {actual_rate:.1%} (expected {expected:.1%})",
                    recommended_action="Retrain confidence model or adjust thresholds",
                    confidence=0.8,
                    target_phase=16
                ))
        
        self.learning_signals.extend(signals)
        return signals
    
    def get_tool_metrics(self, tool_name: str) -> Optional[Dict]:
        """Get metrics for specific tool"""
        return self.tool_metrics.get(tool_name)
    
    def get_all_metrics(self) -> Dict:
        """Get all tool metrics"""
        return self.tool_metrics
    
    def get_signals_for_phase(self, phase: int) -> List[Dict]:
        """Get all signals targeted at specific phase"""
        signals = [asdict(s) for s in self.learning_signals if s.target_phase == phase]
        return signals
    
    def export_signals(self) -> List[Dict]:
        """Export all learning signals"""
        return [asdict(s) for s in self.learning_signals]
