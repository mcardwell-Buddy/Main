"""
Phase 11: Build Signal Emitter

Emits build-level signals to learning_signals.jsonl (append-only).
Signals are read-only observations, not control directives.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

from backend.build_contract import BuildContract, BuildStage
from backend.build_stage_evaluator import BuildStageEvaluation


@dataclass(frozen=True)
class BuildSignal:
    """Immutable build signal."""
    signal_type: str
    signal_layer: str = "build"
    signal_source: str = "build_module"
    payload: Dict[str, Any] = None
    build_id: Optional[str] = None
    created_at: str = ""


class BuildSignalEmitter:
    """Emit build-level signals to JSONL stream."""

    @staticmethod
    def emit_build_created(
        build: BuildContract,
        stream_file: Optional[Path] = None,
    ) -> BuildSignal:
        signal = BuildSignal(
            signal_type="build_created",
            payload={
                "build_id": build.build_id,
                "name": build.name,
                "objective": build.objective,
                "build_type": build.build_type.value,
                "current_stage": build.current_stage.value,
                "status": build.status.value,
                "investment_score": build.investment_score,
                "mission_ids": list(build.mission_ids),
                "artifact_ids": list(build.artifact_ids),
            },
            build_id=build.build_id,
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        BuildSignalEmitter._write_signal(signal, stream_file)
        return signal

    @staticmethod
    def emit_build_stage_evaluated(
        evaluation: BuildStageEvaluation,
        stream_file: Optional[Path] = None,
    ) -> BuildSignal:
        signal = BuildSignal(
            signal_type="build_stage_evaluated",
            payload={
                "build_id": evaluation.build_id,
                "current_stage": evaluation.current_stage.value,
                "next_stage": evaluation.next_stage.value if evaluation.next_stage else None,
                "is_ready": evaluation.is_ready,
                "readiness_score": evaluation.readiness_score,
                "blocking_reasons": evaluation.blocking_reasons,
                "satisfied_requirements": evaluation.satisfied_requirements,
            },
            build_id=evaluation.build_id,
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        BuildSignalEmitter._write_signal(signal, stream_file)
        return signal

    @staticmethod
    def emit_build_stage_ready(
        build_id: str,
        current_stage: BuildStage,
        next_stage: BuildStage,
        stream_file: Optional[Path] = None,
    ) -> BuildSignal:
        signal = BuildSignal(
            signal_type="build_stage_ready",
            payload={
                "build_id": build_id,
                "current_stage": current_stage.value,
                "next_stage": next_stage.value,
            },
            build_id=build_id,
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        BuildSignalEmitter._write_signal(signal, stream_file)
        return signal

    @staticmethod
    def emit_build_completed(
        build_id: str,
        stream_file: Optional[Path] = None,
    ) -> BuildSignal:
        signal = BuildSignal(
            signal_type="build_completed",
            payload={"build_id": build_id},
            build_id=build_id,
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        BuildSignalEmitter._write_signal(signal, stream_file)
        return signal

    @staticmethod
    def emit_build_blocked(
        build_id: str,
        current_stage: BuildStage,
        reasons: List[str],
        stream_file: Optional[Path] = None,
    ) -> BuildSignal:
        signal = BuildSignal(
            signal_type="build_blocked",
            payload={
                "build_id": build_id,
                "current_stage": current_stage.value,
                "blocking_reasons": reasons,
            },
            build_id=build_id,
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        BuildSignalEmitter._write_signal(signal, stream_file)
        return signal

    @staticmethod
    def _write_signal(signal: BuildSignal, stream_file: Optional[Path]) -> None:
        """Append signal to learning_signals.jsonl."""
        if stream_file is None:
            stream_file = Path("outputs/phase25/learning_signals.jsonl")
        stream_file.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(signal)
        if data.get("payload") is None:
            data["payload"] = {}

        with stream_file.open("a", encoding="utf-8") as f:
            json.dump(data, f)
            f.write("\n")

    @staticmethod
    def get_signals_from_file(stream_file: Path) -> List[Dict[str, Any]]:
        """Read signals from JSONL file."""
        if not stream_file.exists():
            return []
        signals = []
        with stream_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    signals.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return signals
