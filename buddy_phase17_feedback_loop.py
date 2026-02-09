"""
Phase 17: Continuous Autonomous Execution - Feedback Loop

This module creates a continuous feedback loop between Phase 17 execution
and Phase 16 meta-learning, enabling real-time adaptation.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional


@dataclass
class FeedbackEvent:
    """Single feedback event from execution to meta-learning"""
    event_id: str
    event_type: str  # "task_success", "task_failure", "heuristic_applied", "confidence_update"
    task_id: str
    wave: int
    data: Dict[str, Any]
    timestamp: str


@dataclass
class LearningSignal:
    """Learning signal derived from feedback"""
    signal_id: str
    signal_type: str  # "heuristic_validation", "policy_adjustment", "risk_recalibration"
    confidence: float
    description: str
    recommendation: str
    supporting_evidence: List[str]
    timestamp: str


class FeedbackLoop:
    """
    Creates continuous feedback between execution (Phase 17) and meta-learning (Phase 16).
    Analyzes execution outcomes in real-time and generates learning signals.
    """
    
    def __init__(self, phase17_output_dir: Path, feedback_output_dir: Path):
        self.phase17_output_dir = Path(phase17_output_dir)
        self.feedback_output_dir = Path(feedback_output_dir)
        self.feedback_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_events: List[FeedbackEvent] = []
        self.learning_signals: List[LearningSignal] = []
        
        self.execution_outcomes = []
        self.heuristic_performance = {}
    
    def load_execution_outcomes(self) -> int:
        """Load execution outcomes from Phase 17"""
        outcomes_file = self.phase17_output_dir / "execution_outcomes.jsonl"
        
        if not outcomes_file.exists():
            raise FileNotFoundError(f"Execution outcomes not found: {outcomes_file}")
        
        with open(outcomes_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.execution_outcomes.append(json.loads(line))
        
        return len(self.execution_outcomes)
    
    def analyze_heuristic_effectiveness(self) -> Dict[str, Dict[str, Any]]:
        """Analyze how effective each heuristic was during execution"""
        print("\n=== Analyzing Heuristic Effectiveness ===")
        
        # Track performance by heuristic
        heuristic_stats = {}
        
        for outcome in self.execution_outcomes:
            for heuristic_id in outcome.get('heuristics_applied', []):
                if heuristic_id not in heuristic_stats:
                    heuristic_stats[heuristic_id] = {
                        "applications": 0,
                        "successes": 0,
                        "failures": 0,
                        "total_confidence_delta": 0.0,
                        "avg_confidence_delta": 0.0,
                        "success_rate": 0.0
                    }
                
                stats = heuristic_stats[heuristic_id]
                stats["applications"] += 1
                stats["total_confidence_delta"] += outcome["confidence_delta"]
                
                if outcome["status"] == "success":
                    stats["successes"] += 1
                else:
                    stats["failures"] += 1
        
        # Calculate averages and rates
        for heuristic_id, stats in heuristic_stats.items():
            if stats["applications"] > 0:
                stats["avg_confidence_delta"] = stats["total_confidence_delta"] / stats["applications"]
                stats["success_rate"] = stats["successes"] / stats["applications"]
                
                print(f"  {heuristic_id}: {stats['applications']} applications, "
                      f"{stats['success_rate']:.1%} success, "
                      f"avg Δconf: {stats['avg_confidence_delta']:+.4f}")
        
        self.heuristic_performance = heuristic_stats
        return heuristic_stats
    
    def generate_feedback_events(self) -> int:
        """Generate feedback events from execution outcomes"""
        event_count = 0
        
        for outcome in self.execution_outcomes:
            # Task completion event
            event_type = "task_success" if outcome["status"] == "success" else "task_failure"
            event = FeedbackEvent(
                event_id=f"evt_{outcome['task_id']}_{event_count}",
                event_type=event_type,
                task_id=outcome["task_id"],
                wave=outcome["wave"],
                data={
                    "initial_confidence": outcome["initial_confidence"],
                    "final_confidence": outcome["final_confidence"],
                    "confidence_delta": outcome["confidence_delta"],
                    "execution_time_ms": outcome["execution_time_ms"],
                    "attempts": outcome["attempts"],
                    "heuristics_applied": outcome["heuristics_applied"]
                },
                timestamp=outcome["timestamp"]
            )
            self.feedback_events.append(event)
            event_count += 1
            
            # Heuristic application events
            for heuristic_id in outcome.get('heuristics_applied', []):
                event = FeedbackEvent(
                    event_id=f"evt_heuristic_{heuristic_id}_{event_count}",
                    event_type="heuristic_applied",
                    task_id=outcome["task_id"],
                    wave=outcome["wave"],
                    data={
                        "heuristic_id": heuristic_id,
                        "task_status": outcome["status"],
                        "confidence_impact": outcome["confidence_delta"]
                    },
                    timestamp=outcome["timestamp"]
                )
                self.feedback_events.append(event)
                event_count += 1
        
        return event_count
    
    def generate_learning_signals(self) -> int:
        """Generate learning signals for Phase 16 meta-learning"""
        print("\n=== Generating Learning Signals ===")
        signal_count = 0
        
        # Signal 1: Validate successful heuristics
        for heuristic_id, stats in self.heuristic_performance.items():
            if stats["success_rate"] >= 0.8 and stats["applications"] >= 3:
                signal = LearningSignal(
                    signal_id=f"signal_{signal_count:03d}",
                    signal_type="heuristic_validation",
                    confidence=stats["success_rate"],
                    description=f"Heuristic {heuristic_id} validated with {stats['success_rate']:.1%} success rate",
                    recommendation=f"Continue using {heuristic_id} in future planning",
                    supporting_evidence=[
                        f"{stats['applications']} applications",
                        f"{stats['successes']} successes",
                        f"Avg confidence Δ: {stats['avg_confidence_delta']:+.4f}"
                    ],
                    timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                )
                self.learning_signals.append(signal)
                signal_count += 1
                print(f"  ✓ Validated: {heuristic_id} ({stats['success_rate']:.1%})")
        
        # Signal 2: Identify underperforming heuristics
        for heuristic_id, stats in self.heuristic_performance.items():
            if stats["success_rate"] < 0.6 and stats["applications"] >= 3:
                signal = LearningSignal(
                    signal_id=f"signal_{signal_count:03d}",
                    signal_type="policy_adjustment",
                    confidence=1.0 - stats["success_rate"],
                    description=f"Heuristic {heuristic_id} underperforming at {stats['success_rate']:.1%}",
                    recommendation=f"Re-evaluate or disable {heuristic_id}; consider parameter tuning",
                    supporting_evidence=[
                        f"{stats['applications']} applications",
                        f"{stats['failures']} failures",
                        f"Low success rate: {stats['success_rate']:.1%}"
                    ],
                    timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                )
                self.learning_signals.append(signal)
                signal_count += 1
                print(f"  ⚠ Underperforming: {heuristic_id} ({stats['success_rate']:.1%})")
        
        # Signal 3: Analyze confidence trajectory patterns
        positive_deltas = [o["confidence_delta"] for o in self.execution_outcomes if o["confidence_delta"] > 0]
        negative_deltas = [o["confidence_delta"] for o in self.execution_outcomes if o["confidence_delta"] < 0]
        
        if len(positive_deltas) > len(negative_deltas):
            avg_positive = sum(positive_deltas) / len(positive_deltas) if positive_deltas else 0
            signal = LearningSignal(
                signal_id=f"signal_{signal_count:03d}",
                signal_type="risk_recalibration",
                confidence=0.85,
                description="Overall positive confidence trajectory detected",
                recommendation="Consider relaxing risk thresholds for next wave to increase task throughput",
                supporting_evidence=[
                    f"{len(positive_deltas)} positive confidence deltas",
                    f"Avg positive Δ: {avg_positive:+.4f}",
                    f"Only {len(negative_deltas)} negative deltas"
                ],
                timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            )
            self.learning_signals.append(signal)
            signal_count += 1
            print(f"  ✓ Positive trajectory: Consider relaxing thresholds")
        
        # Signal 4: Retry effectiveness
        retry_outcomes = [o for o in self.execution_outcomes if o["attempts"] > 1]
        if retry_outcomes:
            retry_successes = [o for o in retry_outcomes if o["status"] == "success"]
            retry_rate = len(retry_successes) / len(retry_outcomes)
            
            signal = LearningSignal(
                signal_id=f"signal_{signal_count:03d}",
                signal_type="heuristic_validation",
                confidence=retry_rate,
                description=f"Retry strategy effectiveness: {retry_rate:.1%}",
                recommendation="Continue retry policy with current parameters" if retry_rate > 0.5 
                             else "Adjust retry confidence penalty or max attempts",
                supporting_evidence=[
                    f"{len(retry_outcomes)} retried tasks",
                    f"{len(retry_successes)} retry successes",
                    f"Retry success rate: {retry_rate:.1%}"
                ],
                timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            )
            self.learning_signals.append(signal)
            signal_count += 1
            print(f"  ✓ Retry effectiveness: {retry_rate:.1%}")
        
        return signal_count
    
    def write_feedback(self):
        """Write feedback events and learning signals to output files"""
        # Write feedback events
        events_file = self.feedback_output_dir / "feedback_events.jsonl"
        with open(events_file, 'w', encoding='utf-8') as f:
            for event in self.feedback_events:
                event_dict = {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "task_id": event.task_id,
                    "wave": event.wave,
                    "data": event.data,
                    "timestamp": event.timestamp
                }
                f.write(json.dumps(event_dict) + '\n')
        
        # Write learning signals
        signals_file = self.feedback_output_dir / "learning_signals.jsonl"
        with open(signals_file, 'w', encoding='utf-8') as f:
            for signal in self.learning_signals:
                signal_dict = {
                    "signal_id": signal.signal_id,
                    "signal_type": signal.signal_type,
                    "confidence": signal.confidence,
                    "description": signal.description,
                    "recommendation": signal.recommendation,
                    "supporting_evidence": signal.supporting_evidence,
                    "timestamp": signal.timestamp
                }
                f.write(json.dumps(signal_dict) + '\n')
        
        # Write heuristic performance summary
        perf_file = self.feedback_output_dir / "heuristic_performance.json"
        with open(perf_file, 'w', encoding='utf-8') as f:
            json.dump(self.heuristic_performance, f, indent=2)
        
        print(f"\n✓ Feedback written to {self.feedback_output_dir}")
    
    def create_feedback_loop_summary(self) -> Dict[str, Any]:
        """Create comprehensive feedback loop summary"""
        return {
            "feedback_events_generated": len(self.feedback_events),
            "learning_signals_generated": len(self.learning_signals),
            "heuristics_analyzed": len(self.heuristic_performance),
            "execution_outcomes_processed": len(self.execution_outcomes),
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }


def main():
    """Main feedback loop execution"""
    phase17_output_dir = Path("outputs/phase17")
    feedback_output_dir = Path("outputs/phase17")
    
    print(f"\n{'='*70}")
    print(f"Phase 17: Feedback Loop Analysis")
    print(f"{'='*70}")
    
    feedback_loop = FeedbackLoop(phase17_output_dir, feedback_output_dir)
    
    # Load execution outcomes
    num_outcomes = feedback_loop.load_execution_outcomes()
    print(f"Loaded {num_outcomes} execution outcomes")
    
    # Analyze heuristic effectiveness
    feedback_loop.analyze_heuristic_effectiveness()
    
    # Generate feedback events
    num_events = feedback_loop.generate_feedback_events()
    print(f"\nGenerated {num_events} feedback events")
    
    # Generate learning signals
    num_signals = feedback_loop.generate_learning_signals()
    print(f"Generated {num_signals} learning signals")
    
    # Write feedback
    feedback_loop.write_feedback()
    
    # Summary
    summary = feedback_loop.create_feedback_loop_summary()
    print(f"\n{'='*70}")
    print(f"Feedback Loop Summary:")
    print(f"  Feedback Events: {summary['feedback_events_generated']}")
    print(f"  Learning Signals: {summary['learning_signals_generated']}")
    print(f"  Heuristics Analyzed: {summary['heuristics_analyzed']}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
