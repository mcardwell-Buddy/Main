"""
Phase 9: Mission Orchestrator

Manages multiple missions with fatigue-aware prioritization.

Determines:
- What runs now (respects fatigue budget)
- What waits (queued for later)
- What is paused (good ideas, but not now)

Hard constraints:
- NO parallel execution (orchestrate, don't execute)
- NO task spawning
- NO autonomy (advisory only)
- NO learning loops
- NO mission killing (PAUSE is advisory)
- READ-ONLY analysis

Mission States:
  ACTIVE: Currently running (suggested top priority)
  QUEUED: Waiting for budget availability
  PAUSED: Good idea but human should defer (can be resumed)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from uuid import uuid4

from backend.tradeoff_evaluator import TradeoffScore


class MissionStatus(Enum):
    """Mission lifecycle state."""
    ACTIVE = "ACTIVE"         # Currently prioritized
    QUEUED = "QUEUED"         # Waiting in queue
    PAUSED = "PAUSED"         # Deferred (good but not now)


@dataclass(frozen=True)
class MissionEntry:
    """Immutable mission description."""
    mission_id: str
    description: str
    estimated_effort_minutes: int
    estimated_payoff_minutes: int      # Value ROI calculation
    tradeoff_score: Optional[TradeoffScore] = None
    status: MissionStatus = MissionStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.utcnow)
    paused_reason: str = ""
    
    def roi_ratio(self) -> float:
        """Return time ROI (payoff/effort)."""
        if self.estimated_effort_minutes == 0:
            return 1.0
        return self.estimated_payoff_minutes / self.estimated_effort_minutes
    
    def is_good_idea(self) -> bool:
        """Is this a good idea (positive ROI)?"""
        return self.roi_ratio() > 1.0


@dataclass(frozen=True)
class MissionPriority:
    """Immutable priority assignment for a mission."""
    mission_id: str
    rank: int                          # 1 = top priority
    score: float                       # 0.0-1.0, higher = more important
    status: MissionStatus
    reason: str                        # Why this rank?
    effort_minutes: int
    payoff_minutes: int


@dataclass(frozen=True)
class OrchestrationPlan:
    """Immutable prioritization plan."""
    timestamp: datetime
    budget_used_minutes: int
    budget_remaining_minutes: int
    fatigue_state: str                # e.g., "NORMAL"
    active_mission: Optional[MissionEntry] = None
    queued_missions: List[MissionEntry] = field(default_factory=list)
    paused_missions: List[MissionEntry] = field(default_factory=list)
    priorities: List[MissionPriority] = field(default_factory=list)
    total_queued_effort: int = 0
    total_paused_effort: int = 0
    recommendation: str = ""
    reasoning: List[str] = field(default_factory=list)


class MissionOrchestrator:
    """Manages mission prioritization with fatigue awareness."""
    
    def __init__(self):
        """Initialize empty mission store."""
        self._missions: Dict[str, MissionEntry] = {}
        self._active_mission: Optional[str] = None
    
    def add_mission(
        self,
        description: str,
        estimated_effort_minutes: int,
        estimated_payoff_minutes: int,
        tradeoff_score: Optional[TradeoffScore] = None,
        mission_id: Optional[str] = None
    ) -> MissionEntry:
        """Add a new mission to the portfolio."""
        if mission_id is None:
            mission_id = str(uuid4())
        
        mission = MissionEntry(
            mission_id=mission_id,
            description=description,
            estimated_effort_minutes=estimated_effort_minutes,
            estimated_payoff_minutes=estimated_payoff_minutes,
            tradeoff_score=tradeoff_score,
            status=MissionStatus.QUEUED,
            created_at=datetime.utcnow()
        )
        
        self._missions[mission_id] = mission
        return mission
    
    def get_mission(self, mission_id: str) -> Optional[MissionEntry]:
        """Get mission by ID."""
        return self._missions.get(mission_id)
    
    def pause_mission(
        self,
        mission_id: str,
        reason: str = "Deferred for later"
    ) -> MissionEntry:
        """Pause a mission (make it advisory)."""
        mission = self._missions.get(mission_id)
        if mission is None:
            raise ValueError(f"Mission {mission_id} not found")
        
        paused = MissionEntry(
            mission_id=mission.mission_id,
            description=mission.description,
            estimated_effort_minutes=mission.estimated_effort_minutes,
            estimated_payoff_minutes=mission.estimated_payoff_minutes,
            tradeoff_score=mission.tradeoff_score,
            status=MissionStatus.PAUSED,
            paused_reason=reason,
            created_at=mission.created_at
        )
        
        self._missions[mission_id] = paused
        if self._active_mission == mission_id:
            self._active_mission = None
        return paused
    
    def resume_mission(self, mission_id: str) -> MissionEntry:
        """Resume a paused mission."""
        mission = self._missions.get(mission_id)
        if mission is None:
            raise ValueError(f"Mission {mission_id} not found")
        
        if mission.status != MissionStatus.PAUSED:
            raise ValueError(f"Mission {mission_id} is not paused")
        
        resumed = MissionEntry(
            mission_id=mission.mission_id,
            description=mission.description,
            estimated_effort_minutes=mission.estimated_effort_minutes,
            estimated_payoff_minutes=mission.estimated_payoff_minutes,
            tradeoff_score=mission.tradeoff_score,
            status=MissionStatus.QUEUED,
            created_at=mission.created_at
        )
        
        self._missions[mission_id] = resumed
        return resumed
    
    def set_active_mission(self, mission_id: Optional[str]) -> None:
        """Set which mission is currently active."""
        if mission_id is not None and mission_id not in self._missions:
            raise ValueError(f"Mission {mission_id} not found")
        
        self._active_mission = mission_id
    
    def get_active_mission(self) -> Optional[MissionEntry]:
        """Get currently active mission."""
        if self._active_mission is None:
            return None
        return self._missions.get(self._active_mission)
    
    def prioritize_missions(
        self,
        available_budget_minutes: int,
        max_recommendations: int = 5
    ) -> Tuple[List[MissionPriority], List[str]]:
        """
        Prioritize missions based on ROI and budget constraints.
        
        Returns:
            (priorities list, reasoning list)
        """
        queued = [m for m in self._missions.values() if m.status == MissionStatus.QUEUED]
        
        # Sort by ROI (payoff/effort), descending
        # Ties broken by effort (prefer quick wins)
        sorted_missions = sorted(
            queued,
            key=lambda m: (m.roi_ratio(), -m.estimated_effort_minutes),
            reverse=True
        )
        
        priorities: List[MissionPriority] = []
        used_budget = 0
        reasoning: List[str] = []
        
        for rank, mission in enumerate(sorted_missions[:max_recommendations], 1):
            roi = mission.roi_ratio()
            
            # Can we afford this mission?
            can_afford = (used_budget + mission.estimated_effort_minutes) <= available_budget_minutes
            
            # Calculate priority score (0.0-1.0)
            # Factors: ROI, budget feasibility, effort size
            roi_score = min(1.0, roi / 3.0)  # 3.0x ROI = perfect score
            budget_score = 1.0 if can_afford else 0.3  # Penalty if over budget
            efficiency_score = 1.0 / (1.0 + (mission.estimated_effort_minutes / 60.0))
            
            final_score = (roi_score * 0.5 + budget_score * 0.3 + efficiency_score * 0.2)
            
            priority = MissionPriority(
                mission_id=mission.mission_id,
                rank=rank,
                score=final_score,
                status=MissionStatus.QUEUED if can_afford else MissionStatus.PAUSED,
                reason=self._get_priority_reason(mission, can_afford, roi),
                effort_minutes=mission.estimated_effort_minutes,
                payoff_minutes=mission.estimated_payoff_minutes
            )
            
            priorities.append(priority)
            
            if can_afford:
                used_budget += mission.estimated_effort_minutes
            else:
                reasoning.append(
                    f"Rank {rank}: {mission.mission_id[:8]}... "
                    f"(ROI {roi:.1f}x, but exceeds budget)"
                )
        
        return priorities, reasoning
    
    @staticmethod
    def _get_priority_reason(
        mission: MissionEntry,
        can_afford: bool,
        roi: float
    ) -> str:
        """Get reason for priority assignment."""
        if not can_afford:
            return f"Good idea ({roi:.1f}x ROI) but deferred due to budget"
        
        if roi >= 3.0:
            return f"High-value work ({roi:.1f}x ROI, quick win)"
        elif roi >= 2.0:
            return f"Strong ROI ({roi:.1f}x, good value)"
        elif roi >= 1.5:
            return f"Positive ROI ({roi:.1f}x, worth doing)"
        else:
            return f"Low ROI ({roi:.1f}x) but within budget"
    
    def get_queue_summary(self) -> Tuple[int, int, int]:
        """Get mission counts (active, queued, paused)."""
        active = 1 if self._active_mission else 0
        queued = sum(1 for m in self._missions.values() if m.status == MissionStatus.QUEUED)
        paused = sum(1 for m in self._missions.values() if m.status == MissionStatus.PAUSED)
        return active, queued, paused
    
    def get_missions_by_status(self, status: MissionStatus) -> List[MissionEntry]:
        """Get all missions with given status."""
        return [m for m in self._missions.values() if m.status == status]
    
    def get_total_effort(self, status: Optional[MissionStatus] = None) -> int:
        """Total effort minutes for missions (optionally filtered by status)."""
        missions = (
            self._missions.values()
            if status is None
            else self.get_missions_by_status(status)
        )
        return sum(m.estimated_effort_minutes for m in missions)
    
    def get_total_payoff(self, status: Optional[MissionStatus] = None) -> int:
        """Total payoff minutes for missions (optionally filtered by status)."""
        missions = (
            self._missions.values()
            if status is None
            else self.get_missions_by_status(status)
        )
        return sum(m.estimated_payoff_minutes for m in missions)
    
    def get_portfolio_roi(self) -> float:
        """Get average ROI across all missions."""
        if not self._missions:
            return 1.0
        
        total_roi = sum(m.roi_ratio() for m in self._missions.values())
        return total_roi / len(self._missions)
    
    def get_deferred_good_ideas(self) -> List[MissionEntry]:
        """Get paused missions that have positive ROI (good ideas being deferred)."""
        paused = self.get_missions_by_status(MissionStatus.PAUSED)
        return [m for m in paused if m.is_good_idea()]
    
    def get_portfolio_state(self) -> Dict[str, Any]:
        """Get complete portfolio state snapshot."""
        return {
            "total_missions": len(self._missions),
            "active": self.get_missions_by_status(MissionStatus.ACTIVE),
            "queued": self.get_missions_by_status(MissionStatus.QUEUED),
            "paused": self.get_missions_by_status(MissionStatus.PAUSED),
            "total_effort": self.get_total_effort(),
            "total_payoff": self.get_total_payoff(),
            "portfolio_roi": self.get_portfolio_roi(),
            "deferred_good_ideas": self.get_deferred_good_ideas(),
        }
