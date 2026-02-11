"""
Phase 14: Meta-Learning Engine

Analyzes Phase 12 & 13 execution patterns to extract operational heuristics,
detect success/failure patterns, and propose policy optimizations.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple
from pathlib import Path
from collections import defaultdict
import statistics


@dataclass
class MetaInsight:
    """Meta-learning insight from execution patterns."""
    insight_type: str  # "success_pattern", "failure_pattern", "confidence_drift", "policy_optimization"
    description: str
    confidence: float
    supporting_evidence: List[str]
    recommendation: str
    frequency: int
    affected_tasks: List[str]


@dataclass
class OperationalHeuristic:
    """Extracted heuristic for task planning."""
    heuristic_id: str
    category: str  # "risk_assessment", "confidence_calibration", "task_sequencing", "rollback_prevention"
    rule: str
    applicability: str  # "universal", "low_risk", "medium_risk", "high_risk"
    confidence: float
    supporting_evidence: int
    recommended_weight: float


class MetaLearningEngine:
    """Extracts patterns and insights from execution data."""

    def __init__(self, output_dir: str = "outputs/phase14"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.insights: List[MetaInsight] = []
        self.heuristics: List[OperationalHeuristic] = []
        self.patterns: Dict[str, Any] = {}
        self.policy_recommendations: List[Dict[str, Any]] = []

    def analyze_phase12_outcomes(self, phase12_dir: str = "outputs/phase12") -> Dict[str, Any]:
        """Analyze Phase 12 execution data to extract patterns."""
        phase12_path = Path(phase12_dir)

        # Load all Phase 12 JSONL data
        task_outcomes = self._load_jsonl(phase12_path / "task_outcomes.jsonl")
        confidence_updates = self._load_jsonl(phase12_path / "confidence_updates.jsonl")
        strategic_decisions = self._load_jsonl(phase12_path / "strategic_decisions.jsonl")
        policy_updates = self._load_jsonl(phase12_path / "policy_updates.jsonl")

        # Analyze task execution patterns
        self._analyze_task_patterns(task_outcomes)

        # Analyze confidence dynamics
        self._analyze_confidence_dynamics(confidence_updates)

        # Analyze strategic decisions
        self._analyze_strategic_patterns(strategic_decisions)

        # Extract heuristics
        self._extract_operational_heuristics(task_outcomes, confidence_updates)

        # Generate policy recommendations
        self._generate_policy_recommendations(policy_updates)

        return {
            "insights_count": len(self.insights),
            "heuristics_count": len(self.heuristics),
            "policy_recommendations": len(self.policy_recommendations),
            "patterns": self.patterns,
        }

    def analyze_phase13_outcomes(self, phase13_dir: str = "outputs/phase13") -> Dict[str, Any]:
        """Analyze Phase 13 live execution data (if available)."""
        phase13_path = Path(phase13_dir)

        if not phase13_path.exists():
            return {"status": "phase13_not_available", "insights": []}

        # Load Phase 13 JSONL data
        task_outcomes = self._load_jsonl(phase13_path / "task_outcomes.jsonl")
        safety_gate_decisions = self._load_jsonl(phase13_path / "safety_gate_decisions.jsonl")

        # Analyze live execution vs dry-run
        self._analyze_live_vs_dryrun(task_outcomes)

        # Analyze safety gate effectiveness
        self._analyze_safety_gate_patterns(safety_gate_decisions)

        return {
            "status": "phase13_analyzed",
            "insights_count": len(self.insights),
            "heuristics_count": len(self.heuristics),
        }

    def _analyze_task_patterns(self, outcomes: List[Dict[str, Any]]) -> None:
        """Extract patterns from task execution outcomes."""
        if not outcomes:
            return

        # Group by risk level
        by_risk = defaultdict(list)
        for outcome in outcomes:
            by_risk[outcome.get("risk_level", "UNKNOWN")].append(outcome)

        # Calculate success rates per risk level
        for risk_level, tasks in by_risk.items():
            completed = sum(1 for t in tasks if t.get("status") == "completed")
            failed = sum(1 for t in tasks if t.get("status") == "failed")
            success_rate = completed / len(tasks) if tasks else 0.0

            avg_confidence = statistics.mean(
                [t.get("confidence_score", 0.5) for t in tasks if "confidence_score" in t]
            ) if tasks else 0.0

            self.patterns[f"{risk_level}_success_rate"] = success_rate
            self.patterns[f"{risk_level}_avg_confidence"] = avg_confidence
            self.patterns[f"{risk_level}_count"] = len(tasks)

            # Create insight
            if success_rate > 0.8:
                insight = MetaInsight(
                    insight_type="success_pattern",
                    description=f"{risk_level} risk tasks show {success_rate*100:.1f}% success rate",
                    confidence=min(success_rate, 0.95),
                    supporting_evidence=[f"{completed}/{len(tasks)} tasks completed"],
                    recommendation=f"Prioritize {risk_level.lower()} risk tasks in future waves",
                    frequency=len(tasks),
                    affected_tasks=[t.get("task_id", "") for t in tasks],
                )
                self.insights.append(insight)

    def _analyze_confidence_dynamics(self, updates: List[Dict[str, Any]]) -> None:
        """Analyze how confidence changes through waves."""
        if not updates:
            return

        confidence_deltas = [u.get("confidence_delta", 0) for u in updates if "confidence_delta" in u]

        if not confidence_deltas:
            return

        avg_delta = statistics.mean(confidence_deltas)
        median_delta = statistics.median(confidence_deltas)
        std_dev = statistics.stdev(confidence_deltas) if len(confidence_deltas) > 1 else 0

        self.patterns["confidence_avg_delta"] = avg_delta
        self.patterns["confidence_median_delta"] = median_delta
        self.patterns["confidence_stdev"] = std_dev

        if avg_delta > 0.01:
            insight = MetaInsight(
                insight_type="confidence_drift",
                description=f"Confidence trending upward (+{avg_delta*100:.2f}% avg per task)",
                confidence=0.75,
                supporting_evidence=[f"Median delta: {median_delta*100:.2f}%"],
                recommendation="Maintain current confidence calibration strategy",
                frequency=len(confidence_deltas),
                affected_tasks=[],
            )
            self.insights.append(insight)

    def _analyze_strategic_patterns(self, decisions: List[Dict[str, Any]]) -> None:
        """Analyze strategic decision patterns."""
        if not decisions:
            return

        decision_types = defaultdict(int)
        for decision in decisions:
            decision_type = decision.get("decision_type", "unknown")
            decision_types[decision_type] += 1

        self.patterns["decision_type_distribution"] = dict(decision_types)

        # Extract most common decision type
        if decision_types:
            most_common = max(decision_types.items(), key=lambda x: x[1])
            insight = MetaInsight(
                insight_type="success_pattern",
                description=f"Most common strategic decision: {most_common[0]} ({most_common[1]} instances)",
                confidence=0.8,
                supporting_evidence=[f"Frequency: {most_common[1]}/{len(decisions)}"],
                recommendation=f"Leverage {most_common[0]} strategy in Phase 14 planning",
                frequency=most_common[1],
                affected_tasks=[],
            )
            self.insights.append(insight)

    def _analyze_live_vs_dryrun(self, outcomes: List[Dict[str, Any]]) -> None:
        """Analyze live execution vs dry-run outcomes."""
        live_tasks = [t for t in outcomes if not t.get("dry_run", False)]
        dryrun_tasks = [t for t in outcomes if t.get("dry_run", False)]

        live_success = sum(1 for t in live_tasks if t.get("status") == "completed") / len(
            live_tasks
        ) if live_tasks else 0
        dryrun_success = sum(1 for t in dryrun_tasks if t.get("status") == "completed") / len(
            dryrun_tasks
        ) if dryrun_tasks else 0

        self.patterns["live_success_rate"] = live_success
        self.patterns["dryrun_success_rate"] = dryrun_success

        if live_success > 0:
            insight = MetaInsight(
                insight_type="success_pattern",
                description=f"Live execution success rate: {live_success*100:.1f}%",
                confidence=0.85,
                supporting_evidence=[f"{sum(1 for t in live_tasks if t.get('status') == 'completed')}/{len(live_tasks)} live tasks completed"],
                recommendation="Increase live task allocation in future waves",
                frequency=len(live_tasks),
                affected_tasks=[t.get("task_id", "") for t in live_tasks],
            )
            self.insights.append(insight)

    def _analyze_safety_gate_patterns(self, decisions: List[Dict[str, Any]]) -> None:
        """Analyze safety gate decision patterns."""
        if not decisions:
            return

        statuses = defaultdict(int)
        for decision in decisions:
            status = decision.get("approval_status", "unknown")
            statuses[status] += 1

        self.patterns["safety_gate_distribution"] = dict(statuses)

        # Analyze approval rate
        approved = statuses.get("APPROVED", 0)
        total = sum(statuses.values())
        approval_rate = approved / total if total > 0 else 0

        self.patterns["approval_rate"] = approval_rate

        if approval_rate > 0.8:
            insight = MetaInsight(
                insight_type="success_pattern",
                description=f"High approval rate: {approval_rate*100:.1f}%",
                confidence=0.8,
                supporting_evidence=[f"{approved}/{total} tasks approved by safety gates"],
                recommendation="Maintain current safety gate thresholds",
                frequency=total,
                affected_tasks=[],
            )
            self.insights.append(insight)

    def _extract_operational_heuristics(self, outcomes: List[Dict[str, Any]], updates: List[Dict[str, Any]]) -> None:
        """Extract reusable operational heuristics."""
        if not outcomes:
            return

        # Heuristic 1: Low-risk tasks have high success rate
        low_risk_tasks = [t for t in outcomes if t.get("risk_level") == "LOW"]
        low_risk_success = sum(1 for t in low_risk_tasks if t.get("status") == "completed") / len(
            low_risk_tasks
        ) if low_risk_tasks else 0

        if low_risk_success > 0.85:
            heuristic = OperationalHeuristic(
                heuristic_id="h_low_risk_priority",
                category="task_sequencing",
                rule="Prioritize LOW risk tasks as foundation for wave",
                applicability="universal",
                confidence=min(low_risk_success, 0.95),
                supporting_evidence=len(low_risk_tasks),
                recommended_weight=1.5,
            )
            self.heuristics.append(heuristic)

        # Heuristic 2: Confidence-based task filtering
        high_confidence_tasks = [t for t in outcomes if t.get("confidence_score", 0) >= 0.75]
        high_conf_success = sum(1 for t in high_confidence_tasks if t.get("status") == "completed") / len(
            high_confidence_tasks
        ) if high_confidence_tasks else 0

        if high_conf_success > 0.8:
            heuristic = OperationalHeuristic(
                heuristic_id="h_high_confidence_selection",
                category="risk_assessment",
                rule="Prioritize tasks with confidence >= 0.75",
                applicability="universal",
                confidence=min(high_conf_success, 0.95),
                supporting_evidence=len(high_confidence_tasks),
                recommended_weight=1.4,
            )
            self.heuristics.append(heuristic)

        # Heuristic 3: Rollback prevention
        failed_tasks = [t for t in outcomes if t.get("status") == "failed"]
        if failed_tasks:
            heuristic = OperationalHeuristic(
                heuristic_id="h_failure_prevention",
                category="rollback_prevention",
                rule="Avoid tasks with historical failures; increase retry_multiplier",
                applicability="medium_risk",
                confidence=0.85,
                supporting_evidence=len(failed_tasks),
                recommended_weight=0.8,
            )
            self.heuristics.append(heuristic)

    def _generate_policy_recommendations(self, updates: List[Dict[str, Any]]) -> None:
        """Generate policy recommendations for Phase 15."""
        if not updates:
            return

        # Analyze policy adaptation trend
        latest_policies = {}
        for update in updates:
            wave = update.get("wave", 0)
            latest_policies[wave] = update.get("new_policy", {})

        if len(latest_policies) > 1:
            waves = sorted(latest_policies.keys())
            first_policy = latest_policies[waves[0]]
            last_policy = latest_policies[waves[-1]]

            # Track threshold changes
            threshold_change = last_policy.get("high_risk_threshold", 0) - first_policy.get("high_risk_threshold", 0)

            if threshold_change > 0.05:
                recommendation = {
                    "type": "increase_high_risk_threshold",
                    "rationale": f"High-risk threshold increased by {threshold_change:.2f} across waves",
                    "action": "Consider further increasing threshold in Phase 15 if safety gates remain effective",
                    "confidence": 0.75,
                }
                self.policy_recommendations.append(recommendation)

            # Track retry multiplier changes
            retry_change = last_policy.get("retry_multiplier", 1.0) - first_policy.get("retry_multiplier", 1.0)

            if retry_change > 0.1:
                recommendation = {
                    "type": "increase_retry_strategy",
                    "rationale": f"Retry multiplier increased by {retry_change:.2f} for failure recovery",
                    "action": "Implement adaptive retry with exponential backoff in Phase 15",
                    "confidence": 0.75,
                }
                self.policy_recommendations.append(recommendation)

    def _load_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        """Load JSONL file."""
        if not path.exists():
            return []

        data = []
        try:
            with open(path, "r") as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
        except Exception as e:
            print(f"Warning: Failed to load {path}: {e}")

        return data

    def get_insights(self) -> List[MetaInsight]:
        """Return all extracted insights."""
        return self.insights

    def get_heuristics(self) -> List[OperationalHeuristic]:
        """Return all extracted heuristics."""
        return self.heuristics

    def get_policy_recommendations(self) -> List[Dict[str, Any]]:
        """Return all policy recommendations."""
        return self.policy_recommendations

    def write_meta_artifacts(self, wave: int) -> None:
        """Write meta-learning artifacts for a wave."""
        wave_dir = self.output_dir / f"wave_{wave}"
        wave_dir.mkdir(exist_ok=True)

        # Write insights
        with open(wave_dir / f"meta_insights.jsonl", "w") as f:
            for insight in self.insights:
                f.write(json.dumps(asdict(insight)) + "\n")

        # Write heuristics
        with open(wave_dir / f"heuristics.jsonl", "w") as f:
            for heuristic in self.heuristics:
                f.write(json.dumps(asdict(heuristic)) + "\n")

        # Write patterns summary
        with open(wave_dir / f"patterns.json", "w") as f:
            json.dump(self.patterns, f, indent=2)

        # Write policy recommendations
        with open(wave_dir / f"policy_recommendations.json", "w") as f:
            json.dump(self.policy_recommendations, f, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all extracted meta-learning data."""
        return {
            "insights": [asdict(i) for i in self.insights],
            "heuristics": [asdict(h) for h in self.heuristics],
            "patterns": self.patterns,
            "policy_recommendations": self.policy_recommendations,
            "metrics": {
                "total_insights": len(self.insights),
                "total_heuristics": len(self.heuristics),
                "total_recommendations": len(self.policy_recommendations),
            },
        }

