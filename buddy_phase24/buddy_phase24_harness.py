"""
Phase 24: Harness - End-to-end orchestration pipeline

Coordinates Phase 21 plans through Phase 24 orchestration and produces Phase 25+ outputs.
Implements the full orchestration cycle with proper state management and audit trails.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path
from .buddy_phase24_tool_orchestrator import ToolOrchestrator, ToolExecutionPlan
from .buddy_phase24_feedback_loop import FeedbackLoop, ToolOutcome
from .buddy_phase24_monitor import Monitor


@dataclass
class Phase24ExecutionConfig:
    """Configuration for Phase 24 execution"""
    output_dir: Path
    dry_run_only: bool = False
    max_live_escalations: int = 5
    approval_required_for_high_risk: bool = True
    confidence_threshold_for_live: float = 0.75
    enable_rollback_on_failure: bool = True


class Phase24Harness:
    """
    End-to-end orchestration pipeline for Phase 24
    
    Responsibilities:
    1. Load Phase 21 plans
    2. Coordinate Phase 22 validation
    3. Run Phase 24 orchestration
    4. Emit outputs for Phase 25+
    """
    
    def __init__(self, config: Phase24ExecutionConfig):
        self.config = config
        self.orchestrator = ToolOrchestrator()
        self.feedback_loop = FeedbackLoop()
        self.monitor = Monitor()
        self.execution_log: List[Dict] = []
        self.phase21_plans: List[Dict] = []
        self.phase22_validations: List[Dict] = []
    
    def load_phase21_plans(self, plans: List[Dict]) -> bool:
        """
        Load execution plans from Phase 21
        
        Returns: bool indicating if load successful
        """
        try:
            self.phase21_plans = plans
            return True
        except Exception as e:
            print(f"Failed to load Phase 21 plans: {e}")
            return False
    
    def load_phase22_validations(self, validations: List[Dict]) -> bool:
        """
        Load validation results from Phase 22
        
        Returns: bool indicating if load successful
        """
        try:
            self.phase22_validations = validations
            return True
        except Exception as e:
            print(f"Failed to load Phase 22 validations: {e}")
            return False
    
    def execute_orchestration_pipeline(self) -> Dict:
        """
        Execute the complete Phase 24 pipeline
        
        Steps:
        1. For each Phase 21 plan:
           a. Validate against Phase 22 results
           b. Create ToolExecutionPlan
           c. Execute through orchestrator
           d. Collect outcomes
           e. Generate feedback signals
           f. Update monitoring
        2. Emit final outputs
        """
        pipeline_result = {
            "pipeline_id": f"phase24_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "plans_processed": 0,
            "plans_successful": 0,
            "plans_failed": 0,
            "total_tools_executed": 0,
            "total_conflicts": 0,
            "total_rollbacks": 0,
            "orchestration_results": []
        }
        
        for i, phase21_plan in enumerate(self.phase21_plans):
            # Find corresponding Phase 22 validation
            phase22_validation = None
            if i < len(self.phase22_validations):
                phase22_validation = self.phase22_validations[i]
            
            # Create execution plan
            execution_plan = self._create_execution_plan(
                phase21_plan,
                phase22_validation
            )
            
            # Execute orchestration
            result = self.orchestrator.execute_orchestration_cycle(execution_plan)
            
            # Collect outcomes and update feedback loop
            for tool_result in result.tool_results:
                outcome = ToolOutcome(
                    tool_name=tool_result["tool_name"],
                    agent_id=tool_result["result"]["agent_id"],
                    execution_mode=tool_result["result"]["execution_mode"],
                    success=tool_result["status"] == "executed",
                    confidence_predicted=tool_result["result"].get("confidence", 0.5),
                    execution_time_seconds=0.1  # Simplified
                )
                self.feedback_loop.record_outcome(outcome)
            
            # Update monitoring
            orchestrator_summary = self.orchestrator.emit_orchestration_summary()
            self.monitor.update_metrics(orchestrator_summary)
            
            # Log execution
            self.execution_log.append({
                "plan_index": i,
                "plan_id": execution_plan.plan_id,
                "result": asdict(result)
            })
            
            pipeline_result["plans_processed"] += 1
            if result.successful_executions > 0:
                pipeline_result["plans_successful"] += 1
            else:
                pipeline_result["plans_failed"] += 1
            
            pipeline_result["total_tools_executed"] += result.successful_executions
            pipeline_result["total_conflicts"] += result.conflicts_detected
            pipeline_result["total_rollbacks"] += result.rollbacks_executed
            pipeline_result["orchestration_results"].append(asdict(result))
        
        pipeline_result["end_time"] = datetime.now(timezone.utc).isoformat()
        
        # Generate final outputs
        self._emit_outputs(pipeline_result)
        
        return pipeline_result
    
    def _create_execution_plan(self, 
                              phase21_plan: Dict,
                              phase22_validation: Optional[Dict]) -> ToolExecutionPlan:
        """Create ToolExecutionPlan from Phase 21 and 22 data"""
        
        # Extract agent assignments from Phase 21
        agent_assignments = phase21_plan.get("agent_assignments", {
            "agent_0": ["vision_inspect", "form_fill"],
            "agent_1": ["button_click"],
            "agent_2": ["memory_search"],
            "agent_3": ["goal_query"]
        })
        
        # Extract execution order
        execution_order = phase21_plan.get("execution_order", 
                                          list(set(
                                              tool 
                                              for tools in agent_assignments.values() 
                                              for tool in tools
                                          )))
        
        # Extract confidence scores or use defaults
        confidence_scores = phase21_plan.get("confidence_scores", {})
        for tool in execution_order:
            if tool not in confidence_scores:
                confidence_scores[tool] = 0.7  # Default confidence
        
        return ToolExecutionPlan(
            plan_id=f"exec_plan_{len(self.execution_log)}",
            agent_assignments=agent_assignments,
            execution_order=execution_order,
            confidence_scores=confidence_scores,
            phase21_plan_id=phase21_plan.get("plan_id"),
            phase22_validation_id=phase22_validation.get("validation_id") if phase22_validation else None
        )
    
    def _emit_outputs(self, pipeline_result: Dict):
        """
        Emit all Phase 24 outputs to files
        
        Files generated:
        - tool_execution_log.jsonl
        - orchestration_summary.json
        - execution_state_transitions.jsonl
        - tool_conflicts.json
        - rollback_events.jsonl
        - learning_signals.jsonl
        - system_health.json
        """
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Tool execution log (JSONL)
        execution_log_file = self.config.output_dir / "tool_execution_log.jsonl"
        with open(execution_log_file, 'w') as f:
            for entry in self.execution_log:
                f.write(json.dumps(entry) + '\n')
        
        # 2. Orchestration summary
        summary_file = self.config.output_dir / "orchestration_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(pipeline_result, f, indent=2)
        
        # 3. Execution state transitions (JSONL)
        transitions_file = self.config.output_dir / "execution_state_transitions.jsonl"
        with open(transitions_file, 'w') as f:
            summary = self.orchestrator.emit_orchestration_summary()
            for transition in summary.get("state_transitions", []):
                f.write(json.dumps(transition) + '\n')
        
        # 4. Tool conflicts
        conflicts_file = self.config.output_dir / "tool_conflicts.json"
        conflict_summary = self.orchestrator.conflict_resolver.get_conflict_summary()
        with open(conflicts_file, 'w') as f:
            json.dump(conflict_summary, f, indent=2)
        
        # 5. Rollback events (JSONL)
        rollback_file = self.config.output_dir / "rollback_events.jsonl"
        # Simplified: track rollback summary
        with open(rollback_file, 'w') as f:
            f.write(json.dumps({
                "total_rollbacks": pipeline_result["total_rollbacks"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }) + '\n')
        
        # 6. Learning signals (JSONL)
        signals_file = self.config.output_dir / "learning_signals.jsonl"
        with open(signals_file, 'w') as f:
            # Analyze and generate signals
            self.feedback_loop.analyze_tool_reliability()
            self.feedback_loop.analyze_execution_modes()
            self.feedback_loop.analyze_confidence_calibration()
            
            for signal in self.feedback_loop.export_signals():
                f.write(json.dumps(signal) + '\n')
        
        # 7. System health
        health_file = self.config.output_dir / "system_health.json"
        health = self.monitor.calculate_health_score()
        anomalies = self.monitor.detect_anomalies()
        health_report = {
            "health_assessment": health,
            "anomalies": [asdict(a) for a in anomalies],
            "metrics": self.monitor.get_metrics_summary(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(health_file, 'w') as f:
            json.dump(health_report, f, indent=2)
