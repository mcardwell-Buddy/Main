"""
Phase 11: Build Stage Evaluator

Deterministically evaluates whether a build can move stages.
Evaluation only - no transitions executed automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from Back_End.build_contract import BuildContract, BuildStage


COMPLETED_MISSION_STATUSES = {"completed", "succeeded", "done", "complete"}


@dataclass(frozen=True)
class BuildStageEvaluation:
    """Immutable evaluation result for a build stage."""
    build_id: str
    current_stage: BuildStage
    next_stage: Optional[BuildStage]
    is_ready: bool
    readiness_score: float
    blocking_reasons: List[str] = field(default_factory=list)
    satisfied_requirements: List[str] = field(default_factory=list)


class BuildStageEvaluator:
    """Deterministic evaluator for build stage readiness."""

    @staticmethod
    def evaluate(
        build: BuildContract,
        mission_statuses: Optional[Dict[str, str]] = None,
        goal_evaluations: Optional[List[Dict[str, Any]]] = None,
        artifact_ids: Optional[List[str]] = None,
        investment_score: Optional[float] = None,
    ) -> BuildStageEvaluation:
        """
        Evaluate readiness to move from current stage to next stage.

        Args:
            build: BuildContract
            mission_statuses: mapping mission_id -> status
            goal_evaluations: list of goal evaluation dicts (goal_satisfied bool)
            artifact_ids: list of artifact IDs produced
            investment_score: optional investment score for build

        Returns:
            BuildStageEvaluation (read-only)
        """
        mission_statuses = mission_statuses or {}
        goal_evaluations = goal_evaluations or []
        artifact_ids = artifact_ids or list(build.artifact_ids)
        investment_score = investment_score if investment_score is not None else build.investment_score

        current = build.current_stage
        next_stage = BuildStageEvaluator._next_stage(current)

        blocking: List[str] = []
        satisfied: List[str] = []

        # Global checks
        if not build.name:
            blocking.append("missing_build_name")
        else:
            satisfied.append("build_named")

        if not build.objective:
            blocking.append("missing_objective")
        else:
            satisfied.append("objective_defined")

        # Stage-specific checks
        if current == BuildStage.DESIGN:
            if build.mission_ids:
                satisfied.append("missions_planned")
            else:
                blocking.append("no_missions_planned")

            if investment_score is not None:
                if investment_score >= 0.4:
                    satisfied.append("investment_score_meets_hold")
                else:
                    blocking.append("investment_score_below_hold")

        elif current == BuildStage.IMPLEMENTATION:
            if BuildStageEvaluator._all_missions_completed(build.mission_ids, mission_statuses):
                satisfied.append("all_missions_completed")
            else:
                blocking.append("missions_incomplete")

            if artifact_ids:
                satisfied.append("artifacts_present")
            else:
                blocking.append("no_artifacts_produced")

        elif current == BuildStage.VALIDATION:
            goal_satisfied = BuildStageEvaluator._goal_satisfied(goal_evaluations)
            if goal_satisfied is True:
                satisfied.append("goals_satisfied")
            elif goal_satisfied is False:
                satisfied.append("goals_failed")
            else:
                blocking.append("no_goal_evaluation")

            if not artifact_ids:
                blocking.append("no_artifacts_for_validation")
            else:
                satisfied.append("validation_artifacts_present")

        elif current == BuildStage.ITERATION:
            if BuildStageEvaluator._all_missions_completed(build.mission_ids, mission_statuses):
                satisfied.append("iteration_missions_completed")
            else:
                blocking.append("iteration_missions_incomplete")

            if artifact_ids:
                satisfied.append("iteration_artifacts_present")
            else:
                blocking.append("iteration_no_artifacts")

        elif current == BuildStage.COMPLETE:
            satisfied.append("build_complete")

        # Determine readiness
        is_ready = len(blocking) == 0 and next_stage is not None
        readiness_score = BuildStageEvaluator._calculate_readiness_score(satisfied, blocking)

        # Override next_stage based on validation results
        if current == BuildStage.VALIDATION:
            goal_satisfied = BuildStageEvaluator._goal_satisfied(goal_evaluations)
            if goal_satisfied is True:
                next_stage = BuildStage.COMPLETE
            elif goal_satisfied is False:
                next_stage = BuildStage.ITERATION

        return BuildStageEvaluation(
            build_id=build.build_id,
            current_stage=current,
            next_stage=next_stage,
            is_ready=is_ready,
            readiness_score=readiness_score,
            blocking_reasons=blocking,
            satisfied_requirements=satisfied,
        )

    @staticmethod
    def _next_stage(current: BuildStage) -> Optional[BuildStage]:
        """Deterministically map current stage to next stage."""
        if current == BuildStage.DESIGN:
            return BuildStage.IMPLEMENTATION
        if current == BuildStage.IMPLEMENTATION:
            return BuildStage.VALIDATION
        if current == BuildStage.VALIDATION:
            return BuildStage.ITERATION
        if current == BuildStage.ITERATION:
            return BuildStage.VALIDATION
        return None

    @staticmethod
    def _all_missions_completed(mission_ids: List[str], mission_statuses: Dict[str, str]) -> bool:
        if not mission_ids:
            return False
        for mission_id in mission_ids:
            status = mission_statuses.get(mission_id, "")
            if status.lower() not in COMPLETED_MISSION_STATUSES:
                return False
        return True

    @staticmethod
    def _goal_satisfied(goal_evaluations: List[Dict[str, Any]]) -> Optional[bool]:
        """Return latest goal_satisfied if provided."""
        if not goal_evaluations:
            return None
        latest = goal_evaluations[-1]
        if "goal_satisfied" in latest:
            return bool(latest.get("goal_satisfied"))
        return None

    @staticmethod
    def _calculate_readiness_score(satisfied: List[str], blocking: List[str]) -> float:
        """Deterministic readiness score 0.0-1.0."""
        total = len(satisfied) + len(blocking)
        if total == 0:
            return 0.0
        return round(len(satisfied) / total, 3)

