"""
Phase 10: Investment Signal Emitter

Emits investment evaluation signals to learning_signals.jsonl (append-only).

Signal Format:
  signal_type: "investment_evaluation"
  signal_layer: "economic"
  signal_source: "investment_core"
  payload: Complete investment analysis

Hard constraints:
- NO autonomy (signal only)
- NO auto-execution
- READ-ONLY observation
- JSONL append-only (immutable log)
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json

from Back_End.investment_core import (
    InvestmentCandidate, InvestmentScore, InvestmentCore
)


@dataclass(frozen=True)
class InvestmentEvaluationSignal:
    """An immutable investment evaluation signal."""
    signal_type: str = "investment_evaluation"
    signal_layer: str = "economic"
    signal_source: str = "investment_core"
    
    # Core evaluation data
    candidate_id: str = ""
    candidate_type: str = ""
    description: str = ""
    
    # Scores and metrics
    investment_score: float = 0.0
    expected_return: float = 0.0
    estimated_cost: float = 0.0
    risk_adjusted: float = 0.0
    risk_band: str = ""
    
    # Recommendation
    recommendation: str = ""
    confidence: float = 0.0
    
    # Context
    time_horizon_impact: str = ""
    reusability_multiplier: float = 1.0
    
    # Reasoning
    reasoning: List[str] = None
    
    # Metadata
    created_at: str = ""
    mission_id: Optional[str] = None


class InvestmentSignalEmitter:
    """Emits investment evaluation signals to JSONL stream."""
    
    @staticmethod
    def emit_investment_signal(
        score: InvestmentScore,
        candidate: InvestmentCandidate,
        mission_id: Optional[str] = None,
        stream_file: Optional[Path] = None
    ) -> InvestmentEvaluationSignal:
        """
        Emit an investment evaluation signal.
        
        Returns:
            InvestmentEvaluationSignal
        """
        signal = InvestmentEvaluationSignal(
            candidate_id=score.candidate_id,
            candidate_type=score.candidate_type.value,
            description=candidate.description,
            investment_score=score.investment_score,
            expected_return=score.expected_return,
            estimated_cost=score.estimated_cost,
            risk_adjusted=score.risk_adjusted,
            risk_band=score.risk_band.value,
            recommendation=score.recommendation.value,
            confidence=score.confidence,
            time_horizon_impact=score.time_horizon_impact,
            reusability_multiplier=score.reusability_multiplier,
            reasoning=score.reasoning,
            created_at=datetime.utcnow().isoformat() + "Z",
            mission_id=mission_id or candidate.mission_id
        )
        
        if stream_file:
            InvestmentSignalEmitter._write_signal(signal, stream_file)
        
        return signal
    
    @staticmethod
    def emit_batch_signals(
        scores: List[InvestmentScore],
        candidates_map: Dict[str, InvestmentCandidate],
        stream_file: Optional[Path] = None
    ) -> List[InvestmentEvaluationSignal]:
        """
        Emit multiple investment evaluation signals.
        
        Returns:
            List of InvestmentEvaluationSignal
        """
        signals = []
        
        for score in scores:
            candidate = candidates_map.get(score.candidate_id)
            if candidate is None:
                continue
            
            signal = InvestmentSignalEmitter.emit_investment_signal(
                score, candidate, stream_file=stream_file
            )
            signals.append(signal)
        
        return signals
    
    @staticmethod
    def _write_signal(
        signal: InvestmentEvaluationSignal,
        stream_file: Path
    ) -> None:
        """Write signal to JSONL file (append-only)."""
        stream_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict, handling None values
        signal_dict = asdict(signal)
        
        with open(stream_file, "a", encoding="utf-8") as f:
            json.dump(signal_dict, f)
            f.write("\n")
    
    @staticmethod
    def get_signals_from_file(stream_file: Path) -> List[InvestmentEvaluationSignal]:
        """Read all signals from JSONL file."""
        if not stream_file.exists():
            return []
        
        signals = []
        with open(stream_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    # Convert to dataclass (handling reasoning list)
                    signals.append(InvestmentEvaluationSignal(**data))
        
        return signals
    
    @staticmethod
    def get_latest_signal(stream_file: Path) -> Optional[InvestmentEvaluationSignal]:
        """Get most recent signal from file."""
        signals = InvestmentSignalEmitter.get_signals_from_file(stream_file)
        return signals[-1] if signals else None
    
    @staticmethod
    def get_signals_for_candidate(
        stream_file: Path,
        candidate_id: str
    ) -> List[InvestmentEvaluationSignal]:
        """Get all signals for a specific candidate."""
        all_signals = InvestmentSignalEmitter.get_signals_from_file(stream_file)
        return [s for s in all_signals if s.candidate_id == candidate_id]
    
    @staticmethod
    def get_recommended_signals(
        stream_file: Path
    ) -> List[InvestmentEvaluationSignal]:
        """Get all signals with buy recommendations."""
        all_signals = InvestmentSignalEmitter.get_signals_from_file(stream_file)
        return [s for s in all_signals if s.recommendation in ["buy", "strong_buy"]]
    
    @staticmethod
    def emit_portfolio_summary(
        core: InvestmentCore,
        stream_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Emit a portfolio analysis summary (not a individual signal).
        
        Returns advisory summary only - never executes.
        """
        analysis = core.get_portfolio_analysis()
        
        summary = {
            "signal_type": "investment_portfolio_analysis",
            "signal_layer": "economic",
            "signal_source": "investment_core",
            "total_candidates": analysis.get("total_candidates", 0),
            "recommended_count": analysis.get("recommended", 0),
            "high_risk_count": analysis.get("high_risk", 0),
            "average_score": analysis.get("average_score", 0.0),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "note": "This is advisory analysis only. No actions taken."
        }
        
        if stream_file:
            stream_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stream_file, "a", encoding="utf-8") as f:
                json.dump(summary, f)
                f.write("\n")
        
        return summary

