"""
Mission Cost Accountant: Tracks normalized costs for every mission execution.
Purely read-only instrumentation - no behavior changes, no retries, no autonomy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MissionCostReport:
    """Normalized cost report for a mission execution."""
    mission_id: str
    total_duration_sec: float
    pages_visited: int
    selectors_attempted: int
    selectors_failed: int
    retries_total: int
    time_cost: float
    page_cost: int
    failure_cost: int
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "mission_id": self.mission_id,
            "total_duration_sec": self.total_duration_sec,
            "pages_visited": self.pages_visited,
            "selectors_attempted": self.selectors_attempted,
            "selectors_failed": self.selectors_failed,
            "retries_total": self.retries_total,
            "time_cost": self.time_cost,
            "page_cost": self.page_cost,
            "failure_cost": self.failure_cost,
            "timestamp": self.timestamp
        }
    
    def to_signal(self) -> Dict[str, Any]:
        """Convert to learning signal format."""
        return {
            "signal_type": "mission_cost_report",
            "signal_layer": "mission",
            "signal_source": "mission_cost_accountant",
            "mission_id": self.mission_id,
            "total_duration_sec": self.total_duration_sec,
            "pages_visited": self.pages_visited,
            "selectors_attempted": self.selectors_attempted,
            "selectors_failed": self.selectors_failed,
            "retries_total": self.retries_total,
            "cost_units": {
                "time_cost": self.time_cost,
                "page_cost": self.page_cost,
                "failure_cost": self.failure_cost
            },
            "timestamp": self.timestamp
        }


class MissionCostAccountant:
    """
    Computes normalized cost metrics for mission executions.
    
    Tracks:
    - total_duration_sec: Total time spent in seconds
    - pages_visited: Number of pages navigated
    - selectors_attempted: Total selector operations attempted
    - selectors_failed: Number of selector failures
    - retries_total: Total retry attempts
    
    Computes deterministic cost_units:
    - time_cost: Duration in seconds
    - page_cost: Number of pages
    - failure_cost: Number of failures
    
    Read-only instrumentation - does not affect mission execution.
    """
    
    def __init__(self, signals_file: str = "backend/learning_signals.jsonl"):
        """
        Initialize the cost accountant.
        
        Args:
            signals_file: Path to learning signals file
        """
        self.signals_file = Path(signals_file)
    
    def compute_costs(self, mission_id: str) -> Optional[MissionCostReport]:
        """
        Compute cost metrics for a completed mission.
        
        Reads learning signals to extract:
        - Mission duration from status updates
        - Selector outcomes (attempted, failed, retries)
        - Page navigation count
        
        Args:
            mission_id: The mission to compute costs for
            
        Returns:
            MissionCostReport with normalized costs, or None if insufficient data
        """
        if not self.signals_file.exists():
            return None
        
        # Read all signals for this mission
        mission_signals = self._read_mission_signals(mission_id)
        
        if not mission_signals:
            return None
        
        # Extract metrics
        duration_sec = self._compute_duration(mission_signals)
        pages_visited = self._count_pages_visited(mission_signals)
        selectors_attempted = self._count_selectors_attempted(mission_signals)
        selectors_failed = self._count_selectors_failed(mission_signals)
        retries_total = self._count_retries(mission_signals)
        
        # Compute cost units (deterministic)
        time_cost = duration_sec
        page_cost = pages_visited
        failure_cost = selectors_failed
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        return MissionCostReport(
            mission_id=mission_id,
            total_duration_sec=duration_sec,
            pages_visited=pages_visited,
            selectors_attempted=selectors_attempted,
            selectors_failed=selectors_failed,
            retries_total=retries_total,
            time_cost=time_cost,
            page_cost=page_cost,
            failure_cost=failure_cost,
            timestamp=timestamp
        )
    
    def _read_mission_signals(self, mission_id: str) -> List[Dict[str, Any]]:
        """Read all signals related to a specific mission."""
        signals = []
        
        try:
            with open(self.signals_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            signal = json.loads(line)
                            if signal.get("mission_id") == mission_id:
                                signals.append(signal)
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass
        
        return signals
    
    def _compute_duration(self, signals: List[Dict[str, Any]]) -> float:
        """
        Compute total mission duration in seconds.
        
        Uses mission_status_update signals to find start and end times.
        """
        start_time = None
        end_time = None
        
        for signal in signals:
            if signal.get("signal_type") == "mission_status_update":
                timestamp_str = signal.get("timestamp")
                status = signal.get("status")
                
                if not timestamp_str:
                    continue
                
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    if status == "active" and start_time is None:
                        start_time = timestamp
                    elif status in ["completed", "failed", "aborted"]:
                        end_time = timestamp
                except Exception:
                    continue
        
        if start_time and end_time:
            duration = (end_time - start_time).total_seconds()
            return max(0.0, duration)
        
        return 0.0
    
    def _count_pages_visited(self, signals: List[Dict[str, Any]]) -> int:
        """
        Count number of unique pages visited during mission.
        
        Uses page_number from selector_outcome signals.
        """
        pages = set()
        
        for signal in signals:
            if signal.get("signal_type") == "selector_outcome":
                page_number = signal.get("page_number")
                if page_number is not None:
                    pages.add(page_number)
        
        return len(pages)
    
    def _count_selectors_attempted(self, signals: List[Dict[str, Any]]) -> int:
        """
        Count total selector operations attempted.
        
        Each selector_outcome signal represents one attempt.
        """
        count = 0
        
        for signal in signals:
            if signal.get("signal_type") == "selector_outcome":
                count += 1
        
        return count
    
    def _count_selectors_failed(self, signals: List[Dict[str, Any]]) -> int:
        """
        Count selector operations that failed.
        
        Counts selector_outcome signals with outcome="failure".
        """
        count = 0
        
        for signal in signals:
            if signal.get("signal_type") == "selector_outcome":
                if signal.get("outcome") == "failure":
                    count += 1
        
        return count
    
    def _count_retries(self, signals: List[Dict[str, Any]]) -> int:
        """
        Count total retry attempts across all selector operations.
        
        Sums retry_count from all selector_outcome signals.
        """
        total_retries = 0
        
        for signal in signals:
            if signal.get("signal_type") == "selector_outcome":
                retry_count = signal.get("retry_count", 0)
                total_retries += retry_count
        
        return total_retries
    
    def should_emit_signal(self, report: Optional[MissionCostReport]) -> bool:
        """
        Determine if cost report signal should be emitted.
        
        Always emit when we have a valid report.
        
        Args:
            report: The cost report to check
            
        Returns:
            True if signal should be emitted
        """
        return report is not None
