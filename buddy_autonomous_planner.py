"""
Phase 14: Autonomous Planner

Plans new multi-wave operational workflows using Phase 12 & 13 insights,
applying meta-learning heuristics and safety constraints.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple
from pathlib import Path


@dataclass
class PlannedTask:
    """Task planned for execution."""
    task_id: str
    wave: int
    title: str
    tool: str
    risk_level: str
    confidence: float
    priority: int
    dependencies: List[str]
    justification: str
    heuristics_applied: List[str]
    expected_outcome: str


@dataclass
class WavePlan:
    """Complete plan for a wave."""
    wave: int
    planned_tasks: List[PlannedTask]
    total_tasks: int
    estimated_success_rate: float
    estimated_avg_confidence: float
    high_risk_count: int
    deferred_tasks: List[str]
    safety_rationale: str


class AutonomousPlanner:
    """Plans autonomous operational workflows."""

    def __init__(self, meta_engine, policy: Dict[str, Any], output_dir: str = "outputs/phase14"):
        self.meta_engine = meta_engine
        self.policy = policy
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.wave_plans: List[WavePlan] = []
        self.planned_tasks: List[PlannedTask] = []

    def plan_waves(self, num_waves: int = 3) -> List[WavePlan]:
        """Plan multiple waves autonomously."""
        self.wave_plans = []
        self.planned_tasks = []

        for wave in range(1, num_waves + 1):
            wave_plan = self._plan_wave(wave)
            self.wave_plans.append(wave_plan)

        return self.wave_plans

    def _plan_wave(self, wave: int) -> WavePlan:
        """Plan a single wave."""
        # Generate tasks for this wave
        tasks = self._generate_wave_tasks(wave)

        # Apply heuristics and safety gates
        planned_tasks = []
        deferred = []
        high_risk_count = 0

        for task in tasks:
            # Apply meta-learning heuristics
            heuristics = self._select_heuristics(task)
            task["heuristics_applied"] = [h.heuristic_id for h in heuristics]

            # Boost confidence from heuristics
            confidence_boost = sum(h.recommended_weight * 0.02 for h in heuristics)
            task["confidence"] = min(task.get("confidence", 0.7) + confidence_boost, 0.99)

            # Evaluate safety gate
            safety_status, safety_reason = self._evaluate_task_safety(task)

            if safety_status == "APPROVED":
                planned_task = PlannedTask(
                    task_id=task.get("task_id", f"wave{wave}_task"),
                    wave=wave,
                    title=task.get("title", ""),
                    tool=task.get("tool", ""),
                    risk_level=task.get("risk_level", "MEDIUM"),
                    confidence=task.get("confidence", 0.7),
                    priority=task.get("priority", 5),
                    dependencies=task.get("dependencies", []),
                    justification=f"Approved by safety gates. Rationale: {safety_reason}",
                    heuristics_applied=task.get("heuristics_applied", []),
                    expected_outcome=self._predict_outcome(task),
                )
                planned_tasks.append(planned_task)

            else:  # DEFERRED or REJECTED
                deferred.append(task.get("task_id", ""))

            if task.get("risk_level") == "HIGH":
                high_risk_count += 1

        # Calculate wave metrics
        avg_confidence = sum(t.confidence for t in planned_tasks) / len(
            planned_tasks
        ) if planned_tasks else 0.7
        success_rate = self._estimate_wave_success_rate(planned_tasks)

        # Create wave plan
        wave_plan = WavePlan(
            wave=wave,
            planned_tasks=planned_tasks,
            total_tasks=len(planned_tasks),
            estimated_success_rate=success_rate,
            estimated_avg_confidence=avg_confidence,
            high_risk_count=high_risk_count,
            deferred_tasks=deferred,
            safety_rationale=f"Safety gates enforced: {len(planned_tasks)} approved, {len(deferred)} deferred",
        )

        self.planned_tasks.extend(planned_tasks)
        return wave_plan

    def _generate_wave_tasks(self, wave: int) -> List[Dict[str, Any]]:
        """Generate candidate tasks for a wave."""
        tasks = []

        # Strategy 1: Based on Phase 12 success patterns
        insights = self.meta_engine.get_insights()
        success_patterns = [i for i in insights if i.insight_type == "success_pattern"]

        for idx, pattern in enumerate(success_patterns[:2]):  # Use top 2 patterns
            task = {
                "task_id": f"wave{wave}_task{idx+1}",
                "title": f"Execute pattern: {pattern.description[:40]}",
                "tool": "web_action",
                "risk_level": "LOW",
                "confidence": 0.85,
                "priority": 10,
                "dependencies": [],
            }
            tasks.append(task)

        # Strategy 2: Medium-risk exploration tasks
        task = {
            "task_id": f"wave{wave}_exploration",
            "title": f"Explore operational boundary (wave {wave})",
            "tool": "web_action",
            "risk_level": "MEDIUM",
            "confidence": 0.70,
            "priority": 7,
            "dependencies": [t["task_id"] for t in tasks],
        }
        tasks.append(task)

        # Strategy 3: High-confidence LOW-risk consolidation
        task = {
            "task_id": f"wave{wave}_consolidation",
            "title": f"Consolidate successful patterns",
            "tool": "analysis",
            "risk_level": "LOW",
            "confidence": 0.90,
            "priority": 8,
            "dependencies": [t["task_id"] for t in tasks if t.get("risk_level") == "LOW"],
        }
        tasks.append(task)

        return tasks

    def _select_heuristics(self, task: Dict[str, Any]) -> List[Any]:
        """Select applicable heuristics for a task."""
        risk_level = task.get("risk_level", "MEDIUM").lower()
        applicable = []

        for heuristic in self.meta_engine.get_heuristics():
            if (
                heuristic.applicability == "universal"
                or heuristic.applicability == f"{risk_level}_risk"
            ):
                applicable.append(heuristic)

        return applicable

    def _evaluate_task_safety(self, task: Dict[str, Any]) -> Tuple[str, str]:
        """Evaluate if task can be executed."""
        risk_level = task.get("risk_level", "MEDIUM")
        confidence = task.get("confidence", 0.7)
        high_risk_threshold = self.policy.get("high_risk_threshold", 0.8)

        if risk_level == "LOW":
            if confidence >= 0.5:
                return "APPROVED", "LOW risk with sufficient confidence"
            else:
                return "DEFERRED", "Confidence below threshold for LOW risk (0.5)"

        elif risk_level == "MEDIUM":
            if confidence >= 0.75:
                return "APPROVED", "MEDIUM risk with sufficient confidence"
            else:
                return "DEFERRED", "Confidence below threshold for MEDIUM risk (0.75)"

        elif risk_level == "HIGH":
            if confidence >= high_risk_threshold:
                return "APPROVED", f"HIGH risk with sufficient confidence ({high_risk_threshold})"
            else:
                return "DEFERRED", f"HIGH risk requires confidence >= {high_risk_threshold}; deferring"

        else:
            return "DEFERRED", "UNKNOWN risk level; deferring"

    def _estimate_wave_success_rate(self, tasks: List[PlannedTask]) -> float:
        """Estimate success rate for wave."""
        if not tasks:
            return 0.0

        success_rates = []
        for task in tasks:
            # Base success rate by risk level
            base_rate = {
                "LOW": 0.90,
                "MEDIUM": 0.75,
                "HIGH": 0.60,
            }
            base = base_rate.get(task.risk_level, 0.70)

            # Adjust by confidence
            adjusted = base * (0.5 + task.confidence)
            success_rates.append(min(adjusted, 0.95))

        return sum(success_rates) / len(success_rates) if success_rates else 0.7

    def _predict_outcome(self, task: Dict[str, Any]) -> str:
        """Predict likely outcome of task."""
        confidence = task.get("confidence", 0.7)
        risk_level = task.get("risk_level", "MEDIUM")

        if confidence >= 0.85:
            return f"High probability of success for {risk_level} risk task"
        elif confidence >= 0.70:
            return f"Moderate probability of success for {risk_level} risk task"
        else:
            return f"Lower probability of success; deferral may be optimal"

    def write_wave_plans(self) -> None:
        """Write planned waves to output directory."""
        for wave_plan in self.wave_plans:
            wave_dir = self.output_dir / f"wave_{wave_plan.wave}"
            wave_dir.mkdir(exist_ok=True)

            # Write planned tasks
            with open(wave_dir / "planned_tasks.jsonl", "w") as f:
                for task in wave_plan.planned_tasks:
                    f.write(json.dumps(asdict(task)) + "\n")

            # Write wave plan summary
            with open(wave_dir / "wave_plan.json", "w") as f:
                plan_dict = asdict(wave_plan)
                plan_dict["planned_tasks"] = [asdict(t) for t in wave_plan.planned_tasks]
                json.dump(plan_dict, f, indent=2)

    def get_plans(self) -> List[WavePlan]:
        """Return all wave plans."""
        return self.wave_plans

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of planning results."""
        return {
            "total_waves": len(self.wave_plans),
            "total_planned_tasks": len(self.planned_tasks),
            "waves": [
                {
                    "wave": plan.wave,
                    "planned_tasks": plan.total_tasks,
                    "deferred_tasks": len(plan.deferred_tasks),
                    "estimated_success_rate": plan.estimated_success_rate,
                    "estimated_avg_confidence": plan.estimated_avg_confidence,
                }
                for plan in self.wave_plans
            ],
        }

