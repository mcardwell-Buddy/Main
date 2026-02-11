"""
Phase 6 Step 5: Whiteboard Phase 6 Panels

Exposes Phase 6 (Cognition Layer) intelligence in the Whiteboard as default-visible, 
read-only panels.

Panels:
- Capability Boundary: Task classification (DIGITAL/PHYSICAL/HYBRID)
- Human Energy: Effort estimation + rest awareness
- Scalability Assessment: Parallel potential + bottlenecks

Hard constraints:
- NO execution changes
- NO autonomy
- NO mission triggering
- READ-ONLY over reality assessments
- Deterministic rendering only
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


class Phase6WhiteboardPanels:
    """
    Renders Phase 6 Cognition intelligence panels for the Whiteboard.
    
    All panels are read-only, default-visible, and non-executing.
    Shows what Buddy can do, what user must do, and what can be scaled.
    """
    
    def __init__(self):
        """Initialize Phase 6 panel renderer."""
        self.latest_assessment = None
    
    def set_reality_assessment(self, assessment: Dict[str, Any]) -> None:
        """
        Set the latest reality assessment for rendering.
        
        Args:
            assessment: RealityAssessment dict
        """
        self.latest_assessment = assessment
    
    def render_capability_boundary_panel(self) -> str:
        """
        Render Capability Boundary panel showing task type classification.
        
        Displays: DIGITAL | PHYSICAL | HYBRID classification
        
        Returns:
            Formatted panel text
        """
        lines = []
        lines.append("┌─────────────────────────────────────────────────────────┐")
        lines.append("│ CAPABILITY BOUNDARY - What Kind of Task?                │")
        lines.append("│ [Read-Only • No Actions]                                │")
        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")
        
        if not self.latest_assessment:
            lines.append("  No assessment available")
            lines.append("")
            return "\n".join(lines)
        
        capability = self.latest_assessment.get("capability", "unknown").upper()
        reasoning = self.latest_assessment.get("reasoning_by_model", {}).get("capability", "")
        
        # Map capability to display
        capability_map = {
            "DIGITAL": "🖥️  DIGITAL - Software/automation executable",
            "PHYSICAL": "🏢 PHYSICAL - Requires in-person/hands-on",
            "HYBRID": "↔️  HYBRID - Mix of digital + physical"
        }
        
        display = capability_map.get(capability, f"❓ {capability}")
        
        lines.append(f"  Capability Type: {display}")
        
        if reasoning:
            # Format reasoning to fit panel width
            wrapped = self._wrap_text(reasoning, 55)
            lines.append("")
            lines.append("  Reasoning:")
            for line in wrapped:
                lines.append(f"    {line}")
        
        lines.append("")
        return "\n".join(lines)
    
    def render_human_energy_panel(self) -> str:
        """
        Render Human Energy panel showing effort estimation and rest awareness.
        
        Displays: LOW/MEDIUM/HIGH + time estimates + rest window
        
        Returns:
            Formatted panel text
        """
        lines = []
        lines.append("┌─────────────────────────────────────────────────────────┐")
        lines.append("│ HUMAN ENERGY - Effort & Rest Awareness                  │")
        lines.append("│ [Read-Only • No Actions]                                │")
        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")
        
        if not self.latest_assessment:
            lines.append("  No assessment available")
            lines.append("")
            return "\n".join(lines)
        
        effort = self.latest_assessment.get("effort_level", "unknown").upper()
        min_min = self.latest_assessment.get("min_minutes", 0)
        est_min = self.latest_assessment.get("estimated_minutes", 0)
        max_min = self.latest_assessment.get("max_minutes", 0)
        
        # Map effort to display
        effort_map = {
            "LOW": ("⚡ LOW", "Quick task (minutes)", "can execute anytime"),
            "MEDIUM": ("⚙️  MEDIUM", "Moderate effort (15-30 min)", "plan dedicated time"),
            "HIGH": ("⚠️  HIGH", "Significant effort (30+ min)", "schedule rest after"),
        }
        
        effort_icon, effort_desc, effort_note = effort_map.get(effort, ("❓", f"{effort}", ""))
        
        lines.append(f"  Effort Level: {effort_icon} {effort_desc}")
        lines.append(f"  Time Estimate: {est_min:.0f} min (range: {min_min:.0f}-{max_min:.0f})")
        lines.append(f"  Note: {effort_note}")
        
        # Rest warning if high effort
        if effort == "HIGH":
            lines.append("")
            lines.append("  ⏰ REST WINDOW: Max 120 min continuous")
            lines.append("     Schedule rest breaks after high-effort tasks")
        
        reasoning = self.latest_assessment.get("reasoning_by_model", {}).get("energy", "")
        if reasoning:
            wrapped = self._wrap_text(reasoning, 55)
            lines.append("")
            lines.append("  Reasoning:")
            for line in wrapped:
                lines.append(f"    {line}")
        
        lines.append("")
        return "\n".join(lines)
    
    def render_scalability_assessment_panel(self) -> str:
        """
        Render Scalability Assessment panel showing parallel potential.
        
        Displays: SCALABLE/NON_SCALABLE/CONDITIONAL + bottlenecks + units
        
        Returns:
            Formatted panel text
        """
        lines = []
        lines.append("┌─────────────────────────────────────────────────────────┐")
        lines.append("│ SCALABILITY ASSESSMENT - Parallel Potential             │")
        lines.append("│ [Read-Only • No Actions]                                │")
        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")
        
        if not self.latest_assessment:
            lines.append("  No assessment available")
            lines.append("")
            return "\n".join(lines)
        
        scalability = self.latest_assessment.get("scalability", "unknown").upper()
        bottleneck = self.latest_assessment.get("bottleneck_type", "none")
        units = self.latest_assessment.get("parallelizable_units", 1)
        
        # Map scalability to display
        scalability_map = {
            "SCALABLE": "📈 SCALABLE - Can be parallelized",
            "NON_SCALABLE": "📊 NON_SCALABLE - Sequential processing required",
            "CONDITIONAL": "⚙️  CONDITIONAL - Depends on conditions"
        }
        
        display = scalability_map.get(scalability, f"❓ {scalability}")
        
        lines.append(f"  Scalability: {display}")
        
        # Show bottleneck if not "none"
        if bottleneck and bottleneck.lower() != "none":
            bottleneck_map = {
                "human": "Human bottleneck - can't parallelize",
                "system": "System bottleneck - limited resources",
                "temporal": "Temporal bottleneck - time constraints",
                "sequential": "Sequential processing required",
                "data_dependency": "Data dependencies prevent parallelization"
            }
            bottleneck_desc = bottleneck_map.get(bottleneck, bottleneck)
            lines.append(f"  Bottleneck: {bottleneck_desc}")
        
        # Show parallelizable units
        if units > 1:
            lines.append(f"  Parallel Units: {units} ({self._unit_category(units)})")
        else:
            lines.append(f"  Parallel Units: Single (sequential execution)")
        
        # Show conditions if conditional
        conditions = self.latest_assessment.get("conditions", [])
        if scalability == "CONDITIONAL" and conditions and conditions != ["None"]:
            lines.append("")
            lines.append("  Conditions for Scaling:")
            for cond in conditions[:3]:  # Show first 3 conditions
                if cond and cond != "None":
                    lines.append(f"    • {cond}")
        
        reasoning = self.latest_assessment.get("reasoning_by_model", {}).get("scalability", "")
        if reasoning:
            wrapped = self._wrap_text(reasoning, 55)
            lines.append("")
            lines.append("  Reasoning:")
            for line in wrapped:
                lines.append(f"    {line}")
        
        lines.append("")
        return "\n".join(lines)
    
    def render_unified_reality_panel(self) -> str:
        """
        Render unified Reality Assessment panel with role assignment and risk.
        
        Displays: WHO_DOES_WHAT + RISK_LEVEL + KEY_CONDITIONS
        
        Returns:
            Formatted panel text
        """
        lines = []
        lines.append("┌─────────────────────────────────────────────────────────┐")
        lines.append("│ UNIFIED REALITY ASSESSMENT                              │")
        lines.append("│ [Read-Only • No Actions]                                │")
        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")
        
        if not self.latest_assessment:
            lines.append("  No assessment available")
            lines.append("")
            return "\n".join(lines)
        
        # Role assignment
        role = self.latest_assessment.get("who_does_what", "unknown").upper()
        role_map = {
            "BUDDY": "🤖 Buddy can execute directly",
            "USER": "👤 User must execute",
            "BOTH": "👥 Collaboration needed",
            "ESCALATE": "⬆️  Requires management review"
        }
        role_desc = role_map.get(role, f"❓ {role}")
        lines.append(f"  Task Assignment: {role_desc}")
        
        # Risk level
        risk = self.latest_assessment.get("risk_level", "unknown").upper()
        risk_map = {
            "LOW": ("🟢 LOW", "Safe to proceed"),
            "MEDIUM": ("🟡 MEDIUM", "Proceed with caution"),
            "HIGH": ("🔴 HIGH", "Significant concerns"),
            "CRITICAL": ("🛑 CRITICAL", "Requires escalation")
        }
        risk_icon, risk_note = risk_map.get(risk, ("❓", f"{risk}"))
        lines.append(f"  Risk Level: {risk_icon} - {risk_note}")
        
        # Key conditions
        conditions = self.latest_assessment.get("conditions", [])
        if conditions and conditions != ["None"]:
            lines.append("")
            lines.append("  Required Conditions:")
            for i, cond in enumerate(conditions[:3], 1):
                if cond and cond != "None":
                    lines.append(f"    {i}. {cond}")
        
        # Risk notes (top 2)
        risk_notes = self.latest_assessment.get("risk_notes", [])
        if risk_notes:
            lines.append("")
            lines.append("  Risk Notes:")
            for i, note in enumerate(risk_notes[:2], 1):
                lines.append(f"    • {note}")
        
        # Integrated reasoning
        reasoning = self.latest_assessment.get("reasoning", "")
        if reasoning:
            wrapped = self._wrap_text(reasoning, 55)
            lines.append("")
            lines.append("  Reasoning:")
            for line in wrapped:
                lines.append(f"    {line}")
        
        lines.append("")
        return "\n".join(lines)
    
    def render_chat_summary_hints(self) -> str:
        """
        Render hints for chat reply summarization.
        
        Provides templates for: "What Buddy can do" / "What you must do" / "What can be scaled"
        
        Returns:
            Formatted summary hints
        """
        lines = []
        lines.append("┌─────────────────────────────────────────────────────────┐")
        lines.append("│ CHAT REPLY HINTS - Key Points to Summarize              │")
        lines.append("│ [Read-Only • Suggestions Only]                          │")
        lines.append("└─────────────────────────────────────────────────────────┘")
        lines.append("")
        
        if not self.latest_assessment:
            lines.append("  No assessment available")
            lines.append("")
            return "\n".join(lines)
        
        capability = self.latest_assessment.get("capability", "").lower()
        role = self.latest_assessment.get("who_does_what", "").lower()
        scalability = self.latest_assessment.get("scalability", "").lower()
        units = self.latest_assessment.get("parallelizable_units", 1)
        
        # What Buddy can do
        lines.append("  ✓ What Buddy Can Do:")
        if "digital" in capability or role == "buddy":
            lines.append("    • Execute digital/automated tasks")
        if role == "both" and "hybrid" in capability:
            lines.append("    • Help with digital components")
        if "scalable" in scalability and units > 1:
            lines.append(f"    • Process {units}+ items in parallel")
        lines.append("")
        
        # What user must do
        lines.append("  ✓ What You Must Do:")
        if "physical" in capability or role == "user":
            lines.append("    • Execute physical/in-person tasks")
        if role == "both":
            lines.append("    • Provide decisions/approvals")
        if "high" in self.latest_assessment.get("effort_level", "").lower():
            lines.append("    • Schedule dedicated time")
        if role == "escalate":
            lines.append("    • Escalate to management")
        lines.append("")
        
        # What can be scaled
        lines.append("  ✓ What Can Be Scaled:")
        if "scalable" in scalability and units > 1:
            lines.append(f"    • {units} parallel units available")
        elif "conditional" in scalability:
            lines.append("    • Scalable with conditions (see above)")
        else:
            lines.append("    • Sequential processing only")
        lines.append("")
        
        return "\n".join(lines)
    
    def render_all_panels(self) -> str:
        """
        Render all Phase 6 panels as a unified whiteboard section.
        
        Returns:
            Complete Phase 6 whiteboard section
        """
        lines = []
        lines.append("")
        lines.append("=" * 61)
        lines.append("PHASE 6: COGNITION LAYER - Reality Assessment")
        lines.append("=" * 61)
        lines.append("")
        
        lines.append(self.render_capability_boundary_panel())
        lines.append(self.render_human_energy_panel())
        lines.append(self.render_scalability_assessment_panel())
        lines.append(self.render_unified_reality_panel())
        lines.append(self.render_chat_summary_hints())
        
        lines.append("=" * 61)
        lines.append("")
        
        return "\n".join(lines)
    
    def _wrap_text(self, text: str, width: int = 55) -> List[str]:
        """
        Wrap text to fit within panel width.
        
        Args:
            text: Text to wrap
            width: Maximum line width
            
        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > width:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word) + 1
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines
    
    def _unit_category(self, units: int) -> str:
        """
        Categorize parallelizable units.
        
        Args:
            units: Number of parallelizable units
            
        Returns:
            Category description
        """
        if units <= 1:
            return "single"
        elif units <= 10:
            return "few"
        elif units <= 100:
            return "batch"
        else:
            return "large batch"


def create_phase6_panel_renderer() -> Phase6WhiteboardPanels:
    """Create a Phase 6 panel renderer instance."""
    return Phase6WhiteboardPanels()

