"""
Phase 8: Tradeoff Signal Emitter

Emits economic tradeoff signals to execution stream (JSONL append-only).

Signal Format:
  signal_type: "economic_tradeoff"
  signal_layer: "economic"
  signal_source: "tradeoff_engine"
  payload:
    decision: PROCEED | PAUSE | REJECT
    adjusted_value: float
    roi_ratio: float
    opportunity_cost_score: float
    cognitive_load: str
    value_type: str
    rationale: str
    key_factors: List[str]
  work_id: optional
  created_at: ISO timestamp

Hard constraints:
- NO autonomy (advisory only)
- NO auto-escalation
- NO mission killing
- READ-ONLY observation
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import json

from Back_End.tradeoff_evaluator import TradeoffEvaluator, TradeoffOpportunity, TradeoffScore


@dataclass
class TradeoffSignal:
    """A tradeoff governance signal."""
    signal_type: str = "economic_tradeoff"
    signal_layer: str = "economic"
    signal_source: str = "tradeoff_engine"
    decision: str = ""
    adjusted_value: float = 0.0
    roi_ratio: float = 0.0
    opportunity_cost_score: float = 0.0
    cognitive_load: str = ""
    value_type: str = ""
    rationale: str = ""
    key_factors: List[str] = None
    work_id: Optional[str] = None
    created_at: str = ""

    def __post_init__(self):
        """Ensure defaults."""
        if self.key_factors is None:
            self.key_factors = []
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "signal_type": self.signal_type,
            "signal_layer": self.signal_layer,
            "signal_source": self.signal_source,
            "payload": {
                "decision": self.decision,
                "adjusted_value": self.adjusted_value,
                "roi_ratio": self.roi_ratio,
                "opportunity_cost_score": self.opportunity_cost_score,
                "cognitive_load": self.cognitive_load,
                "value_type": self.value_type,
                "rationale": self.rationale,
                "key_factors": self.key_factors,
            },
            "work_id": self.work_id,
            "created_at": self.created_at,
        }


class TradeoffSignalEmitter:
    """
    Emits tradeoff signals to execution stream.
    Pure observation - does not control execution.
    """

    def __init__(self, stream_dir: Optional[str] = None):
        """Initialize signal emitter."""
        self._stream_dir = Path(stream_dir or "outputs/tradeoff_signals")
        self._stream_dir.mkdir(parents=True, exist_ok=True)
        self._evaluator = TradeoffEvaluator()

    def emit_tradeoff_signal(
        self,
        opportunity: TradeoffOpportunity,
        work_id: Optional[str] = None,
        stream_file: Optional[str] = None
    ) -> TradeoffSignal:
        """
        Evaluate opportunity and emit tradeoff signal.

        Args:
            opportunity: TradeoffOpportunity to evaluate
            work_id: Optional work/opportunity identifier
            stream_file: Optional custom stream file path

        Returns:
            TradeoffSignal that was emitted
        """
        # Evaluate tradeoff
        score = self._evaluator.evaluate(opportunity)

        # Convert to signal
        signal = TradeoffSignal(
            decision=score.decision.value,
            adjusted_value=score.adjusted_value,
            roi_ratio=score.roi_ratio,
            opportunity_cost_score=score.opportunity_cost_score,
            cognitive_load=score.cognitive_load.value,
            value_type=score.value_type.value,
            rationale=score.rationale,
            key_factors=score.key_factors,
            work_id=work_id,
        )

        # Write to stream
        self._write_signal(signal, stream_file)

        return signal

    def emit_batch_signals(
        self,
        opportunities: List[TradeoffOpportunity],
        stream_file: Optional[str] = None
    ) -> List[TradeoffSignal]:
        """
        Emit signals for multiple opportunities.

        Args:
            opportunities: List of TradeoffOpportunity
            stream_file: Optional custom stream file

        Returns:
            List of TradeoffSignal emitted
        """
        signals = []
        scores = self._evaluator.evaluate_multiple(opportunities)

        for score, opp in zip(scores, [o for o in opportunities]):
            signal = TradeoffSignal(
                decision=score.decision.value,
                adjusted_value=score.adjusted_value,
                roi_ratio=score.roi_ratio,
                opportunity_cost_score=score.opportunity_cost_score,
                cognitive_load=score.cognitive_load.value,
                value_type=score.value_type.value,
                rationale=score.rationale,
                key_factors=score.key_factors,
                work_id=opp.name,
            )
            self._write_signal(signal, stream_file)
            signals.append(signal)

        return signals

    def _write_signal(self, signal: TradeoffSignal, stream_file: Optional[str] = None) -> None:
        """Write signal to JSONL stream (append-only)."""
        if not stream_file:
            stream_file = self._stream_dir / "tradeoff_signals.jsonl"
        else:
            stream_file = Path(stream_file)

        # Ensure directory exists
        stream_file.parent.mkdir(parents=True, exist_ok=True)

        # Append signal as JSON line
        with stream_file.open("a", encoding="utf-8") as f:
            json.dump(signal.to_dict(), f, ensure_ascii=False)
            f.write("\n")

    def get_signals_from_file(self, stream_file: str) -> List[Dict[str, Any]]:
        """Read all signals from a stream file."""
        stream_path = Path(stream_file)
        signals = []

        if stream_path.exists():
            with stream_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        signals.append(data)

        return signals

    def get_latest_signal(self, stream_file: Optional[str] = None) -> Optional[TradeoffSignal]:
        """Get the most recent signal from stream."""
        if not stream_file:
            stream_file = self._stream_dir / "tradeoff_signals.jsonl"
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

    def get_proceed_opportunities(
        self,
        opportunities: List[TradeoffOpportunity]
    ) -> List[tuple]:
        """
        Filter opportunities recommended to proceed.

        Returns:
            List of (TradeoffOpportunity, TradeoffScore) tuples sorted by value
        """
        scores = self._evaluator.evaluate_multiple(opportunities)
        result = []
        
        for score, opp in zip(scores, sorted(opportunities, key=lambda o: o.name)):
            if score.decision.value == "PROCEED":
                result.append((opp, score))
        
        return result

