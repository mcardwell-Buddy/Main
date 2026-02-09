"""Buddy Phase 11 Learning Analyzer.

Analyzes Phase 10 outcomes to identify patterns, misalignments, and
opportunities for policy refinement and workflow expansion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class LearningInsight:
    insight_type: str
    description: str
    confidence: float
    supporting_evidence: List[str]
    recommendation: str


class LearningAnalyzer:
    def __init__(self, phase10_dir: Path):
        self.phase10_dir = phase10_dir
        self.outcomes: List[Dict[str, Any]] = []
        self.confidence_updates: List[Dict[str, Any]] = []
        self.policy_updates: List[Dict[str, Any]] = []
        self._load_artifacts()

    def _load_artifacts(self):
        outcomes_path = self.phase10_dir / "task_outcomes.jsonl"
        if outcomes_path.exists():
            lines = outcomes_path.read_text(encoding="utf-8").splitlines()
            self.outcomes = [json.loads(line) for line in lines if line.strip()]

        confidence_path = self.phase10_dir / "confidence_updates.jsonl"
        if confidence_path.exists():
            lines = confidence_path.read_text(encoding="utf-8").splitlines()
            self.confidence_updates = [json.loads(line) for line in lines if line.strip()]

        policy_path = self.phase10_dir / "policy_updates.jsonl"
        if policy_path.exists():
            lines = policy_path.read_text(encoding="utf-8").splitlines()
            self.policy_updates = [json.loads(line) for line in lines if line.strip()]

    def analyze(self) -> List[LearningInsight]:
        insights = []
        insights.extend(self._analyze_confidence_alignment())
        insights.extend(self._analyze_deferred_patterns())
        insights.extend(self._analyze_success_patterns())
        insights.extend(self._analyze_policy_effectiveness())
        return insights

    def _analyze_confidence_alignment(self) -> List[LearningInsight]:
        insights = []
        
        # Find tasks where confidence was misaligned with outcome
        over_confident = []
        under_confident = []
        
        for outcome in self.outcomes:
            if outcome.get("status") == "completed":
                initial_conf = outcome.get("confidence_score", 0.5)
                # Successful task with low initial confidence = under-confident
                if initial_conf < 0.6:
                    under_confident.append(outcome.get("task_id"))
            elif outcome.get("status") == "failed":
                initial_conf = outcome.get("confidence_score", 0.5)
                # Failed task with high initial confidence = over-confident
                if initial_conf > 0.7:
                    over_confident.append(outcome.get("task_id"))
        
        if under_confident:
            insights.append(LearningInsight(
                insight_type="confidence_misalignment",
                description=f"Under-confident on {len(under_confident)} successful tasks",
                confidence=0.8,
                supporting_evidence=[f"Task {tid} succeeded despite low confidence" for tid in under_confident[:3]],
                recommendation="Increase initial confidence for similar low-risk tasks"
            ))
        
        if over_confident:
            insights.append(LearningInsight(
                insight_type="confidence_misalignment",
                description=f"Over-confident on {len(over_confident)} failed tasks",
                confidence=0.9,
                supporting_evidence=[f"Task {tid} failed despite high confidence" for tid in over_confident[:3]],
                recommendation="Add validation steps before high-confidence task execution"
            ))
        
        return insights

    def _analyze_deferred_patterns(self) -> List[LearningInsight]:
        insights = []
        deferred = [o for o in self.outcomes if o.get("status") == "deferred"]
        
        if not deferred:
            return insights
        
        high_risk_deferred = [d for d in deferred if d.get("risk_level") == "HIGH"]
        if high_risk_deferred:
            avg_conf = sum(d.get("confidence_score", 0) for d in high_risk_deferred) / len(high_risk_deferred)
            insights.append(LearningInsight(
                insight_type="deferred_high_risk",
                description=f"{len(high_risk_deferred)} high-risk tasks deferred (avg conf: {avg_conf:.2f})",
                confidence=0.95,
                supporting_evidence=[
                    f"Task {d.get('task_id')} deferred at confidence {d.get('confidence_score', 0):.2f}"
                    for d in high_risk_deferred[:3]
                ],
                recommendation="Implement confidence-boosting strategies via low-risk precursor tasks"
            ))
        
        return insights

    def _analyze_success_patterns(self) -> List[LearningInsight]:
        insights = []
        completed = [o for o in self.outcomes if o.get("status") == "completed"]
        
        if not completed:
            return insights
        
        # Group by risk level
        by_risk = {}
        for task in completed:
            risk = task.get("risk_level", "UNKNOWN")
            by_risk.setdefault(risk, []).append(task)
        
        for risk_level, tasks in by_risk.items():
            success_rate = len(tasks) / len([o for o in self.outcomes if o.get("risk_level") == risk_level])
            if success_rate >= 0.9:
                insights.append(LearningInsight(
                    insight_type="high_success_risk_level",
                    description=f"{risk_level} risk tasks show {success_rate:.0%} success rate",
                    confidence=0.85,
                    supporting_evidence=[f"{len(tasks)} {risk_level} tasks completed"],
                    recommendation=f"Consider increasing complexity for {risk_level} risk workflows"
                ))
        
        return insights

    def _analyze_policy_effectiveness(self) -> List[LearningInsight]:
        insights = []
        
        if not self.policy_updates:
            return insights
        
        # Check if policy has stabilized
        last_3 = self.policy_updates[-3:] if len(self.policy_updates) >= 3 else self.policy_updates
        changes = sum(1 for p in last_3 if p.get("changes", []))
        
        if changes == 0:
            insights.append(LearningInsight(
                insight_type="policy_stabilization",
                description="Policy has stabilized with no recent changes",
                confidence=0.9,
                supporting_evidence=["No policy changes in last 3 waves"],
                recommendation="Consider exploring new workflow patterns to test policy boundaries"
            ))
        
        return insights

    def get_confidence_elevation_candidates(self) -> List[Dict[str, Any]]:
        """Identify deferred tasks that could be elevated with confidence boosting."""
        candidates = []
        deferred = [o for o in self.outcomes if o.get("status") == "deferred"]
        
        for task in deferred:
            if task.get("risk_level") == "HIGH":
                current_conf = task.get("confidence_score", 0)
                gap = 0.8 - current_conf
                candidates.append({
                    "task_id": task.get("task_id"),
                    "current_confidence": current_conf,
                    "target_confidence": 0.8,
                    "confidence_gap": gap,
                    "strategy": "precursor_tasks" if gap > 0.15 else "validation_step"
                })
        
        return candidates
