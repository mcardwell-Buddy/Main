"""
Phase 6 Step 5 Visibility - UI Integration Examples

Quick reference showing how Phase 6 cognition is exposed in the UI.
"""

# =============================================================================
# EXAMPLE 1: WHITEBOARD PANEL RENDERING
# =============================================================================

EXAMPLE_ASSESSMENT_1 = {
    "task_description": "Process batch of 500 customer records in parallel",
    "who_does_what": "BOTH",
    "capability": "HYBRID",
    "effort_level": "MEDIUM",
    "scalability": "SCALABLE",
    "estimated_minutes": 15.0,
    "min_minutes": 5.0,
    "max_minutes": 30.0,
    "parallelizable_units": 500,
    "bottleneck_type": "none",
    "risk_level": "LOW",
    "risk_notes": ["Moderate effort needed"],
    "conditions": ["Requires approval for final execution"],
    "reasoning": "Collaboration between Buddy and user needed. Task is hybrid, requires medium effort, and is scalable. Overall risk: LOW",
    "reasoning_by_model": {
        "capability": "Classified as HYBRID: ambiguous task requiring handoff or approval.",
        "energy": "MEDIUM effort (33% confidence). Estimated 15 minutes (5-30 range).",
        "scalability": "SCALABLE (89% confidence). Parallelizable units: 500"
    }
}

WHITEBOARD_OUTPUT_1 = """
============================================================
PHASE 6: COGNITION LAYER - Reality Assessment
============================================================

┌─────────────────────────────────────────────────────────┐
│ CAPABILITY BOUNDARY - What Kind of Task?                │
│ [Read-Only • No Actions]                                │
└─────────────────────────────────────────────────────────┘

  Capability Type: ↔️  HYBRID - Mix of digital + physical
  
  Reasoning:
    Classified as HYBRID: ambiguous task requiring
    handoff or approval.

┌─────────────────────────────────────────────────────────┐
│ HUMAN ENERGY - Effort & Rest Awareness                  │
│ [Read-Only • No Actions]                                │
└─────────────────────────────────────────────────────────┘

  Effort Level: ⚙️  MEDIUM
  Time Estimate: 15 min (range: 5-30)
  Note: plan dedicated time

┌─────────────────────────────────────────────────────────┐
│ SCALABILITY ASSESSMENT - Parallel Potential             │
│ [Read-Only • No Actions]                                │
└─────────────────────────────────────────────────────────┘

  Scalability: 📈 SCALABLE - Can be parallelized
  Parallel Units: 500 (large batch)
  
  Reasoning:
    SCALABLE (89% confidence). Parallelizable units:
    500

┌─────────────────────────────────────────────────────────┐
│ UNIFIED REALITY ASSESSMENT                              │
│ [Read-Only • No Actions]                                │
└─────────────────────────────────────────────────────────┘

  Task Assignment: 👥 Collaboration between Buddy and user
  Risk Level: 🟢 LOW - Safe to proceed
  
  Required Conditions:
    1. Requires approval for final execution

  Reasoning:
    Collaboration between Buddy and user needed. Task
    is hybrid, requires medium effort, and is scalable.
    Overall risk: LOW

┌─────────────────────────────────────────────────────────┐
│ CHAT REPLY HINTS - Key Points to Summarize              │
│ [Read-Only • Suggestions Only]                          │
└─────────────────────────────────────────────────────────┘

  ✓ What Buddy Can Do:
    • Help with automation and coordination
    • Process 500+ items in parallel

  ✓ What You Must Do:
    • Provide approvals and decisions

  ✓ What Can Be Scaled:
    • 500 parallel execution units available

============================================================
"""

# =============================================================================
# EXAMPLE 2: CHAT RESPONSE WITH VISIBILITY
# =============================================================================

CHAT_RESPONSE_2 = """
I can help you negotiate this contract with the client. This is a complex task
that will require your active involvement.

---

**What Buddy can do:**
• Prepare documentation and communication templates

**What you must do:**
• Execute negotiations directly
• Make final approval decisions

**What can be scaled:**
• Sequential processing only (human-dependent negotiation)

---

**Timeline**: 60 minutes of focused time recommended
**Risk Level**: CRITICAL (high effort + human bottleneck)
**Note**: This requires your direct engagement
"""

# =============================================================================
# EXAMPLE 3: RESPONSE ENVELOPE WITH REALITY ASSESSMENT
# =============================================================================

RESPONSE_ENVELOPE_3 = {
    "response_type": "text",
    "summary": "Ready to process customer batch updates",
    "artifacts": [],
    "missions_spawned": [],
    "signals_emitted": [],
    "reality_assessment": {
        "task_description": "Update customer records in batch",
        "who_does_what": "BUDDY",
        "capability": "DIGITAL",
        "effort_level": "LOW",
        "scalability": "SCALABLE",
        "estimated_minutes": 10.0,
        "min_minutes": 5.0,
        "max_minutes": 20.0,
        "parallelizable_units": 100,
        "bottleneck_type": "none",
        "risk_level": "LOW",
        "risk_notes": [],
        "conditions": ["None"],
        "reasoning": "Buddy can execute this directly...",
        "reasoning_by_model": {
            "capability": "DIGITAL",
            "energy": "LOW",
            "scalability": "SCALABLE"
        },
        "session_id": "session-123",
        "timestamp": "2026-02-07T10:30:00"
    },
    "live_stream_id": None,
    "ui_hints": None,
    "timestamp": "2026-02-07T10:30:00",
    "metadata": {}
}

# =============================================================================
# EXAMPLE 4: HIGH-RISK ESCALATION VISIBILITY
# =============================================================================

