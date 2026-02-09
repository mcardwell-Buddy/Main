"""
Proposal Presenter: Unified mission proposal generation

Transforms TaskBreakdown into a cohesive, user-friendly proposal.

Philosophy:
- Single cohesive presentation (NOT 3 fragments)
- Show what Buddy does, what human does
- Show costs upfront
- Show time investment required
- User decides if worth it (no "approve" recommendation)

NO execution. Pure presentation. Deterministic only.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from backend.task_breakdown_and_proposal import TaskBreakdown, TaskStep, StepType
from backend.cost_estimator import MissionCost

logger = logging.getLogger(__name__)


@dataclass
class UnifiedProposal:
    """
    Single cohesive mission proposal.
    
    Contains everything user needs to make informed decision:
    - What will happen (narrative + structured steps)
    - What Buddy does vs what human does
    - Costs (upfront, broken down)
    - Time requirements (Buddy + human)
    - What happens next (if approved)
    """
    
    # Mission identification
    mission_id: str
    mission_title: str
    objective: str
    
    # Narrative summary (2-3 sentences)
    executive_summary: str
    
    # Detailed breakdown
    task_breakdown: TaskBreakdown
    
    # Key metrics (derived from breakdown)
    total_steps: int
    buddy_steps: int
    human_steps: int
    hybrid_steps: int
    
    # Cost summary
    total_cost_usd: float
    cost_breakdown: List[Dict[str, Any]]  # Service-level costs
    
    # Time summary
    estimated_buddy_time_seconds: float
    estimated_human_time_minutes: int
    estimated_total_time_minutes: int
    
    # Human involvement details
    requires_approval: bool
    has_blocking_steps: bool
    human_actions_required: List[Dict[str, Any]]
    
    # Next steps
    approval_options: List[str]  # e.g., ["Approve", "Modify", "Reject"]
    what_happens_next: str  # Plain text explanation
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    proposal_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict for frontend."""
        return {
            'mission_id': self.mission_id,
            'mission_title': self.mission_title,
            'objective': self.objective,
            'executive_summary': self.executive_summary,
            'task_breakdown': self.task_breakdown.to_dict(),
            'metrics': {
                'total_steps': self.total_steps,
                'buddy_steps': self.buddy_steps,
                'human_steps': self.human_steps,
                'hybrid_steps': self.hybrid_steps
            },
            'costs': {
                'total_usd': round(self.total_cost_usd, 4),
                'breakdown': self.cost_breakdown
            },
            'time': {
                'buddy_seconds': round(self.estimated_buddy_time_seconds, 1),
                'human_minutes': self.estimated_human_time_minutes,
                'total_minutes': self.estimated_total_time_minutes
            },
            'human_involvement': {
                'requires_approval': self.requires_approval,
                'has_blocking_steps': self.has_blocking_steps,
                'actions_required': self.human_actions_required
            },
            'next_steps': {
                'approval_options': self.approval_options,
                'what_happens_next': self.what_happens_next
            },
            'metadata': {
                'created_at': self.created_at,
                'proposal_version': self.proposal_version
            }
        }


