"""
Reality Reasoner - Phase 6 Step 4

Read-only aggregator combining:
- Capability Boundary Model (DIGITAL/PHYSICAL/HYBRID)
- Human Energy Model (LOW/MEDIUM/HIGH effort)
- Scaling Assessment Model (SCALABLE/NON_SCALABLE/CONDITIONAL)

PURPOSE:
Synthesize task analysis across all cognition models to produce
actionable reality assessment without execution or autonomy changes.

OUTPUT:
RealityAssessment with:
- who_does_what: Buddy | User | Both | Escalate
- human_cost: Effort level + time estimate
- scalability: Parallel potential
- capability_type: Digital/Physical/Hybrid
- risk_notes: Aggregated constraints
- reasoning: Human-readable summary

NO ACTIONS:
- Assessment only
- No execution changes
- No agent spawning
- No scheduling
- Read-only aggregation
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Tuple
from uuid import uuid4

# Import the three models
from capability_boundary_model import (
    CapabilityBoundaryModel,
    Capability,
)
from human_energy_model import (
    HumanEnergyModel,
    EffortLevel,
)
from scaling_assessment_model import (
    ScalingAssessmentModel,
    ScalabilityLevel,
)


class RoleAssignment(Enum):
    """Who should handle this task."""
    BUDDY = "BUDDY"          # Buddy can execute directly
    USER = "USER"            # Requires human execution
    BOTH = "BOTH"            # Collaboration needed
    ESCALATE = "ESCALATE"    # Needs management review


class RiskLevel(Enum):
    """Overall risk assessment."""
    LOW = "LOW"              # Can execute safely
    MEDIUM = "MEDIUM"        # Proceed with caution
    HIGH = "HIGH"            # Significant concerns
    CRITICAL = "CRITICAL"    # Requires escalation


@dataclass
class RealityAssessment:
    """Combined reality assessment across all cognition models."""
    task_description: str
    
    # Role assignment
    who_does_what: RoleAssignment
    
    # Component assessments
    capability: Capability
    effort_level: EffortLevel
    scalability: ScalabilityLevel
    
    # Effort details
    estimated_minutes: float
    min_minutes: float
    max_minutes: float
    
    # Scalability details
    parallelizable_units: int
    bottleneck_type: str  # human, system, temporal, sequential, data_dependency, none
    
    # Risk assessment
    risk_level: RiskLevel
    risk_notes: List[str]
    conditions: List[str]  # Required conditions for execution
    
    # Reasoning
    reasoning: str
    reasoning_by_model: Dict[str, str]  # Per-model reasoning
    
    # Metadata
    session_id: str
    timestamp: str


class RealityReasoner:
    """Read-only aggregator reasoning about task reality."""

    def __init__(self):
        """Initialize Reality Reasoner with all component models."""
        self.capability_model = CapabilityBoundaryModel()
        self.energy_model = HumanEnergyModel()
        self.scaling_model = ScalingAssessmentModel()
        self.session_id = str(uuid4())

    def assess_reality(self, task_description: str) -> RealityAssessment:
        """
        Assess the complete reality of a task across all dimensions.

        This is a read-only assessment combining:
        1. What kind of task (capability boundary)
        2. How much human effort (energy model)
        3. Can it scale (scaling assessment)

        Args:
            task_description: Description of the task

        Returns:
            RealityAssessment with comprehensive analysis
        """
        # Get component assessments (read-only, no execution)
        capability_result = self.capability_model.classify_task(task_description)
        energy_result = self.energy_model.estimate_human_cost(task_description)
        scaling_result = self.scaling_model.assess_scalability(task_description)

        # Determine role assignment
        role = self._determine_role(
            capability_result.capability,
            energy_result.effort_level,
            scaling_result.scalability_level,
            scaling_result.bottleneck_type
        )

        # Assess risk
        risk_level, risk_notes = self._assess_risk(
            capability_result.capability,
            energy_result.effort_level,
            scaling_result.scalability_level,
            scaling_result.bottleneck_type,
            energy_result.rest_warning,
            energy_result.rest_recommendation
        )

        # Generate conditions
        conditions = self._generate_conditions(
            capability_result.capability,
            energy_result.effort_level,
            scaling_result.conditions_for_scale,
            energy_result.rest_recommendation
        )

        # Generate integrated reasoning
        reasoning = self._generate_integrated_reasoning(
            role,
            capability_result.capability,
            energy_result.effort_level,
            scaling_result.scalability_level,
            risk_level
        )

        # Capture per-model reasoning
        reasoning_by_model = {
            "capability": capability_result.reasoning,
            "energy": energy_result.reasoning,
            "scalability": scaling_result.reasoning,
        }

        return RealityAssessment(
            task_description=task_description,
            who_does_what=role,
            capability=capability_result.capability,
            effort_level=energy_result.effort_level,
            scalability=scaling_result.scalability_level,
            estimated_minutes=energy_result.estimated_minutes,
            min_minutes=energy_result.min_minutes,
            max_minutes=energy_result.max_minutes,
            parallelizable_units=scaling_result.parallelizable_units,
            bottleneck_type=scaling_result.bottleneck_type,
            risk_level=risk_level,
            risk_notes=risk_notes,
            conditions=conditions,
            reasoning=reasoning,
            reasoning_by_model=reasoning_by_model,
            session_id=self.session_id,
            timestamp=datetime.now().isoformat()
        )

    def _determine_role(
        self,
        capability: Capability,
        effort: EffortLevel,
        scalability: ScalabilityLevel,
        bottleneck_type: str
    ) -> RoleAssignment:
        """
        Determine who should handle this task.

        Logic:
        - BUDDY: Digital + LOW/MEDIUM effort + Scalable
        - USER: Physical + any effort
        - BOTH: Hybrid, or approval needed
        - ESCALATE: High effort + human bottleneck
        """
        # User tasks
        if capability == Capability.PHYSICAL:
            return RoleAssignment.USER

        # Escalation cases
        if effort == EffortLevel.HIGH and bottleneck_type == "human":
            return RoleAssignment.ESCALATE

        # Hybrid requires collaboration
        if capability == Capability.HYBRID:
            return RoleAssignment.BOTH

        # Digital with approval/conditions
        if scalability == ScalabilityLevel.CONDITIONAL:
            return RoleAssignment.BOTH

        # Pure digital, low-medium effort
        if capability == Capability.DIGITAL:
            if effort in [EffortLevel.LOW, EffortLevel.MEDIUM]:
                return RoleAssignment.BUDDY
            else:
                return RoleAssignment.BOTH

        return RoleAssignment.BOTH

    def _assess_risk(
        self,
        capability: Capability,
        effort: EffortLevel,
        scalability: ScalabilityLevel,
        bottleneck_type: str,
        rest_warning: bool,
        rest_recommendation: str
    ) -> Tuple[RiskLevel, List[str]]:
        """
        Assess overall risk of executing this task.

        Risk factors:
        - HIGH effort = higher risk
        - Human bottleneck = higher risk
        - Non-scalable with high effort = higher risk
        - Rest constraints = higher risk
        """
        risk_notes = []
        risk_score = 0

        # Effort risk
        if effort == EffortLevel.HIGH:
            risk_score += 2
            risk_notes.append("High human effort required")
        elif effort == EffortLevel.MEDIUM:
            risk_score += 1
            risk_notes.append("Moderate effort needed")

        # Bottleneck risk
        if bottleneck_type == "human":
            risk_score += 2
            risk_notes.append("Human bottleneck: cannot parallelize")
        elif bottleneck_type in ["system", "temporal"]:
            risk_score += 1
            risk_notes.append(f"System bottleneck: {bottleneck_type}")

        # Scalability risk (non-scalable high-effort is risky)
        if scalability == ScalabilityLevel.NON_SCALABLE and effort == EffortLevel.HIGH:
            risk_score += 2
            risk_notes.append("Non-scalable but high effort")

        # Rest constraints
        if rest_warning:
            risk_score += 1
            if rest_recommendation == "EXCEEDS_LIMIT":
                risk_score += 1
                risk_notes.append("Exceeds human rest window")
            else:
                risk_notes.append("Approaching human rest limit")

        # Physical capability risk
        if capability == Capability.PHYSICAL:
            risk_score += 1
            risk_notes.append("Requires physical/in-person execution")

        # Determine risk level
        if risk_score >= 6:
            return RiskLevel.CRITICAL, risk_notes
        elif risk_score >= 4:
            return RiskLevel.HIGH, risk_notes
        elif risk_score >= 2:
            return RiskLevel.MEDIUM, risk_notes
        else:
            return RiskLevel.LOW, risk_notes

    def _generate_conditions(
        self,
        capability: Capability,
        effort: EffortLevel,
        scaling_conditions: List[str],
        rest_recommendation: str
    ) -> List[str]:
        """Generate execution conditions required for this task."""
        conditions = []

        # Capability conditions
        if capability == Capability.HYBRID:
            conditions.append("Requires approval for final execution")

        if capability == Capability.PHYSICAL:
            conditions.append("Requires human availability")

        # Effort conditions
        if effort == EffortLevel.HIGH:
            conditions.append("Schedule for sufficient time")

        # Scaling conditions
        conditions.extend(scaling_conditions)

        # Rest conditions
        if rest_recommendation == "NEAR_LIMIT":
            conditions.append("Execute after human rest period")
        elif rest_recommendation == "EXCEEDS_LIMIT":
            conditions.append("Requires rest before execution")

        return conditions if conditions else ["None"]

    def _generate_integrated_reasoning(
        self,
        role: RoleAssignment,
        capability: Capability,
        effort: EffortLevel,
        scalability: ScalabilityLevel,
        risk: RiskLevel
    ) -> str:
        """Generate integrated reasoning across all models."""
        role_map = {
            RoleAssignment.BUDDY: "Buddy can execute this directly",
            RoleAssignment.USER: "Human must execute this task",
            RoleAssignment.BOTH: "Collaboration between Buddy and user needed",
            RoleAssignment.ESCALATE: "Escalate to management for review",
        }

        capability_map = {
            Capability.DIGITAL: "digital capability",
            Capability.PHYSICAL: "physical task",
            Capability.HYBRID: "hybrid (digital + physical)",
        }

        return (
            f"Reality Assessment: {role_map[role]}. "
            f"Task is {capability_map[capability]}, "
            f"requires {effort.value.lower()} effort, "
            f"and is {scalability.value.lower()}. "
            f"Overall risk: {risk.value}"
        )

    def get_session_info(self) -> Dict[str, str]:
        """Get session information."""
        return {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat()
        }


def get_reality_reasoner() -> RealityReasoner:
    """Get singleton-like instance of RealityReasoner."""
    return RealityReasoner()


def assess_reality(task_description: str) -> RealityAssessment:
    """
    Convenience function to assess task reality.

    Args:
        task_description: Description of the task

    Returns:
        RealityAssessment
    """
    reasoner = RealityReasoner()
    return reasoner.assess_reality(task_description)