WHITEBOARD_OUTPUT_4 = """
============================================================
PHASE 6: COGNITION LAYER - Reality Assessment
============================================================

┌─────────────────────────────────────────────────────────┐
│ CAPABILITY BOUNDARY - What Kind of Task?                │
│ [Read-Only • No Actions]                                │
└─────────────────────────────────────────────────────────┘

  Capability Type: 🏢 PHYSICAL - Requires in-person/hands-on

┌─────────────────────────────────────────────────────────┐
│ HUMAN ENERGY - Effort & Rest Awareness                  │
│ [Read-Only • No Actions]                                │
└─────────────────────────────────────────────────────────┘

  Effort Level: ⚠️  HIGH
  Time Estimate: 120 min (range: 60-240)
  Note: schedule rest after

  ⏰ REST WINDOW: Max 120 min continuous
     Schedule rest breaks after high-effort tasks

┌─────────────────────────────────────────────────────────┐
│ SCALABILITY ASSESSMENT - Parallel Potential             │
│ [Read-Only • No Actions]                                │
└─────────────────────────────────────────────────────────┘

  Scalability: 📊 NON_SCALABLE - Sequential processing
  Bottleneck: Human bottleneck - can't parallelize
  Parallel Units: Single (sequential execution)

┌─────────────────────────────────────────────────────────┐
│ UNIFIED REALITY ASSESSMENT                              │
│ [Read-Only • No Actions]                                │
└─────────────────────────────────────────────────────────┘

  Task Assignment: ⬆️  Requires management review
  Risk Level: 🛑 CRITICAL - Requires escalation
  
  Required Conditions:
    1. Requires human availability
    2. Schedule for sufficient time
    3. Requires rest before execution
  
  Risk Notes:
    • High human effort required
    • Human bottleneck: cannot parallelize
    • Non-scalable but high effort

┌─────────────────────────────────────────────────────────┐
│ CHAT REPLY HINTS - Key Points to Summarize              │
│ [Read-Only • Suggestions Only]                          │
└─────────────────────────────────────────────────────────┘

  ✓ What Buddy Can Do:
    • Provide preparation and research
    • Generate documentation

  ✓ What You Must Do:
    • Execute this task in person
    • Schedule adequate time
    • Escalate to management if needed

  ✓ What Can Be Scaled:
    • Sequential processing only

============================================================
"""

# =============================================================================
# INTEGRATION USAGE
# =============================================================================

"""
Usage in application code:

from response_envelope import ResponseEnvelope, ResponseType
from phase6_visibility import assess_and_enrich
from learning.whiteboard_phase6_panels import Phase6WhiteboardPanels

# 1. Create response
response = ResponseEnvelope(
    response_type=ResponseType.TEXT,
    summary="Processing your request..."
)

# 2. Enrich with Phase 6 assessment
response = assess_and_enrich(response, "Batch process 1000 records")

# 3. Use in chat reply
enricher = Phase6VisibilityEnricher()
hints = enricher.generate_chat_summary_hints(response.reality_assessment)
chat_reply = enricher.format_chat_response_with_reality(
    response.summary,
    response.reality_assessment
)

# 4. Render whiteboard panels
panels = Phase6WhiteboardPanels()
panels.set_reality_assessment(response.reality_assessment)
whiteboard_section = panels.render_all_panels()

# 5. Get individual panels as needed
capability_panel = panels.render_capability_boundary_panel()
energy_panel = panels.render_human_energy_panel()
scalability_panel = panels.render_scalability_assessment_panel()
unified_panel = panels.render_unified_reality_panel()
chat_hints = panels.render_chat_summary_hints()
"""

# =============================================================================
# KEY VISIBILITY FEATURES
# =============================================================================

KEY_FEATURES = """
Phase 6 Step 5 makes the following visible in the UI:

1. CAPABILITY BOUNDARY PANEL
   Shows: DIGITAL | PHYSICAL | HYBRID
   Purpose: Clarify what kind of work this is
   Users see: Visual icon + description + reasoning

2. HUMAN ENERGY PANEL
   Shows: LOW | MEDIUM | HIGH effort + time + rest window
   Purpose: Show effort required and rest constraints
   Users see: Effort level + estimated time + rest warnings

3. SCALABILITY ASSESSMENT PANEL
   Shows: SCALABLE | NON_SCALABLE | CONDITIONAL + bottleneck + units
   Purpose: Show parallel potential and constraints
   Users see: Scalability level + bottleneck + parallel units available

4. UNIFIED REALITY ASSESSMENT PANEL
   Shows: WHO_DOES_WHAT + RISK_LEVEL + CONDITIONS + RISKS
   Purpose: Show task assignment and risk summary
   Users see: Role (Buddy/User/Both/Escalate) + Risk + Conditions

5. CHAT SUMMARY HINTS PANEL
   Shows: What Buddy can do | What you must do | What can be scaled
   Purpose: Template for chat responses
   Users see: Three bullet-point sections for chat reply

ALL FEATURES:
✓ Read-only (no actions)
✓ Visible by default (not hidden)
✓ Deterministic (same input → same display)
✓ Clear icons and colors for visual scanning
✓ Responsive to different screen sizes
✓ Non-intrusive (doesn't change behavior)
"""

if __name__ == "__main__":
    print(KEY_FEATURES)
    print("\n" + "="*60)
    print("EXAMPLE 1: Batch Processing Task")
    print("="*60)
    print(WHITEBOARD_OUTPUT_1)
    print("\n" + "="*60)
    print("EXAMPLE 2: Chat Response with Visibility")
    print("="*60)
    print(CHAT_RESPONSE_2)
    print("\n" + "="*60)
    print("EXAMPLE 4: High-Risk Task Visibility")
    print("="*60)
    print(WHITEBOARD_OUTPUT_4)
