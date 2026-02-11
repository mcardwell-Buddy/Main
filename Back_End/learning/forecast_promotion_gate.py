"""
Phase 4 Step 8: Forecast-to-Mission Promotion Gate

Defines the exact, auditable conditions under which a forecast may be promoted
into a mission objective.

HARD CONSTRAINTS:
- NO automatic mission creation
- NO autonomy
- NO execution side effects
- Explicit approval required
- Deterministic gating only
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class PromotionEligibility:
    """Represents the eligibility of a forecast for mission promotion."""
    forecast_id: str
    eligible: bool
    reasons: List[str]
    timestamp: str
    
    # Detailed criteria status
    domain_allows_promotion: bool = False
    confidence_meets_cap: bool = False
    reliability_sufficient: bool = False
    no_high_drift: bool = False
    evaluation_delay_met: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class PromotionSignal:
    """Signal emitted when a forecast is evaluated for promotion."""
    signal_type: str = "forecast_promotion_evaluated"
    signal_layer: str = "temporal"
    signal_source: str = "forecast_promotion_gate"
    forecast_id: str = ""
    eligible: bool = False
    reasons: List[str] = None
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSONL serialization."""
        if self.reasons is None:
            self.reasons = []
        return {
            "signal_type": self.signal_type,
            "signal_layer": self.signal_layer,
            "signal_source": self.signal_source,
            "forecast_id": self.forecast_id,
            "eligible": self.eligible,
            "reasons": self.reasons,
            "timestamp": self.timestamp
        }


