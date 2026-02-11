"""Buddy Phase 11 Autonomous Goal Generator.

Generates new workflow goals based on Phase 10 learning insights and
deferred task patterns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from buddy_goal_manager import TaskSpec, Goal
from buddy_learning_analyzer import LearningAnalyzer


@dataclass
class AutonomousGoal:
    goal_id: str
    description: str
    tasks: List[TaskSpec]
    learning_basis: str
    expected_outcome: str


class AutonomousGoalGenerator:
    def __init__(self, analyzer: LearningAnalyzer):
        self.analyzer = analyzer

    def generate_goals(self, wave: int) -> List[AutonomousGoal]:
        goals = []
        
        # Generate confidence-boosting workflows for deferred high-risk tasks
        candidates = self.analyzer.get_confidence_elevation_candidates()
        for i, candidate in enumerate(candidates[:2]):  # Limit to 2 per wave
            goals.append(self._create_confidence_boosting_goal(candidate, wave, i))
        
        # Generate exploration workflows based on success patterns
        insights = self.analyzer.analyze()
        high_success_insights = [ins for ins in insights if ins.insight_type == "high_success_risk_level"]
        if high_success_insights:
            goals.append(self._create_exploration_goal(wave))
        
        # Generate validation workflows for misaligned confidence
        misalignment_insights = [ins for ins in insights if ins.insight_type == "confidence_misalignment"]
        if misalignment_insights:
            goals.append(self._create_validation_goal(wave))
        
        return goals

    def _create_confidence_boosting_goal(
        self,
        candidate: Dict[str, Any],
        wave: int,
        index: int
    ) -> AutonomousGoal:
        """Create a workflow with precursor tasks to boost confidence."""
        task_id_base = candidate.get("task_id", f"deferred_{index}")
        
        tasks = [
            TaskSpec(
                task_id=f"{task_id_base}_precursor_inspect",
                title="Precursor: Inspect target",
                tool="web_inspect",
                priority="MEDIUM",
                risk="LOW",
                confidence=0.8,
                dependencies=[],
                branches=[],
                metadata={"wave": wave, "type": "precursor"}
            ),
            TaskSpec(
                task_id=f"{task_id_base}_precursor_extract",
                title="Precursor: Extract validation data",
                tool="web_extract",
                priority="MEDIUM",
                risk="LOW",
                confidence=0.75,
                dependencies=[f"{task_id_base}_precursor_inspect"],
                branches=[],
                metadata={"wave": wave, "type": "precursor"}
            ),
            TaskSpec(
                task_id=f"{task_id_base}_elevated",
                title="Elevated: High-risk action (post-validation)",
                tool="high_risk_submit",
                priority="HIGH",
                risk="HIGH",
                confidence=min(0.82, candidate.get("current_confidence", 0.6) + 0.2),
                dependencies=[f"{task_id_base}_precursor_extract"],
                branches=[],
                metadata={"wave": wave, "type": "elevated"}
            )
        ]
        
        return AutonomousGoal(
            goal_id=f"confidence_boost_wave{wave}_{index}",
            description=f"Confidence-boosting workflow for {task_id_base}",
            tasks=tasks,
            learning_basis="deferred_high_risk",
            expected_outcome="Elevated task executes after confidence boost via precursors"
        )

    def _create_exploration_goal(self, wave: int) -> AutonomousGoal:
        """Create exploratory workflow to test policy boundaries."""
        tasks = [
            TaskSpec(
                task_id=f"explore_wave{wave}_a",
                title="Explore: Complex multi-step workflow",
                tool="web_inspect",
                priority="LOW",
                risk="LOW",
                confidence=0.7,
                dependencies=[],
                branches=[],
                metadata={"wave": wave, "type": "exploration"}
            ),
            TaskSpec(
                task_id=f"explore_wave{wave}_b",
                title="Explore: Medium-risk branching",
                tool="web_click",
                priority="MEDIUM",
                risk="MEDIUM",
                confidence=0.68,
                dependencies=[f"explore_wave{wave}_a"],
                branches=[],
                metadata={"wave": wave, "type": "exploration"}
            )
        ]
        
        return AutonomousGoal(
            goal_id=f"exploration_wave{wave}",
            description="Exploratory workflow to test policy boundaries",
            tasks=tasks,
            learning_basis="high_success_risk_level",
            expected_outcome="Validate policy effectiveness on new patterns"
        )

    def _create_validation_goal(self, wave: int) -> AutonomousGoal:
        """Create validation workflow for confidence recalibration."""
        tasks = [
            TaskSpec(
                task_id=f"validate_wave{wave}_low_conf",
                title="Validate: Low-confidence task (expected success)",
                tool="web_inspect",
                priority="MEDIUM",
                risk="LOW",
                confidence=0.55,
                dependencies=[],
                branches=[],
                metadata={"wave": wave, "type": "validation"}
            ),
            TaskSpec(
                task_id=f"validate_wave{wave}_high_conf",
                title="Validate: High-confidence task (check calibration)",
                tool="web_extract",
                priority="MEDIUM",
                risk="LOW",
                confidence=0.85,
                dependencies=[f"validate_wave{wave}_low_conf"],
                branches=[],
                metadata={"wave": wave, "type": "validation"}
            )
        ]
        
        return AutonomousGoal(
            goal_id=f"validation_wave{wave}",
            description="Validation workflow for confidence recalibration",
            tasks=tasks,
            learning_basis="confidence_misalignment",
            expected_outcome="Recalibrate confidence based on observed outcomes"
        )

