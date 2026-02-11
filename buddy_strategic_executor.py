"""
Phase 12: Strategic Executor with Adaptive Decision-Making
Extends SimulatedExecutor with strategic reasoning based on Phase 11 learning insights.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from buddy_dynamic_task_scheduler import TaskScheduler, TaskPriority, RiskLevel
from phase2_confidence import GradedConfidenceCalculator, ConfidenceFactors
from buddy_simulated_executor import SimulatedExecutor, TaskOutcome
from buddy_learning_analyzer import LearningAnalyzer, LearningInsight

logger = logging.getLogger(__name__)


@dataclass
class StrategicDecision:
    """Represents a strategic decision made during execution."""
    task_id: str
    decision_type: str  # confidence_elevation, alternate_path, priority_boost, deferred_retry
    rationale: str
    supporting_insights: List[str]
    confidence_before: float
    confidence_after: float
    timestamp: str


class StrategicExecutor(SimulatedExecutor):
    """
    Executes workflows with strategic decision-making based on learning insights.
    
    Capabilities:
    - Elevate confidence for tasks matching successful patterns
    - Choose alternate paths based on deferred task analysis
    - Boost priority for high-value tasks
    - Apply retry strategies informed by past outcomes
    """
    
    def __init__(self, output_dir: Path, learning_insights: List[LearningInsight], wave: int):
        super().__init__(output_dir)
        self.learning_insights = learning_insights
        self.wave = wave
        self.strategic_decisions: List[StrategicDecision] = []
        
        # Build insight index for quick lookup
        self._index_insights()
        
    def _index_insights(self):
        """Index insights by type for efficient lookup."""
        self.insights_by_type: Dict[str, List[LearningInsight]] = {}
        for insight in self.learning_insights:
            insight_type = insight.get("insight_type", "unknown")
            if insight_type not in self.insights_by_type:
                self.insights_by_type[insight_type] = []
            self.insights_by_type[insight_type].append(insight)
    
    def _apply_strategic_adjustments(
        self,
        task_id: str,
        risk_level: RiskLevel,
        confidence: float
    ) -> tuple[float, Optional[StrategicDecision]]:
        """
        Apply strategic adjustments to task confidence based on learning insights.
        
        Returns:
            Tuple of (adjusted_confidence, strategic_decision)
        """
        adjusted_confidence = confidence
        decision = None
        
        # Check for deferred high-risk patterns
        if risk_level == RiskLevel.HIGH and confidence < 0.8:
            deferred_insights = self.insights_by_type.get("deferred_high_risk", [])
            if deferred_insights:
                # Check if this is a recurring pattern we can elevate
                for insight in deferred_insights:
                    if insight.get("confidence", 0) >= 0.9:  # High-confidence insight
                        # Boost confidence by 0.15 for strategic elevation
                        adjusted_confidence = min(confidence + 0.15, 0.85)
                        decision = StrategicDecision(
                            task_id=task_id,
                            decision_type="confidence_elevation",
                            rationale=f"Elevated confidence based on high-confidence insight: {insight.get('description')}",
                            supporting_insights=[insight.get("recommendation", "")],
                            confidence_before=confidence,
                            confidence_after=adjusted_confidence,
                            timestamp=datetime.utcnow().isoformat()
                        )
                        logger.info(f"Strategic elevation: {task_id} confidence {confidence:.2f} → {adjusted_confidence:.2f}")
                        break
        
        # Check for high-success risk level patterns
        success_insights = self.insights_by_type.get("high_success_risk_level", [])
        for insight in success_insights:
            desc = insight.get("description", "")
            if risk_level.name in desc and "100% success" in desc:
                # Small boost for tasks in proven successful risk categories
                boost = 0.05
                adjusted_confidence = min(confidence + boost, 1.0)
                if decision is None:  # Don't override elevation decision
                    decision = StrategicDecision(
                        task_id=task_id,
                        decision_type="pattern_boost",
                        rationale=f"Confidence boost for {risk_level.name} risk category with proven success",
                        supporting_insights=[insight.get("description", "")],
                        confidence_before=confidence,
                        confidence_after=adjusted_confidence,
                        timestamp=datetime.utcnow().isoformat()
                    )
                break
        
        return adjusted_confidence, decision
    
    def execute_wave(
        self,
        tasks: List[Dict[str, Any]],
        workflow_id: str
    ) -> tuple[List[Dict[str, Any]], List[Dict], List[Dict]]:
        """
        Execute wave with strategic decision-making.
        
        Returns:
            Tuple of (outcomes, self_questions, confidence_updates)
        """
        logger.info(f"Strategic execution: wave {self.wave}, {len(tasks)} tasks")
        
        # Apply strategic adjustments before execution
        adjusted_tasks = []
        for task in tasks:
            task_copy = task.copy()
            original_confidence = task_copy.get("confidence_score", 0.7)
            risk_str = task_copy.get("risk_level", "LOW").upper()
            risk_level = RiskLevel[risk_str]
            
            adjusted_confidence, decision = self._apply_strategic_adjustments(
                task_copy["task_id"],
                risk_level,
                original_confidence
            )
            
            task_copy["confidence_score"] = adjusted_confidence
            adjusted_tasks.append(task_copy)
            
            if decision:
                self.strategic_decisions.append(decision)
        
        # Simulate task execution
        outcomes = []
        questions = []
        updates = []
        
        for task in adjusted_tasks:
            task_id = task["task_id"]
            confidence = task["confidence_score"]
            risk_str = task.get("risk_level", "LOW").upper()
            risk_level = RiskLevel[risk_str]
            
            # Check if should defer
            if risk_level == RiskLevel.HIGH and confidence < 0.8:
                outcome = {
                    "task_id": task_id,
                    "wave": self.wave,
                    "workflow_id": workflow_id,
                    "status": "deferred",
                    "risk_level": risk_str,
                    "confidence_score": confidence,
                    "retries": 0,
                    "execution_time_ms": 0.0,
                    "dry_run": True,
                    "error": None,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Simulate execution
                outcome = {
                    "task_id": task_id,
                    "wave": self.wave,
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "risk_level": risk_str,
                    "confidence_score": confidence,
                    "retries": 1,
                    "execution_time_ms": 20.0,
                    "dry_run": True,
                    "error": None,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            outcomes.append(outcome)
            
            # Generate self-questions
            for q_type in ["success", "dependencies", "side_effects", "correctness"]:
                questions.append({
                    "task_id": task_id,
                    "wave": self.wave,
                    "question": f"[{q_type.upper()}] Did the task {q_type}?",
                    "answer": "yes",
                    "confidence": 0.85,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Generate confidence update
            new_confidence = confidence + 0.05 if outcome["status"] == "completed" else confidence - 0.05
            updates.append({
                "task_id": task_id,
                "wave": self.wave,
                "confidence_before": confidence,
                "confidence_after": new_confidence,
                "adjustment_reason": "post_execution_recalibration",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Log strategic decisions
        self._log_strategic_decisions()
        
        return outcomes, questions, updates
    
    def _log_strategic_decisions(self):
        """Log all strategic decisions for this wave."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        decisions_file = self.output_dir / f"strategic_decisions_wave_{self.wave}.jsonl"
        with open(decisions_file, "w") as f:
            for decision in self.strategic_decisions:
                f.write(json.dumps(asdict(decision)) + "\n")
        
        logger.info(f"Logged {len(self.strategic_decisions)} strategic decisions")
    
    def get_strategic_summary(self) -> Dict[str, Any]:
        """Get summary of strategic decisions for reporting."""
        return {
            "total_decisions": len(self.strategic_decisions),
            "by_type": self._count_decisions_by_type(),
            "avg_confidence_boost": self._avg_confidence_boost(),
            "decisions": [asdict(d) for d in self.strategic_decisions]
        }
    
    def _count_decisions_by_type(self) -> Dict[str, int]:
        """Count decisions by type."""
        counts = {}
        for decision in self.strategic_decisions:
            dtype = decision.decision_type
            counts[dtype] = counts.get(dtype, 0) + 1
        return counts
    
    def _avg_confidence_boost(self) -> float:
        """Calculate average confidence boost across all decisions."""
        if not self.strategic_decisions:
            return 0.0
        total_boost = sum(
            d.confidence_after - d.confidence_before
            for d in self.strategic_decisions
        )
        return total_boost / len(self.strategic_decisions)

