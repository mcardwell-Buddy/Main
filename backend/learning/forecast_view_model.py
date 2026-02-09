"""
Phase 4 Step 4: Forecast Presentation Layer

Renders forecast-ready insights without enabling decisions or actions.

Hard constraints:
- NO advice
- NO commands
- NO execution hooks
- NO autonomy
- NO LLM usage
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime, timezone


@dataclass
class ForecastView:
    """
    Read-only forecast view model.
    
    Presents insights without any action recommendations or execution hooks.
    """
    domain: str
    summary: str
    confidence: float
    trend: str  # "improving", "degrading", "stable"
    limitations: List[str]
    timestamp: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ForecastView':
        """Create from dictionary."""
        return cls(**data)


class ForecastViewRenderer:
    """
    Renders forecast views from temporal signals and drift warnings.
    
    Pure presentation layer - no actions, no advice, no autonomy.
    """
    
    # Standard limitations for all forecast views
    STANDARD_LIMITATIONS = [
        "This is not advice",
        "No action taken",
        "Human review required",
        "Observational only",
        "Not predictive"
    ]
    
    def __init__(self, signals_file: Path, domain_contracts_file: Path):
        """
        Initialize renderer.
        
        Args:
            signals_file: Path to learning_signals.jsonl
            domain_contracts_file: Path to forecast_domains.json
        """
        self.signals_file = signals_file
        self.domain_contracts_file = domain_contracts_file
        self.temporal_trends = []
        self.drift_warnings = []
        self.domain_contracts = {}
    
    def load_signals(self) -> None:
        """Load temporal trends and drift warnings from signals file."""
        if not self.signals_file.exists():
            return
        
        self.temporal_trends = []
        self.drift_warnings = []
        
        with open(self.signals_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    signal = json.loads(line)
                    
                    if signal.get("signal_type") == "temporal_trend_detected":
                        self.temporal_trends.append(signal)
                    elif signal.get("signal_type") == "drift_warning":
                        self.drift_warnings.append(signal)
                
                except json.JSONDecodeError:
                    continue
    
    def load_domain_contracts(self) -> None:
        """Load domain contracts from JSON file."""
        if not self.domain_contracts_file.exists():
            return
        
        with open(self.domain_contracts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Index contracts by domain name
        for contract in data.get("contracts", []):
            self.domain_contracts[contract["domain_name"]] = contract
    
    def _calculate_trend_direction(self, layer: str) -> str:
        """
        Calculate overall trend direction for a layer.
        
        Args:
            layer: Target layer name
            
        Returns:
            "improving", "degrading", or "stable"
        """
        # Get latest trends for this layer
        layer_trends = [t for t in self.temporal_trends if t.get("target_layer") == layer]
        
        if not layer_trends:
            return "stable"
        
        # Check for drift warnings
        layer_warnings = [w for w in self.drift_warnings if w.get("target_layer") == layer]
        
        if layer_warnings:
            # If any high severity warnings, it's degrading
            high_severity = any(w.get("severity") == "high" for w in layer_warnings)
            if high_severity:
                return "degrading"
            
            # If any medium severity warnings, it's degrading
            medium_severity = any(w.get("severity") == "medium" for w in layer_warnings)
            if medium_severity:
                return "degrading"
        
        # Look at recent short-window trend
        short_trends = [t for t in layer_trends if t.get("window") == "short"]
        if short_trends:
            latest = short_trends[-1]
            trend = latest.get("trend")
            
            if trend == "up":
                return "improving"
            elif trend == "down":
                return "degrading"
        
        return "stable"
    
    def _calculate_confidence(self, layer: str, domain_contract: dict) -> float:
        """
        Calculate confidence score for forecast.
        
        Args:
            layer: Target layer name
            domain_contract: Domain contract configuration
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Start with average confidence from temporal trends
        layer_trends = [t for t in self.temporal_trends if t.get("target_layer") == layer]
        
        if not layer_trends:
            return 0.0
        
        # Get average confidence from trends
        confidences = [t.get("avg_confidence", 0.0) for t in layer_trends if t.get("avg_confidence") is not None]
        
        if not confidences:
            # Use success rate as proxy if confidence not available
            success_rates = [t.get("success_rate", 0.0) for t in layer_trends if t.get("success_rate") is not None]
            if success_rates:
                avg_confidence = sum(success_rates) / len(success_rates)
            else:
                avg_confidence = 0.0
        else:
            avg_confidence = sum(confidences) / len(confidences)
        
        # Apply domain confidence cap
        domain_cap = domain_contract.get("confidence_cap", 1.0)
        capped_confidence = min(avg_confidence, domain_cap)
        
        # Reduce confidence if drift warnings present
        layer_warnings = [w for w in self.drift_warnings if w.get("target_layer") == layer]
        if layer_warnings:
            # Reduce by 20% per warning (up to 60% reduction)
            reduction = min(0.2 * len(layer_warnings), 0.6)
            capped_confidence *= (1.0 - reduction)
        
        return round(capped_confidence, 2)
    
    def _generate_summary(self, layer: str, trend: str, warnings: List[dict]) -> str:
        """
        Generate human-readable summary.
        
        Args:
            layer: Target layer name
            trend: Trend direction
            warnings: Drift warnings for this layer
            
        Returns:
            Summary string
        """
        parts = []
        
        # Layer status
        parts.append(f"Layer: {layer}")
        
        # Trend description
        if trend == "improving":
            parts.append("Recent trend shows improvement")
        elif trend == "degrading":
            parts.append("Recent trend shows degradation")
        else:
            parts.append("Recent trend appears stable")
        
        # Warning count
        if warnings:
            parts.append(f"{len(warnings)} drift warning(s) detected")
            
            # Group by type
            warning_types = {}
            for w in warnings:
                wtype = w.get("drift_type", "unknown")
                warning_types[wtype] = warning_types.get(wtype, 0) + 1
            
            for wtype, count in warning_types.items():
                parts.append(f"  - {wtype}: {count}")
        else:
            parts.append("No drift warnings")
        
        return ". ".join(parts)
    
    def _get_domain_limitations(self, domain_contract: dict) -> List[str]:
        """
        Get domain-specific limitations.
        
        Args:
            domain_contract: Domain contract configuration
            
        Returns:
            List of limitation strings
        """
        limitations = self.STANDARD_LIMITATIONS.copy()
        
        # Add confidence cap limitation
        cap = domain_contract.get("confidence_cap", 1.0)
        limitations.append(f"Confidence capped at {cap}")
        
        # Add evaluation delay
        delay = domain_contract.get("evaluation_delay_hours", 0)
        limitations.append(f"Evaluation delay: {delay} hours")
        
        # Add forbidden actions count
        forbidden_count = len(domain_contract.get("forbidden_actions", []))
        limitations.append(f"{forbidden_count} forbidden action(s)")
        
        return limitations
    
    def render_view(self, domain_name: str, target_layer: str) -> Optional[ForecastView]:
        """
        Render a forecast view for a specific domain and layer.
        
        Args:
            domain_name: Domain name (must exist in contracts)
            target_layer: Target signal layer
            
        Returns:
            ForecastView or None if domain not found
        """
        # Get domain contract
        domain_contract = self.domain_contracts.get(domain_name)
        if not domain_contract:
            return None
        
        # Check if layer is allowed for this domain
        allowed_layers = domain_contract.get("allowed_signal_layers", [])
        if target_layer not in allowed_layers:
            return None
        
        # Calculate trend direction
        trend = self._calculate_trend_direction(target_layer)
        
        # Get warnings for this layer
        layer_warnings = [w for w in self.drift_warnings if w.get("target_layer") == target_layer]
        
        # Generate summary
        summary = self._generate_summary(target_layer, trend, layer_warnings)
        
        # Calculate confidence
        confidence = self._calculate_confidence(target_layer, domain_contract)
        
        # Get limitations
        limitations = self._get_domain_limitations(domain_contract)
        
        # Create view
        view = ForecastView(
            domain=domain_name,
            summary=summary,
            confidence=confidence,
            trend=trend,
            limitations=limitations,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return view
    
    def render_all_views(self) -> List[ForecastView]:
        """
        Render all possible forecast views.
        
        Returns:
            List of ForecastView objects
        """
        views = []
        
        # Load data
        self.load_signals()
        self.load_domain_contracts()
        
        # Render view for each domain + layer combination
        for domain_name, domain_contract in self.domain_contracts.items():
            allowed_layers = domain_contract.get("allowed_signal_layers", [])
            
            for layer in allowed_layers:
                # Check if we have data for this layer
                has_trends = any(t.get("target_layer") == layer for t in self.temporal_trends)
                
                if has_trends:
                    view = self.render_view(domain_name, layer)
                    if view:
                        views.append(view)
        
        return views


def generate_whiteboard_section(views: List[ForecastView]) -> str:
    """
    Generate whiteboard-compatible text section.
    
    Args:
        views: List of ForecastView objects
        
    Returns:
        Formatted whiteboard section text
    """
    lines = []
    lines.append("=" * 60)
    lines.append("FORECAST VIEWS (Read-Only)")
    lines.append("=" * 60)
    lines.append("")
    
    if not views:
        lines.append("No forecast views available")
        lines.append("")
        return "\n".join(lines)
    
    for i, view in enumerate(views, 1):
        lines.append(f"View {i}: {view.domain} / {view.summary.split(':')[1].split('.')[0].strip() if ':' in view.summary else 'unknown'}")
        lines.append(f"  Trend: {view.trend}")
        lines.append(f"  Confidence: {view.confidence}")
        lines.append(f"  Summary: {view.summary}")
        lines.append(f"  Limitations:")
        for limitation in view.limitations:
            lines.append(f"    - {limitation}")
        lines.append("")
    
    lines.append("=" * 60)
    lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    """Generate example forecast views."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # Setup paths
    signals_file = Path(__file__).parent.parent.parent / "outputs" / "phase25" / "learning_signals.jsonl"
    contracts_file = Path(__file__).parent.parent.parent / "outputs" / "phase25" / "forecast_domains.json"
    
    # Create renderer
    renderer = ForecastViewRenderer(signals_file, contracts_file)
    
    # Render all views
    print("Rendering forecast views...")
    views = renderer.render_all_views()
    print(f"Generated {len(views)} views")
    print()
    
    # Display whiteboard section
    whiteboard_text = generate_whiteboard_section(views)
    print(whiteboard_text)
