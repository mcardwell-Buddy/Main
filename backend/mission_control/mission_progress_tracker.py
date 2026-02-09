"""
Mission Control: Progress tracking for mission objectives.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, Optional


@dataclass
class MissionProgressTracker:
    total_items_collected: int = 0
    pages_since_last_increase: int = 0
    last_progress_timestamp: Optional[str] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MissionProgressTracker":
        return MissionProgressTracker(
            total_items_collected=int(data.get("total_items_collected", 0)),
            pages_since_last_increase=int(data.get("pages_since_last_increase", 0)),
            last_progress_timestamp=data.get("last_progress_timestamp")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_items_collected": self.total_items_collected,
            "pages_since_last_increase": self.pages_since_last_increase,
            "last_progress_timestamp": self.last_progress_timestamp
        }

    def update(self, items_collected_this_step: int, pages_visited: int) -> None:
        if items_collected_this_step > 0:
            self.total_items_collected += items_collected_this_step
            self.pages_since_last_increase = 0
            self.last_progress_timestamp = datetime.now(timezone.utc).isoformat()
        else:
            self.pages_since_last_increase += max(pages_visited, 1)
            if not self.last_progress_timestamp:
                self.last_progress_timestamp = datetime.now(timezone.utc).isoformat()
