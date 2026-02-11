"""
Parallelization Detector for Multi-Step Missions

Analyzes task steps to identify opportunities for parallel execution:
- Independent steps (no dependencies)
- Time savings calculation
- Execution graph generation
- Risk assessment for parallel execution

Philosophy:
- Automatic detection (not opt-in)
- Clear communication of opportunities
- Show time savings to user
- Conservative dependency analysis

Author: Buddy Phase 2 Architecture Team
Date: February 11, 2026
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Types of dependencies between steps"""
    DATA_DEPENDENCY = "data"  # Output of step A needed by step B
    BLOCKING = "blocking"  # Step A must wait for human action
    SEQUENTIAL = "sequential"  # Steps must run in order
    INDEPENDENT = "independent"  # Steps can run in parallel


@dataclass
class ParallelizationOpportunity:
    """
    Represents an opportunity for parallel execution.
    
    Example:
    - Steps [2, 3, 4] can run in parallel after step 1 completes
    - Time savings: 45 seconds
    - Risk: LOW (no data dependencies)
    """
    parallel_steps: List[int]  # Step numbers that can run in parallel
    depends_on_step: Optional[int] = None  # Must wait for this step first
    time_savings_seconds: float = 0.0  # Estimated time saved
    sequential_time_seconds: float = 0.0  # Time if run sequentially
    parallel_time_seconds: float = 0.0  # Time if run in parallel
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    risk_factors: List[str] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'parallel_steps': self.parallel_steps,
            'depends_on_step': self.depends_on_step,
            'time_savings_seconds': round(self.time_savings_seconds, 1),
            'sequential_time_seconds': round(self.sequential_time_seconds, 1),
            'parallel_time_seconds': round(self.parallel_time_seconds, 1),
            'risk_level': self.risk_level,
            'risk_factors': self.risk_factors,
            'description': self.description
        }
    
    def to_human_readable(self) -> str:
        """Generate human-readable description"""
        steps_str = ', '.join([f"Step {s}" for s in self.parallel_steps])
        
        if self.depends_on_step:
            timing = f"after Step {self.depends_on_step} completes"
        else:
            timing = "immediately"
        
        savings = f"{int(self.time_savings_seconds)}s faster"
        
        return f"{steps_str} can run in parallel {timing} ({savings})"


