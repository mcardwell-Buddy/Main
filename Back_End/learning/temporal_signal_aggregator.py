"""
Temporal Signal Aggregator: Phase 4x Step 1

Aggregates historical signals over time and emits trend metadata.

CONSTRAINTS:
- READ-ONLY over existing logs
- Append-only signals
- Deterministic only
- NO predictions or causal inference
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import statistics


# Constants
LEARNING_SIGNALS_FILE = Path(os.environ.get("LEARNING_SIGNALS_FILE", "outputs/phase25/learning_signals.jsonl"))

# Window sizes
WINDOW_SHORT = 10
WINDOW_MEDIUM = 50
WINDOW_LONG = 200

# Supported signal layers
SUPPORTED_LAYERS = ["selector", "intent", "mission", "opportunity"]


class TemporalAggregator:
    """Aggregates signals over time and detects trends."""
    
    def __init__(self, signals_file: Path = LEARNING_SIGNALS_FILE):
        self.signals_file = signals_file
        self.signals_by_layer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
    def load_signals(self) -> None:
        """Load all signals from JSONL file."""
        if not self.signals_file.exists():
            return
        
        with open(self.signals_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    signal = json.loads(line)
                    layer = signal.get("signal_layer")
                    if layer in SUPPORTED_LAYERS:
                        self.signals_by_layer[layer].append(signal)
                except json.JSONDecodeError:
                    continue
    
    def compute_rolling_metrics(
        self, 
        signals: List[Dict[str, Any]], 
        window_size: int
    ) -> Optional[Dict[str, Any]]:
        """
        Compute rolling metrics for a window of signals.
        
        Returns:
            Dict with rolling_count, success_rate, avg_confidence, trend_direction, volatility
            or None if insufficient data
        """
        if len(signals) < 2:
            return None
        
        # Take last N signals
        window_signals = signals[-window_size:] if len(signals) >= window_size else signals
        
        if len(window_signals) == 0:
            return None
        
        # Count successes (if applicable)
        success_count = 0
        total_with_outcome = 0
        confidences = []
        
        for signal in window_signals:
            # Check for outcome field
            outcome = signal.get("outcome")
            if outcome in ["success", "failure"]:
                total_with_outcome += 1
                if outcome == "success":
                    success_count += 1
            
            # Collect confidence values
            confidence = signal.get("confidence")
            if confidence is not None and isinstance(confidence, (int, float)):
                confidences.append(float(confidence))
        
        # Compute metrics
        rolling_count = len(window_signals)
        
        success_rate = None
        if total_with_outcome > 0:
            success_rate = success_count / total_with_outcome
        
        avg_confidence = None
        if confidences:
            avg_confidence = statistics.mean(confidences)
        
        # Compute trend direction based on first half vs second half
        trend_direction = self._compute_trend(window_signals)
        
        # Compute volatility (variance of confidence scores)
        volatility = None
        if len(confidences) >= 2:
            volatility = statistics.variance(confidences)
        
        return {
            "rolling_count": rolling_count,
            "success_rate": success_rate,
            "avg_confidence": avg_confidence,
            "trend_direction": trend_direction,
            "volatility": volatility
        }
    
    def _compute_trend(self, signals: List[Dict[str, Any]]) -> str:
        """
        Compute trend direction by comparing first half to second half.
        
        Returns: "up", "down", or "flat"
        """
        if len(signals) < 4:
            return "flat"
        
        # Split into first and second half
        mid = len(signals) // 2
        first_half = signals[:mid]
        second_half = signals[mid:]
        
        # Compare success rates if available
        first_successes = sum(1 for s in first_half if s.get("outcome") == "success")
        first_total = sum(1 for s in first_half if s.get("outcome") in ["success", "failure"])
        
        second_successes = sum(1 for s in second_half if s.get("outcome") == "success")
        second_total = sum(1 for s in second_half if s.get("outcome") in ["success", "failure"])
        
        if first_total > 0 and second_total > 0:
            first_rate = first_successes / first_total
            second_rate = second_successes / second_total
            
            # Use 5% threshold to avoid noise
            if second_rate > first_rate + 0.05:
                return "up"
            elif second_rate < first_rate - 0.05:
                return "down"
            else:
                return "flat"
        
        # Fallback: compare confidence values
        first_confidences = [s.get("confidence") for s in first_half if s.get("confidence") is not None]
        second_confidences = [s.get("confidence") for s in second_half if s.get("confidence") is not None]
        
        if first_confidences and second_confidences:
            first_avg = statistics.mean(first_confidences)
            second_avg = statistics.mean(second_confidences)
            
            if second_avg > first_avg + 0.05:
                return "up"
            elif second_avg < first_avg - 0.05:
                return "down"
        
        return "flat"
    
    def aggregate_layer(self, layer: str) -> List[Dict[str, Any]]:
        """
        Aggregate signals for a specific layer across all windows.
        
        Returns:
            List of temporal_trend_detected signals
        """
        signals = self.signals_by_layer.get(layer, [])
        
        if not signals:
            return []
        
        trends = []
        
        # Compute for each window size
        windows = [
            ("short", WINDOW_SHORT),
            ("medium", WINDOW_MEDIUM),
            ("long", WINDOW_LONG)
        ]
        
        for window_name, window_size in windows:
            metrics = self.compute_rolling_metrics(signals, window_size)
            
            if metrics is None:
                continue
            
            # Create temporal trend signal
            trend_signal = {
                "signal_type": "temporal_trend_detected",
                "signal_layer": "temporal",
                "signal_source": "temporal_aggregator",
                "target_layer": layer,
                "window": window_name,
                "trend": metrics["trend_direction"],
                "rolling_count": metrics["rolling_count"],
                "avg_confidence": metrics["avg_confidence"],
                "volatility": metrics["volatility"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Add success_rate if available
            if metrics["success_rate"] is not None:
                trend_signal["success_rate"] = metrics["success_rate"]
            
            trends.append(trend_signal)
        
        return trends
    
    def aggregate_all(self) -> List[Dict[str, Any]]:
        """
        Aggregate signals across all supported layers.
        
        Returns:
            List of all temporal_trend_detected signals
        """
        all_trends = []
        
        for layer in SUPPORTED_LAYERS:
            layer_trends = self.aggregate_layer(layer)
            all_trends.extend(layer_trends)
        
        return all_trends
    
    def emit_trends(self, trends: List[Dict[str, Any]]) -> int:
        """
        Emit temporal trend signals to learning_signals.jsonl.
        
        Returns:
            Number of signals written
        """
        if not trends:
            return 0
        
        # Ensure directory exists
        self.signals_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Append signals
        with open(self.signals_file, 'a', encoding='utf-8') as f:
            for trend in trends:
                f.write(json.dumps(trend) + '\n')
        
        return len(trends)
    
    def run(self) -> Dict[str, Any]:
        """
        Execute full temporal aggregation pipeline.
        
        Returns:
            Summary statistics
        """
        # Load signals
        self.load_signals()
        
        # Aggregate trends
        trends = self.aggregate_all()
        
        # Emit trends
        emitted_count = self.emit_trends(trends)
        
        # Compute summary
        summary = {
            "total_signals_loaded": sum(len(signals) for signals in self.signals_by_layer.values()),
            "signals_by_layer": {layer: len(signals) for layer, signals in self.signals_by_layer.items()},
            "trends_detected": len(trends),
            "trends_emitted": emitted_count,
            "trends_by_layer": defaultdict(int)
        }
        
        for trend in trends:
            summary["trends_by_layer"][trend["target_layer"]] += 1
        
        return summary


def aggregate_temporal_signals(signals_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main entry point for temporal signal aggregation.
    
    Args:
        signals_file: Optional path to signals file (defaults to LEARNING_SIGNALS_FILE)
    
    Returns:
        Summary dictionary with aggregation statistics
    """
    if signals_file is None:
        signals_file = LEARNING_SIGNALS_FILE
    
    aggregator = TemporalAggregator(signals_file)
    return aggregator.run()


if __name__ == "__main__":
    # Run aggregation
    summary = aggregate_temporal_signals()
    
    print("Temporal Signal Aggregation Complete")
    print("=" * 50)
    print(f"Total signals loaded: {summary['total_signals_loaded']}")
    print(f"Signals by layer: {dict(summary['signals_by_layer'])}")
    print(f"Trends detected: {summary['trends_detected']}")
    print(f"Trends emitted: {summary['trends_emitted']}")
    print(f"Trends by layer: {dict(summary['trends_by_layer'])}")

