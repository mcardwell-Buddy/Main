"""
Phase 6 Visibility Integration

Bridges Phase 6 (Cognition Layer) reality assessments into UI presentation.

Provides:
1. Reality assessment enrichment for ResponseEnvelope
2. Chat summary generation from reality assessment
3. Whiteboard panel rendering

NO execution changes. READ-ONLY exposure only.
"""

from typing import Optional, Dict, Any
from dataclasses import asdict

try:
    from reality_reasoner import RealityReasoner, assess_reality
    REALITY_REASONER_AVAILABLE = True
except ImportError:
    REALITY_REASONER_AVAILABLE = False

try:
    from learning.whiteboard_phase6_panels import Phase6WhiteboardPanels
    WHITEBOARD_PANELS_AVAILABLE = True
except ImportError:
    WHITEBOARD_PANELS_AVAILABLE = False


class Phase6VisibilityEnricher:
    """
    Enriches ResponseEnvelope with Phase 6 reality assessment and visibility hints.
    
    Read-only integration:
    - Adds reality_assessment to ResponseEnvelope
    - Generates chat summary hints
    - Prepares whiteboard panels
    """
    
    def __init__(self):
        """Initialize enricher."""
        self.reasoner = None
        self.panel_renderer = None
        
        if REALITY_REASONER_AVAILABLE:
            self.reasoner = RealityReasoner()
        
        if WHITEBOARD_PANELS_AVAILABLE:
            self.panel_renderer = Phase6WhiteboardPanels()
    
    def enrich_response_with_assessment(
        self,
        response_envelope: 'ResponseEnvelope',
        task_description: str
    ) -> 'ResponseEnvelope':
        """
        Enrich ResponseEnvelope with Phase 6 reality assessment.
        
        Args:
            response_envelope: ResponseEnvelope to enrich
            task_description: Description of the task being assessed
            
        Returns:
            Enriched ResponseEnvelope
        """
        if not self.reasoner:
            return response_envelope
        
        # Get reality assessment
        assessment = self.reasoner.assess_reality(task_description)
        
        # Convert to dict for serialization
        assessment_dict = asdict(assessment)
        
        # Set on response envelope
        response_envelope.set_reality_assessment(assessment_dict)
        
        return response_envelope
    
    def generate_chat_summary_hints(
        self,
        assessment_dict: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate chat summary hints from reality assessment.
        
        Produces:
        - what_buddy_can_do: What Buddy can execute
        - what_you_must_do: What user must handle
        - what_can_be_scaled: Parallelization potential
        
        Args:
            assessment_dict: Reality assessment dict
            
        Returns:
            Dict with summary hints
        """
        hints = {
            "what_buddy_can_do": "",
            "what_you_must_do": "",
            "what_can_be_scaled": ""
        }
        
        if not assessment_dict:
            return hints
        
        # Extract key fields
        capability = assessment_dict.get("capability", "").lower()
        role = assessment_dict.get("who_does_what", "").lower()
        scalability = assessment_dict.get("scalability", "").lower()
        units = assessment_dict.get("parallelizable_units", 1)
        effort = assessment_dict.get("effort_level", "").lower()
        
        # What Buddy can do
        can_do_parts = []
        if "digital" in capability or role == "buddy":
            can_do_parts.append("Execute digital/automated components")
        if role == "both" and "hybrid" in capability:
            can_do_parts.append("Help with automation and coordination")
        if "scalable" in scalability and units > 1:
            can_do_parts.append(f"Process {units}+ items in parallel")
        
        hints["what_buddy_can_do"] = " • ".join(can_do_parts) if can_do_parts else "Support execution"
        
        # What you must do
        must_do_parts = []
        if "physical" in capability or role == "user":
            must_do_parts.append("Execute physical/in-person components")
        if role == "both":
            must_do_parts.append("Provide approvals and decisions")
        if "high" in effort:
            must_do_parts.append("Schedule dedicated time")
        if role == "escalate":
            must_do_parts.append("Escalate to management")
        if not must_do_parts:
            must_do_parts.append("Review and validate results")
        
        hints["what_you_must_do"] = " • ".join(must_do_parts)
        
        # What can be scaled
        scale_parts = []
        if "scalable" in scalability and units > 1:
            scale_parts.append(f"{units} parallel execution units available")
        elif "conditional" in scalability:
            scale_parts.append("Scalable with conditions (requires setup)")
        else:
            scale_parts.append("Sequential processing required")
        
        hints["what_can_be_scaled"] = " • ".join(scale_parts)
        
        return hints
    
    def get_whiteboard_panel_hint(
        self,
        assessment_dict: Dict[str, Any],
        panel_type: str = "unified"
    ) -> str:
        """
        Get whiteboard panel rendering for UI.
        
        Panel types:
        - "capability": Capability boundary panel
        - "energy": Human energy panel
        - "scalability": Scalability assessment panel
        - "unified": Full unified reality panel
        - "hints": Chat summary hints
        - "all": All panels
        
        Args:
            assessment_dict: Reality assessment dict
            panel_type: Which panel to render
            
        Returns:
            Formatted panel text
        """
        if not self.panel_renderer or not assessment_dict:
            return "Assessment not available"
        
        # Set the assessment
        self.panel_renderer.set_reality_assessment(assessment_dict)
        
        # Render requested panel
        if panel_type == "capability":
            return self.panel_renderer.render_capability_boundary_panel()
        elif panel_type == "energy":
            return self.panel_renderer.render_human_energy_panel()
        elif panel_type == "scalability":
            return self.panel_renderer.render_scalability_assessment_panel()
        elif panel_type == "unified":
            return self.panel_renderer.render_unified_reality_panel()
        elif panel_type == "hints":
            return self.panel_renderer.render_chat_summary_hints()
        elif panel_type == "all":
            return self.panel_renderer.render_all_panels()
        else:
            return "Unknown panel type"
    
    def format_chat_response_with_reality(
        self,
        base_summary: str,
        assessment_dict: Dict[str, Any]
    ) -> str:
        """
        Format chat response incorporating reality assessment summary.
        
        Adds:
        - What Buddy can do
        - What you must do
        - What can be scaled
        
        Args:
            base_summary: Base chat response
            assessment_dict: Reality assessment dict
            
        Returns:
            Enriched summary
        """
        if not assessment_dict:
            return base_summary
        
        hints = self.generate_chat_summary_hints(assessment_dict)
        
        # Build enriched response
        lines = [base_summary]
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**What Buddy can do:**")
        lines.append(f"• {hints['what_buddy_can_do']}")
        lines.append("")
        lines.append("**What you must do:**")
        lines.append(f"• {hints['what_you_must_do']}")
        lines.append("")
        lines.append("**What can be scaled:**")
        lines.append(f"• {hints['what_can_be_scaled']}")
        
        return "\n".join(lines)


def create_visibility_enricher() -> Phase6VisibilityEnricher:
    """Create a Phase 6 visibility enricher instance."""
    return Phase6VisibilityEnricher()


def assess_and_enrich(
    response_envelope: 'ResponseEnvelope',
    task_description: str
) -> 'ResponseEnvelope':
    """
    Convenience function to assess task and enrich ResponseEnvelope.
    
    Args:
        response_envelope: ResponseEnvelope to enrich
        task_description: Task description
        
    Returns:
        Enriched ResponseEnvelope with reality_assessment
    """
    enricher = create_visibility_enricher()
    return enricher.enrich_response_with_assessment(response_envelope, task_description)
