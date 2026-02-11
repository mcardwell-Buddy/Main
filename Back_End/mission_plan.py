"""
Mission Planning Data Structures

Defines MissionPlan and ToolOption for mission planning with tool selection.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ToolOption:
    """Ranked tool option for a mission"""
    tool_name: str
    confidence: float  # 0.0-1.0 from pattern matching
    performance_score: float  # 0.0-1.0 from historical data
    combined_score: float  # weighted average
    reasoning: str
    
    # Cost/duration estimates
    estimated_cost_usd: float
    cost_rationale: str
    estimated_duration_seconds: float
    duration_rationale: str
    
    # Historical data
    success_rate: float
    avg_latency_ms: float
    failure_modes: List[str] = field(default_factory=list)
    failures_in_last_10: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolOption':
        """Create ToolOption from dictionary"""
        return cls(**data)


@dataclass
class MissionPlan:
    """Complete mission plan with tool selection and cost analysis"""
    mission_id: str
    source: str  # "chat"
    status: str  # "planned"
    
    # Original objective (from readiness result)
    objective_description: str
    objective_type: str  # search, extract, navigate
    target_count: Optional[int]
    
    # Scope constraints
    allowed_domains: List[str] = field(default_factory=list)
    max_pages: int = 5
    max_duration_seconds: int = 300
    
    # TOOL SELECTION RESULTS
    primary_tool: Optional[Dict[str, Any]] = None  # ToolOption as dict
    alternative_tools: List[Dict[str, Any]] = field(default_factory=list)  # Top 3 alternatives as dicts
    
    # COST & DURATION ESTIMATES
    total_estimated_cost: float = 0.0
    total_cost_rationale: str = ""
    total_estimated_duration: float = 0.0
    total_duration_rationale: str = ""
    
    # FEASIBILITY ASSESSMENT
    is_feasible: bool = True
    feasibility_issues: List[str] = field(default_factory=list)
    risk_level: str = "LOW"  # "LOW", "MEDIUM", "HIGH"
    
    # Metadata
    created_at: str = field(default_factory=_now_iso)
    raw_chat_message: str = ""
    intent_keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for Firebase"""
        return {
            "mission_id": self.mission_id,
            "source": self.source,
            "status": self.status,
            "objective_description": self.objective_description,
            "objective_type": self.objective_type,
            "target_count": self.target_count,
            "allowed_domains": self.allowed_domains,
            "max_pages": self.max_pages,
            "max_duration_seconds": self.max_duration_seconds,
            "primary_tool": self.primary_tool,
            "alternative_tools": self.alternative_tools,
            "total_estimated_cost": self.total_estimated_cost,
            "total_cost_rationale": self.total_cost_rationale,
            "total_estimated_duration": self.total_estimated_duration,
            "total_duration_rationale": self.total_duration_rationale,
            "is_feasible": self.is_feasible,
            "feasibility_issues": self.feasibility_issues,
            "risk_level": self.risk_level,
            "created_at": self.created_at,
            "raw_chat_message": self.raw_chat_message,
            "intent_keywords": self.intent_keywords,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MissionPlan':
        """Create MissionPlan from dictionary"""
        return cls(**data)