class ParallelizationDetector:
    """
    Detects parallelization opportunities in multi-step missions.
    
    Analysis:
    - Step dependencies (explicit and implicit)
    - Data flow between steps
    - Blocking conditions
    - Time estimates
    """
    
    def __init__(self):
        logger.info("ParallelizationDetector initialized")
    
    def analyze_steps(
        self,
        steps: List[Any],  # List of TaskStep objects
        conservative: bool = True
    ) -> List[ParallelizationOpportunity]:
        """
        Analyze steps and identify parallelization opportunities.
        
        Args:
            steps: List of TaskStep objects
            conservative: If True, only parallelize clearly independent steps
            
        Returns:
            List of ParallelizationOpportunity objects
        """
        opportunities = []
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(steps)
        
        # Find independent step groups
        independent_groups = self._find_independent_groups(steps, dependency_graph)
        
        # Calculate time savings for each group
        for group in independent_groups:
            if len(group['steps']) > 1:  # Only parallel if 2+ steps
                opportunity = self._create_opportunity(
                    group['steps'],
                    group.get('depends_on'),
                    steps,
                    conservative
                )
                if opportunity:
                    opportunities.append(opportunity)
        
        return opportunities
    
    def _build_dependency_graph(
        self,
        steps: List[Any]
    ) -> Dict[int, Set[int]]:
        """
        Build dependency graph showing which steps depend on which.
        
        Returns:
            Dict mapping step_number → set of step numbers it depends on
        """
        graph = {}
        
        for step in steps:
            step_num = step.step_number
            dependencies = set()
            
            # Explicit blocking dependencies
            if hasattr(step, 'is_blocking') and step.is_blocking:
                # Blocked step depends on previous steps
                if step_num > 1:
                    dependencies.add(step_num - 1)
            
            # Data dependencies (implicit from tools)
            # If step uses output from previous step, add dependency
            # For now, assume sequential unless proven independent
            if step_num > 1 and not self._is_clearly_independent(step, steps[:step_num]):
                dependencies.add(step_num - 1)
            
            graph[step_num] = dependencies
        
        return graph
    
    def _is_clearly_independent(
        self,
        step: Any,
        previous_steps: List[Any]
    ) -> bool:
        """
        Check if step is clearly independent from previous steps.
        
        Conservative check - only returns True if obviously independent.
        """
        # Check tool types - some tools are clearly independent
        independent_tools = {'web_search', 'calculate', 'get_time', 'read_file'}
        
        if hasattr(step, 'tools_used') and step.tools_used:
            step_tools = set(step.tools_used)
            # If all tools are independent types, step is independent
            if step_tools.issubset(independent_tools):
                # Check descriptions for data references
                desc_lower = step.description.lower()
                # Look for references like "using results from", "based on", etc.
                dependency_keywords = ['using', 'based on', 'from step', 'from previous', 'result of']
                if any(keyword in desc_lower for keyword in dependency_keywords):
                    return False
                return True
        
        return False
    
    def _find_independent_groups(
        self,
        steps: List[Any],
        dependency_graph: Dict[int, Set[int]]
    ) -> List[Dict[str, Any]]:
        """
        Find groups of steps that can run in parallel.
        
        Returns:
            List of group dicts with 'steps' and optional 'depends_on'
        """
        groups = []
        visited = set()
        
        # Group steps by their dependencies
        for step_num, dependencies in dependency_graph.items():
            if step_num in visited:
                continue
            
            # Find all steps with same dependencies
            group_steps = [step_num]
            for other_num, other_deps in dependency_graph.items():
                if other_num != step_num and other_num not in visited:
                    if other_deps == dependencies:
                        group_steps.append(other_num)
            
            # Mark as visited
            visited.update(group_steps)
            
            # Only create group if 2+ steps
            if len(group_steps) >= 2:
                groups.append({
                    'steps': sorted(group_steps),
                    'depends_on': max(dependencies) if dependencies else None
                })
        
        return groups
    
    def _create_opportunity(
        self,
        parallel_steps: List[int],
        depends_on: Optional[int],
        all_steps: List[Any],
        conservative: bool
    ) -> Optional[ParallelizationOpportunity]:
        """Create ParallelizationOpportunity from analysis"""
        # Get step objects
        step_objs = [s for s in all_steps if s.step_number in parallel_steps]
        
        if not step_objs:
            return None
        
        # Calculate time estimates
        sequential_time = sum(
            getattr(s, 'estimated_buddy_time', 0) or 0
            for s in step_objs
        )
        
        # Parallel time = max of individual times (plus small overhead)
        parallel_time = max(
            getattr(s, 'estimated_buddy_time', 0) or 0
            for s in step_objs
        ) * 1.1  # 10% overhead for parallelization
        
        time_savings = sequential_time - parallel_time
        
        # Assess risk
        risk_level, risk_factors = self._assess_risk(step_objs, conservative)
        
        # Generate description
        if depends_on:
            desc = f"Steps {', '.join(map(str, parallel_steps))} can run in parallel after Step {depends_on}"
        else:
            desc = f"Steps {', '.join(map(str, parallel_steps))} can run in parallel immediately"
        
        return ParallelizationOpportunity(
            parallel_steps=parallel_steps,
            depends_on_step=depends_on,
            time_savings_seconds=time_savings,
            sequential_time_seconds=sequential_time,
            parallel_time_seconds=parallel_time,
            risk_level=risk_level,
            risk_factors=risk_factors,
            description=desc
        )
    
    def _assess_risk(
        self,
        steps: List[Any],
        conservative: bool
    ) -> Tuple[str, List[str]]:
        """
        Assess risk of parallelizing these steps.
        
        Returns:
            (risk_level, risk_factors)
        """
        risk_factors = []
        
        # Check for blocking steps
        if any(getattr(s, 'is_blocking', False) for s in steps):
            risk_factors.append("Contains blocking steps requiring human action")
        
        # Check for shared resources
        tools_used = set()
        for step in steps:
            if hasattr(step, 'tools_used') and step.tools_used:
                for tool in step.tools_used:
                    if tool in tools_used:
                        risk_factors.append(f"Multiple steps use same tool: {tool}")
                    tools_used.add(tool)
        
        # Check for cost
        total_cost = sum(
            getattr(s, 'estimated_cost', None).total_usd if getattr(s, 'estimated_cost', None) else 0
            for s in steps
        )
        if total_cost > 0.50:
            risk_factors.append(f"High parallel execution cost: ${total_cost:.2f}")
        
        # Determine risk level
        if conservative:
            if risk_factors:
                risk_level = "HIGH"
            elif len(steps) > 3:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
        else:
            if len(risk_factors) > 2:
                risk_level = "HIGH"
            elif risk_factors:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
        
        return risk_level, risk_factors


# Singleton instance
parallelization_detector = ParallelizationDetector()
