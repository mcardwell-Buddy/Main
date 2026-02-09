"""
Phase 4 Step 7: Confidence Timeline Builder

Builds confidence evolution timelines for key signal categories.

HARD CONSTRAINTS:
- NO execution changes
- NO autonomy
- READ-ONLY over signals
- Deterministic aggregation only
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict


@dataclass
class TimelinePoint:
    """A single point in a confidence timeline."""
    timestamp: str
    confidence: float
    delta: Optional[float] = None
    rolling_avg: Optional[float] = None


@dataclass
class ConfidenceTimeline:
    """A timeline of confidence values for a specific entity."""
    timeline_type: str  # selector|intent|opportunity|forecast
    entity_id: str
    points: List[TimelinePoint]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timeline_type": self.timeline_type,
            "entity_id": self.entity_id,
            "points": [
                {
                    "timestamp": p.timestamp,
                    "confidence": p.confidence,
                    "delta": p.delta,
                    "rolling_avg": p.rolling_avg
                }
                for p in self.points
            ]
        }


class ConfidenceTimelineBuilder:
    """
    Builds confidence timelines from learning signals.
    
    Supported timeline types:
    - selector: Tracks selector outcome confidence over time
    - intent: Tracks intent action confidence over time
    - opportunity: Tracks opportunity detection confidence over time
    - forecast: Tracks forecast reliability over time
    """
    
    def __init__(self, signals_file: str = "outputs/phase25/learning_signals.jsonl"):
        self.signals_file = signals_file
        self.signals = []
        
    def load_signals(self) -> None:
        """Load signals from JSONL file."""
        signals_path = Path(self.signals_file)
        if not signals_path.exists():
            print(f"Warning: Signals file not found: {self.signals_file}")
            return
        
        with open(signals_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        self.signals.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    
    def build_selector_timelines(self) -> List[ConfidenceTimeline]:
        """Build confidence timelines for selector outcomes."""
        # Group by selector + selector_type
        grouped = defaultdict(list)
        
        for signal in self.signals:
            if signal.get("signal_type") == "selector_outcome":
                selector = signal.get("selector", "")
                selector_type = signal.get("selector_type", "")
                entity_id = f"{selector}|{selector_type}"
                
                timestamp = signal.get("timestamp", "")
                confidence = signal.get("confidence", 0.0)
                
                grouped[entity_id].append({
                    "timestamp": timestamp,
                    "confidence": confidence
                })
        
        # Build timelines
        timelines = []
        for entity_id, points in grouped.items():
            # Sort by timestamp
            points = sorted(points, key=lambda p: p["timestamp"])
            
            # Compute deltas and rolling averages
            timeline_points = []
            for i, point in enumerate(points):
                delta = None
                if i > 0:
                    delta = point["confidence"] - points[i-1]["confidence"]
                
                # Rolling average (window of 3)
                rolling_avg = None
                if i >= 2:
                    rolling_avg = sum(p["confidence"] for p in points[i-2:i+1]) / 3
                
                timeline_points.append(TimelinePoint(
                    timestamp=point["timestamp"],
                    confidence=point["confidence"],
                    delta=delta,
                    rolling_avg=rolling_avg
                ))
            
            if timeline_points:
                timelines.append(ConfidenceTimeline(
                    timeline_type="selector",
                    entity_id=entity_id,
                    points=timeline_points
                ))
        
        return timelines
    
    def build_intent_timelines(self) -> List[ConfidenceTimeline]:
        """Build confidence timelines for intent actions."""
        # Group by goal
        grouped = defaultdict(list)
        
        for signal in self.signals:
            if signal.get("signal_type") in ["navigation_intent_ranked", "intent_action_taken"]:
                goal = signal.get("goal", "unknown")
                entity_id = goal
                
                timestamp = signal.get("timestamp", "")
                confidence = signal.get("confidence", 0.0)
                
                grouped[entity_id].append({
                    "timestamp": timestamp,
                    "confidence": confidence
                })
        
        # Build timelines
        timelines = []
        for entity_id, points in grouped.items():
            # Sort by timestamp
            points = sorted(points, key=lambda p: p["timestamp"])
            
            # Compute deltas and rolling averages
            timeline_points = []
            for i, point in enumerate(points):
                delta = None
                if i > 0:
                    delta = point["confidence"] - points[i-1]["confidence"]
                
                # Rolling average (window of 3)
                rolling_avg = None
                if i >= 2:
                    rolling_avg = sum(p["confidence"] for p in points[i-2:i+1]) / 3
                
                timeline_points.append(TimelinePoint(
                    timestamp=point["timestamp"],
                    confidence=point["confidence"],
                    delta=delta,
                    rolling_avg=rolling_avg
                ))
            
            if timeline_points:
                timelines.append(ConfidenceTimeline(
                    timeline_type="intent",
                    entity_id=entity_id,
                    points=timeline_points
                ))
        
        return timelines
    
    def build_opportunity_timelines(self) -> List[ConfidenceTimeline]:
        """Build confidence timelines for opportunity signals."""
        # Group by signal_id (or generic if not available)
        grouped = defaultdict(list)
        
        for signal in self.signals:
            signal_type = signal.get("signal_type", "")
            if "opportunity" in signal_type.lower() or signal_type in ["confidence_increase", "efficiency_gain"]:
                signal_id = signal.get("signal_id", "generic_opportunity")
                entity_id = signal_id
                
                timestamp = signal.get("timestamp", "")
                confidence = signal.get("confidence", 0.0)
                
                grouped[entity_id].append({
                    "timestamp": timestamp,
                    "confidence": confidence
                })
        
        # Build timelines
        timelines = []
        for entity_id, points in grouped.items():
            # Sort by timestamp
            points = sorted(points, key=lambda p: p["timestamp"])
            
            # Compute deltas and rolling averages
            timeline_points = []
            for i, point in enumerate(points):
                delta = None
                if i > 0:
                    delta = point["confidence"] - points[i-1]["confidence"]
                
                # Rolling average (window of 3)
                rolling_avg = None
                if i >= 2:
                    rolling_avg = sum(p["confidence"] for p in points[i-2:i+1]) / 3
                
                timeline_points.append(TimelinePoint(
                    timestamp=point["timestamp"],
                    confidence=point["confidence"],
                    delta=delta,
                    rolling_avg=rolling_avg
                ))
            
            if timeline_points:
                timelines.append(ConfidenceTimeline(
                    timeline_type="opportunity",
                    entity_id=entity_id,
                    points=timeline_points
                ))
        
        return timelines
    
    def build_forecast_timelines(self) -> List[ConfidenceTimeline]:
        """Build confidence timelines for forecast reliability."""
        # Group by domain
        grouped = defaultdict(list)
        
        for signal in self.signals:
            if signal.get("signal_type") == "forecast_reliability_update":
                domain = signal.get("domain", "unknown")
                entity_id = domain
                
                timestamp = signal.get("timestamp", "")
                # Use reliability_score as confidence proxy
                confidence = signal.get("reliability_score", 0.0)
                
                grouped[entity_id].append({
                    "timestamp": timestamp,
                    "confidence": confidence
                })
        
        # Build timelines
        timelines = []
        for entity_id, points in grouped.items():
            # Sort by timestamp
            points = sorted(points, key=lambda p: p["timestamp"])
            
            # Compute deltas and rolling averages
            timeline_points = []
            for i, point in enumerate(points):
                delta = None
                if i > 0:
                    delta = point["confidence"] - points[i-1]["confidence"]
                
                # Rolling average (window of 3)
                rolling_avg = None
                if i >= 2:
                    rolling_avg = sum(p["confidence"] for p in points[i-2:i+1]) / 3
                
                timeline_points.append(TimelinePoint(
                    timestamp=point["timestamp"],
                    confidence=point["confidence"],
                    delta=delta,
                    rolling_avg=rolling_avg
                ))
            
            if timeline_points:
                timelines.append(ConfidenceTimeline(
                    timeline_type="forecast",
                    entity_id=entity_id,
                    points=timeline_points
                ))
        
        return timelines
    
    def build_all_timelines(self) -> Dict[str, List[ConfidenceTimeline]]:
        """Build all timeline types."""
        self.load_signals()
        
        return {
            "selector": self.build_selector_timelines(),
            "intent": self.build_intent_timelines(),
            "opportunity": self.build_opportunity_timelines(),
            "forecast": self.build_forecast_timelines()
        }
    
    def render_sparkline(self, timeline: ConfidenceTimeline, width: int = 20) -> str:
        """
        Render a sparkline ASCII visualization of the timeline.
        
        Args:
            timeline: The confidence timeline to visualize
            width: Maximum width of sparkline
        
        Returns:
            ASCII sparkline string
        """
        if not timeline.points:
            return "No data"
        
        # Get confidence values
        values = [p.confidence for p in timeline.points]
        
        # Sample if too many points
        if len(values) > width:
            step = len(values) // width
            values = [values[i] for i in range(0, len(values), step)][:width]
        
        # Determine scale
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return "─" * len(values)
        
        # Map to sparkline characters
        # ▁ ▂ ▃ ▄ ▅ ▆ ▇ █
        chars = "▁▂▃▄▅▆▇█"
        
        sparkline = ""
        for val in values:
            normalized = (val - min_val) / (max_val - min_val)
            idx = int(normalized * (len(chars) - 1))
            sparkline += chars[idx]
        
        return sparkline
    
    def render_whiteboard_section(self, timelines: Dict[str, List[ConfidenceTimeline]]) -> str:
        """
        Render confidence timelines for whiteboard display.
        
        Args:
            timelines: Dictionary of timeline lists by type
        
        Returns:
            Formatted string for whiteboard
        """
        output = []
        output.append("┌" + "─" * 78 + "┐")
        output.append("│" + " " * 20 + "CONFIDENCE TIMELINES" + " " * 38 + "│")
        output.append("│" + " " * 78 + "│")
        output.append("│" + " [Read-Only • No Actions]" + " " * 52 + "│")
        output.append("├" + "─" * 78 + "┤")
        
        # Selector timelines
        selector_timelines = timelines.get("selector", [])
        if selector_timelines:
            output.append("│ SELECTOR CONFIDENCE:" + " " * 57 + "│")
            output.append("│" + " " * 78 + "│")
            
            # Show top 5 selectors by point count
            sorted_selectors = sorted(selector_timelines, key=lambda t: len(t.points), reverse=True)[:5]
            
            for timeline in sorted_selectors:
                entity_short = timeline.entity_id[:40] + "..." if len(timeline.entity_id) > 40 else timeline.entity_id
                sparkline = self.render_sparkline(timeline, width=20)
                
                latest = timeline.points[-1] if timeline.points else None
                if latest:
                    conf_str = f"{latest.confidence:.2f}"
                    delta_str = f"({latest.delta:+.2f})" if latest.delta is not None else ""
                    line = f"│   {entity_short:<45} {sparkline} {conf_str} {delta_str}"
                    line = line[:79] + "│"
                    output.append(line)
            
            output.append("│" + " " * 78 + "│")
        
        # Intent timelines
        intent_timelines = timelines.get("intent", [])
        if intent_timelines:
            output.append("│ INTENT CONFIDENCE:" + " " * 60 + "│")
            output.append("│" + " " * 78 + "│")
            
            for timeline in intent_timelines[:5]:
                entity_short = timeline.entity_id[:40] + "..." if len(timeline.entity_id) > 40 else timeline.entity_id
                sparkline = self.render_sparkline(timeline, width=20)
                
                latest = timeline.points[-1] if timeline.points else None
                if latest:
                    conf_str = f"{latest.confidence:.2f}"
                    delta_str = f"({latest.delta:+.2f})" if latest.delta is not None else ""
                    line = f"│   {entity_short:<45} {sparkline} {conf_str} {delta_str}"
                    line = line[:79] + "│"
                    output.append(line)
            
            output.append("│" + " " * 78 + "│")
        
        # Opportunity timelines
        opportunity_timelines = timelines.get("opportunity", [])
        if opportunity_timelines:
            output.append("│ OPPORTUNITY CONFIDENCE:" + " " * 55 + "│")
            output.append("│" + " " * 78 + "│")
            
            for timeline in opportunity_timelines[:5]:
                entity_short = timeline.entity_id[:40] + "..." if len(timeline.entity_id) > 40 else timeline.entity_id
                sparkline = self.render_sparkline(timeline, width=20)
                
                latest = timeline.points[-1] if timeline.points else None
                if latest:
                    conf_str = f"{latest.confidence:.2f}"
                    delta_str = f"({latest.delta:+.2f})" if latest.delta is not None else ""
                    line = f"│   {entity_short:<45} {sparkline} {conf_str} {delta_str}"
                    line = line[:79] + "│"
                    output.append(line)
            
            output.append("│" + " " * 78 + "│")
        
        # Forecast timelines
        forecast_timelines = timelines.get("forecast", [])
        if forecast_timelines:
            output.append("│ FORECAST RELIABILITY:" + " " * 57 + "│")
            output.append("│" + " " * 78 + "│")
            
            for timeline in forecast_timelines:
                entity_short = timeline.entity_id[:40] + "..." if len(timeline.entity_id) > 40 else timeline.entity_id
                sparkline = self.render_sparkline(timeline, width=20)
                
                latest = timeline.points[-1] if timeline.points else None
                if latest:
                    conf_str = f"{latest.confidence:.2f}"
                    delta_str = f"({latest.delta:+.2f})" if latest.delta is not None else ""
                    line = f"│   {entity_short:<45} {sparkline} {conf_str} {delta_str}"
                    line = line[:79] + "│"
                    output.append(line)
            
            output.append("│" + " " * 78 + "│")
        
        # Footer disclaimers
        output.append("├" + "─" * 78 + "┤")
        output.append("│ ⚠ OBSERVATIONAL ONLY • NO EXECUTION CHANGES • NO AUTONOMY" + " " * 19 + "│")
        output.append("└" + "─" * 78 + "┘")
        
        return "\n".join(output)


def render_confidence_timelines(signals_file: str = "outputs/phase25/learning_signals.jsonl") -> str:
    """
    Main entry point for rendering confidence timelines.
    
    Args:
        signals_file: Path to learning signals JSONL file
    
    Returns:
        Formatted whiteboard section
    """
    builder = ConfidenceTimelineBuilder(signals_file)
    timelines = builder.build_all_timelines()
    return builder.render_whiteboard_section(timelines)


if __name__ == "__main__":
    # Demo render
    output = render_confidence_timelines()
    print(output)
    print(f"\n✓ Confidence timelines rendered")
