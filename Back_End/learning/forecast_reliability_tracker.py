"""
Phase 4 Step 5: Meta-Forecasting Confidence Control

Tracks historical forecast accuracy and suppresses unreliable forecasts.

Hard constraints:
- NO new predictions
- NO autonomy
- NO execution changes
- Deterministic only
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict


@dataclass
class ReliabilityMetrics:
    """
    Tracks reliability metrics for a forecast domain.
    """
    domain: str
    forecast_count: int
    evaluation_count: int
    avg_error: float
    confidence_adjustment_factor: float
    last_updated: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReliabilityMetrics':
        """Create from dictionary."""
        return cls(**data)


class ForecastReliabilityTracker:
    """
    Tracks forecast reliability over time.
    
    Monitors forecast accuracy and adjusts confidence accordingly.
    Pure observational - no autonomy or execution changes.
    """
    
    # Reliability thresholds
    SUPPRESSION_THRESHOLD = 0.3  # Below this, forecasts are suppressed
    CONFIDENCE_PENALTY_RATE = 0.5  # Multiply confidence by this if reliability is poor
    MIN_EVALUATIONS = 3  # Minimum evaluations before adjusting confidence
    
    def __init__(self, signals_file: Path, reliability_store: Optional[Path] = None):
        """
        Initialize tracker.
        
        Args:
            signals_file: Path to learning_signals.jsonl
            reliability_store: Optional path to store reliability metrics
        """
        self.signals_file = signals_file
        self.reliability_store = reliability_store or (signals_file.parent / "forecast_reliability.json")
        self.forecast_views = []
        self.reliability_metrics = {}
    
    def load_forecast_views(self) -> None:
        """Load forecast views from signals file."""
        # For this implementation, we'll simulate forecast views
        # In a real system, these would be historical forecast_view records
        self.forecast_views = []
        
        # Note: In practice, we'd have a separate signal type for forecast_view_created
        # For now, we'll work with the structure we have
    
    def load_reliability_metrics(self) -> None:
        """Load existing reliability metrics from store."""
        if not self.reliability_store.exists():
            self.reliability_metrics = {}
            return
        
        with open(self.reliability_store, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.reliability_metrics = {
            domain: ReliabilityMetrics.from_dict(metrics)
            for domain, metrics in data.items()
        }
    
    def save_reliability_metrics(self) -> None:
        """Save reliability metrics to store."""
        # Ensure directory exists
        self.reliability_store.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            domain: metrics.to_dict()
            for domain, metrics in self.reliability_metrics.items()
        }
        
        with open(self.reliability_store, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def initialize_domain_metrics(self, domain: str) -> ReliabilityMetrics:
        """
        Initialize reliability metrics for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            New ReliabilityMetrics instance
        """
        return ReliabilityMetrics(
            domain=domain,
            forecast_count=0,
            evaluation_count=0,
            avg_error=0.0,
            confidence_adjustment_factor=1.0,
            last_updated=datetime.now(timezone.utc).isoformat()
        )
    
    def simulate_forecast_accuracy(self, domain: str, num_forecasts: int = 10) -> List[float]:
        """
        Simulate forecast accuracy for testing.
        
        In production, this would analyze actual forecast vs outcome data.
        
        Args:
            domain: Domain name
            num_forecasts: Number of simulated forecasts
            
        Returns:
            List of error values (0.0-1.0)
        """
        # Simulate different accuracy patterns per domain
        if domain == "internal_system_health":
            # Good accuracy - errors around 0.2
            return [0.15, 0.18, 0.22, 0.20, 0.25, 0.19, 0.21, 0.17, 0.23, 0.20]
        elif domain == "business_opportunity":
            # Moderate accuracy - errors around 0.4
            return [0.35, 0.42, 0.38, 0.45, 0.40, 0.37, 0.43, 0.39, 0.41, 0.44]
        elif domain == "financial_markets":
            # Poor accuracy - errors around 0.7 (should be suppressed)
            return [0.65, 0.72, 0.68, 0.75, 0.70, 0.73, 0.69, 0.71, 0.74, 0.67]
        elif domain == "environmental":
            # Fair accuracy - errors around 0.3
            return [0.28, 0.32, 0.30, 0.35, 0.29, 0.31, 0.33, 0.27, 0.34, 0.30]
        else:
            # Default moderate accuracy
            return [0.4] * num_forecasts
    
    def calculate_reliability_score(self, avg_error: float) -> float:
        """
        Calculate reliability score from average error.
        
        Args:
            avg_error: Average error (0.0-1.0)
            
        Returns:
            Reliability score (0.0-1.0, higher is better)
        """
        # Simple inverse: reliability = 1 - error
        return max(0.0, min(1.0, 1.0 - avg_error))
    
    def calculate_confidence_adjustment(self, reliability: float, eval_count: int) -> float:
        """
        Calculate confidence adjustment factor.
        
        Args:
            reliability: Reliability score (0.0-1.0)
            eval_count: Number of evaluations
            
        Returns:
            Confidence adjustment factor (0.0-1.0)
        """
        # Need minimum evaluations before adjusting
        if eval_count < self.MIN_EVALUATIONS:
            return 1.0
        
        # If reliability is poor, apply penalty
        if reliability < 0.5:
            return self.CONFIDENCE_PENALTY_RATE
        
        # Otherwise, adjust proportionally to reliability
        # Reliability 0.5 -> adjustment 0.5
        # Reliability 1.0 -> adjustment 1.0
        return reliability
    
    def should_suppress_forecast(self, reliability: float, eval_count: int) -> bool:
        """
        Determine if forecast should be suppressed.
        
        Args:
            reliability: Reliability score (0.0-1.0)
            eval_count: Number of evaluations
            
        Returns:
            True if forecast should be suppressed
        """
        # Need minimum evaluations before suppressing
        if eval_count < self.MIN_EVALUATIONS:
            return False
        
        # Suppress if reliability below threshold
        return reliability < self.SUPPRESSION_THRESHOLD
    
    def update_domain_reliability(self, domain: str) -> ReliabilityMetrics:
        """
        Update reliability metrics for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            Updated ReliabilityMetrics
        """
        # Get or create metrics
        if domain not in self.reliability_metrics:
            self.reliability_metrics[domain] = self.initialize_domain_metrics(domain)
        
        metrics = self.reliability_metrics[domain]
        
        # Simulate forecast evaluation
        errors = self.simulate_forecast_accuracy(domain)
        
        # Update metrics
        metrics.forecast_count += len(errors)
        metrics.evaluation_count += len(errors)
        metrics.avg_error = sum(errors) / len(errors)
        
        # Calculate reliability
        reliability = self.calculate_reliability_score(metrics.avg_error)
        
        # Calculate adjustment factor
        metrics.confidence_adjustment_factor = self.calculate_confidence_adjustment(
            reliability,
            metrics.evaluation_count
        )
        
        metrics.last_updated = datetime.now(timezone.utc).isoformat()
        
        return metrics
    
    def emit_reliability_signal(self, metrics: ReliabilityMetrics) -> None:
        """
        Emit forecast_reliability_update signal.
        
        Args:
            metrics: ReliabilityMetrics to emit
        """
        reliability = self.calculate_reliability_score(metrics.avg_error)
        
        signal = {
            "signal_type": "forecast_reliability_update",
            "signal_layer": "temporal",
            "signal_source": "forecast_reliability",
            "domain": metrics.domain,
            "forecast_count": metrics.forecast_count,
            "evaluation_count": metrics.evaluation_count,
            "avg_error": round(metrics.avg_error, 3),
            "reliability_score": round(reliability, 3),
            "confidence_adjustment": round(metrics.confidence_adjustment_factor, 3),
            "timestamp": metrics.last_updated
        }
        
        # Append to signals file
        with open(self.signals_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(signal) + '\n')
    
    def emit_suppression_signal(self, domain: str, reliability: float) -> None:
        """
        Emit forecast_suppressed signal.
        
        Args:
            domain: Domain name
            reliability: Reliability score
        """
        signal = {
            "signal_type": "forecast_suppressed",
            "signal_layer": "temporal",
            "signal_source": "forecast_reliability",
            "domain": domain,
            "reliability_score": round(reliability, 3),
            "reason": f"Reliability ({reliability:.3f}) below threshold ({self.SUPPRESSION_THRESHOLD})",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Append to signals file
        with open(self.signals_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(signal) + '\n')
    
    def track_all_domains(self, domains: List[str]) -> Dict[str, ReliabilityMetrics]:
        """
        Track reliability for all domains.
        
        Args:
            domains: List of domain names
            
        Returns:
            Dictionary of domain -> ReliabilityMetrics
        """
        # Load existing metrics
        self.load_reliability_metrics()
        
        results = {}
        
        for domain in domains:
            # Update metrics
            metrics = self.update_domain_reliability(domain)
            
            # Emit reliability signal
            self.emit_reliability_signal(metrics)
            
            # Check for suppression
            reliability = self.calculate_reliability_score(metrics.avg_error)
            should_suppress = self.should_suppress_forecast(reliability, metrics.evaluation_count)
            
            if should_suppress:
                self.emit_suppression_signal(domain, reliability)
            
            results[domain] = metrics
        
        # Save updated metrics
        self.save_reliability_metrics()
        
        return results


def track_forecast_reliability(
    signals_file: Path,
    domains: List[str]
) -> Dict[str, ReliabilityMetrics]:
    """
    Track forecast reliability for all domains.
    
    Args:
        signals_file: Path to learning_signals.jsonl
        domains: List of domain names to track
        
    Returns:
        Dictionary of domain -> ReliabilityMetrics
    """
    tracker = ForecastReliabilityTracker(signals_file)
    results = tracker.track_all_domains(domains)
    
    # Print summary
    print(f"Forecast Reliability Tracking Complete")
    print(f"Tracked {len(results)} domains")
    print()
    
    for domain, metrics in results.items():
        reliability = tracker.calculate_reliability_score(metrics.avg_error)
        suppressed = tracker.should_suppress_forecast(reliability, metrics.evaluation_count)
        
        print(f"{domain}:")
        print(f"  Forecasts: {metrics.forecast_count}")
        print(f"  Evaluations: {metrics.evaluation_count}")
        print(f"  Avg Error: {metrics.avg_error:.3f}")
        print(f"  Reliability: {reliability:.3f}")
        print(f"  Adjustment: {metrics.confidence_adjustment_factor:.3f}")
        print(f"  Suppressed: {'Yes' if suppressed else 'No'}")
        print()
    
    return results


if __name__ == "__main__":
    """Track forecast reliability for example domains."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # Setup paths
    signals_file = Path(__file__).parent.parent.parent / "outputs" / "phase25" / "learning_signals.jsonl"
    
    # Track all domains
    domains = [
        "internal_system_health",
        "business_opportunity",
        "financial_markets",
        "environmental"
    ]
    
    print("Tracking forecast reliability...")
    print()
    
    results = track_forecast_reliability(signals_file, domains)
    
    print("✓ Reliability tracking complete")

