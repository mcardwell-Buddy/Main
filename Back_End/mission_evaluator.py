"""
Mission Evaluator

Centralized, read-only mission-level evaluation and learning signals.

Purpose:
- Consolidate goal satisfaction, expectation delta, drift, opportunity normalization,
  ambiguity evaluation, and mission cost accounting.
- Callable from any execution path (tools or agents) without changing behavior.
- Feature-flagged and observe-only.
"""

from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from Back_End.mission_control.goal_satisfaction_evaluator import GoalSatisfactionEvaluator
from Back_End.evaluation.expectation_delta_evaluator import ExpectationDeltaEvaluator
from Back_End.evaluation.drift_monitor import DriftMonitor
from Back_End.mission_control.opportunity_normalizer import OpportunityNormalizer
from Back_End.mission_control.ambiguity_evaluator import AmbiguityEvaluator
from Back_End.mission.mission_cost_accountant import MissionCostAccountant
from Back_End.learning.signal_priority import apply_signal_priority
from Back_End.learning.time_context import extract_time_context
from Back_End.mission_control.regret_registry import log_regret


class MissionEvaluator:
    """
    Shared mission evaluator for post-execution analysis.

    Observe-only and non-blocking. Does not alter execution behavior.
    """

    def __init__(
        self,
        enabled: Optional[bool] = None
    ) -> None:
        if enabled is None:
            enabled = os.getenv("MISSION_EVALUATOR_ENABLED", "False").lower() == "true"
        self.enabled = enabled
        
        from Back_End.memory_manager import memory
        self.memory = memory

    def evaluate_after_execution(
        self,
        mission_id: str,
        objective_description: str,
        items_collected: List[Dict[str, Any]],
        context: Dict[str, Any],
        outcome_summary: Dict[str, Any],
        objective: Optional[Any] = None,
        mission_thread_id: Optional[str] = None,
        mission_created_at: Optional[str] = None
    ) -> None:
        """
        Run core mission evaluators after execution completes.

        Args:
            mission_id: Mission identifier
            objective_description: Natural language objective
            items_collected: Extracted items (if any)
            context: Context (page_title, page_url, page_type, items_count)
            outcome_summary: Dict with status, items_collected, reason
            objective: Optional MissionObjective-like object (type, description, target, required_fields)
            mission_thread_id: Optional mission thread
            mission_created_at: Optional creation timestamp for time context
        """
        if not self.enabled:
            return

        try:
            self._evaluate_goal_satisfaction(
                mission_id=mission_id,
                mission_objective=objective_description,
                items_collected=items_collected,
                context=context,
            )

            if objective is not None:
                self._evaluate_expectation_delta(
                    mission_id=mission_id,
                    objective=objective,
                    outcome_summary=outcome_summary,
                    mission_thread_id=mission_thread_id,
                )

            self._normalize_opportunities(
                mission_id=mission_id,
                mission_objective=objective_description,
                items_collected=items_collected,
                context=context,
                mission_created_at=mission_created_at,
            )

            self._evaluate_ambiguity(
                mission_id=mission_id,
                mission_status=outcome_summary.get("status", "unknown"),
                items_collected=len(items_collected or []),
            )

            self._compute_mission_costs(mission_id)
            self._evaluate_concept_drift()
        except Exception:
            # Observe-only: never fail execution
            return

    def emit_mission_outcome(
        self,
        mission_id: str,
        status: str,
        reason: str,
        mission_thread_id: Optional[str] = None,
        mission_created_at: Optional[str] = None
    ) -> None:
        """
        Emit mission_completed / mission_failed signals centrally.

        Args:
            mission_id: Mission identifier
            status: "completed" or "failed"
            reason: Reason string
            mission_thread_id: Optional thread id
            mission_created_at: Optional creation timestamp for time context
        """
        if not self.enabled:
            return

        timestamp = datetime.now(timezone.utc).isoformat()
        signal_type = "mission_completed" if status == "completed" else "mission_failed"

        signal = {
            "signal_type": signal_type,
            "mission_id": mission_id,
            "reason": reason,
            "signal_layer": "mission",
            "signal_source": "mission_control",
            "timestamp": timestamp
        }

        if mission_thread_id:
            signal["mission_thread_id"] = mission_thread_id

        if mission_created_at:
            time_context = extract_time_context(timestamp, mission_created_at)
            signal["time_context"] = time_context

        self._persist_learning_signal(signal)

    def _persist_learning_signal(self, signal: Dict[str, Any]) -> None:
        try:
            signal = apply_signal_priority(signal)
            # Save to Firebase memory
            signal_key = f"mission_eval_signal:{signal.get('timestamp', 'unknown')}"
            self.memory.safe_call("set", signal_key, signal)
            
            # Update index
            index_key = "mission_eval_signal_index"
            existing_index = self.memory.safe_call("get", index_key) or []
            existing_index.append(signal_key)
            if len(existing_index) > 500:
                existing_index = existing_index[-500:]
            self.memory.safe_call("set", index_key, existing_index)
        except Exception:
            # Observe-only: ignore failures
            pass

    def _evaluate_goal_satisfaction(
        self,
        mission_id: str,
        mission_objective: str,
        items_collected: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> None:
        evaluator = GoalSatisfactionEvaluator()
        evaluation = evaluator.evaluate(
            mission_id=mission_id,
            mission_objective=mission_objective,
            items_collected=items_collected,
            context=context,
        )
        signal = evaluation.to_signal()
        self._persist_learning_signal(signal)

    def _evaluate_expectation_delta(
        self,
        mission_id: str,
        objective: Any,
        outcome_summary: Dict[str, Any],
        mission_thread_id: Optional[str] = None
    ) -> None:
        evaluator = ExpectationDeltaEvaluator()
        objective_dict = {
            "type": getattr(objective, "type", None),
            "description": getattr(objective, "description", None),
            "target": getattr(objective, "target", None),
            "required_fields": getattr(objective, "required_fields", None),
        }
        evaluator.evaluate(
            mission_id=mission_id,
            objective=objective_dict,
            outcome_summary=outcome_summary,
            mission_thread_id=mission_thread_id,
        )

    def _evaluate_concept_drift(self) -> None:
        monitor = DriftMonitor(signals_file=self.signals_file)
        monitor.evaluate()

    def _normalize_opportunities(
        self,
        mission_id: str,
        mission_objective: str,
        items_collected: List[Dict[str, Any]],
        context: Dict[str, Any],
        mission_created_at: Optional[str] = None
    ) -> None:
        normalizer = OpportunityNormalizer()
        opportunities = normalizer.normalize(
            mission_id=mission_id,
            mission_objective=mission_objective,
            items_collected=items_collected,
            context=context,
        )

        timestamp = datetime.now(timezone.utc).isoformat()
        signal = {
            "signal_type": "opportunity_normalized",
            "signal_layer": "opportunity",
            "signal_source": "opportunity_normalizer",
            "mission_id": mission_id,
            "opportunities_created": len(opportunities),
            "opportunity_types": self._count_opportunity_types(opportunities),
            "avg_confidence": sum(o.confidence for o in opportunities) / len(opportunities) if opportunities else 0.0,
            "timestamp": timestamp,
        }

        if mission_created_at:
            time_context = extract_time_context(timestamp, mission_created_at)
            signal["time_context"] = time_context

        self._persist_learning_signal(signal)

        avg_confidence = signal["avg_confidence"]
        if len(opportunities) > 0 and avg_confidence < 0.3:
            log_regret(
                mission_id=mission_id,
                action="opportunity_normalization",
                failure_reason="confidence_collapse",
                irreversible=False,
                estimated_cost={
                    "time_lost": 10,
                    "trust_impact": 20,
                    "opportunities_lost": len(opportunities),
                },
                context={
                    "avg_confidence": avg_confidence,
                    "opportunities_created": len(opportunities),
                    "objective": mission_objective,
                },
            )

    def _count_opportunity_types(self, opportunities: List[Any]) -> Dict[str, int]:
        type_counts: Dict[str, int] = {}
        for opp in opportunities:
            opp_type = getattr(opp, "opportunity_type", None)
            if not opp_type:
                continue
            type_counts[opp_type] = type_counts.get(opp_type, 0) + 1
        return type_counts

    def _evaluate_ambiguity(
        self,
        mission_id: str,
        mission_status: str,
        items_collected: int
    ) -> None:
        try:
            signals_file = self.signals_file
            goal_evaluation = None
            opportunity_summary = None

            if signals_file.exists():
                with open(signals_file, "r", encoding="utf-8") as f:
                    for line in reversed(list(f)):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            signal = json.loads(line)
                            if signal.get("mission_id") == mission_id:
                                if signal.get("signal_type") == "goal_evaluation" and not goal_evaluation:
                                    goal_evaluation = signal
                                elif signal.get("signal_type") == "opportunity_normalized" and not opportunity_summary:
                                    opportunity_summary = signal

                            if goal_evaluation and opportunity_summary:
                                break
                        except json.JSONDecodeError:
                            continue

            evaluator = AmbiguityEvaluator()
            evaluation = evaluator.evaluate(
                mission_id=mission_id,
                goal_evaluation=goal_evaluation,
                opportunity_summary=opportunity_summary,
                items_collected=items_collected,
                mission_status=mission_status,
            )

            if evaluator.should_emit_signal(evaluation):
                signal = evaluation.to_signal(mission_id)
                self._persist_learning_signal(signal)
        except Exception:
            pass

    def _compute_mission_costs(self, mission_id: str) -> None:
        accountant = MissionCostAccountant(signals_file=str(self.signals_file))
        cost_report = accountant.compute_costs(mission_id)
        if accountant.should_emit_signal(cost_report):
            signal = cost_report.to_signal()
            self._persist_learning_signal(signal)

