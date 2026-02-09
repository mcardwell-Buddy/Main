"""
Phase 17: Continuous Autonomous Execution - Task Executor

This module executes planned tasks from Phase 16 using learned heuristics and policies.
It applies adaptive strategies in real-time and provides continuous feedback.
"""

import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any


class RiskLevel(Enum):
    """Risk level classification"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ExecutionStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Heuristic:
    """Learned heuristic from Phase 16"""
    heuristic_id: str
    category: str
    name: str
    description: str
    rule: Dict[str, Any]
    confidence: float
    applicability: Dict[str, Any]
    expected_improvement: float


@dataclass
class Task:
    """Task to execute"""
    task_id: str
    wave: int
    risk_level: RiskLevel
    confidence: float
    priority: int
    heuristics_applied: List[str]
    predicted_success_rate: float
    predicted_confidence_delta: float
    approval_status: str
    reason: str
    
    # Execution tracking
    status: ExecutionStatus = ExecutionStatus.PENDING
    attempts: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    actual_confidence: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_id: str
    wave: int
    status: ExecutionStatus
    initial_confidence: float
    final_confidence: float
    confidence_delta: float
    execution_time_ms: float
    attempts: int
    heuristics_applied: List[str]
    error_message: Optional[str]
    timestamp: str


class ContinuousAutonomousExecutor:
    """
    Executes planned tasks continuously using learned heuristics.
    Provides real-time adaptation and feedback to the meta-learning system.
    """
    
    def __init__(self, phase16_dir: Path, phase17_output_dir: Path):
        self.phase16_dir = Path(phase16_dir)
        self.phase17_output_dir = Path(phase17_output_dir)
        self.phase17_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.heuristics: List[Heuristic] = []
        self.tasks: List[Task] = []
        self.results: List[ExecutionResult] = []
        
        # Execution statistics
        self.stats = {
            "tasks_executed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "total_retries": 0,
            "avg_execution_time_ms": 0.0,
            "avg_confidence_improvement": 0.0
        }
    
    def load_heuristics(self) -> int:
        """Load learned heuristics from Phase 16"""
        heuristics_file = self.phase16_dir / "heuristics.jsonl"
        
        if not heuristics_file.exists():
            raise FileNotFoundError(f"Heuristics file not found: {heuristics_file}")
        
        with open(heuristics_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    heuristic = Heuristic(
                        heuristic_id=data['heuristic_id'],
                        category=data['category'],
                        name=data['name'],
                        description=data['description'],
                        rule=data['rule'],
                        confidence=data['confidence'],
                        applicability=data['applicability'],
                        expected_improvement=data['expected_improvement']
                    )
                    self.heuristics.append(heuristic)
        
        return len(self.heuristics)
    
    def load_planned_tasks(self) -> int:
        """Load planned tasks from Phase 16"""
        tasks_file = self.phase16_dir / "planned_tasks.jsonl"
        
        if not tasks_file.exists():
            raise FileNotFoundError(f"Planned tasks file not found: {tasks_file}")
        
        with open(tasks_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    task = Task(
                        task_id=data['task_id'],
                        wave=data['wave'],
                        risk_level=RiskLevel(data['risk_level']),
                        confidence=data['confidence'],
                        priority=data['priority'],
                        heuristics_applied=data.get('heuristics_applied', []),
                        predicted_success_rate=data['predicted_success_rate'],
                        predicted_confidence_delta=data['predicted_confidence_delta'],
                        approval_status=data['approval_status'],
                        reason=data['reason']
                    )
                    self.tasks.append(task)
        
        return len(self.tasks)
    
    def apply_heuristics_to_task(self, task: Task) -> List[str]:
        """Apply relevant heuristics to a task before execution"""
        applied = []
        
        for heuristic in self.heuristics:
            if self._is_heuristic_applicable(heuristic, task):
                # Apply heuristic transformations
                if heuristic.category == "confidence_elevation":
                    self._apply_confidence_boost(heuristic, task)
                    applied.append(heuristic.heuristic_id)
                elif heuristic.category == "risk_assessment":
                    # Already applied during planning, track for execution
                    applied.append(heuristic.heuristic_id)
                elif heuristic.category == "task_prioritization":
                    # Priority already set, but track usage
                    applied.append(heuristic.heuristic_id)
        
        return applied
    
    def _is_heuristic_applicable(self, heuristic: Heuristic, task: Task) -> bool:
        """Check if heuristic applies to task"""
        applicability = heuristic.applicability
        
        # Check confidence_elevation heuristics (H16_002)
        if heuristic.category == "confidence_elevation":
            if task.risk_level.value == "MEDIUM":
                conf_range = heuristic.rule.get("condition", {}).get("confidence_range", [0.7, 0.75])
                if conf_range[0] <= task.confidence <= conf_range[1]:
                    return True
        
        # Check risk_assessment heuristics (H16_003)
        elif heuristic.category == "risk_assessment":
            if task.status == ExecutionStatus.FAILED:
                applicable_risks = heuristic.applicability.get("applicable_risk_levels", [])
                if task.risk_level.value in applicable_risks:
                    return True
        
        # Task prioritization (H16_001) is always applicable
        elif heuristic.category == "task_prioritization":
            return True
        
        return False
    
    def _apply_confidence_boost(self, heuristic: Heuristic, task: Task):
        """Apply confidence boost from heuristic H16_002"""
        boost_amount = heuristic.rule.get("amount", 0.05)
        task.confidence = min(1.0, task.confidence + boost_amount)
    
    def execute_task(self, task: Task) -> ExecutionResult:
        """Execute a single task with heuristic-guided adaptation"""
        task.status = ExecutionStatus.RUNNING
        task.start_time = time.time()
        task.attempts += 1
        
        initial_confidence = task.confidence
        
        # Apply heuristics before execution
        heuristics_applied = self.apply_heuristics_to_task(task)
        task.heuristics_applied.extend(heuristics_applied)
        
        # Simulate task execution with intelligent success prediction
        # Success rate influenced by confidence and risk level
        success_probability = self._calculate_success_probability(task)
        
        # Simulate execution time (5-50ms based on risk)
        execution_delay = random.uniform(0.005, 0.05) if task.risk_level == RiskLevel.LOW else random.uniform(0.01, 0.05)
        time.sleep(execution_delay)
        
        # Determine success/failure
        if random.random() < success_probability:
            task.status = ExecutionStatus.SUCCESS
            # Successful execution improves confidence
            confidence_improvement = random.uniform(0.02, 0.08)
            task.actual_confidence = min(1.0, task.confidence + confidence_improvement)
            self.stats["tasks_succeeded"] += 1
        else:
            task.status = ExecutionStatus.FAILED
            # Failed execution reduces confidence
            confidence_penalty = random.uniform(0.01, 0.05)
            task.actual_confidence = max(0.0, task.confidence - confidence_penalty)
            task.error_message = f"Execution failed for {task.risk_level.value} risk task"
            self.stats["tasks_failed"] += 1
        
        task.end_time = time.time()
        execution_time_ms = (task.end_time - task.start_time) * 1000
        
        # Create result
        result = ExecutionResult(
            task_id=task.task_id,
            wave=task.wave,
            status=task.status,
            initial_confidence=initial_confidence,
            final_confidence=task.actual_confidence,
            confidence_delta=task.actual_confidence - initial_confidence,
            execution_time_ms=execution_time_ms,
            attempts=task.attempts,
            heuristics_applied=list(set(task.heuristics_applied)),
            error_message=task.error_message,
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        )
        
        self.results.append(result)
        self.stats["tasks_executed"] += 1
        
        return result
    
    def _calculate_success_probability(self, task: Task) -> float:
        """Calculate success probability based on task properties"""
        # Base probability from predicted success rate
        base_prob = task.predicted_success_rate
        
        # Adjust for confidence
        confidence_factor = task.confidence
        
        # Adjust for risk level
        risk_factors = {
            RiskLevel.LOW: 1.05,
            RiskLevel.MEDIUM: 0.95,
            RiskLevel.HIGH: 0.85
        }
        risk_factor = risk_factors.get(task.risk_level, 1.0)
        
        # Calculate final probability
        final_prob = base_prob * confidence_factor * risk_factor
        return min(1.0, max(0.0, final_prob))
    
    def retry_failed_task(self, task: Task) -> Optional[ExecutionResult]:
        """Retry a failed task using H16_003 heuristic"""
        # Find retry heuristic
        retry_heuristic = None
        for h in self.heuristics:
            if h.heuristic_id == "H16_003":
                retry_heuristic = h
                break
        
        if not retry_heuristic:
            return None
        
        max_retries = retry_heuristic.rule.get("max_retries", 3)
        if task.attempts >= max_retries:
            return None
        
        # Apply confidence penalty for retry
        confidence_penalty = retry_heuristic.rule.get("confidence_penalty", -0.05)
        task.confidence = max(0.0, task.confidence + confidence_penalty)
        task.status = ExecutionStatus.RETRYING
        
        self.stats["total_retries"] += 1
        
        # Re-execute
        return self.execute_task(task)
    
    def execute_wave(self, wave_num: int) -> List[ExecutionResult]:
        """Execute all tasks in a specific wave"""
        wave_tasks = [t for t in self.tasks if t.wave == wave_num]
        wave_results = []
        
        print(f"\n=== Executing Wave {wave_num} ({len(wave_tasks)} tasks) ===")
        
        for task in sorted(wave_tasks, key=lambda t: t.priority):
            print(f"  Executing {task.task_id} (Risk: {task.risk_level.value}, Confidence: {task.confidence:.2f})...")
            
            result = self.execute_task(task)
            wave_results.append(result)
            
            # Retry failed LOW/MEDIUM risk tasks
            if result.status == ExecutionStatus.FAILED and task.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                print(f"    → Failed! Attempting retry...")
                retry_result = self.retry_failed_task(task)
                if retry_result:
                    wave_results.append(retry_result)
                    if retry_result.status == ExecutionStatus.SUCCESS:
                        print(f"    → Retry succeeded!")
                    else:
                        print(f"    → Retry failed.")
            elif result.status == ExecutionStatus.SUCCESS:
                print(f"    → Success! Confidence: {result.initial_confidence:.2f} → {result.final_confidence:.2f}")
        
        return wave_results
    
    def execute_all_waves(self) -> Dict[str, Any]:
        """Execute all planned waves continuously"""
        print(f"\n{'='*70}")
        print(f"Phase 17: Continuous Autonomous Execution")
        print(f"{'='*70}")
        print(f"Loaded {len(self.heuristics)} heuristics from Phase 16")
        print(f"Loaded {len(self.tasks)} tasks across {max(t.wave for t in self.tasks)} waves")
        
        all_results = []
        
        for wave_num in sorted(set(t.wave for t in self.tasks)):
            wave_results = self.execute_wave(wave_num)
            all_results.extend(wave_results)
        
        # Calculate final statistics
        self._calculate_final_stats()
        
        return {
            "total_tasks": len(self.tasks),
            "total_waves": max(t.wave for t in self.tasks),
            "results": all_results,
            "statistics": self.stats
        }
    
    def _calculate_final_stats(self):
        """Calculate final execution statistics"""
        if self.stats["tasks_executed"] > 0:
            self.stats["success_rate"] = self.stats["tasks_succeeded"] / self.stats["tasks_executed"]
            
            # Average execution time
            total_time = sum(r.execution_time_ms for r in self.results)
            self.stats["avg_execution_time_ms"] = total_time / len(self.results)
            
            # Average confidence improvement
            total_delta = sum(r.confidence_delta for r in self.results)
            self.stats["avg_confidence_improvement"] = total_delta / len(self.results)
    
    def write_results(self):
        """Write execution results to output files"""
        # Write execution outcomes
        outcomes_file = self.phase17_output_dir / "execution_outcomes.jsonl"
        with open(outcomes_file, 'w', encoding='utf-8') as f:
            for result in self.results:
                outcome = {
                    "task_id": result.task_id,
                    "wave": result.wave,
                    "status": result.status.value,
                    "initial_confidence": result.initial_confidence,
                    "final_confidence": result.final_confidence,
                    "confidence_delta": result.confidence_delta,
                    "execution_time_ms": result.execution_time_ms,
                    "attempts": result.attempts,
                    "heuristics_applied": result.heuristics_applied,
                    "error_message": result.error_message,
                    "timestamp": result.timestamp
                }
                f.write(json.dumps(outcome) + '\n')
        
        # Write statistics
        stats_file = self.phase17_output_dir / "phase17_execution_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)
        
        print(f"\n✓ Results written to {self.phase17_output_dir}")


def main():
    """Main execution function"""
    phase16_dir = Path("outputs/phase16")
    phase17_output_dir = Path("outputs/phase17")
    
    executor = ContinuousAutonomousExecutor(phase16_dir, phase17_output_dir)
    
    # Load Phase 16 data
    num_heuristics = executor.load_heuristics()
    num_tasks = executor.load_planned_tasks()
    
    print(f"Loaded {num_heuristics} heuristics and {num_tasks} tasks")
    
    # Execute all waves
    execution_summary = executor.execute_all_waves()
    
    # Write results
    executor.write_results()
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"Execution Summary:")
    print(f"  Tasks Executed: {execution_summary['statistics']['tasks_executed']}")
    print(f"  Success Rate: {execution_summary['statistics']['success_rate']:.1%}")
    print(f"  Total Retries: {execution_summary['statistics']['total_retries']}")
    print(f"  Avg Execution Time: {execution_summary['statistics']['avg_execution_time_ms']:.2f}ms")
    print(f"  Avg Confidence Δ: {execution_summary['statistics']['avg_confidence_improvement']:+.4f}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
