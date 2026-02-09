"""
Phase 7: Delegation Signal Emission

Emits delegation_decision signals to the execution stream.
Signals are read-only observations, not control directives.

Signal Format:
  signal_type: "delegation_decision"
  signal_layer: "governance"
  signal_source: "delegation_engine"
  payload:
    execution_class: AI_EXECUTABLE | HUMAN_REQUIRED | COLLABORATIVE
    rationale: str
    required_human_actions: List[str]
    estimated_human_effort: int (minutes)
    is_blocked: bool
    conditions: List[str]
  mission_id: optional
  created_at: ISO timestamp

Hard constraints:
- NO execution control
- NO mission modification
- APPEND-ONLY to stream
- READ-ONLY analysis
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from backend.delegation_evaluator import DelegationEvaluator, DelegationDecision


@dataclass
class DelegationSignal:
    """A delegation governance signal."""
    signal_type: str = "delegation_decision"
    signal_layer: str = "governance"
    signal_source: str = "delegation_engine"
    execution_class: str = ""
    rationale: str = ""
    required_human_actions: List[str] = None
    estimated_human_effort: int = 0
    is_blocked: bool = False
    blocking_reason: Optional[str] = None
    conditions: List[str] = None
    mission_id: Optional[str] = None
    created_at: str = ""

    def __post_init__(self):
        """Ensure defaults."""
        if self.required_human_actions is None:
            self.required_human_actions = []
        if self.conditions is None:
            self.conditions = []
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "signal_type": self.signal_type,
            "signal_layer": self.signal_layer,
            "signal_source": self.signal_source,
            "payload": {
                "execution_class": self.execution_class,
                "rationale": self.rationale,
                "required_human_actions": self.required_human_actions,
                "estimated_human_effort": self.estimated_human_effort,
                "is_blocked": self.is_blocked,
                "blocking_reason": self.blocking_reason,
                "conditions": self.conditions,
            },
            "mission_id": self.mission_id,
            "created_at": self.created_at,
        }


class DelegationSignalEmitter:
    """
    Emits delegation signals to execution stream.
    Pure observation - does not control execution.
    """

    def __init__(self, stream_dir: Optional[str] = None):
        """Initialize signal emitter."""
        self._stream_dir = Path(stream_dir or "outputs/delegation_signals")
        self._stream_dir.mkdir(parents=True, exist_ok=True)
        self._evaluator = DelegationEvaluator()

    def emit_delegation_signal(
        self,
        task_description: str,
        mission_id: Optional[str] = None,
        stream_file: Optional[str] = None
    ) -> DelegationSignal:
        """
        Evaluate a task and emit a delegation signal.

        Args:
            task_description: Task/goal/intent description
            mission_id: Optional mission ID (not required)
            stream_file: Optional custom stream file path

        Returns:
            DelegationSignal that was emitted
        """
        # Evaluate delegation
        decision = self._evaluator.evaluate(task_description)

        # Convert to signal
        signal = DelegationSignal(
            execution_class=decision.execution_class.value,
            rationale=decision.rationale,
            required_human_actions=[a.action for a in decision.required_human_actions],
            estimated_human_effort=decision.estimated_human_effort,
            is_blocked=decision.is_blocked,
            blocking_reason=decision.blocking_reason,
            conditions=decision.conditions,
            mission_id=mission_id,
        )

        # Write to stream
        self._write_signal(signal, stream_file)

        return signal

    def emit_delegation_signal_from_dict(
        self,
        task_dict: Dict[str, Any],
        mission_id: Optional[str] = None,
        stream_file: Optional[str] = None
    ) -> DelegationSignal:
        """
        Evaluate a task from dictionary and emit signal.

        Args:
            task_dict: Task dictionary (mission, goal, build_intent, etc.)
            mission_id: Optional mission ID
            stream_file: Optional custom stream file

        Returns:
            DelegationSignal that was emitted
        """
        # Evaluate delegation
        decision = self._evaluator.evaluate_from_dict(task_dict)

        # Convert to signal
        signal = DelegationSignal(
            execution_class=decision.execution_class.value,
            rationale=decision.rationale,
            required_human_actions=[a.action for a in decision.required_human_actions],
            estimated_human_effort=decision.estimated_human_effort,
            is_blocked=decision.is_blocked,
            blocking_reason=decision.blocking_reason,
            conditions=decision.conditions,
            mission_id=mission_id,
        )

        # Write to stream
        self._write_signal(signal, stream_file)

        return signal

    def _write_signal(self, signal: DelegationSignal, stream_file: Optional[str] = None) -> None:
        """Write signal to JSONL stream (append-only)."""
        import json

        if not stream_file:
            stream_file = self._stream_dir / "delegation_signals.jsonl"
        else:
            stream_file = Path(stream_file)

        # Ensure directory exists
        stream_file.parent.mkdir(parents=True, exist_ok=True)

        # Append signal as JSON line
        with stream_file.open("a", encoding="utf-8") as f:
            json.dump(signal.to_dict(), f, ensure_ascii=False)
            f.write("\n")

    def get_signals_from_file(self, stream_file: str) -> List[DelegationSignal]:
        """Read all signals from a stream file."""
        import json

        stream_path = Path(stream_file)
        signals = []

        if stream_path.exists():
            with stream_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        # Reconstruct signal (simplified)
                        signals.append(data)

        return signals

    def get_latest_signal(self, stream_file: Optional[str] = None) -> Optional[DelegationSignal]:
        """Get the most recent signal from stream."""
        import json

        if not stream_file:
            stream_file = self._stream_dir / "delegation_signals.jsonl"
        else:
            stream_file = Path(stream_file)

        if not stream_file.exists():
            return None

        latest = None
        with stream_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    latest = json.loads(line)

        return latest
