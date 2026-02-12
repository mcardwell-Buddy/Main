"""
Artifact Cost Reconciliation System (Phase 4b)

Tracks and reconciles artifact costs:
- Cost estimation at artifact creation
- Actual cost tracking during execution
- Cost variance analysis
- Provider-specific pricing
- Reconciliation reports

Non-blocking: cost tracking doesn't affect execution
Feature-flagged: COST_RECONCILIATION_ENABLED controls tracking
Append-only: cost records are immutable
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class CostProvider(Enum):
    """Cost tracking providers/services."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    INTERNAL = "internal"


@dataclass
class CostEstimate:
    """Cost estimate for an artifact."""
    artifact_id: str
    artifact_type: str
    created_at: str  # ISO8601
    provider: str
    model: str
    tokens_estimated: int  # Input or combined
    cost_usd: float
    currency: str = "USD"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CostActual:
    """Actual cost incurred for an artifact."""
    artifact_id: str
    created_at: str  # ISO8601
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    cost_usd: float
    currency: str = "USD"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CostReconciliation:
    """Reconciliation record for an artifact."""
    artifact_id: str
    reconciled_at: str  # ISO8601
    estimated_cost: float
    actual_cost: float
    variance_usd: float
    variance_percent: float
    status: str  # "on_budget", "over_budget", "under_budget"
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CostReconciliationEngine:
    """
    Tracks and reconciles artifact costs.
    
    Manages cost estimates, actuals, and variance analysis.
    """

    def __init__(self):
        """Initialize cost reconciliation engine."""
        self.estimates: Dict[str, CostEstimate] = {}  # artifact_id → estimate
        self.actuals: Dict[str, CostActual] = {}  # artifact_id → actual
        self.reconciliations: Dict[str, CostReconciliation] = {}  # artifact_id → reconciliation
        self._cost_file = Path(__file__).parent / "data" / "artifact_costs.jsonl"
        logger.info("[COST] Reconciliation engine initialized")

    def record_estimate(self, estimate: CostEstimate) -> bool:
        """
        Record cost estimate for artifact.
        
        Args:
            estimate: CostEstimate object
            
        Returns:
            True if recorded successfully
        """
        try:
            self.estimates[estimate.artifact_id] = estimate
            self._append_to_file("estimate", estimate.to_dict())
            logger.debug(
                f"[COST] Recorded estimate: {estimate.artifact_id} = ${estimate.cost_usd:.4f}"
            )
            return True
        except Exception as e:
            logger.warning(f"[COST] Failed to record estimate: {e}")
            return False

    def record_actual(self, actual: CostActual) -> bool:
        """
        Record actual cost for artifact.
        
        Args:
            actual: CostActual object
            
        Returns:
            True if recorded successfully
        """
        try:
            self.actuals[actual.artifact_id] = actual
            self._append_to_file("actual", actual.to_dict())
            logger.debug(
                f"[COST] Recorded actual: {actual.artifact_id} = ${actual.cost_usd:.4f}"
            )
            return True
        except Exception as e:
            logger.warning(f"[COST] Failed to record actual: {e}")
            return False

    def reconcile(self, artifact_id: str, threshold_percent: float = 10.0) -> Optional[CostReconciliation]:
        """
        Reconcile estimated vs actual cost for artifact.
        
        Args:
            artifact_id: Target artifact ID
            threshold_percent: Threshold for "over_budget" (default 10%)
            
        Returns:
            CostReconciliation object or None if missing data
        """
        estimate = self.estimates.get(artifact_id)
        actual = self.actuals.get(artifact_id)
        
        if not estimate or not actual:
            logger.warning(f"[COST] Missing estimate or actual for {artifact_id}")
            return None

        variance_usd = actual.cost_usd - estimate.cost_usd
        variance_percent = (variance_usd / estimate.cost_usd * 100) if estimate.cost_usd > 0 else 0.0
        
        # Determine status
        if variance_percent <= -threshold_percent:
            status = "under_budget"
        elif variance_percent >= threshold_percent:
            status = "over_budget"
        else:
            status = "on_budget"
        
        reconciliation = CostReconciliation(
            artifact_id=artifact_id,
            reconciled_at=datetime.now(timezone.utc).isoformat(),
            estimated_cost=estimate.cost_usd,
            actual_cost=actual.cost_usd,
            variance_usd=variance_usd,
            variance_percent=variance_percent,
            status=status,
            notes=f"Estimated with {estimate.model}, actual used {actual.model}"
        )
        
        self.reconciliations[artifact_id] = reconciliation
        self._append_to_file("reconciliation", reconciliation.to_dict())
        
        logger.info(
            f"[COST] Reconciled {artifact_id}: "
            f"${estimate.cost_usd:.4f} → ${actual.cost_usd:.4f} "
            f"({variance_percent:+.1f}%) {status}"
        )
        
        return reconciliation

    def get_cost_summary(self, artifact_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get cost summary for artifacts.
        
        Args:
            artifact_ids: List of artifact IDs (None = all)
            
        Returns:
            Summary dictionary with totals and statistics
        """
        ids = artifact_ids or list(set(list(self.estimates.keys()) + list(self.actuals.keys())))
        
        total_estimated = 0.0
        total_actual = 0.0
        total_variance = 0.0
        reconciled_count = 0
        over_budget_count = 0
        under_budget_count = 0
        on_budget_count = 0
        
        for artifact_id in ids:
            if artifact_id in self.estimates:
                total_estimated += self.estimates[artifact_id].cost_usd
            if artifact_id in self.actuals:
                total_actual += self.actuals[artifact_id].cost_usd
            if artifact_id in self.reconciliations:
                reconciled_count += 1
                rec = self.reconciliations[artifact_id]
                total_variance += rec.variance_usd
                if rec.status == "over_budget":
                    over_budget_count += 1
                elif rec.status == "under_budget":
                    under_budget_count += 1
                else:
                    on_budget_count += 1
        
        variance_percent = (total_variance / total_estimated * 100) if total_estimated > 0 else 0.0
        
        return {
            "total_estimated_usd": round(total_estimated, 4),
            "total_actual_usd": round(total_actual, 4),
            "total_variance_usd": round(total_variance, 4),
            "variance_percent": round(variance_percent, 2),
            "artifacts_tracked": len(ids),
            "reconciled_count": reconciled_count,
            "over_budget_count": over_budget_count,
            "under_budget_count": under_budget_count,
            "on_budget_count": on_budget_count,
        }

    def get_provider_costs(self, provider: str, artifact_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get costs by provider.
        
        Args:
            provider: Provider name (e.g., "openai", "anthropic")
            artifact_ids: List of artifact IDs (None = all)
            
        Returns:
            Provider cost summary
        """
        ids = artifact_ids or list(set(list(self.estimates.keys()) + list(self.actuals.keys())))
        
        estimated = 0.0
        actual = 0.0
        count = 0
        
        for artifact_id in ids:
            est = self.estimates.get(artifact_id)
            if est and est.provider == provider:
                estimated += est.cost_usd
                count += 1
            
            act = self.actuals.get(artifact_id)
            if act and act.provider == provider:
                actual += act.cost_usd
        
        variance = actual - estimated
        variance_pct = (variance / estimated * 100) if estimated > 0 else 0.0
        
        return {
            "provider": provider,
            "estimated_usd": round(estimated, 4),
            "actual_usd": round(actual, 4),
            "variance_usd": round(variance, 4),
            "variance_percent": round(variance_pct, 2),
            "artifact_count": count,
        }

    def load_from_costs_file(self) -> bool:
        """
        Load cost records from artifact_costs.jsonl.
        
        Returns:
            True if loaded successfully
        """
        if not self._cost_file.exists():
            logger.debug(f"[COST] Costs file not found: {self._cost_file}")
            return False

        try:
            with self._cost_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        record_type = record.get("type")
                        data = record.get("data", {})
                        
                        if record_type == "estimate":
                            estimate = CostEstimate(**data)
                            self.estimates[estimate.artifact_id] = estimate
                        elif record_type == "actual":
                            actual = CostActual(**data)
                            self.actuals[actual.artifact_id] = actual
                        elif record_type == "reconciliation":
                            reconciliation = CostReconciliation(**data)
                            self.reconciliations[reconciliation.artifact_id] = reconciliation
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.debug(f"[COST] Skipped invalid record: {e}")
                        continue
            
            logger.info(
                f"[COST] Loaded {len(self.estimates)} estimates, "
                f"{len(self.actuals)} actuals, {len(self.reconciliations)} reconciliations"
            )
            return True
        
        except Exception as e:
            logger.warning(f"[COST] Failed to load costs: {e}")
            return False

    def _append_to_file(self, record_type: str, data: Dict[str, Any]):
        """Append cost record to JSONL file (non-blocking)."""
        try:
            self._cost_file.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "type": record_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data
            }
            with self._cost_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.debug(f"[COST] Failed to append to costs file: {e}")

    def export_report(self, format: str = "json") -> str:
        """
        Export cost reconciliation report.
        
        Args:
            format: Report format ("json", "csv", "markdown")
            
        Returns:
            Formatted report string
        """
        summary = self.get_cost_summary()
        
        if format == "json":
            return json.dumps(summary, indent=2)
        
        elif format == "csv":
            lines = ["artifact_id,estimated_usd,actual_usd,variance_usd,variance_percent,status"]
            for artifact_id, rec in self.reconciliations.items():
                lines.append(
                    f"{artifact_id},{rec.estimated_cost:.4f},{rec.actual_cost:.4f},"
                    f"{rec.variance_usd:.4f},{rec.variance_percent:.2f},{rec.status}"
                )
            return "\n".join(lines)
        
        elif format == "markdown":
            lines = ["# Cost Reconciliation Report", ""]
            lines.append(f"**Total Estimated**: ${summary['total_estimated_usd']:.4f}")
            lines.append(f"**Total Actual**: ${summary['total_actual_usd']:.4f}")
            lines.append(f"**Total Variance**: ${summary['total_variance_usd']:.4f} ({summary['variance_percent']:+.1f}%)")
            lines.append("")
            lines.append("| Status | Count |")
            lines.append("|--------|-------|")
            lines.append(f"| On Budget | {summary['on_budget_count']} |")
            lines.append(f"| Over Budget | {summary['over_budget_count']} |")
            lines.append(f"| Under Budget | {summary['under_budget_count']} |")
            return "\n".join(lines)
        
        return ""


# Global singleton
_cost_engine: Optional[CostReconciliationEngine] = None


def get_cost_reconciliation_engine() -> CostReconciliationEngine:
    """Get or create global cost reconciliation engine singleton."""
    global _cost_engine
    if _cost_engine is None:
        _cost_engine = CostReconciliationEngine()
    return _cost_engine
