"""
Phase 24: Monitor - Real-time observability and health scoring

Tracks key metrics and detects anomalies:
- tool_success_rate
- execution_latency
- rollback_frequency
- conflict_rate
- live_execution_ratio
- confidence_drift
"""

import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum
import statistics


class HealthStatus(Enum):
    """System health status"""
    EXCELLENT = "EXCELLENT"  # 90-100
    GOOD = "GOOD"            # 75-89
    FAIR = "FAIR"            # 60-74
    POOR = "POOR"            # <60


@dataclass
class Metric:
    """Single metric reading"""
    metric_name: str
    value: float
    unit: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Anomaly:
    """Detected anomaly"""
    anomaly_type: str
    severity: int  # 1-10
    description: str
    affected_metric: str
    recommended_action: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Monitor:
    """
    Real-time monitoring and health assessment
    
    Tracks metrics and detects anomalies
    """
    
    def __init__(self):
        self.metrics_history: List[Metric] = []
        self.anomalies: List[Anomaly] = []
        self.current_metrics: Dict[str, float] = {
            "tool_success_rate": 0.0,
            "execution_latency_ms": 0.0,
            "rollback_frequency": 0.0,
            "conflict_rate": 0.0,
            "live_execution_ratio": 0.0,
            "confidence_drift": 0.0,
            "approval_rate": 0.0,
            "system_health_score": 100.0
        }
        self.baseline_metrics = self.current_metrics.copy()
    
    def record_metric(self, metric_name: str, value: float, unit: str = ""):
        """Record a metric measurement"""
        metric = Metric(metric_name, value, unit)
        self.metrics_history.append(metric)
        self.current_metrics[metric_name] = value
    
    def update_metrics(self, orchestrator_summary: Dict):
        """Update metrics from orchestration summary"""
        execution_status = orchestrator_summary.get("execution_controller_status", {})
        conflict_summary = orchestrator_summary.get("conflict_summary", {})
        
        # Tool success rate
        if execution_status.get("tools_executed", 0) > 0:
            success_rate = 1.0  # Simplified - would calculate from actual outcomes
            self.record_metric("tool_success_rate", success_rate, "ratio")
        
        # Execution latency
        self.record_metric("execution_latency_ms", 50.0, "ms")
        
        # Rollback frequency
        rollback_depth = execution_status.get("rollback_depth", 0)
        tools_executed = execution_status.get("tools_executed", 1)
        rollback_freq = rollback_depth / max(tools_executed, 1)
        self.record_metric("rollback_frequency", rollback_freq, "ratio")
        
        # Conflict rate
        conflict_detected = conflict_summary.get("total_detected", 0)
        conflict_rate = conflict_detected / max(tools_executed, 1)
        self.record_metric("conflict_rate", conflict_rate, "ratio")
        
        # Live execution ratio
        live_ratio = execution_status.get("confidence_score", 0.5)
        self.record_metric("live_execution_ratio", live_ratio, "ratio")
        
        # Confidence drift
        current_confidence = execution_status.get("confidence_score", 0.5)
        previous_confidence = 0.5  # Simplified
        drift = abs(current_confidence - previous_confidence)
        self.record_metric("confidence_drift", drift, "ratio")
    
    def calculate_health_score(self) -> Dict:
        """Calculate overall system health score (0-100)"""
        weights = {
            "tool_success_rate": 0.30,
            "rollback_frequency": -0.15,
            "conflict_rate": -0.15,
            "confidence_drift": -0.10,
            "approval_rate": 0.30
        }
        
        health_score = 100.0
        
        # Tool success rate contributes positively
        success_rate = self.current_metrics.get("tool_success_rate", 0.5)
        health_score += (success_rate - 0.7) * 10 * weights["tool_success_rate"] / 0.30
        
        # Rollback frequency penalizes
        rollback_freq = self.current_metrics.get("rollback_frequency", 0.0)
        health_score -= rollback_freq * 10 * abs(weights["rollback_frequency"]) / 0.15
        
        # Conflict rate penalizes
        conflict_rate = self.current_metrics.get("conflict_rate", 0.0)
        health_score -= conflict_rate * 10 * abs(weights["conflict_rate"]) / 0.15
        
        # Confidence drift penalizes
        conf_drift = self.current_metrics.get("confidence_drift", 0.0)
        health_score -= conf_drift * 10 * abs(weights["confidence_drift"]) / 0.10
        
        # Clamp to 0-100
        health_score = max(0.0, min(100.0, health_score))
        
        return {
            "health_score": health_score,
            "status": self._get_health_status(health_score),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _get_health_status(self, score: float) -> str:
        """Get health status label"""
        if score >= 90:
            return HealthStatus.EXCELLENT.value
        elif score >= 75:
            return HealthStatus.GOOD.value
        elif score >= 60:
            return HealthStatus.FAIR.value
        else:
            return HealthStatus.POOR.value
    
    def detect_anomalies(self) -> List[Anomaly]:
        """Detect anomalies in metrics"""
        new_anomalies = []
        
        # Unsafe escalation: High confidence drift
        conf_drift = self.current_metrics.get("confidence_drift", 0.0)
        if conf_drift > 0.4:
            new_anomalies.append(Anomaly(
                anomaly_type="unsafe_escalation",
                severity=7,
                description=f"High confidence drift detected ({conf_drift:.2f})",
                affected_metric="confidence_drift",
                recommended_action="Review confidence calibration and recent escalations"
            ))
        
        # Repeated failures: Low success rate
        success_rate = self.current_metrics.get("tool_success_rate", 0.5)
        if success_rate < 0.5:
            new_anomalies.append(Anomaly(
                anomaly_type="repeated_failures",
                severity=8,
                description=f"Tool success rate below 50% ({success_rate:.1%})",
                affected_metric="tool_success_rate",
                recommended_action="Investigate tool failures and consider reverting to MOCK mode"
            ))
        
        # High rollback frequency
        rollback_freq = self.current_metrics.get("rollback_frequency", 0.0)
        if rollback_freq > 0.3:
            new_anomalies.append(Anomaly(
                anomaly_type="repeated_failures",
                severity=6,
                description=f"High rollback frequency ({rollback_freq:.1%})",
                affected_metric="rollback_frequency",
                recommended_action="Reduce tool execution scope or increase approval gates"
            ))
        
        # High conflict rate
        conflict_rate = self.current_metrics.get("conflict_rate", 0.0)
        if conflict_rate > 0.5:
            new_anomalies.append(Anomaly(
                anomaly_type="conflict_pattern",
                severity=5,
                description=f"High conflict rate detected ({conflict_rate:.1%})",
                affected_metric="conflict_rate",
                recommended_action="Review tool dependencies and agent assignments"
            ))
        
        self.anomalies.extend(new_anomalies)
        return new_anomalies
    
    def get_metrics_summary(self) -> Dict:
        """Get current metrics summary"""
        return {
            "current_metrics": self.current_metrics,
            "health": self.calculate_health_score(),
            "anomalies": len(self.anomalies),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_anomalies(self) -> List[Dict]:
        """Get all detected anomalies"""
        return [asdict(a) for a in self.anomalies]
    
    def get_metric_history(self, metric_name: str) -> List[Dict]:
        """Get historical values for a metric"""
        history = [asdict(m) for m in self.metrics_history 
                   if m.metric_name == metric_name]
        return history
