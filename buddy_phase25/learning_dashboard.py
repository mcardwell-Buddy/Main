"""
Phase 25: Learning Dashboard

Visualizes how Buddy is learning, adapting, and improving over time.
Displays confidence trajectories, learning signals, tool performance trends,
and failure-to-insight chains.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from .dashboard_state_models import (
    LearningDashboardState, LearningSignal, ConfidenceTrajectory,
    MetricPoint
)
from .dashboard_adapters.phase_adapters import LearningDashboardAdapter
from .phase24_adapters import Phase24AggregateAdapter


class LearningDashboard:
    """
    Learning Dashboard displays:
    1. Confidence trajectory with trend analysis
    2. Learning signals from Phase 16/19/24
    3. Tool performance metrics and trends
    4. Strategy/heuristic evolution
    5. Failure → insight → improvement chains
    """
    
    def __init__(self):
        self.adapter = LearningDashboardAdapter()
        self.phase24_adapter = Phase24AggregateAdapter()
        self.current_state: Optional[LearningDashboardState] = None
    
    def load(self) -> LearningDashboardState:
        """Load learning dashboard state"""
        self.current_state = self.adapter.build_state()
        return self.current_state
    
    def get_learning_summary(self) -> str:
        """Get human-readable learning summary"""
        if not self.current_state:
            return "No learning data available"
        
        summary_parts = []
        
        # Confidence trajectory
        conf = self.current_state.confidence_trajectory
        summary_parts.append(
            f"📈 Confidence: {conf.current_confidence:.2%} "
            f"(avg: {conf.average_confidence:.2%}, trend: {conf.confidence_trend})"
        )
        
        # Recent signals
        signal_counts = {}
        for signal in self.current_state.recent_signals[:10]:
            signal_type = signal.signal_type
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
        
        if signal_counts:
            signal_str = ", ".join([f"{k}:{v}" for k, v in signal_counts.items()])
            summary_parts.append(f"📊 Recent Signals: {signal_str}")
        
        # Tool metrics
        if self.current_state.tool_metrics:
            top_tools = sorted(
                self.current_state.tool_metrics.items(),
                key=lambda x: x[1].get("confidence_score", 0),
                reverse=True
            )[:3]
            tools_str = ", ".join([f"{t[0]}({t[1].get('confidence_score', 0):.1%})" for t in top_tools])
            summary_parts.append(f"🛠️ Top Tools: {tools_str}")
        
        # Improvement chains
        if self.current_state.failure_to_insight_chains:
            summary_parts.append(
                f"🔄 Improvement Chains: {len(self.current_state.failure_to_insight_chains)} identified"
            )
        
        return " | ".join(summary_parts)
    
    def get_confidence_visualization(self, width: int = 60, height: int = 10) -> str:
        """Generate ASCII visualization of confidence trajectory"""
        if not self.current_state or not self.current_state.confidence_trajectory.metric_points:
            return "No confidence data"
        
        points = self.current_state.confidence_trajectory.metric_points
        if not points:
            return "No confidence data"
        
        # Scale values 0-100 to height
        values = [p.value * 100 for p in points[-width:]]  # Last width points
        
        if not values:
            return "No confidence data"
        
        max_val = max(values) if values else 100
        min_val = min(values) if values else 0
        range_val = max_val - min_val if max_val > min_val else 1
        
        # Create visualization
        lines = []
        for row in range(height, 0, -1):
            line = ""
            threshold = (row / height) * range_val + min_val
            for val in values:
                if val >= threshold:
                    line += "█"
                else:
                    line += " "
            lines.append(f"{row*10:3d}% | {line}")
        
        lines.append("    +" + "─" * len(values))
        lines.append(f"Current: {self.current_state.confidence_trajectory.current_confidence:.1%}")
        
        return "\n".join(lines)
    
    def get_learning_signals_table(self, limit: int = 20) -> str:
        """Generate table of recent learning signals"""
        if not self.current_state or not self.current_state.recent_signals:
            return "No learning signals"
        
        lines = ["Phase | Signal Type | Tool | Confidence | Insight"]
        lines.append("─" * 80)
        
        for signal in self.current_state.recent_signals[:limit]:
            tool_name = signal.tool_name or "system"
            insight_trunc = (signal.insight[:40] + "...") if len(signal.insight) > 40 else signal.insight
            
            lines.append(
                f"{signal.source_phase:>2d}    | "
                f"{signal.signal_type:<15s} | "
                f"{tool_name:<10s} | "
                f"{signal.confidence:>7.0%}    | "
                f"{insight_trunc}"
            )
        
        return "\n".join(lines)
    
    def get_tool_performance_table(self) -> str:
        """Generate table of tool performance metrics"""
        if not self.current_state or not self.current_state.tool_metrics:
            return "No tool metrics available"
        
        lines = ["Tool | Execution Time (ms) | Confidence | Success"]
        lines.append("─" * 50)
        
        for tool_name, metrics in sorted(self.current_state.tool_metrics.items())[:20]:
            lines.append(
                f"{tool_name:<15s} | "
                f"{metrics.get('execution_time_ms', 0):>6.1f}         | "
                f"{metrics.get('confidence_score', 0):>7.0%}    | "
                f"{'✓' if metrics.get('success') else '✗'}"
            )
        
        return "\n".join(lines)
    
    def get_improvement_chains(self) -> str:
        """Display failure → insight → improvement chains"""
        if not self.current_state or not self.current_state.failure_to_insight_chains:
            return "No improvement chains identified yet"
        
        lines = []
        for i, chain in enumerate(self.current_state.failure_to_insight_chains[:10], 1):
            lines.append(f"\n🔗 Chain #{i}:")
            lines.append(f"  ❌ Failure: {chain.get('failure_pattern', 'unknown')[:60]}")
            lines.append(f"  💡 Insight: {chain.get('insight_gained', 'unknown')[:60]}")
            lines.append(f"  ✅ Action:  {chain.get('improvement_action', 'pending')[:60]}")
        
        return "\n".join(lines)
    
    def export_state(self, filepath: str):
        """Export dashboard state to JSON"""
        if self.current_state:
            import json
            with open(filepath, 'w') as f:
                json.dump(asdict(self.current_state), f, indent=2, default=str)


@dataclass
class LearningDashboardWidget:
    """Individual widget in learning dashboard"""
    widget_id: str
    widget_type: str  # "chart", "table", "text", "metric"
    title: str
    data: Dict[str, Any]
    refresh_interval_seconds: int = 30


class LearningDashboardBuilder:
    """Builder for learning dashboard with custom widgets"""
    
    def __init__(self):
        self.dashboard = LearningDashboard()
        self.widgets: List[LearningDashboardWidget] = []
    
    def build_default_widgets(self) -> List[LearningDashboardWidget]:
        """Build default set of widgets"""
        state = self.dashboard.load()
        
        widgets = []
        
        # Confidence metric
        widgets.append(LearningDashboardWidget(
            widget_id="confidence_metric",
            widget_type="metric",
            title="Current Confidence",
            data={
                "value": f"{state.confidence_trajectory.current_confidence:.1%}",
                "trend": state.confidence_trajectory.confidence_trend,
                "average": f"{state.confidence_trajectory.average_confidence:.1%}"
            }
        ))
        
        # Signal count
        widgets.append(LearningDashboardWidget(
            widget_id="signal_count",
            widget_type="metric",
            title="Recent Learning Signals",
            data={
                "total": len(state.recent_signals),
                "by_phase": {str(p): len(s) for p, s in state.signals_by_phase.items()}
            }
        ))
        
        # Tool performance
        widgets.append(LearningDashboardWidget(
            widget_id="tool_performance",
            widget_type="table",
            title="Top Performing Tools",
            data={
                "tools": state.tool_metrics
            }
        ))
        
        # Learning signals
        widgets.append(LearningDashboardWidget(
            widget_id="recent_signals",
            widget_type="table",
            title="Recent Learning Signals",
            data={
                "signals": [asdict(s) for s in state.recent_signals[:20]]
            }
        ))
        
        # Phase 24: Learning Signals (High Confidence)
        high_conf_signals = self.phase24_adapter.learning_signals.get_high_confidence_signals(threshold=0.85)
        if high_conf_signals:
            widgets.append(LearningDashboardWidget(
                widget_id="phase24_high_confidence_signals",
                widget_type="table",
                title="Phase 24 High-Confidence Learning Signals (>0.85)",
                data={
                    "signals": [
                        {
                            "tool": s.tool_name,
                            "type": s.signal_type,
                            "insight": s.insight,
                            "confidence": f"{s.confidence:.2f}",
                            "action": s.recommended_action
                        }
                        for s in high_conf_signals[:10]
                    ]
                }
            ))
        
        # Phase 24: Tool Performance Trends
        tool_stats = self.phase24_adapter.execution_log.get_tool_statistics()
        if tool_stats:
            widgets.append(LearningDashboardWidget(
                widget_id="phase24_tool_trends",
                widget_type="table",
                title="Phase 24 Tool Performance Trends",
                data={
                    "tools": [
                        {
                            "tool": name,
                            "total_calls": stats["total_calls"],
                            "success_rate": f"{(stats['successful'] / max(stats['total_calls'], 1) * 100):.1f}%",
                            "avg_confidence": f"{stats['avg_confidence']:.2f}",
                            "avg_time_ms": f"{stats['avg_duration_ms']:.1f}"
                        }
                        for name, stats in sorted(
                            tool_stats.items(),
                            key=lambda x: x[1]["avg_confidence"],
                            reverse=True
                        )[:15]
                    ]
                }
            ))
        
        # Improvement chains
        widgets.append(LearningDashboardWidget(
            widget_id="improvement_chains",
            widget_type="text",
            title="Failure → Insight → Improvement Chains",
            data={
                "chains": state.failure_to_insight_chains
            }
        ))
        
        self.widgets = widgets
        return widgets
