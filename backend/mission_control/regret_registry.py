"""
Regret Registry: Persist irreversible failures and high-cost mistakes.

Phase 4 Step 6: Regret Registry
- Maintains permanent record of failures and costly mistakes
- Prevents blind repetition of high-cost actions
- Read-only for observability (no blocking behavior yet)
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import os


# Support environment variable overrides for testing
REGRET_REGISTRY_FILE = Path(os.environ.get("REGRET_REGISTRY_FILE", "outputs/phase25/regret_registry.jsonl"))


class RegretEntry:
    """Represents a single regret event."""
    
    # Irreversibility level
    IRREVERSIBLE = "irreversible"
    HIGH_COST = "high_cost"
    CAUTION_WARRANTED = "caution_warranted"
    
    # Severity tiers
    SEVERITY_CRITICAL = "critical"       # Irreversible damage
    SEVERITY_HIGH = "high"               # High cost, likely irreversible
    SEVERITY_MEDIUM = "medium"           # Moderate cost, worth remembering
    SEVERITY_LOW = "low"                 # Low cost or uncertain
    
    def __init__(
        self,
        mission_id: str,
        action: str,
        failure_reason: str,
        irreversible: bool,
        estimated_cost: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Create a regret entry.
        
        Args:
            mission_id: ID of failed mission
            action: What was attempted (selector, navigation, etc.)
            failure_reason: Why it failed (timeout, no_element, error, etc.)
            irreversible: Whether failure is irreversible
            estimated_cost: Dict with time_lost, trust_impact, opportunities_lost
            context: Additional context (goal, URL, etc.)
        """
        self.mission_id = mission_id
        self.action = action
        self.failure_reason = failure_reason
        self.irreversible = irreversible
        self.estimated_cost = estimated_cost
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        
        # Calculate severity based on costs and irreversibility
        self.severity = self._calculate_severity()
    
    def _calculate_severity(self) -> str:
        """Calculate severity based on cost and irreversibility."""
        if self.irreversible:
            return self.SEVERITY_CRITICAL
        
        total_cost = (
            self.estimated_cost.get("time_lost", 0) +
            self.estimated_cost.get("trust_impact", 0) +
            self.estimated_cost.get("opportunities_lost", 0)
        )
        
        if total_cost >= 100:
            return self.SEVERITY_HIGH
        elif total_cost >= 50:
            return self.SEVERITY_MEDIUM
        else:
            return self.SEVERITY_LOW
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mission_id": self.mission_id,
            "action": self.action,
            "failure_reason": self.failure_reason,
            "irreversible": self.irreversible,
            "severity": self.severity,
            "estimated_cost": self.estimated_cost,
            "context": self.context,
            "timestamp": self.timestamp
        }


def log_regret(
    mission_id: str,
    action: str,
    failure_reason: str,
    irreversible: bool,
    estimated_cost: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Log a regret entry to the registry.
    
    Args:
        mission_id: ID of failed mission
        action: Action that failed
        failure_reason: Reason for failure
        irreversible: Whether failure is irreversible
        estimated_cost: Cost breakdown (time_lost, trust_impact, opportunities_lost)
        context: Additional context
    
    Returns:
        The logged entry as dictionary
    """
    entry = RegretEntry(
        mission_id=mission_id,
        action=action,
        failure_reason=failure_reason,
        irreversible=irreversible,
        estimated_cost=estimated_cost,
        context=context
    )
    
    entry_dict = entry.to_dict()
    
    # Ensure directory exists
    REGRET_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to registry
    with open(REGRET_REGISTRY_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry_dict) + '\n')
    
    return entry_dict


def get_regrets(
    mission_id: Optional[str] = None,
    irreversible_only: bool = False,
    min_severity: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Read regrets from registry.
    
    Args:
        mission_id: Optional filter by mission_id
        irreversible_only: Only return irreversible failures
        min_severity: Minimum severity (critical > high > medium > low)
    
    Returns:
        List of regret entries
    """
    if not REGRET_REGISTRY_FILE.exists():
        return []
    
    severity_order = {
        RegretEntry.SEVERITY_CRITICAL: 4,
        RegretEntry.SEVERITY_HIGH: 3,
        RegretEntry.SEVERITY_MEDIUM: 2,
        RegretEntry.SEVERITY_LOW: 1
    }
    
    min_severity_level = severity_order.get(min_severity, 0) if min_severity else 0
    
    regrets = []
    with open(REGRET_REGISTRY_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                
                # Apply filters
                if mission_id and entry.get("mission_id") != mission_id:
                    continue
                
                if irreversible_only and not entry.get("irreversible"):
                    continue
                
                if min_severity:
                    entry_severity_level = severity_order.get(entry.get("severity"), 0)
                    if entry_severity_level < min_severity_level:
                        continue
                
                regrets.append(entry)
            except json.JSONDecodeError:
                continue
    
    return regrets


def get_regret_summary() -> Dict[str, Any]:
    """
    Get summary statistics of all regrets.
    
    Returns:
        Dictionary with summary stats
    """
    regrets = get_regrets()
    
    if not regrets:
        return {
            "total_regrets": 0,
            "irreversible_count": 0,
            "high_severity_count": 0,
            "total_cost": {
                "time_lost": 0,
                "trust_impact": 0,
                "opportunities_lost": 0
            },
            "failure_reasons": {}
        }
    
    irreversible_count = sum(1 for r in regrets if r.get("irreversible"))
    high_severity_count = sum(1 for r in regrets if r.get("severity") in ["critical", "high"])
    
    # Aggregate costs
    total_cost = {
        "time_lost": sum(r.get("estimated_cost", {}).get("time_lost", 0) for r in regrets),
        "trust_impact": sum(r.get("estimated_cost", {}).get("trust_impact", 0) for r in regrets),
        "opportunities_lost": sum(r.get("estimated_cost", {}).get("opportunities_lost", 0) for r in regrets)
    }
    
    # Count failure reasons
    failure_reasons = {}
    for r in regrets:
        reason = r.get("failure_reason", "unknown")
        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
    
    return {
        "total_regrets": len(regrets),
        "irreversible_count": irreversible_count,
        "high_severity_count": high_severity_count,
        "total_cost": total_cost,
        "failure_reasons": failure_reasons
    }


def get_regrets_by_action(action: str) -> List[Dict[str, Any]]:
    """Get all regrets for a specific action type."""
    regrets = get_regrets()
    return [r for r in regrets if r.get("action") == action]


def get_irreversible_regrets() -> List[Dict[str, Any]]:
    """Get all irreversible regrets, sorted by severity."""
    return get_regrets(irreversible_only=True)


def has_critical_regrets_for_mission(mission_id: str) -> bool:
    """Check if a mission has critical regrets."""
    regrets = get_regrets(mission_id=mission_id, min_severity=RegretEntry.SEVERITY_CRITICAL)
    return len(regrets) > 0
