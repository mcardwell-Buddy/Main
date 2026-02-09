"""
Phase 24: Tool Orchestrator - Central coordinator for multi-agent tool execution

Accepts plans from Phase 21/22, allocates tools to agents, enforces execution order,
and aggregates results across agents.
"""

import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional
from datetime import datetime, timezone
from .buddy_phase24_tool_contracts import tool_contract_registry, ExecutionMode
from .buddy_phase24_execution_controller import ExecutionController
from .buddy_phase24_conflict_resolver import ConflictResolver


@dataclass
class ToolExecutionPlan:
    """Plan for tool execution"""
    plan_id: str
    agent_assignments: Dict[str, List[str]]  # agent_id -> [tool_names]
    execution_order: List[str]  # Ordered list of tool executions
    confidence_scores: Dict[str, float]  # tool_name -> confidence
    phase21_plan_id: Optional[str] = None
    phase22_validation_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class OrchestrationResult:
    """Result of orchestration cycle"""
    plan_id: str
    total_tools: int
    successful_executions: int
    failed_executions: int
    tool_results: List[Dict] = field(default_factory=list)
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    rollbacks_executed: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ToolOrchestrator:
    """
    Central coordinator for multi-agent tool execution
    
    Responsibilities:
    - Accept and validate execution plans
    - Allocate tools to agents
    - Enforce execution order and dependencies
    - Validate tool contracts
    - Aggregate results
    - Emit audit outputs
    """
    
    def __init__(self):
        self.execution_controller = ExecutionController()
        self.conflict_resolver = ConflictResolver()
        self.active_plans: Dict[str, ToolExecutionPlan] = {}
        self.execution_history: List[OrchestrationResult] = []
    
    def register_tool_execution(self, plan: ToolExecutionPlan) -> tuple[bool, str]:
        """
        Register a new tool execution plan
        
        Validates against contracts and detects conflicts
        
        Returns: (success: bool, message: str)
        """
        # Validate all tools exist in contract registry
        all_tools = []
        for agent_tools in plan.agent_assignments.values():
            all_tools.extend(agent_tools)
        
        for tool_name in all_tools:
            valid, msg = tool_contract_registry.validate_tool_request(tool_name, ExecutionMode.MOCK)
            if not valid:
                return False, f"Invalid tool request: {msg}"
        
        # Detect conflicts
        conflicts = self.conflict_resolver.detect_conflicts(plan.agent_assignments)
        if conflicts:
            conflict_desc = f"Detected {len(conflicts)} conflict(s)"
            # Resolve conflicts automatically
            resolutions = self.conflict_resolver.resolve_conflicts(conflicts)
            return True, f"{conflict_desc}, {len(resolutions)} resolution(s) applied"
        
        self.active_plans[plan.plan_id] = plan
        return True, "Plan registered and validated"
    
    def allocate_tools(self, agent_id: str, tools: List[str]) -> Dict:
        """
        Allocate tools to specific agent
        
        Returns: Allocation result
        """
        allocation = {
            "agent_id": agent_id,
            "tools_allocated": len(tools),
            "tools": tools,
            "status": "allocated",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Register each tool with conflict resolver
        for tool in tools:
            self.conflict_resolver.register_tool_execution(tool, agent_id)
        
        return allocation
    
    def resolve_tool_conflicts(self) -> Dict:
        """
        Resolve any detected conflicts
        
        Returns: Resolution summary
        """
        summary = self.conflict_resolver.get_conflict_summary()
        return summary
    
    def execute_orchestration_cycle(self, plan: ToolExecutionPlan) -> OrchestrationResult:
        """
        Execute complete orchestration cycle for a plan
        
        1. Validate plan
        2. Detect conflicts
        3. Resolve conflicts
        4. Execute tools in order
        5. Aggregate results
        """
        result = OrchestrationResult(
            plan_id=plan.plan_id,
            total_tools=sum(len(tools) for tools in plan.agent_assignments.values()),
            successful_executions=0,
            failed_executions=0
        )
        
        # Validate plan registration
        valid, msg = self.register_tool_execution(plan)
        if not valid:
            result.failed_executions = result.total_tools
            return result
        
        # Detect conflicts
        conflicts = self.conflict_resolver.detect_conflicts(plan.agent_assignments)
        result.conflicts_detected = len(conflicts)
        
        if conflicts:
            resolutions = self.conflict_resolver.resolve_conflicts(conflicts)
            result.conflicts_resolved = len(resolutions)
        
        # Execute tools in order
        for tool_name in plan.execution_order:
            # Find agent for tool
            agent_id = None
            for agent, tools in plan.agent_assignments.items():
                if tool_name in tools:
                    agent_id = agent
                    break
            
            if not agent_id:
                result.failed_executions += 1
                continue
            
            # Get tool confidence
            confidence = plan.confidence_scores.get(tool_name, 0.5)
            
            # Get tool contract
            contract = tool_contract_registry.get(tool_name)
            if not contract:
                result.failed_executions += 1
                continue
            
            # Determine execution mode
            execution_mode = self.execution_controller.evaluate_execution_mode(
                contract, confidence
            )
            
            # Execute tool
            tool_result = self.execution_controller.execute_tool_action(
                tool_name=tool_name,
                action_data={
                    "agent_id": agent_id,
                    "confidence": confidence,
                    "execution_mode": execution_mode.value
                },
                execution_mode=execution_mode
            )
            
            result.tool_results.append(tool_result)
            result.successful_executions += 1
        
        self.execution_history.append(result)
        return result
    
    def emit_orchestration_summary(self) -> Dict:
        """
        Emit summary of orchestration activities
        
        Returns: Comprehensive summary for outputs
        """
        return {
            "active_plans": len(self.active_plans),
            "total_cycles_executed": len(self.execution_history),
            "execution_controller_status": self.execution_controller.get_execution_status(),
            "conflict_summary": self.conflict_resolver.get_conflict_summary(),
            "state_transitions": self.execution_controller.get_state_transitions(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_execution_history(self) -> List[Dict]:
        """Get history of all orchestration cycles"""
        return [asdict(result) for result in self.execution_history]
