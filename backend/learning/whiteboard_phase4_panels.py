"""
Phase 4 Step 6: Whiteboard Phase 4 Panels

Exposes Phase 4 intelligence in the Whiteboard as default-visible, read-only panels.

Hard constraints:
- NO execution changes
- NO autonomy
- NO mission triggering
- READ-ONLY over signals
- Deterministic rendering only
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Import confidence timeline builder for Phase 4 Step 7
try:
    from backend.learning.confidence_timeline_builder import (
        ConfidenceTimelineBuilder,
        render_confidence_timelines
    )
    TIMELINE_SUPPORT = True
except ImportError:
    TIMELINE_SUPPORT = False

# Import forecast promotion gate for Phase 4 Step 8
try:
    from backend.learning.forecast_promotion_gate import (
        ForecastPromotionGate
    )
    PROMOTION_GATE_SUPPORT = True
except ImportError:
    PROMOTION_GATE_SUPPORT = False


class Phase4WhiteboardPanels:
    """
    Renders Phase 4 intelligence panels for the Whiteboard.
    
    All panels are read-only, default-visible, and non-executing.
    """
    
    def __init__(self, signals_file: Path, contracts_file: Optional[Path] = None):
        """
        Initialize panel renderer.
        
        Args:
            signals_file: Path to learning_signals.jsonl
            contracts_file: Optional path to forecast_domains.json
        """
        self.signals_file = signals_file
        self.contracts_file = contracts_file
        self.temporal_trends = []
        self.drift_warnings = []
        self.reliability_updates = []
        self.domain_contracts = {}
    
    def load_signals(self) -> None:
        """Load signals from JSONL file."""
        if not self.signals_file.exists():
            return
        
        self.temporal_trends = []
        self.drift_warnings = []
        self.reliability_updates = []
        
        with open(self.signals_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    signal = json.loads(line)
                    signal_type = signal.get("signal_type")
                    
                    if signal_type == "temporal_trend_detected":
                        self.temporal_trends.append(signal)
                    elif signal_type == "drift_warning":
                        self.drift_warnings.append(signal)
                    elif signal_type == "forecast_reliability_update":
                        self.reliability_updates.append(signal)
                
                except json.JSONDecodeError:
                    continue
    
    def load_domain_contracts(self) -> None:
        """Load domain contracts if available."""
        if not self.contracts_file or not self.contracts_file.exists():
            return
        
        with open(self.contracts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Index contracts by domain name
        for contract in data.get("contracts", []):
            self.domain_contracts[contract["domain_name"]] = contract
    
    def render_system_health_panel(self) -> str:
        """
        Render System Health panel showing temporal trends.
        
        Returns:
            Formatted panel text
        """
        lines = []
        lines.append("┌─────────────────────────────────────────────────────────┐")
        lines.append("│ SYSTEM HEALTH - Temporal Trends                         │")
        lines.append("│ [Read-Only • No Actions]                                │")
        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")
        
        if not self.temporal_trends:
            lines.append("  No temporal trends detected")
            lines.append("")
            return "\n".join(lines)
        
        # Group by target layer
        by_layer = {}
        for trend in self.temporal_trends:
            layer = trend.get("target_layer", "unknown")
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(trend)
        
        # Display each layer
        for layer, trends in sorted(by_layer.items()):
            lines.append(f"  Layer: {layer.upper()}")
            
            # Group by window
            by_window = {}
            for trend in trends:
                window = trend.get("window", "unknown")
                by_window[window] = trend
            
            # Display windows in order
            for window in ["short", "medium", "long"]:
                if window not in by_window:
                    continue
                
                trend = by_window[window]
                trend_dir = trend.get("trend", "unknown")
                avg_conf = trend.get("avg_confidence", 0.0)
                volatility = trend.get("volatility")
                success_rate = trend.get("success_rate")
                count = trend.get("rolling_count", 0)
                
                # Format trend indicator
                if trend_dir == "up":
                    trend_icon = "↑"
                elif trend_dir == "down":
                    trend_icon = "↓"
                else:
                    trend_icon = "→"
                
                # Format volatility indicator
                if volatility is not None:
                    if volatility < 0.01:
                        vol_icon = "●"  # stable
                    elif volatility < 0.05:
                        vol_icon = "◐"  # moderate
                    else:
                        vol_icon = "○"  # high
                    vol_str = f"{vol_icon} {volatility:.3f}"
                else:
                    vol_str = "N/A"
                
                # Build line
                line_parts = [
                    f"    {window:6s}: {trend_icon} {trend_dir:5s}",
                    f"count={count:3d}",
                    f"conf={avg_conf:.2f}" if avg_conf > 0 else "conf=N/A",
                    f"vol={vol_str}"
                ]
                
                if success_rate is not None:
                    line_parts.append(f"success={success_rate:.1%}")
                
                lines.append("  " + " │ ".join(line_parts))
            
            lines.append("")
        
        return "\n".join(lines)
    
    def render_drift_warnings_panel(self) -> str:
        """
        Render Drift & Risk Warnings panel.
        
        Returns:
            Formatted panel text
        """
        lines = []
        lines.append("┌─────────────────────────────────────────────────────────┐")
        lines.append("│ DRIFT & RISK WARNINGS                                   │")
        lines.append("│ [Read-Only • No Actions]                                │")
        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")
        
        if not self.drift_warnings:
            lines.append("  No drift warnings detected")
            lines.append("")
            return "\n".join(lines)
        
        # Group by severity
        by_severity = {"high": [], "medium": [], "low": []}
        for warning in self.drift_warnings:
            severity = warning.get("severity", "low")
            if severity in by_severity:
                by_severity[severity].append(warning)
        
        # Display warnings by severity
        for severity in ["high", "medium", "low"]:
            warnings = by_severity[severity]
            if not warnings:
                continue
            
            # Severity icon
            if severity == "high":
                icon = "🔴"
            elif severity == "medium":
                icon = "🟡"
            else:
                icon = "⚪"
            
            lines.append(f"  {icon} {severity.upper()} ({len(warnings)})")
            
            for warning in warnings:
                layer = warning.get("target_layer", "unknown")
                drift_type = warning.get("drift_type", "unknown")
                timestamp = warning.get("timestamp", "")
                evidence = warning.get("evidence", [])
                
                lines.append(f"    • {layer} - {drift_type}")
                if evidence:
                    for ev in evidence[:2]:  # Show first 2 pieces of evidence
                        lines.append(f"      {ev}")
                if timestamp:
                    # Parse and format timestamp
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime("%Y-%m-%d %H:%M")
                        lines.append(f"      First seen: {time_str}")
                    except:
                        pass
                lines.append("")
        
        return "\n".join(lines)
    
    def render_forecast_readiness_panel(self) -> str:
        """
        Render Forecast Readiness panel.
        
        Returns:
            Formatted panel text
        """
        lines = []
        lines.append("┌─────────────────────────────────────────────────────────┐")
        lines.append("│ FORECAST READINESS                                      │")
        lines.append("│ [Observation Only • No Predictions • No Actions]        │")
        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")
        
        if not self.reliability_updates:
            lines.append("  No forecast reliability data available")
            lines.append("")
            return "\n".join(lines)
        
        # Get latest reliability update per domain
        latest_by_domain = {}
        for update in self.reliability_updates:
            domain = update.get("domain")
            if domain:
                latest_by_domain[domain] = update
        
        if not latest_by_domain:
            lines.append("  No forecast reliability data available")
            lines.append("")
            return "\n".join(lines)
        
        # Display each domain
        for domain, update in sorted(latest_by_domain.items()):
            reliability = update.get("reliability_score", 0.0)
            confidence_adj = update.get("confidence_adjustment", 1.0)
            eval_count = update.get("evaluation_count", 0)
            
            # Status badge
            if reliability < 0.3:
                status = "🔴 SUPPRESSED"
            elif reliability < 0.5:
                status = "🟡 LOW"
            elif reliability < 0.7:
                status = "🟢 MODERATE"
            else:
                status = "🟢 GOOD"
            
            lines.append(f"  Domain: {domain}")
            lines.append(f"    Status: {status}")
            lines.append(f"    Reliability: {reliability:.3f}")
            lines.append(f"    Confidence Adjustment: {confidence_adj:.3f}")
            lines.append(f"    Evaluations: {eval_count}")
            
            # Get domain contract if available
            contract = self.domain_contracts.get(domain)
            if contract:
                cap = contract.get("confidence_cap", 1.0)
                delay = contract.get("evaluation_delay_hours", 0)
                lines.append(f"    Domain Cap: {cap}")
                lines.append(f"    Evaluation Delay: {delay}h")
            
            lines.append("    ⚠️  Limitations:")
            lines.append("      • This is not advice")
            lines.append("      • No action taken")
            lines.append("      • Human review required")
            lines.append("")
        
        return "\n".join(lines)
    
    def render_promotion_gate_panel(self) -> str:
        """
        Render forecast-to-mission promotion eligibility panel (Phase 4 Step 8).
        
        Shows which forecasts are eligible for mission creation based on
        deterministic gate criteria.
        
        Returns:
            Formatted panel string
        """
        lines = []
        lines.append("┌─────────────────────────────────────────────────────────┐")
        lines.append("│ FORECAST PROMOTION ELIGIBILITY                          │")
        lines.append("│ [Observational • Manual Approval Required]              │")
        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")
        
        if not PROMOTION_GATE_SUPPORT:
            lines.append("  Promotion gate not available")
            lines.append("")
            return "\n".join(lines)
        
        try:
            gate = ForecastPromotionGate(
                str(self.signals_file),
                str(self.contracts_file) if self.contracts_file else None
            )
            evaluations = gate.evaluate_all_forecasts()
            
            if not evaluations:
                lines.append("  No forecasts to evaluate")
                lines.append("")
                return "\n".join(lines)
            
            # Count by status
            eligible = [e for e in evaluations if e.eligible]
            ineligible = [e for e in evaluations if not e.eligible]
            
            # Show eligible forecasts
            if eligible:
                lines.append("  🟢 ELIGIBLE FOR MISSION CREATION:")
                for eval in eligible:
                    lines.append(f"    • {eval.forecast_id}")
                    # Show key reasons
                    for reason in eval.reasons[:2]:
                        if "below" not in reason.lower():
                            lines.append(f"      ✓ {reason}")
                lines.append("")
            
            # Show ineligible forecasts with reasons
            if ineligible:
                lines.append("  🔴 INELIGIBLE (awaiting conditions):")
                for eval in ineligible[:3]:  # Show top 3
                    lines.append(f"    • {eval.forecast_id}")
                    # Show first blocking reason
                    for reason in eval.reasons:
                        if "below" in reason.lower() or "no " in reason.lower():
                            lines.append(f"      ✗ {reason}")
                            break
                if len(ineligible) > 3:
                    lines.append(f"    ... and {len(ineligible) - 3} more")
                lines.append("")
            
            # Summary
            lines.append(f"  Summary: {len(eligible)} eligible, {len(ineligible)} awaiting conditions")
            lines.append("")
            
        except Exception as e:
            lines.append(f"  Error: {e}")
            lines.append("")
        
        return "\n".join(lines)
    
    def render_all_panels(self) -> str:
        """
        Render all Phase 4 panels.
        
        Returns:
            Complete formatted whiteboard section
        """
        # Load data
        self.load_signals()
        self.load_domain_contracts()
        
        lines = []
        lines.append("")
        lines.append("=" * 61)
        lines.append(" PHASE 4 INTELLIGENCE - READ-ONLY OBSERVATIONAL PANELS")
        lines.append("=" * 61)
        lines.append("")
        
        # Panel 1: System Health
        lines.append(self.render_system_health_panel())
        
        # Panel 2: Drift Warnings
        lines.append(self.render_drift_warnings_panel())
        
        # Panel 3: Forecast Readiness
        lines.append(self.render_forecast_readiness_panel())
        
        # Panel 4: Confidence Timelines (Phase 4 Step 7)
        if TIMELINE_SUPPORT:
            try:

                timeline_output = render_confidence_timelines(str(self.signals_file))
                lines.append(timeline_output)
            except Exception as e:
                lines.append(f"\n⚠️  Confidence Timeline Error: {e}\n")
        
        # Panel 5: Forecast Promotion Gate (Phase 4 Step 8)
        if PROMOTION_GATE_SUPPORT:
            try:
                lines.append(self.render_promotion_gate_panel())
            except Exception as e:
                lines.append(f"\n⚠️  Promotion Gate Error: {e}\n")
        
        lines.append("=" * 61)
        lines.append("")
        lines.append("⚠️  IMPORTANT: These panels are OBSERVATIONAL ONLY")
        lines.append("   • No execution changes")
        lines.append("   • No autonomy")
        lines.append("   • No mission triggering")
        lines.append("   • Read-only data display")
        lines.append("")
        
        return "\n".join(lines)


def render_phase4_whiteboard(
    signals_file: Path,
    contracts_file: Optional[Path] = None
) -> str:
    """
    Render Phase 4 whiteboard panels.
    
    Args:
        signals_file: Path to learning_signals.jsonl
        contracts_file: Optional path to forecast_domains.json
        
    Returns:
        Formatted whiteboard text
    """
    panels = Phase4WhiteboardPanels(signals_file, contracts_file)
    return panels.render_all_panels()


if __name__ == "__main__":
    """Render Phase 4 whiteboard panels."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # Setup paths
    signals_file = Path(__file__).parent.parent.parent / "outputs" / "phase25" / "learning_signals.jsonl"
    contracts_file = Path(__file__).parent.parent.parent / "outputs" / "phase25" / "forecast_domains.json"
    
    # Render panels
    print("Rendering Phase 4 whiteboard panels...")
    print()
    
    whiteboard_text = render_phase4_whiteboard(signals_file, contracts_file)
    print(whiteboard_text)
    
    print("✓ Phase 4 panels rendered")
