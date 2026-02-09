"""
Program Registry: Groups related missions under a goal.
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


PROGRAMS_FILE = Path("outputs/phase25/programs.jsonl")


@dataclass
class Program:
    """Program that groups related missions under a goal."""
    program_id: str
    goal_id: str
    description: str
    status: str  # active | paused | completed
    mission_ids: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "program_id": self.program_id,
            "goal_id": self.goal_id,
            "description": self.description,
            "status": self.status,
            "mission_ids": self.mission_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Program:
        return Program(
            program_id=data["program_id"],
            goal_id=data["goal_id"],
            description=data["description"],
            status=data["status"],
            mission_ids=data.get("mission_ids", []),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat())
        )

    def to_signal(self) -> Dict[str, Any]:
        """Convert to learning signal format."""
        return {
            "signal_type": "program_created",
            "signal_layer": "program",
            "signal_source": "program_registry",
            "program_id": self.program_id,
            "goal_id": self.goal_id,
            "description": self.description,
            "status": self.status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class ProgramRegistry:
    """
    Registry for managing programs.
    Programs group missions but do NOT execute.
    """

    def __init__(self, programs_file: Optional[Path] = None):
        self.programs_file = programs_file or PROGRAMS_FILE
        self.programs_file.parent.mkdir(parents=True, exist_ok=True)

    def create_program(
        self,
        goal_id: str,
        description: str,
        status: str = "active"
    ) -> Program:
        """
        Create a new program under a goal.
        
        Args:
            goal_id: Parent goal ID
            description: Natural language description
            status: active | paused | completed (default: active)
        
        Returns:
            Created Program object
        """
        program = Program(
            program_id=str(uuid.uuid4()),
            goal_id=goal_id,
            description=description,
            status=status,
            mission_ids=[]
        )
        
        self._persist_program(program)
        self._emit_signal(program.to_signal())
        
        return program

    def get_program(self, program_id: str) -> Optional[Program]:
        """Retrieve program by ID."""
        programs = self._load_programs()
        for program_data in programs:
            if program_data["program_id"] == program_id:
                return Program.from_dict(program_data)
        return None

    def list_programs(
        self,
        goal_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Program]:
        """
        List programs, optionally filtered.
        
        Args:
            goal_id: Filter by parent goal
            status: Filter by status (active | paused | completed)
        
        Returns:
            List of Program objects
        """
        programs = self._load_programs()
        program_objects = [Program.from_dict(p) for p in programs]
        
        if goal_id:
            program_objects = [p for p in program_objects if p.goal_id == goal_id]
        
        if status:
            program_objects = [p for p in program_objects if p.status == status]
        
        return program_objects

    def update_program_status(
        self,
        program_id: str,
        status: str
    ) -> Optional[Program]:
        """Update program status."""
        program = self.get_program(program_id)
        if not program:
            return None
        
        program.status = status
        program.updated_at = datetime.now(timezone.utc).isoformat()
        
        self._update_program(program)
        
        return program

    def add_mission_to_program(
        self,
        program_id: str,
        mission_id: str
    ) -> Optional[Program]:
        """Link a mission to a program."""
        program = self.get_program(program_id)
        if not program:
            return None
        
        if mission_id not in program.mission_ids:
            program.mission_ids.append(mission_id)
            program.updated_at = datetime.now(timezone.utc).isoformat()
            self._update_program(program)
            
            # Emit mission_linked signal
            self._emit_signal({
                "signal_type": "mission_linked",
                "signal_layer": "program",
                "signal_source": "program_registry",
                "mission_id": mission_id,
                "program_id": program_id,
                "goal_id": program.goal_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        return program

    def get_active_program(self, goal_id: Optional[str] = None) -> Optional[Program]:
        """Get the most recently updated active program (optionally for a specific goal)."""
        active_programs = self.list_programs(goal_id=goal_id, status="active")
        if not active_programs:
            return None
        
        # Sort by updated_at descending
        active_programs.sort(key=lambda p: p.updated_at, reverse=True)
        return active_programs[0]

    def _load_programs(self) -> List[Dict[str, Any]]:
        """Load all programs from file."""
        if not self.programs_file.exists():
            return []
        
        programs = []
        with open(self.programs_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        programs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return programs

    def _persist_program(self, program: Program) -> None:
        """Append program to file."""
        with open(self.programs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(program.to_dict()) + "\n")

                                f.write(json.dumps(apply_signal_priority(signal)) + "\n")
        """Update existing program in file."""
        programs = self._load_programs()
        
        # Find and update
        for i, p in enumerate(programs):
            if p["program_id"] == program.program_id:
                programs[i] = program.to_dict()
                break
        
        # Rewrite file
        with open(self.programs_file, "w", encoding="utf-8") as f:
            for p in programs:
                f.write(json.dumps(p) + "\n")

    def _emit_signal(self, signal: Dict[str, Any]) -> None:
        """Emit signal to learning_signals.jsonl."""
        signals_file = Path("outputs/phase25/learning_signals.jsonl")
        signals_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(signals_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(signal) + "\n")
