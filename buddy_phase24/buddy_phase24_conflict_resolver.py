"""
Phase 24: Conflict Resolver - Detect and resolve multi-agent tool conflicts

Identifies resource conflicts, ordering constraints, and execution incompatibilities.
Implements resolution strategies: delay, reassign, downgrade, or abort.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from datetime import datetime, timezone


class ConflictType(Enum):
    """Types of conflicts that can occur"""
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"        # Tools accessing same resource
    ORDERING_CONFLICT = "ORDERING_CONFLICT"        # Dependency ordering issue
    RATE_LIMIT_CONFLICT = "RATE_LIMIT_CONFLICT"    # External rate limit exceeded
    DUPLICATE_ACTION = "DUPLICATE_ACTION"          # Identical irreversible action twice
    PERMISSION_CONFLICT = "PERMISSION_CONFLICT"    # Permission denied
    TIMEOUT_CONFLICT = "TIMEOUT_CONFLICT"          # Concurrent timeouts


class ResolutionStrategy(Enum):
    """Conflict resolution strategies"""
    DELAY = "DELAY"              # Delay execution
    REASSIGN = "REASSIGN"        # Reassign to different agent
    DOWNGRADE = "DOWNGRADE"      # Downgrade execution mode
    ABORT = "ABORT"              # Abort execution


@dataclass
class Conflict:
    """Represents a detected conflict"""
    conflict_type: ConflictType
    tool_1: str
    tool_2: str
    agent_1: str
    agent_2: str
    severity: int  # 1-10
    description: str
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class ConflictResolution:
    """Resolution for a conflict"""
    conflict: Conflict
    strategy: ResolutionStrategy
    action: str  # Specific action to take
    delay_seconds: Optional[int] = None
    reassign_to_agent: Optional[str] = None
    downgrade_to_mode: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class ConflictResolver:
    """
    Detects and resolves multi-agent tool conflicts
    
    Maintains:
    - Tool dependency graph
    - Resource usage tracking
    - Rate limit state
    - Execution history for duplicate detection
    """
    
    def __init__(self):
        self.conflicts: List[Conflict] = []
        self.resolutions: List[ConflictResolution] = []
        self.active_tools: Dict[str, str] = {}  # tool_name -> agent_id
        self.tool_dependencies: Dict[str, Set[str]] = self._build_dependency_graph()
        self.resource_locks: Dict[str, str] = {}  # resource -> agent_id
        self.rate_limit_state: Dict[str, int] = {}  # service -> remaining_quota
        self.execution_history: List[Dict] = []
        self.max_conflicts_before_abort = 5
    
    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build tool dependency relationships"""
        return {
            "button_click": {"vision_inspect", "form_fill"},
            "form_fill": {"vision_inspect"},
            "ghl_create_contact": {"ghl_search"},
            "mployer_add_contact": {"mployer_search"},
            "msgraph_send_email": {"memory_search"},
            "web_action_irreversible": {"vision_inspect", "button_click"}
        }
    
    def detect_conflicts(self, 
                        planned_tools: Dict[str, List[str]]) -> List[Conflict]:
        """
        Detect conflicts in planned tool usage across agents
        
        Args:
            planned_tools: Dict[agent_id] -> List[tool_name]
        
        Returns: List of detected conflicts
        """
        detected_conflicts = []
        
        # Check for resource conflicts
        for agent_id, tools in planned_tools.items():
            for tool_name in tools:
                # Check if tool already in use
                if tool_name in self.active_tools:
                    conflicting_agent = self.active_tools[tool_name]
                    if conflicting_agent != agent_id:
                        conflict = Conflict(
                            conflict_type=ConflictType.RESOURCE_CONFLICT,
                            tool_1=tool_name,
                            tool_2=tool_name,
                            agent_1=agent_id,
                            agent_2=conflicting_agent,
                            severity=8,
                            description=f"Tool '{tool_name}' is already in use by agent {conflicting_agent}"
                        )
                        detected_conflicts.append(conflict)
        
        # Check for ordering conflicts (dependencies)
        for agent_id, tools in planned_tools.items():
            for i, tool in enumerate(tools):
                dependencies = self.tool_dependencies.get(tool, set())
                for dependency in dependencies:
                    # Check if dependency comes after this tool
                    if dependency in tools and tools.index(dependency) < i:
                        conflict = Conflict(
                            conflict_type=ConflictType.ORDERING_CONFLICT,
                            tool_1=tool,
                            tool_2=dependency,
                            agent_1=agent_id,
                            agent_2=agent_id,
                            severity=6,
                            description=f"Tool '{tool}' depends on '{dependency}' but '{dependency}' runs after"
                        )
                        detected_conflicts.append(conflict)
        
        # Check for duplicate irreversible actions
        for agent_id, tools in planned_tools.items():
            for tool in tools:
                if tool in ["ghl_create_contact", "mployer_add_contact", "msgraph_send_email"]:
                    # Check execution history
                    recent_count = sum(1 for h in self.execution_history[-10:]
                                      if h.get("tool_name") == tool)
                    if recent_count > 0:
                        conflict = Conflict(
                            conflict_type=ConflictType.DUPLICATE_ACTION,
                            tool_1=tool,
                            tool_2=tool,
                            agent_1=agent_id,
                            agent_2=agent_id,
                            severity=9,
                            description=f"Attempting to execute irreversible tool '{tool}' multiple times"
                        )
                        detected_conflicts.append(conflict)
        
        self.conflicts.extend(detected_conflicts)
        return detected_conflicts
    
    def resolve_conflicts(self, conflicts: List[Conflict]) -> List[ConflictResolution]:
        """
        Resolve detected conflicts using appropriate strategies
        
        Returns: List of resolutions
        """
        resolutions = []
        
        for conflict in conflicts:
            resolution = self._choose_resolution_strategy(conflict)
            resolutions.append(resolution)
            self.resolutions.append(resolution)
        
        return resolutions
    
    def _choose_resolution_strategy(self, conflict: Conflict) -> ConflictResolution:
        """Choose best resolution strategy for a conflict"""
        
        # RESOURCE_CONFLICT: Try to delay second tool
        if conflict.conflict_type == ConflictType.RESOURCE_CONFLICT:
            return ConflictResolution(
                conflict=conflict,
                strategy=ResolutionStrategy.DELAY,
                action=f"Delay tool '{conflict.tool_2}' on agent '{conflict.agent_2}'",
                delay_seconds=5
            )
        
        # ORDERING_CONFLICT: Reassign the dependent tool
        elif conflict.conflict_type == ConflictType.ORDERING_CONFLICT:
            return ConflictResolution(
                conflict=conflict,
                strategy=ResolutionStrategy.REASSIGN,
                action=f"Reassign '{conflict.tool_1}' to later phase",
                reassign_to_agent=conflict.agent_1
            )
        
        # DUPLICATE_ACTION: Always abort irreversible duplicates
        elif conflict.conflict_type == ConflictType.DUPLICATE_ACTION:
            return ConflictResolution(
                conflict=conflict,
                strategy=ResolutionStrategy.ABORT,
                action=f"Abort duplicate irreversible action '{conflict.tool_1}'"
            )
        
        # RATE_LIMIT_CONFLICT: Downgrade execution mode
        elif conflict.conflict_type == ConflictType.RATE_LIMIT_CONFLICT:
            return ConflictResolution(
                conflict=conflict,
                strategy=ResolutionStrategy.DOWNGRADE,
                action=f"Downgrade tool '{conflict.tool_1}' to DRY_RUN mode",
                downgrade_to_mode="DRY_RUN"
            )
        
        # Default: Delay
        else:
            return ConflictResolution(
                conflict=conflict,
                strategy=ResolutionStrategy.DELAY,
                action=f"Delay tool execution to resolve {conflict.conflict_type.value}",
                delay_seconds=3
            )
    
    def register_tool_execution(self, tool_name: str, agent_id: str):
        """Register tool as active"""
        self.active_tools[tool_name] = agent_id
        self.execution_history.append({
            "tool_name": tool_name,
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def unregister_tool_execution(self, tool_name: str):
        """Unregister tool as no longer active"""
        if tool_name in self.active_tools:
            del self.active_tools[tool_name]
    
    def update_rate_limit(self, service: str, remaining: int):
        """Update rate limit for external service"""
        self.rate_limit_state[service] = remaining
    
    def check_rate_limit(self, service: str) -> bool:
        """Check if service has rate limit quota"""
        return self.rate_limit_state.get(service, 100) > 0
    
    def get_conflict_summary(self) -> Dict:
        """Get summary of all conflicts"""
        return {
            "total_detected": len(self.conflicts),
            "total_resolved": len(self.resolutions),
            "by_type": {
                ct.value: len([c for c in self.conflicts if c.conflict_type == ct])
                for ct in ConflictType
            },
            "by_strategy": {
                rs.value: len([r for r in self.resolutions if r.strategy == rs])
                for rs in ResolutionStrategy
            },
            "active_tools": self.active_tools,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