class ForecastPromotionGate:
    """
    Gates forecast-to-mission promotion based on explicit criteria.
    
    A forecast MAY be eligible for promotion if ALL of the following are true:
    1. Domain contract allows promotion
    2. Forecast confidence >= domain confidence_cap
    3. Forecast reliability adjustment >= 0.8
    4. No active drift_warning with severity=high for same domain
    5. Forecast has existed for >= evaluation_delay_hours
    """
    
    # Minimum reliability adjustment threshold for promotion eligibility
    MIN_RELIABILITY_ADJUSTMENT = 0.8
    
    def __init__(
        self,
        signals_file: str = "outputs/phase25/learning_signals.jsonl",
        contracts_file: str = "outputs/phase25/forecast_domains.json",
        reliability_file: str = "outputs/phase25/forecast_reliability.json"
    ):
        self.signals_file = signals_file
        self.contracts_file = contracts_file
        self.reliability_file = reliability_file
        
        self.signals = []
        self.contracts = {}
        self.reliability_metrics = {}
        self.temporal_trends = {}
        self.drift_warnings = {}
        self.reliability_updates = {}
    
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
        
        # Index signals by type
        for signal in self.signals:
            signal_type = signal.get("signal_type", "")
            
            if signal_type == "temporal_trend_detected":
                target_layer = signal.get("target_layer", "")
                domain = target_layer  # For simplicity, use layer as domain key
                if domain not in self.temporal_trends:
                    self.temporal_trends[domain] = []
                self.temporal_trends[domain].append(signal)
            
            elif signal_type == "drift_warning":
                domain = signal.get("domain", "")
                if domain not in self.drift_warnings:
                    self.drift_warnings[domain] = []
                self.drift_warnings[domain].append(signal)
            
            elif signal_type == "forecast_reliability_update":
                domain = signal.get("domain", "")
                if domain not in self.reliability_updates:
                    self.reliability_updates[domain] = []
                self.reliability_updates[domain].append(signal)
    
    def load_domain_contracts(self) -> None:
        """Load domain contracts from JSON file."""
        contracts_path = Path(self.contracts_file)
        if not contracts_path.exists():
            print(f"Warning: Contracts file not found: {self.contracts_file}")
            return
        
        try:
            with open(contracts_path, 'r') as f:
                data = json.load(f)
            
            # Check if data has a "contracts" key (wrapper format)
            if isinstance(data, dict) and "contracts" in data:
                # Convert list of contracts to dict keyed by domain_name
                contracts_list = data.get("contracts", [])
                self.contracts = {}
                for contract in contracts_list:
                    domain_name = contract.get("domain_name")
                    if domain_name:
                        self.contracts[domain_name] = contract
            else:
                # Assume it's already in dict format
                self.contracts = data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse contracts file")
    
    def load_reliability_metrics(self) -> None:
        """Load reliability metrics from JSON file."""
        reliability_path = Path(self.reliability_file)
        if not reliability_path.exists():
            print(f"Warning: Reliability file not found: {self.reliability_file}")
            return
        
        try:
            with open(reliability_path, 'r') as f:
                self.reliability_metrics = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse reliability file")
    
    def _get_latest_reliability(self, domain: str) -> Optional[Dict]:
        """Get latest reliability update for a domain."""
        domain_updates = self.reliability_updates.get(domain, [])
        if domain_updates:
            # Return the most recent update
            return domain_updates[-1]
        
        # Fall back to reliability metrics file
        metric = self.reliability_metrics.get(domain, {})
        if metric:
            # Convert to signal format for consistency
            return {
                "domain": domain,
                "confidence_adjustment": metric.get("confidence_adjustment_factor", 0.0),
                "reliability_score": 1.0 - metric.get("avg_error", 0.5),
                "timestamp": metric.get("last_updated", "")
            }
        
        return None
    
    def _has_high_drift(self, domain: str) -> bool:
        """Check if domain has active high-severity drift warning."""
        domain_warnings = self.drift_warnings.get(domain, [])
        
        for warning in domain_warnings:
            severity = warning.get("severity", "").lower()
            if severity == "high":
                return True
        
        return False
    
    def _check_domain_allows_promotion(self, domain: str) -> Tuple[bool, str]:
        """
        Check if domain contract allows promotion.
        
        Returns:
            (allowed, reason_string)
        """
        # For now, assume all domains allow promotion
        # In future, could add explicit allow_promotion flag to contracts
        domain_contract = self.contracts.get(domain, {})
        
        if not domain_contract:
            return False, f"Domain '{domain}' not in contracts"
        
        # All domains can be promoted unless explicitly forbidden
        return True, f"Domain '{domain}' allows promotion"
    
    def _check_confidence_meets_cap(self, domain: str, forecast_confidence: float) -> Tuple[bool, str]:
        """
        Check if forecast confidence >= domain confidence_cap.
        
        Returns:
            (meets_cap, reason_string)
        """
        domain_contract = self.contracts.get(domain, {})
        confidence_cap = domain_contract.get("confidence_cap", 0.5)
        
        meets = forecast_confidence >= confidence_cap
        if meets:
            return True, f"Confidence {forecast_confidence:.2f} meets cap {confidence_cap:.2f}"
        else:
            return False, f"Confidence {forecast_confidence:.2f} below cap {confidence_cap:.2f}"
    
    def _check_reliability_sufficient(self, domain: str) -> Tuple[bool, str]:
        """
        Check if forecast reliability adjustment >= 0.8.
        
        Returns:
            (sufficient, reason_string)
        """
        reliability = self._get_latest_reliability(domain)
        
        if not reliability:
            return False, f"No reliability data available for domain '{domain}'"
        
        # Try confidence_adjustment first, fall back to confidence_adjustment_factor
        confidence_adj = reliability.get("confidence_adjustment") or reliability.get("confidence_adjustment_factor", 0.0)
        
        meets = confidence_adj >= self.MIN_RELIABILITY_ADJUSTMENT
        if meets:
            return True, f"Reliability adjustment {confidence_adj:.2f} >= {self.MIN_RELIABILITY_ADJUSTMENT:.2f}"
        else:
            return False, f"Reliability adjustment {confidence_adj:.2f} < {self.MIN_RELIABILITY_ADJUSTMENT:.2f}"
    
    def _check_no_high_drift(self, domain: str) -> Tuple[bool, str]:
        """
        Check if there's no active high-severity drift warning.
        
        Returns:
            (no_high_drift, reason_string)
        """
        has_high = self._has_high_drift(domain)
        
        if has_high:
            return False, f"Domain '{domain}' has active high-severity drift warning"
        else:
            return True, f"No high-severity drift warnings for domain '{domain}'"
    
    def _check_evaluation_delay_met(self, domain: str, forecast_created_timestamp: str) -> Tuple[bool, str]:
        """
        Check if forecast has existed for >= evaluation_delay_hours.
        
        Returns:
            (delay_met, reason_string)
        """
        domain_contract = self.contracts.get(domain, {})
        delay_hours = domain_contract.get("evaluation_delay_hours", 0)
        
        # Parse timestamps
        try:
            created = datetime.fromisoformat(forecast_created_timestamp.replace('Z', '+00:00'))
            now = datetime.now(created.tzinfo) if created.tzinfo else datetime.now()
            elapsed = (now - created).total_seconds() / 3600
            
            meets = elapsed >= delay_hours
            if meets:
                return True, f"Forecast age {elapsed:.1f}h meets delay {delay_hours}h"
            else:
                return False, f"Forecast age {elapsed:.1f}h below delay {delay_hours}h"
        except Exception as e:
            return False, f"Failed to parse timestamps: {e}"
    
    def evaluate_promotion(
        self,
        forecast_id: str,
        domain: str,
        forecast_confidence: float,
        forecast_created_timestamp: str
    ) -> PromotionEligibility:
        """
        Evaluate whether a forecast is eligible for mission promotion.
        
        Args:
            forecast_id: Unique forecast identifier
            domain: Domain (from domain contracts)
            forecast_confidence: Current confidence value (0.0-1.0)
            forecast_created_timestamp: ISO8601 creation timestamp
        
        Returns:
            PromotionEligibility object with evaluation results
        """
        reasons = []
        all_criteria_met = True
        
        # Criterion 1: Domain allows promotion
        domain_ok, reason = self._check_domain_allows_promotion(domain)
        reasons.append(reason)
        if not domain_ok:
            all_criteria_met = False
        
        # Criterion 2: Confidence meets cap
        conf_ok, reason = self._check_confidence_meets_cap(domain, forecast_confidence)
        reasons.append(reason)
        if not conf_ok:
            all_criteria_met = False
        
        # Criterion 3: Reliability sufficient
        rel_ok, reason = self._check_reliability_sufficient(domain)
        reasons.append(reason)
        if not rel_ok:
            all_criteria_met = False
        
        # Criterion 4: No high drift
        drift_ok, reason = self._check_no_high_drift(domain)
        reasons.append(reason)
        if not drift_ok:
            all_criteria_met = False
        
        # Criterion 5: Evaluation delay met
        delay_ok, reason = self._check_evaluation_delay_met(domain, forecast_created_timestamp)
        reasons.append(reason)
        if not delay_ok:
            all_criteria_met = False
        
        now = datetime.now(datetime.now().astimezone().tzinfo).isoformat()
        
        eligibility = PromotionEligibility(
            forecast_id=forecast_id,
            eligible=all_criteria_met,
            reasons=reasons,
            timestamp=now,
            domain_allows_promotion=domain_ok,
            confidence_meets_cap=conf_ok,
            reliability_sufficient=rel_ok,
            no_high_drift=drift_ok,
            evaluation_delay_met=delay_ok
        )
        
        return eligibility
    
    def emit_promotion_signal(self, eligibility: PromotionEligibility, output_file: str = "outputs/phase25/learning_signals.jsonl") -> bool:
        """
        Emit a forecast_promotion_evaluated signal to the signals file.
        
        Args:
            eligibility: PromotionEligibility object
            output_file: Path to signals JSONL file
        
        Returns:
            True if signal was appended successfully
        """
        try:
            signal = PromotionSignal(
                forecast_id=eligibility.forecast_id,
                eligible=eligibility.eligible,
                reasons=eligibility.reasons,
                timestamp=eligibility.timestamp
            )
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Append signal to JSONL file
            with open(output_path, 'a') as f:
                f.write(json.dumps(signal.to_dict()) + '\n')
            
            return True
        except Exception as e:
            print(f"Error emitting signal: {e}")
            return False
    
    def evaluate_all_forecasts(self) -> List[PromotionEligibility]:
        """
        Evaluate all domains from contracts for promotion eligibility.
        
        Returns:
            List of PromotionEligibility objects
        """
        self.load_signals()
        self.load_domain_contracts()
        self.load_reliability_metrics()
        
        evaluations = []
        
        for domain in self.contracts.keys():
            # Get latest reliability for this domain
            latest_reliability = self._get_latest_reliability(domain)
            
            if not latest_reliability:
                continue
            
            # Create forecast_id from domain
            timestamp_str = latest_reliability.get("timestamp", "")
            # Extract date from timestamp
            timestamp_date = timestamp_str[:10] if timestamp_str else "unknown"
            forecast_id = f"forecast_{domain}_{timestamp_date}"
            
            # Get confidence from reliability - use reliability_score if available
            if "reliability_score" in latest_reliability:
                confidence = latest_reliability.get("reliability_score", 0.0)
            else:
                # Fall back: calculate from avg_error
                confidence = 1.0 - latest_reliability.get("avg_error", 0.5)
            
            # Use timestamp from reliability
            timestamp = latest_reliability.get("timestamp", datetime.now().isoformat())
            
            # Evaluate
            eligibility = self.evaluate_promotion(
                forecast_id=forecast_id,
                domain=domain,
                forecast_confidence=confidence,
                forecast_created_timestamp=timestamp
            )
            
            evaluations.append(eligibility)
        
        return evaluations


def evaluate_and_emit_promotions(
    signals_file: str = "outputs/phase25/learning_signals.jsonl",
    contracts_file: str = "outputs/phase25/forecast_domains.json",
    reliability_file: str = "outputs/phase25/forecast_reliability.json"
) -> List[PromotionEligibility]:
    """
    Evaluate all forecasts and emit signals.
    
    Args:
        signals_file: Path to signals JSONL
        contracts_file: Path to domain contracts
        reliability_file: Path to reliability metrics
    
    Returns:
        List of PromotionEligibility evaluations
    """
    gate = ForecastPromotionGate(signals_file, contracts_file, reliability_file)
    evaluations = gate.evaluate_all_forecasts()
    
    for evaluation in evaluations:
        gate.emit_promotion_signal(evaluation, signals_file)
    
    return evaluations


if __name__ == "__main__":
    # Demo evaluation
    evaluations = evaluate_and_emit_promotions()
    
    print(f"Evaluated {len(evaluations)} forecasts for promotion eligibility")
    
    for eval in evaluations:
        status = "✓ ELIGIBLE" if eval.eligible else "✗ INELIGIBLE"
        print(f"\n{status}: {eval.forecast_id}")
        for reason in eval.reasons:
            print(f"  • {reason}")