class ProposalPresenter:
    """
    Generates unified mission proposals from task breakdowns.
    
    Takes TaskBreakdown + mission metadata, produces UnifiedProposal
    ready for frontend rendering.
    """
    
    def __init__(self):
        logger.info("ProposalPresenter initialized")
    
    def create_proposal(
        self,
        mission_id: str,
        objective: str,
        task_breakdown: TaskBreakdown,
        mission_title: Optional[str] = None
    ) -> UnifiedProposal:
        """
        Create unified proposal from task breakdown.
        
        Args:
            mission_id: Unique mission identifier
            objective: Mission objective
            task_breakdown: Complete task breakdown from TaskBreakdownEngine
            mission_title: Optional custom title (auto-generated if None)
            
        Returns:
            UnifiedProposal: Complete unified proposal
        """
        logger.info(f"Creating proposal for mission {mission_id}")
        
        # Generate title if not provided
        if not mission_title:
            mission_title = self._generate_title(objective)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(task_breakdown)
        
        # Extract metrics with null safety
        total_steps = len(task_breakdown.steps) if task_breakdown.steps else 0
        buddy_steps = getattr(task_breakdown, 'pure_buddy_steps', 0) or 0
        human_steps = getattr(task_breakdown, 'pure_human_steps', 0) or 0
        hybrid_steps = getattr(task_breakdown, 'hybrid_steps', 0) or 0
        
        # Extract cost breakdown with validation
        total_cost_obj = getattr(task_breakdown, 'total_cost', None)
        if not total_cost_obj:
            logger.warning(f"Mission {mission_id} has no cost object. Using zero cost.")
            total_cost_obj = MissionCost(total_usd=0.0, service_costs=[], currency="USD")
        
        cost_breakdown = self._extract_cost_breakdown(total_cost_obj)
        
        # Calculate total time (Buddy time + human time) with null safety
        buddy_time = getattr(task_breakdown, 'total_buddy_time_seconds', 0) or 0
        human_time = getattr(task_breakdown, 'total_human_time_minutes', 0) or 0
        total_time_minutes = int(buddy_time / 60) + int(human_time) if (buddy_time + human_time) > 0 else 1
        
        # Extract human actions
        human_actions = self._extract_human_actions(task_breakdown.steps)
        
        # Determine approval options
        approval_options = self._determine_approval_options(task_breakdown)
        
        # Generate "what happens next" explanation
        what_happens_next = self._generate_what_happens_next(task_breakdown)
        
        proposal = UnifiedProposal(
            mission_id=mission_id,
            mission_title=mission_title,
            objective=objective,
            executive_summary=executive_summary,
            task_breakdown=task_breakdown,
            total_steps=total_steps,
            buddy_steps=buddy_steps,
            human_steps=human_steps,
            hybrid_steps=hybrid_steps,
            total_cost_usd=total_cost_obj.total_usd,
            cost_breakdown=cost_breakdown,
            estimated_buddy_time_seconds=buddy_time,
            estimated_human_time_minutes=human_time,
            estimated_total_time_minutes=total_time_minutes,
            requires_approval=task_breakdown.requires_human_approval,
            has_blocking_steps=task_breakdown.has_blocking_steps,
            human_actions_required=human_actions,
            approval_options=approval_options,
            what_happens_next=what_happens_next
        )
        
        logger.info(
            f"Proposal created: {total_steps} steps, "
            f"${total_cost_obj.total_usd:.4f}, "
            f"{total_time_minutes}min total"
        )
        
        return proposal
    
    def _generate_title(self, objective: str) -> str:
        """Generate mission title from objective."""
        # Take first 60 chars or up to first period
        if '.' in objective:
            title = objective.split('.')[0]
        else:
            title = objective[:60]
        
        # Capitalize first letter
        return title.strip().capitalize()
    
    def _generate_executive_summary(self, breakdown: TaskBreakdown) -> str:
        """
        Generate 2-3 sentence executive summary.
        
        Format:
        - Sentence 1: What Buddy will do
        - Sentence 2: What human needs to do (if applicable)
        - Sentence 3: Cost and time summary
        """
        sentences = []
        
        # Sentence 1: Buddy's role
        if breakdown.pure_buddy_steps > 0 or breakdown.hybrid_steps > 0:
            buddy_work = breakdown.pure_buddy_steps + breakdown.hybrid_steps
            sentences.append(
                f"Buddy will execute {buddy_work} automated step{'s' if buddy_work != 1 else ''}"
                f"{' including research, analysis, and content generation' if any('search' in s.description.lower() or 'generate' in s.description.lower() for s in breakdown.steps) else ''}."
            )
        
        # Sentence 2: Human's role (if applicable)
        if breakdown.pure_human_steps > 0 or breakdown.requires_human_approval:
            human_work = breakdown.pure_human_steps
            if human_work > 0:
                sentences.append(
                    f"You'll handle {human_work} decision{'s' if human_work != 1 else ''} or approval{'s' if human_work != 1 else ''} "
                    f"that require human judgment."
                )
            elif breakdown.requires_human_approval:
                sentences.append("Your approval will be required before execution begins.")
        
        # Sentence 3: Cost and time
        cost = breakdown.total_cost.total_usd
        time_mins = int(breakdown.total_buddy_time_seconds / 60) + breakdown.total_human_time_minutes
        
        if cost > 0:
            sentences.append(
                f"Estimated cost: ${cost:.2f}, total time: ~{time_mins} minute{'s' if time_mins != 1 else ''}."
            )
        else:
            sentences.append(
                f"No API costs required, estimated time: ~{time_mins} minute{'s' if time_mins != 1 else ''}."
            )
        
        return " ".join(sentences)
    
    def _extract_cost_breakdown(self, mission_cost: MissionCost) -> List[Dict[str, Any]]:
        """Extract service-level cost breakdown with credit/dollar distinction."""
        breakdown = []
        
        for service_cost in mission_cost.service_costs:
            if service_cost.service == 'serpapi':
                # SerpAPI: Show credits, not dollars (quota-based service)
                breakdown.append({
                    'service': 'serpapi',
                    'type': 'credits',
                    'credits_needed': service_cost.operation_count,
                    'tier': service_cost.tier,
                    'cost_usd': 0.00,  # Already paid fixed monthly fee
                    'details': service_cost.details,
                    'note': 'Uses monthly quota credits'
                })
            else:
                # OpenAI/Firestore: Show actual dollar costs (pay-per-use)
                breakdown.append({
                    'service': service_cost.service,
                    'type': 'dollars',
                    'cost_usd': round(service_cost.total_cost, 4),
                    'operations': service_cost.operation_count,
                    'tier': service_cost.tier,
                'details': service_cost.details
            })
        
        return breakdown
    
    def _extract_human_actions(self, steps: List[TaskStep]) -> List[Dict[str, Any]]:
        """Extract all human actions from steps."""
        actions = []
        
        for step in steps:
            for human_action in step.human_actions:
                actions.append({
                    'step_number': step.step_number,
                    'step_description': step.description,
                    'action': human_action.action,
                    'description': human_action.description,
                    'estimated_minutes': human_action.estimated_minutes,
                    'is_blocking': human_action.is_blocking
                })
        
        return actions
    
    def _determine_approval_options(self, breakdown: TaskBreakdown) -> List[str]:
        """Determine approval options based on breakdown."""
        options = []
        
        # Always offer these
        options.append("Approve")
        options.append("Modify")
        
        # If has blocking steps, offer "Review Steps"
        if breakdown.has_blocking_steps:
            options.append("Review Steps")
        
        # Always offer reject
        options.append("Reject")
        
        return options
    
    def _generate_what_happens_next(self, breakdown: TaskBreakdown) -> str:
        """Generate explanation of what happens after approval."""
        if breakdown.has_blocking_steps:
            return (
                "If you approve, Buddy will begin execution but will pause at any step "
                "requiring your input or approval. You'll be notified when human action is needed."
            )
        elif breakdown.requires_human_approval:
            return (
                "If you approve, Buddy will execute all automated steps. "
                "You'll receive updates as each step completes and a final summary when done."
            )
        else:
            return (
                "If you approve, Buddy will execute all steps autonomously. "
                "You'll receive a completion notification with results."
            )
