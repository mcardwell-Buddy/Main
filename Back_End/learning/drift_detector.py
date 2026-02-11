"""
Drift & Degradation Detector: Phase 4x Step 2

Detects when Buddy's performance is degrading over time.

CONSTRAINTS:
- READ-ONLY over existing signals
- NO navigation or execution changes
- NO autonomy, retries, or LLM usage
- Observability only - no blocking or corrective action
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


# Constants
LEARNING_SIGNALS_FILE = Path(os.environ.get("LEARNING_SIGNALS_FILE", "outputs/phase25/learning_signals.jsonl"))

# Detection thresholds
CONFIDENCE_DECAY_THRESHOLD = 0.15  # 15% drop
SUCCESS_RATE_DECAY_THRESHOLD = 0.15  # 15% drop
VOLATILITY_SPIKE_THRESHOLD = 2.0  # 2x increase

# Severity levels
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"


class DriftDetector:
    """Detects performance degradation over time."""
    
    def __init__(self, signals_file: Path = LEARNING_SIGNALS_FILE):
        self.signals_file = signals_file
        self.temporal_trends: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
    def load_temporal_trends(self) -> None:
        """Load temporal_trend_detected signals from JSONL file."""
        if not self.signals_file.exists():
            return
        
        with open(self.signals_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    signal = json.loads(line)
                    if signal.get("signal_type") == "temporal_trend_detected":
                        target_layer = signal.get("target_layer")
                        if target_layer:
                            self.temporal_trends[target_layer].append(signal)
                except json.JSONDecodeError:
                    continue
    
    def get_latest_trends_by_layer(self, layer: str) -> Dict[str, Dict[str, Any]]:
        """
        Get the latest trend for each window size for a specific layer.
        
        Returns:
            Dict mapping window name to trend signal
        """
        trends = self.temporal_trends.get(layer, [])
        
        if not trends:
            return {}
        
        # Sort by timestamp to get latest
        trends_sorted = sorted(trends, key=lambda t: t.get("timestamp", ""), reverse=True)
        
        # Get latest for each window
        latest_by_window = {}
        for trend in trends_sorted:
            window = trend.get("window")
            if window and window not in latest_by_window:
                latest_by_window[window] = trend
        
        return latest_by_window
    
    def detect_confidence_decay(
        self, 
        layer: str, 
        trends: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect confidence decay by comparing windows.
        
        Returns drift warning if >15% drop detected
        """
        # Need at least 2 windows to compare
        if len(trends) < 2:
            return None
        
        # Compare short vs medium, medium vs long
        windows_to_compare = [
            ("short", "medium"),
            ("medium", "long")
        ]
        
        evidence = []
        max_drop = 0.0
        
        for window1, window2 in windows_to_compare:
            if window1 not in trends or window2 not in trends:
                continue
            
            conf1 = trends[window1].get("avg_confidence")
            conf2 = trends[window2].get("avg_confidence")
            
            # Skip if either is None
            if conf1 is None or conf2 is None:
                continue
            
            # Calculate drop (short should be more recent, so compare short vs longer windows)
            # If short window has lower confidence than longer windows, that's decay
            if window1 == "short" and conf1 < conf2:
                drop = conf2 - conf1
                drop_pct = drop / conf2 if conf2 > 0 else 0
                
                if drop_pct > max_drop:
                    max_drop = drop_pct
                
                if drop_pct >= CONFIDENCE_DECAY_THRESHOLD:
                    evidence.append(
                        f"Confidence dropped {drop_pct:.1%} from {window2} ({conf2:.3f}) to {window1} ({conf1:.3f})"
                    )
        
        if not evidence:
            return None
        
        # Determine severity
        severity = self._calculate_severity(max_drop, CONFIDENCE_DECAY_THRESHOLD)
        
        return {
            "signal_type": "drift_warning",
            "signal_layer": "temporal",
            "signal_source": "drift_detector",
            "target_layer": layer,
            "drift_type": "confidence_decay",
            "severity": severity,
            "evidence": evidence,
            "max_degradation": max_drop,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def detect_success_rate_degradation(
        self, 
        layer: str, 
        trends: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect success rate degradation by comparing windows.
        
        Returns drift warning if >15% drop detected
        """
        if len(trends) < 2:
            return None
        
        windows_to_compare = [
            ("short", "medium"),
            ("medium", "long")
        ]
        
        evidence = []
        max_drop = 0.0
        
        for window1, window2 in windows_to_compare:
            if window1 not in trends or window2 not in trends:
                continue
            
            rate1 = trends[window1].get("success_rate")
            rate2 = trends[window2].get("success_rate")
            
            if rate1 is None or rate2 is None:
                continue
            
            # Check for degradation (recent window worse than older)
            if window1 == "short" and rate1 < rate2:
                drop = rate2 - rate1
                drop_pct = drop / rate2 if rate2 > 0 else 0
                
                if drop_pct > max_drop:
                    max_drop = drop_pct
                
                if drop_pct >= SUCCESS_RATE_DECAY_THRESHOLD:
                    evidence.append(
                        f"Success rate dropped {drop_pct:.1%} from {window2} ({rate2:.1%}) to {window1} ({rate1:.1%})"
                    )
        
        if not evidence:
            return None
        
        severity = self._calculate_severity(max_drop, SUCCESS_RATE_DECAY_THRESHOLD)
        
        return {
            "signal_type": "drift_warning",
            "signal_layer": "temporal",
            "signal_source": "drift_detector",
            "target_layer": layer,
            "drift_type": "success_rate_degradation",
            "severity": severity,
            "evidence": evidence,
            "max_degradation": max_drop,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def detect_volatility_spike(
        self, 
        layer: str, 
        trends: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect volatility spikes by comparing windows.
        
        Returns drift warning if volatility increases by 2x or more
        """
        if len(trends) < 2:
            return None
        
        windows_to_compare = [
            ("short", "medium"),
            ("medium", "long")
        ]
        
        evidence = []
        max_spike = 0.0
        
        for window1, window2 in windows_to_compare:
            if window1 not in trends or window2 not in trends:
                continue
            
            vol1 = trends[window1].get("volatility")
            vol2 = trends[window2].get("volatility")
            
            if vol1 is None or vol2 is None:
                continue
            
            # Skip if baseline volatility is zero
            if vol2 == 0:
                continue
            
            # Check for spike (recent window more volatile than older)
            if window1 == "short" and vol1 > vol2:
                spike_ratio = vol1 / vol2
                
                if spike_ratio > max_spike:
                    max_spike = spike_ratio
                
                if spike_ratio >= VOLATILITY_SPIKE_THRESHOLD:
                    evidence.append(
                        f"Volatility increased {spike_ratio:.1f}x from {window2} ({vol2:.4f}) to {window1} ({vol1:.4f})"
                    )
        
        if not evidence:
            return None
        
        # Severity based on spike magnitude
        if max_spike >= 4.0:
            severity = SEVERITY_HIGH
        elif max_spike >= 3.0:
            severity = SEVERITY_MEDIUM
        else:
            severity = SEVERITY_LOW
        
        return {
            "signal_type": "drift_warning",
            "signal_layer": "temporal",
            "signal_source": "drift_detector",
            "target_layer": layer,
            "drift_type": "volatility_spike",
            "severity": severity,
            "evidence": evidence,
            "max_spike": max_spike,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_severity(self, degradation: float, threshold: float) -> str:
        """Calculate severity based on degradation magnitude."""
        if degradation >= threshold * 2:  # 2x threshold
            return SEVERITY_HIGH
        elif degradation >= threshold * 1.5:  # 1.5x threshold
            return SEVERITY_MEDIUM
        else:
            return SEVERITY_LOW
    
    def detect_drift_for_layer(self, layer: str) -> List[Dict[str, Any]]:
        """
        Detect all types of drift for a specific layer.
        
        Returns:
            List of drift warnings
        """
        trends = self.get_latest_trends_by_layer(layer)
        
        if not trends:
            return []
        
        warnings = []
        
        # Check confidence decay
        confidence_warning = self.detect_confidence_decay(layer, trends)
        if confidence_warning:
            warnings.append(confidence_warning)
        
        # Check success rate degradation
        success_warning = self.detect_success_rate_degradation(layer, trends)
        if success_warning:
            warnings.append(success_warning)
        
        # Check volatility spikes
        volatility_warning = self.detect_volatility_spike(layer, trends)
        if volatility_warning:
            warnings.append(volatility_warning)
        
        return warnings
    
    def detect_all_drift(self) -> List[Dict[str, Any]]:
        """
        Detect drift across all layers.
        
        Returns:
            List of all drift warnings
        """
        all_warnings = []
        
        for layer in self.temporal_trends.keys():
            layer_warnings = self.detect_drift_for_layer(layer)
            all_warnings.extend(layer_warnings)
        
        return all_warnings
    
    def emit_warnings(self, warnings: List[Dict[str, Any]]) -> int:
        """
        Emit drift warnings to learning_signals.jsonl.
        
        Returns:
            Number of warnings written
        """
        if not warnings:
            return 0
        
        # Ensure directory exists
        self.signals_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Append warnings
        with open(self.signals_file, 'a', encoding='utf-8') as f:
            for warning in warnings:
                f.write(json.dumps(warning) + '\n')
        
        return len(warnings)
    
    def run(self) -> Dict[str, Any]:
        """
        Execute drift detection pipeline.
        
        Returns:
            Summary statistics
        """
        # Load temporal trends
        self.load_temporal_trends()
        
        # Detect drift
        warnings = self.detect_all_drift()
        
        # Emit warnings
        emitted_count = self.emit_warnings(warnings)
        
        # Compute summary
        summary = {
            "temporal_trends_loaded": sum(len(trends) for trends in self.temporal_trends.values()),
            "trends_by_layer": {layer: len(trends) for layer, trends in self.temporal_trends.items()},
            "drift_warnings_detected": len(warnings),
            "drift_warnings_emitted": emitted_count,
            "warnings_by_layer": defaultdict(int),
            "warnings_by_type": defaultdict(int),
            "warnings_by_severity": defaultdict(int)
        }
        
        for warning in warnings:
            summary["warnings_by_layer"][warning["target_layer"]] += 1
            summary["warnings_by_type"][warning["drift_type"]] += 1
            summary["warnings_by_severity"][warning["severity"]] += 1
        
        return summary


def detect_drift(signals_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main entry point for drift detection.
    
    Args:
        signals_file: Optional path to signals file
    
    Returns:
        Summary dictionary with detection statistics
    """
    if signals_file is None:
        signals_file = LEARNING_SIGNALS_FILE
    
    detector = DriftDetector(signals_file)
    return detector.run()


if __name__ == "__main__":
    # Run drift detection
    summary = detect_drift()
    
    print("Drift & Degradation Detection Complete")
    print("=" * 50)
    print(f"Temporal trends loaded: {summary['temporal_trends_loaded']}")
    print(f"Trends by layer: {dict(summary['trends_by_layer'])}")
    print(f"Drift warnings detected: {summary['drift_warnings_detected']}")
    print(f"Drift warnings emitted: {summary['drift_warnings_emitted']}")
    
    if summary['warnings_by_layer']:
        print(f"Warnings by layer: {dict(summary['warnings_by_layer'])}")
    if summary['warnings_by_type']:
        print(f"Warnings by type: {dict(summary['warnings_by_type'])}")
    if summary['warnings_by_severity']:
        print(f"Warnings by severity: {dict(summary['warnings_by_severity'])}")

