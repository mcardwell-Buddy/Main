"""
Task Breakdown and Proposal Engine

Integrates GoalDecomposer + DelegationEvaluator + CostEstimator
to create comprehensive task breakdowns with:
- What Buddy does (fully autonomous)
- What human does (manual tasks)
- What requires collaboration (hybrid tasks)
- Cost estimates for each step
- Time estimates for human involvement

Philosophy:
- Buddy amplifies human, doesn't compete
- Show facts, not recommendations
- User decides if worth the investment
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from backend.goal_decomposer import GoalDecomposer
from backend.delegation_evaluator import DelegationEvaluator, ExecutionClass, HumanAction
from backend.cost_estimator import CostEstimator, MissionCost, ServiceTier, ModelType

logger = logging.getLogger(__name__)


class StepType(Enum):
    """Classification of task steps."""
    PURE_BUDDY = "pure_buddy"  # Fully autonomous
    PURE_HUMAN = "pure_human"  # Human decision/action required
    HYBRID = "hybrid"  # Buddy does work, human reviews/approves


@dataclass
class TaskStep:
    """A single step in task breakdown."""
    step_number: int
    description: str
    step_type: StepType
    execution_class: ExecutionClass  # From DelegationEvaluator
    
    # Cost/time estimates
    estimated_cost: Optional[MissionCost] = None
    estimated_buddy_time: Optional[float] = None  # seconds
    estimated_human_time: Optional[int] = None  # minutes
    
    # Human involvement details
    human_actions: List[HumanAction] = field(default_factory=list)
    is_blocking: bool = False  # Blocks subsequent steps
    blocking_reason: Optional[str] = None
    
    # Tool/API usage
    tools_used: List[str] = field(default_factory=list)
    api_calls: List[str] = field(default_factory=list)
    
    # Metadata
    rationale: Optional[str] = None
    confidence: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'step_number': self.step_number,
            'description': self.description,
            'step_type': self.step_type.value,
            'execution_class': self.execution_class.value,
            'estimated_cost': self.estimated_cost.to_dict() if self.estimated_cost else None,
            'estimated_buddy_time': self.estimated_buddy_time,
            'estimated_human_time': self.estimated_human_time,
            'human_actions': [
                {
                    'action': ha.action,
                    'description': ha.description,
                    'estimated_minutes': ha.estimated_minutes,
                    'is_blocking': ha.is_blocking
                }
                for ha in self.human_actions
            ],
            'is_blocking': self.is_blocking,
            'blocking_reason': self.blocking_reason,
            'tools_used': self.tools_used,
            'api_calls': self.api_calls,
            'rationale': self.rationale,
            'confidence': self.confidence
        }


@dataclass
class TaskBreakdown:
    """Complete task breakdown with cost and time estimates."""
    goal: str
    steps: List[TaskStep]
    
    # Summary statistics
    total_cost: MissionCost
    total_buddy_time_seconds: float
    total_human_time_minutes: int
    
    # Step counts by type
    pure_buddy_steps: int
    pure_human_steps: int
    hybrid_steps: int
    
    # Flags
    has_blocking_steps: bool
    requires_human_approval: bool
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    breakdown_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'goal': self.goal,
            'steps': [step.to_dict() for step in self.steps],
            'total_cost': self.total_cost.to_dict(),
            'total_buddy_time_seconds': round(self.total_buddy_time_seconds, 2),
            'total_human_time_minutes': self.total_human_time_minutes,
            'pure_buddy_steps': self.pure_buddy_steps,
            'pure_human_steps': self.pure_human_steps,
            'hybrid_steps': self.hybrid_steps,
            'has_blocking_steps': self.has_blocking_steps,
            'requires_human_approval': self.requires_human_approval,
            'created_at': self.created_at,
            'breakdown_version': self.breakdown_version
        }


class TaskBreakdownEngine:
    """
    Orchestrates task breakdown analysis.
    
    Uses existing components:
    - GoalDecomposer: Break goal into steps
    - DelegationEvaluator: Classify execution requirements
    - CostEstimator: Calculate API costs
    
    Outputs unified TaskBreakdown for ProposalPresenter.
    """
    
    # Tool cost estimation heuristics
    TOOL_COST_HEURISTICS = {
        'web_search': {'serpapi_searches': 1},
        'serp_search': {'serpapi_searches': 1},
        'google_search': {'serpapi_searches': 1},
        'llm_call': {
            'openai_calls': [{
                'model': ModelType.GPT_4O_MINI,
                'input_tokens': 1000,
                'output_tokens': 500
            }]
        },
        'database_query': {'firestore_reads': 10},
        'database_write': {'firestore_writes': 5},
    }
    
    # Buddy execution time heuristics (seconds)
    BUDDY_TIME_HEURISTICS = {
        'web_search': 3.0,
        'llm_call': 2.0,
        'database_query': 0.5,
        'database_write': 0.8,
        'file_read': 0.2,
        'file_write': 0.5,
        'api_call': 2.0,
    }
    
    def __init__(
        self,
        serpapi_tier: ServiceTier = ServiceTier.FREE,
        goal_decomposer: Optional[GoalDecomposer] = None,
        delegation_evaluator: Optional[DelegationEvaluator] = None,
        cost_estimator: Optional[CostEstimator] = None
    ):
        """
        Initialize task breakdown engine.
        
        Args:
            serpapi_tier: Current SerpAPI subscription tier
            goal_decomposer: Optional custom GoalDecomposer
            delegation_evaluator: Optional custom DelegationEvaluator
            cost_estimator: Optional custom CostEstimator
        """
        self.goal_decomposer = goal_decomposer or GoalDecomposer()
        self.delegation_evaluator = delegation_evaluator or DelegationEvaluator()
        self.cost_estimator = cost_estimator or CostEstimator(serpapi_tier)
        
        logger.info(f"TaskBreakdownEngine initialized with SerpAPI tier: {serpapi_tier.value}")
    
    def analyze_task(self, goal: str, context: Optional[Dict[str, Any]] = None) -> TaskBreakdown:
        """
        Analyze task and create comprehensive breakdown.
        
        Args:
            goal: User's goal/mission objective
            context: Optional context (tools available, constraints, etc.)
            
        Returns:
            TaskBreakdown: Complete task analysis
        """
        # Validate input
        if not goal or not goal.strip():
            logger.warning("Empty goal provided to analyze_task")
            return TaskBreakdown(
                goal="",
                steps=[],
                total_cost=MissionCost(total_usd=0.0, service_costs=[], currency="USD"),
                total_buddy_time_seconds=0,
                total_human_time_minutes=0,
                pure_buddy_steps=0,
                pure_human_steps=0,
                hybrid_steps=0,
                has_blocking_steps=False,
                requires_human_approval=False
            )
        
        logger.info(f"Analyzing task: {goal}")
        
        # Step 1: Decompose goal into subgoals
        try:
            decomposition = self.goal_decomposer.classify_goal(goal)
        except Exception as e:
            logger.error(f"GoalDecomposer failed: {e}. Treating as atomic goal.")
            decomposition = {'is_composite': False}
        
        # Step 2: Create task steps
        steps = []
        try:
            is_composite = decomposition.get('is_composite', False)
            subgoals = decomposition.get('subgoals', []) if is_composite else []
            
            # Validate subgoals list
            if is_composite and not subgoals:
                logger.warning("Composite goal marked but no subgoals found. Treating as atomic.")
                is_composite = False
            
            if is_composite:
                # Multiple subgoals
                for idx, subgoal_dict in enumerate(subgoals, 1):
                    desc = subgoal_dict.get('subgoal', subgoal_dict.get('description', '')) if isinstance(subgoal_dict, dict) else str(subgoal_dict)
                    if not desc:
                        desc = goal
                    step = self._analyze_step(
                        step_number=idx,
                        description=desc,
                        context=context
                    )
                    steps.append(step)
            else:
                # Single atomic goal
                step = self._analyze_step(
                    step_number=1,
                    description=goal,
                    context=context
                )
                steps.append(step)
        except Exception as e:
            logger.error(f"Failed to create task steps: {e}. Creating fallback step.")
            step = self._analyze_step(
                step_number=1,
                description=goal,
                context=context
            )
            steps.append(step)
        
        # Step 3: Calculate totals
        total_cost = self._aggregate_costs([s.estimated_cost for s in steps if s.estimated_cost])
        total_buddy_time = sum(s.estimated_buddy_time or 0 for s in steps)
        total_human_time = sum(s.estimated_human_time or 0 for s in steps)
        
        # Step 4: Count step types
        pure_buddy = sum(1 for s in steps if s.step_type == StepType.PURE_BUDDY)
        pure_human = sum(1 for s in steps if s.step_type == StepType.PURE_HUMAN)
        hybrid = sum(1 for s in steps if s.step_type == StepType.HYBRID)
        
        # Step 5: Check for blocking conditions
        has_blocking = any(s.is_blocking for s in steps)
        requires_approval = any(s.step_type in [StepType.PURE_HUMAN, StepType.HYBRID] for s in steps)
        
        breakdown = TaskBreakdown(
            goal=goal,
            steps=steps,
            total_cost=total_cost,
            total_buddy_time_seconds=total_buddy_time,
            total_human_time_minutes=total_human_time,
            pure_buddy_steps=pure_buddy,
            pure_human_steps=pure_human,
            hybrid_steps=hybrid,
            has_blocking_steps=has_blocking,
            requires_human_approval=requires_approval
        )
        
        logger.info(
            f"Task breakdown complete: {len(steps)} steps, "
            f"${total_cost.total_usd:.4f}, "
            f"{total_human_time}min human time"
        )
        
        return breakdown
    
    def _analyze_step(
        self,
        step_number: int,
        description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskStep:
        """Analyze a single step."""
        # Get delegation decision with error handling
        try:
            delegation = self.delegation_evaluator.evaluate(description)
        except Exception as e:
            logger.error(f"DelegationEvaluator failed for step '{description}': {e}. Using safe defaults.")
            # Fallback to safe defaults
            from backend.action_readiness_engine import ExecutionResult, ExecutionClass
            delegation = ExecutionResult(
                execution_class=ExecutionClass.AI_EXECUTABLE,
                required_human_actions=[],
                confidence=0.5
            )
        
        # Classify step type
        step_type = self._classify_step_type(delegation.execution_class, delegation.required_human_actions)
        
        # Estimate costs
        estimated_cost = self._estimate_step_cost(description, context)
        
        # Estimate Buddy execution time
        estimated_buddy_time = self._estimate_buddy_time(description, context)
        
        # Get human time from delegation
        estimated_human_time = delegation.estimated_human_effort
        
        # Extract tools/APIs used
        tools_used = self._extract_tools(description)
        api_calls = self._extract_apis(description)
        
        return TaskStep(
            step_number=step_number,
            description=description,
            step_type=step_type,
            execution_class=delegation.execution_class,
            estimated_cost=estimated_cost,
            estimated_buddy_time=estimated_buddy_time,
            estimated_human_time=estimated_human_time,
            human_actions=delegation.required_human_actions,
            is_blocking=delegation.is_blocked,
            blocking_reason=delegation.blocking_reason,
            tools_used=tools_used,
            api_calls=api_calls,
            rationale=delegation.rationale,
            confidence=delegation.confidence
        )
    
    def _classify_step_type(
        self,
        execution_class: ExecutionClass,
        human_actions: List[HumanAction]
    ) -> StepType:
        """Classify step type based on execution class and human actions."""
        if execution_class == ExecutionClass.AI_EXECUTABLE and not human_actions:
            return StepType.PURE_BUDDY
        elif execution_class == ExecutionClass.HUMAN_REQUIRED:
            return StepType.PURE_HUMAN
        else:
            # COLLABORATIVE or AI_EXECUTABLE with human actions
            return StepType.HYBRID
    
    def _estimate_step_cost(
        self,
        description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> MissionCost:
        """Estimate cost for a single step."""
        # Extract tools from description
        tools = self._extract_tools(description)
        
        # Aggregate costs from tools
        serpapi_searches = 0
        openai_calls = []
        firestore_reads = 0
        firestore_writes = 0
        
        for tool in tools:
            tool_lower = tool.lower()
            if tool_lower in self.TOOL_COST_HEURISTICS:
                heuristics = self.TOOL_COST_HEURISTICS[tool_lower]
                serpapi_searches += heuristics.get('serpapi_searches', 0)
                if 'openai_calls' in heuristics:
                    openai_calls.extend(heuristics['openai_calls'])
                firestore_reads += heuristics.get('firestore_reads', 0)
                firestore_writes += heuristics.get('firestore_writes', 0)
        
        # If no tools detected, assume minimal LLM call
        if not tools:
            openai_calls.append({
                'model': ModelType.GPT_4O_MINI,
                'input_tokens': 500,
                'output_tokens': 250
            })
        
        return self.cost_estimator.estimate_mission_cost(
            serpapi_searches=serpapi_searches,
            openai_calls=openai_calls if openai_calls else None,
            firestore_reads=firestore_reads,
            firestore_writes=firestore_writes
        )
    
    def _estimate_buddy_time(
        self,
        description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Estimate Buddy execution time in seconds."""
        tools = self._extract_tools(description)
        
        total_time = 0.0
        for tool in tools:
            tool_lower = tool.lower()
            if tool_lower in self.BUDDY_TIME_HEURISTICS:
                total_time += self.BUDDY_TIME_HEURISTICS[tool_lower]
        
        # Minimum 0.5 seconds for any step
        return max(0.5, total_time)
    
    def _extract_tools(self, description: str) -> List[str]:
        """Extract tool names from description."""
        tools = []
        description_lower = description.lower()
        
        tool_keywords = {
            'web_search': ['search', 'google', 'find online', 'look up'],
            'llm_call': ['generate', 'write', 'create text', 'compose', 'draft'],
            'database_query': ['read', 'fetch', 'get data', 'retrieve', 'query'],
            'database_write': ['save', 'store', 'write', 'update', 'insert'],
            'api_call': ['api', 'call', 'request', 'fetch from'],
            'file_read': ['read file', 'open file', 'load file'],
            'file_write': ['write file', 'save file', 'create file']
        }
        
        for tool, keywords in tool_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                tools.append(tool)
        
        return tools
    
    def _extract_apis(self, description: str) -> List[str]:
        """Extract API names from description."""
        apis = []
        description_lower = description.lower()
        
        api_keywords = {
            'SerpAPI': ['search', 'google', 'serp'],
            'OpenAI': ['llm', 'gpt', 'generate', 'write'],
            'Firestore': ['database', 'firestore', 'store', 'save'],
            'GoHighLevel': ['gohighlevel', 'ghl', 'crm'],
            'Microsoft Graph': ['microsoft', 'outlook', 'calendar', 'email']
        }
        
        for api, keywords in api_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                apis.append(api)
        
        return apis
    
    def _aggregate_costs(self, costs: List[MissionCost]) -> MissionCost:
        """Aggregate multiple MissionCost objects into one."""
        if not costs or all(not isinstance(c, MissionCost) for c in costs):
            return MissionCost(
                total_usd=0.0,
                service_costs=[],
                currency="USD",
                tier_recommendations={},
                warnings=[]
            )
        
        # Filter out None costs
        costs = [c for c in costs if c is not None]
        if not costs:
            return MissionCost(
                total_usd=0.0,
                service_costs=[],
                currency="USD",
                tier_recommendations={},
                warnings=[]
            )
        
        # Sum all costs
        total = sum(c.total_usd for c in costs if hasattr(c, 'total_usd'))
        
        # Combine service costs
        all_service_costs = []
        for cost in costs:
            if hasattr(cost, 'service_costs') and cost.service_costs:
                all_service_costs.extend(cost.service_costs)
        
        # Combine warnings
        all_warnings = []
        for cost in costs:
            if hasattr(cost, 'warnings') and cost.warnings:
                all_warnings.extend(cost.warnings)
        
        return MissionCost(
            total_usd=total,
            service_costs=all_service_costs,
            currency="USD",
            tier_recommendations={},
            warnings=list(set(all_warnings))  # Deduplicate
        )
