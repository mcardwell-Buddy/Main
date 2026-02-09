"""
Goal Registry: Long-lived objectives that group programs.
Phase 3 Step 2.75: Pure structure, no execution logic.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.learning.signal_priority import apply_signal_priority
from pathlib import Path
from typing import Any, Dict, List, Optional


GOALS_FILE = Path("outputs/phase25/goals.jsonl")


@dataclass
class Goal:
    """Long-lived objective that groups related programs."""
    goal_id: str
    description: str
    created_at: str
    status: str  # active | paused | completed
    program_ids: List[str] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "created_at": self.created_at,
            "status": self.status,
            "program_ids": self.program_ids,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Goal:
        return Goal(
            goal_id=data["goal_id"],
            description=data["description"],
            created_at=data["created_at"],
            status=data["status"],
            program_ids=data.get("program_ids", []),
            updated_at=data.get("updated_at", data["created_at"])
        )

    def to_signal(self) -> Dict[str, Any]:
        """Convert to learning signal format."""
        return {
            "signal_type": "goal_created",
            "signal_layer": "goal",
            "signal_source": "goal_registry",
            "goal_id": self.goal_id,
            "description": self.description,
            "status": self.status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class GoalRegistry:
    """
    Registry for managing goals.
    Goals are long-lived and do NOT execute.
    """

    def __init__(self, goals_file: Optional[Path] = None):
        self.goals_file = goals_file or GOALS_FILE
        self.goals_file.parent.mkdir(parents=True, exist_ok=True)

    def create_goal(
        self,
        description: str,
        status: str = "active"
    ) -> Goal:
        """
        Create a new goal.
        
        Args:
            description: Natural language description of the goal
            status: active | paused | completed (default: active)
        
        Returns:
            Created Goal object
        """
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            description=description,
            created_at=datetime.now(timezone.utc).isoformat(),
            status=status,
            program_ids=[]
        )
        
        self._persist_goal(goal)
        self._emit_signal(goal.to_signal())
        
        return goal

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Retrieve goal by ID."""
        goals = self._load_goals()
        for goal_data in goals:
            if goal_data["goal_id"] == goal_id:
                return Goal.from_dict(goal_data)
        return None

    def list_goals(self, status: Optional[str] = None) -> List[Goal]:
        """
        List all goals, optionally filtered by status.
        
        Args:
            status: Filter by status (active | paused | completed)
        
        Returns:
            List of Goal objects
        """
        goals = self._load_goals()
        goal_objects = [Goal.from_dict(g) for g in goals]
        
        if status:
            goal_objects = [g for g in goal_objects if g.status == status]
        
        return goal_objects

    def update_goal_status(self, goal_id: str, status: str) -> Optional[Goal]:
        """Update goal status."""
        goal = self.get_goal(goal_id)
        if not goal:
            return None
        
        goal.status = status
        goal.updated_at = datetime.now(timezone.utc).isoformat()
        
        self._update_goal(goal)
        
        return goal

    def add_program_to_goal(self, goal_id: str, program_id: str) -> Optional[Goal]:
        """Link a program to a goal."""
        goal = self.get_goal(goal_id)
        if not goal:
            return None
        
        if program_id not in goal.program_ids:
            goal.program_ids.append(program_id)
            goal.updated_at = datetime.now(timezone.utc).isoformat()
            self._update_goal(goal)
        
        return goal

    def get_active_goal(self) -> Optional[Goal]:
        """Get the most recently updated active goal."""
        active_goals = self.list_goals(status="active")
        if not active_goals:
            return None
        
        # Sort by updated_at descending
        active_goals.sort(key=lambda g: g.updated_at, reverse=True)
        return active_goals[0]

    def _load_goals(self) -> List[Dict[str, Any]]:
        """Load all goals from file."""
        if not self.goals_file.exists():
            return []
        
        goals = []
        with open(self.goals_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        goals.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return goals

    def _persist_goal(self, goal: Goal) -> None:
        """Append goal to file."""
        with open(self.goals_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(goal.to_dict()) + "\n")

                                f.write(json.dumps(apply_signal_priority(signal)) + "\n")
        """Update existing goal in file."""
        goals = self._load_goals()
        
        # Find and update
        for i, g in enumerate(goals):
            if g["goal_id"] == goal.goal_id:
                goals[i] = goal.to_dict()
                break
        
        # Rewrite file
        with open(self.goals_file, "w", encoding="utf-8") as f:
            for g in goals:
                f.write(json.dumps(g) + "\n")

    def _emit_signal(self, signal: Dict[str, Any]) -> None:
        """Emit signal to learning_signals.jsonl."""
        signals_file = Path("outputs/phase25/learning_signals.jsonl")
        signals_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(signals_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(signal) + "\n")
