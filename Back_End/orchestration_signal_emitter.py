"""
Phase 9: Orchestration Signal Emitter

Emits mission prioritization signals to execution stream (JSONL append-only).

Signal Format:
  signal_type: "mission_prioritization"
  signal_layer: "orchestration"
  signal_source: "mission_orchestrator"
  payload:
    active_mission_id: optional
    queued_missions: List[mission_id]
    paused_missions: List[mission_id]
    budget_used_pct: int
    fatigue_state: str
    top_priorities: List[{mission_id, rank, score, reason}]
    deferred_good_ideas: List[mission_id]
  created_at: ISO timestamp

Hard constraints:
- NO autonomy (signal only)
- NO auto-execution
- READ-ONLY observation
- JSONL append-only (immutable log)
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json

from Back_End.mission_orchestrator import (
    MissionOrchestrator, MissionEntry, MissionPriority, MissionStatus
)
from Back_End.fatigue_model import FatigueScore


@dataclass(frozen=True)
class MissionPrioritizationSignal:
    """An orchestration mission prioritization signal."""
    signal_type: str = "mission_prioritization"
    signal_layer: str = "orchestration"
    signal_source: str = "mission_orchestrator"
    
    # Payload
    active_mission_id: Optional[str] = None
    queued_count: int = 0
    paused_count: int = 0
    budget_used_pct: int = 0
    fatigue_state: str = ""
    
    # Prioritization details
    top_priority_rank_1: Optional[str] = None
    top_priority_rank_2: Optional[str] = None
    top_priority_rank_3: Optional[str] = None
    
    # Summary
    total_queued_effort_minutes: int = 0
    total_paused_effort_minutes: int = 0
    recommendation: str = ""
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    work_id: Optional[str] = None


class OrchestrationSignalEmitter:
    """Emits mission prioritization signals to JSONL stream."""
    
    @staticmethod
    def emit_prioritization_signal(
        orchestrator: MissionOrchestrator,
        fatigue_score: FatigueScore,
        priorities: List[MissionPriority],
        work_id: Optional[str] = None,
        stream_file: Optional[Path] = None
    ) -> MissionPrioritizationSignal:
        """
        Emit a prioritization signal.
        
        Returns:
            MissionPrioritizationSignal
        """
        active_mission = orchestrator.get_active_mission()
        active_id = active_mission.mission_id if active_mission else None
        
        queued = orchestrator.get_missions_by_status(MissionStatus.QUEUED)
        paused = orchestrator.get_missions_by_status(MissionStatus.PAUSED)
        
        # Top 3 priorities
        top_ranks = [None, None, None]
        for priority in priorities[:3]:
            if priority.rank <= 3:
                top_ranks[priority.rank - 1] = priority.mission_id
        
        signal = MissionPrioritizationSignal(
            active_mission_id=active_id,
            queued_count=len(queued),
            paused_count=len(paused),
            budget_used_pct=int(fatigue_score.exhaustion_ratio * 100),
            fatigue_state=fatigue_score.state.value,
            top_priority_rank_1=top_ranks[0],
            top_priority_rank_2=top_ranks[1],
            top_priority_rank_3=top_ranks[2],
            total_queued_effort_minutes=sum(m.estimated_effort_minutes for m in queued),
            total_paused_effort_minutes=sum(m.estimated_effort_minutes for m in paused),
            recommendation=fatigue_score.recommendation,
            work_id=work_id,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        
        if stream_file:
            OrchestrationSignalEmitter._write_signal(signal, stream_file)
        
        return signal
    
    @staticmethod
    def emit_batch_signals(
        orchestrators: Dict[str, MissionOrchestrator],
        fatigue_scores: Dict[str, FatigueScore],
        priorities_map: Dict[str, List[MissionPriority]],
        stream_file: Optional[Path] = None
    ) -> List[MissionPrioritizationSignal]:
        """
        Emit multiple prioritization signals.
        
        Returns:
            List of MissionPrioritizationSignal
        """
        signals = []
        
        for work_id, orchestrator in orchestrators.items():
            fatigue = fatigue_scores.get(work_id)
            priorities = priorities_map.get(work_id, [])
            
            if fatigue is None:
                continue
            
            signal = OrchestrationSignalEmitter.emit_prioritization_signal(
                orchestrator, fatigue, priorities, work_id, stream_file
            )
            signals.append(signal)
        
        return signals
    
    @staticmethod
    def _write_signal(
        signal: MissionPrioritizationSignal,
        stream_file: Path
    ) -> None:
        """Write signal to JSONL file (append-only)."""
        stream_file.parent.mkdir(parents=True, exist_ok=True)
        
        signal_dict = asdict(signal)
        
        with open(stream_file, "a", encoding="utf-8") as f:
            json.dump(signal_dict, f)
            f.write("\n")
    
    @staticmethod
    def get_signals_from_file(stream_file: Path) -> List[MissionPrioritizationSignal]:
        """Read all signals from JSONL file."""
        if not stream_file.exists():
            return []
        
        signals = []
        with open(stream_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    signals.append(MissionPrioritizationSignal(**data))
        
        return signals
    
    @staticmethod
    def get_latest_signal(stream_file: Path) -> Optional[MissionPrioritizationSignal]:
        """Get most recent signal from file."""
        signals = OrchestrationSignalEmitter.get_signals_from_file(stream_file)
        return signals[-1] if signals else None
    
    @staticmethod
    def get_signals_for_work(
        stream_file: Path,
        work_id: str
    ) -> List[MissionPrioritizationSignal]:
        """Get all signals for a specific work ID."""
        all_signals = OrchestrationSignalEmitter.get_signals_from_file(stream_file)
        return [s for s in all_signals if s.work_id == work_id]
    
    @staticmethod
    def emit_pause_advisory(
        mission_id: str,
        reason: str,
        expected_resumption: str = "Later",
        work_id: Optional[str] = None,
        stream_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Emit a signal about pausing/deferring a mission.
        
        Returns:
            Advisory record (advisory only, not binding)
        """
        advisory = {
            "signal_type": "mission_pause_advisory",
            "signal_layer": "orchestration",
            "signal_source": "mission_orchestrator",
            "mission_id": mission_id,
            "reason": reason,
            "expected_resumption": expected_resumption,
            "note": "This is advisory - human can override",
            "work_id": work_id,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        if stream_file:
            stream_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stream_file, "a", encoding="utf-8") as f:
                json.dump(advisory, f)
                f.write("\n")
        
        return advisory

