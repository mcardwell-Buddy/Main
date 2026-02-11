#!/usr/bin/env python3
"""
PHASE 2 QUICK START INTEGRATION GUIDE
======================================

Complete walkthrough for integrating Phase 2 into backend/main.py

Time to complete: 45 minutes
Difficulty: Medium
Prerequisites: Read PHASE_2_DESIGN_DOCUMENT.md section 1-3

This script provides:
  1. Copy-paste ready code snippets
  2. Step-by-step integration instructions
  3. Testing procedures after integration
  4. Troubleshooting guide
"""

# ============================================================================
# STEP 0: PREREQUISITES & VERIFICATION
# ============================================================================

# Verify Phase 2 files exist:
import os
import sys

phase2_files = [
    'phase2_confidence.py',
    'phase2_prevalidation.py',
    'phase2_approval_gates.py',
    'phase2_clarification.py',
    'phase2_soul_integration.py',
    'phase2_response_schema.py',
]

print("=" * 70)
print("PHASE 2 INTEGRATION QUICK START")
print("=" * 70)
print()

missing_files = []
for f in phase2_files:
    if os.path.exists(f):
        print(f"✓ {f} found")
    else:
        print(f"✗ {f} MISSING")
        missing_files.append(f)

if missing_files:
    print()
    print(f"ERROR: Missing {len(missing_files)} Phase 2 files:")
    for f in missing_files:
        print(f"  - {f}")
    print()
    print("Download Phase 2 files from repository before proceeding.")
    sys.exit(1)

print()
print("✓ All Phase 2 files present")
print()

# ============================================================================
# STEP 1: ENVIRONMENT CONFIGURATION
# ============================================================================

print("=" * 70)
print("STEP 1: ENVIRONMENT CONFIGURATION")
print("=" * 70)
print()

print("""
Add these to your .env file:

# Phase 2 Feature Flags
PHASE2_ENABLED=True
PHASE2_PRE_VALIDATION_ENABLED=True
PHASE2_APPROVAL_GATES_ENABLED=True
PHASE2_CLARIFICATION_ENABLED=True
PHASE2_GRADED_CONFIDENCE_ENABLED=True

# Soul System Configuration
SOUL_SYSTEM_TYPE=mock
SOUL_SYSTEM_URL=http://localhost:8001
SOUL_API_KEY=test-key-for-development

# Approval Gates Configuration
APPROVAL_TIMEOUT_SECONDS=300
HIGH_CONFIDENCE_THRESHOLD=0.85
MEDIUM_CONFIDENCE_THRESHOLD=0.55

Verify with:
    python -c "import os; print(os.getenv('PHASE2_ENABLED'))"
    # Should print: True
""")

print()

# ============================================================================
# STEP 2: IMPORT PHASE 2 MODULES
# ============================================================================

print("=" * 70)
print("STEP 2: IMPORT PHASE 2 MODULES")
print("=" * 70)
print()

print("""
Add to top of backend/main.py (after existing imports):

---BEGIN COPY-PASTE---

# Phase 2 Systems (Graded Confidence, Approval Gates, etc.)
from phase2_confidence import (
    GradedConfidenceCalculator, ConfidenceFactors
)
from phase2_prevalidation import PreValidator
from phase2_approval_gates import ApprovalGates, ExecutionPath
from phase2_clarification import ClarificationGenerator
from phase2_soul_integration import MockSoulSystem
from phase2_response_schema import Phase2ResponseBuilder

---END COPY-PASTE---

Verify imports work:
    python -c "from phase2_confidence import GradedConfidenceCalculator; print('✓ Imports OK')"
""")

# Test imports
try:
    from phase2_confidence import GradedConfidenceCalculator, ConfidenceFactors
    from phase2_prevalidation import PreValidator
    from phase2_approval_gates import ApprovalGates, ExecutionPath
    from phase2_clarification import ClarificationGenerator
    from phase2_soul_integration import MockSoulSystem
    from phase2_response_schema import Phase2ResponseBuilder
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

print()

# ============================================================================
# STEP 3: INITIALIZE PHASE 2 SYSTEMS
# ============================================================================

print("=" * 70)
print("STEP 3: INITIALIZE PHASE 2 SYSTEMS")
print("=" * 70)
print()

print("""
Add to FastAPI app initialization (in startup event or before app.run()):

---BEGIN COPY-PASTE---

import os
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Initialize Phase 2 systems
    global confidence_calculator, pre_validator, approval_gates, \\
           clarification_generator, soul_system, response_builder
    
    confidence_calculator = GradedConfidenceCalculator()
    
    pre_validator = PreValidator(
        available_tools=[
            'button_clicker', 'element_finder', 'form_filler',
            'text_extractor', 'screenshot_taker',
            # Add your actual tool names here
        ]
    )
    
    soul_system = MockSoulSystem()  # Use HTTPSoulClient in production
    
    approval_gates = ApprovalGates(
        soul_integration=soul_system,
        high_confidence_threshold=float(
            os.getenv('HIGH_CONFIDENCE_THRESHOLD', '0.85')
        ),
        medium_confidence_threshold=float(
            os.getenv('MEDIUM_CONFIDENCE_THRESHOLD', '0.55')
        ),
    )
    
    clarification_generator = ClarificationGenerator()
    response_builder = Phase2ResponseBuilder()
    
    print("✓ Phase 2 systems initialized")

# Declare globals at module level for use in endpoints
confidence_calculator = None
pre_validator = None
approval_gates = None
clarification_generator = None
soul_system = None
response_builder = None

---END COPY-PASTE---
""")

print()

# ============================================================================
# STEP 4: UPDATE /reasoning/execute ENDPOINT
# ============================================================================

print("=" * 70)
print("STEP 4: UPDATE /reasoning/execute ENDPOINT")
print("=" * 70)
print()

print("""
Replace your existing /reasoning/execute endpoint with Phase 2 version.

This is the most complex step. Full code is in:
    PHASE_2_IMPLEMENTATION_GUIDE.md - Section 4, Step 3

Quick version (pseudo-code):

---BEGIN COPY-PASTE---

@app.post("/reasoning/execute")
async def execute_reasoning(request: ReasoningRequest) -> dict:
    goal = request.goal
    session_id = request.session_id or str(uuid.uuid4())
    
    # PHASE 2: PRE-VALIDATION
    if os.getenv('PHASE2_PRE_VALIDATION_ENABLED') == 'True':
        validation_result = pre_validator.validate_goal(goal)
        if validation_result.validation_status == "pre_validation_failed":
            return response_builder.build_validation_failed(
                goal=goal,
                validation_result=validation_result
            ).to_dict()
    
    # PHASE 1: AGENT REASONING
    reasoning_result = agent_reasoning(goal)  # Existing function
    
    # PHASE 2: GRADED CONFIDENCE
    if os.getenv('PHASE2_GRADED_CONFIDENCE_ENABLED') == 'True':
        factors = ConfidenceFactors(
            goal_understanding=reasoning_result['understanding'].get('clarity', 0.5),
            tool_availability=len(reasoning_result['tools_used']) / 
                             max(len(reasoning_result.get('tools_proposed', [])), 1),
            context_richness=0.5,  # From session context
            tool_confidence=0.8,   # From tool metadata
        )
        base_confidence = confidence_calculator.calculate(factors)
        confidence = max(0.0, min(1.0, base_confidence))
    else:
        confidence = 1.0 if reasoning_result['success'] else 0.0
    
    # PHASE 2: APPROVAL GATES
    if os.getenv('PHASE2_APPROVAL_GATES_ENABLED') == 'True':
        decision = approval_gates.decide(
            confidence=confidence,
            goal=goal,
            reasoning_summary=reasoning_result['reasoning_summary'],
            tools_proposed=reasoning_result['tools_used'],
        )
        
        # Route based on execution path
        if decision.execution_path == ExecutionPath.HIGH_CONFIDENCE:
            tool_results = execute_tools(reasoning_result['tools_used'])
            return response_builder.build_high_confidence_execution(
                goal=goal,
                tools_used=reasoning_result['tools_used'],
                tool_results=tool_results,
                confidence=confidence,
            ).to_dict()
        
        elif decision.execution_path == ExecutionPath.APPROVED:
            # Request approval
            approval_request_id = str(uuid.uuid4())
            soul_result = soul_system.validate_approval_request(
                decision.approval_request.to_dict()
            )
            return response_builder.build_awaiting_approval(
                goal=goal,
                confidence=confidence,
                approval_request_id=approval_request_id,
                tools_proposed=reasoning_result['tools_used'],
            ).to_dict()
        
        elif decision.execution_path == ExecutionPath.CLARIFICATION:
            # Request clarification
            clarification_request = clarification_generator.generate_clarification(
                goal=goal,
                confidence=confidence,
            )
            return response_builder.build_clarification_needed(
                goal=goal,
                confidence=confidence,
                clarification_request_id=clarification_request.request_id,
            ).to_dict()
        
        else:  # REJECTED
            return response_builder.build_execution_failed(
                goal=goal,
                confidence=confidence,
                error_message="Confidence too low for execution",
            ).to_dict()
    
    else:  # Phase 2 disabled, use Phase 1 fallback
        if reasoning_result['success']:
            tool_results = execute_tools(reasoning_result['tools_used'])
        else:
            tool_results = []
        
        return {
            'success': reasoning_result['success'],
            'result': {
                'reasoning_summary': reasoning_result['reasoning_summary'],
                'tool_results': tool_results,
                'tools_used': reasoning_result['tools_used'],
                'understanding': reasoning_result['understanding'],
                'confidence': confidence,
            },
            'approval_state': 'none',
            'execution_path': 'suggested',
        }

---END COPY-PASTE---

For complete, production-ready code, see:
    PHASE_2_IMPLEMENTATION_GUIDE.md - Section 4, Step 3
""")

print()

# ============================================================================
# STEP 5: ADD APPROVAL RESPONSE ENDPOINT
# ============================================================================

print("=" * 70)
print("STEP 5: ADD APPROVAL RESPONSE ENDPOINT")
print("=" * 70)
print()

print("""
Add this new endpoint to handle approval decisions:

---BEGIN COPY-PASTE---

from pydantic import BaseModel

class ApprovalResponse(BaseModel):
    request_id: str
    approved: bool
    feedback: str = ""
    approver_id: str = None

@app.post("/approval/respond/{request_id}")
async def submit_approval(request_id: str, response: ApprovalResponse) -> dict:
    '''Handle approval decision from Soul/user.'''
    
    if response.approved:
        # Execute the goal now
        # Need to retrieve original goal from cache/Soul
        # Then execute_tools and return results
        return {
            'success': True,
            'decision_id': request_id,
            'message': 'Goal will be executed',
        }
    else:
        # Goal was rejected
        return {
            'success': False,
            'decision_id': request_id,
            'message': 'Goal execution rejected',
        }

---END COPY-PASTE---
""")

print()

# ============================================================================
# STEP 6: UPDATE RESPONSE SCHEMA
# ============================================================================

print("=" * 70)
print("STEP 6: UPDATE RESPONSE SCHEMA")
print("=" * 70)
print()

print("""
Ensure all HTTP responses include these fields:

Standard HTTP 200 Response (always):
{
    "success": bool,
    "result": {
        "reasoning_summary": str,
        "tool_results": list,
        "tools_used": list,
        "understanding": dict,
        "confidence": float,        // NEW: [0.0, 1.0]
    },
    "approval_state": str,          // NEW: none | awaiting_approval | approved | denied
    "soul_request_id": str,         // NEW: for tracking
    "execution_path": str,          // NEW: high_confidence | approved | clarification | rejected
    "timestamp": str,
}

Verify with:
    curl -X POST http://localhost:8000/reasoning/execute \\
      -H "Content-Type: application/json" \\
      -d '{"goal": "Click the submit button"}'
    
    # Check response includes all Phase 2 fields
""")

print()

# ============================================================================
# STEP 7: TESTING
# ============================================================================

print("=" * 70)
print("STEP 7: LOCAL TESTING")
print("=" * 70)
print()

print("""
Test scenarios to verify Phase 2 is working:

1. HIGH CONFIDENCE TEST
   Goal: "Click the button with id='submit'"
   Expected: Immediate execution, confidence > 0.85

2. MEDIUM CONFIDENCE TEST
   Goal: "Fill in the form"
   Expected: Approval request, 0.55 < confidence < 0.85

3. LOW CONFIDENCE TEST
   Goal: "Help me"
   Expected: Clarification request, confidence < 0.55

4. PRE-VALIDATION FAILURE TEST
   Goal: ""  (empty)
   Expected: Pre-validation failed before reasoning

Testing script:
    python -c "
from phase2_confidence import GradedConfidenceCalculator, ConfidenceFactors

calc = GradedConfidenceCalculator()

# High confidence
factors_high = ConfidenceFactors(0.95, 0.90, 0.85, 0.90)
print(f'High: {calc.calculate(factors_high):.2%}')  # ~90%

# Medium confidence
factors_med = ConfidenceFactors(0.70, 0.65, 0.60, 0.70)
print(f'Medium: {calc.calculate(factors_med):.2%}')  # ~66%

# Low confidence
factors_low = ConfidenceFactors(0.40, 0.50, 0.30, 0.45)
print(f'Low: {calc.calculate(factors_low):.2%}')  # ~42%
"
""")

print()

# ============================================================================
# STEP 8: MONITORING
# ============================================================================

print("=" * 70)
print("STEP 8: MONITORING & METRICS")
print("=" * 70)
print()

print("""
Key metrics to track after Phase 2 deployment:

Per-Goal Metrics:
  - confidence (should be continuous, 0.0-1.0)
  - execution_path (high_confidence | approved | clarification | rejected)
  - approval_state (none | awaiting_approval | approved | denied | timeout)

Aggregate Metrics (hourly):
  - approval_request_rate (target: 15-25%)
  - approval_timeout_rate (target: <5%)
  - pre_validation_catch_rate (target: >80%)
  - confidence_mean (target: 0.60-0.70)
  - tool_selection_accuracy (target: 100%, no regression)

Dashboard SQL Query Template:
    SELECT
        execution_path,
        COUNT(*) as count,
        AVG(confidence) as avg_confidence,
        MIN(confidence) as min_confidence,
        MAX(confidence) as max_confidence
    FROM reasoning_executions
    WHERE timestamp > NOW() - INTERVAL '1 hour'
    GROUP BY execution_path

Alert Setup:
    - Alert if approval_timeout_rate > 10%
    - Alert if tool_selection_accuracy < 95%
    - Alert if confidence_mean < 0.50
""")

print()

# ============================================================================
# STEP 9: ROLLBACK PROCEDURES
# ============================================================================

print("=" * 70)
print("STEP 9: ROLLBACK PROCEDURES")
print("=" * 70)
print()

print("""
If Phase 2 causes issues:

Quick Disable (fastest):
    export PHASE2_ENABLED=False
    systemctl restart buddy-reasoning-service
    
    Verify: curl http://localhost:8000/reasoning/execute
    Should see Phase 1 fallback behavior

Partial Disable:
    export PHASE2_GRADED_CONFIDENCE_ENABLED=False     # Use Phase 1 confidence
    export PHASE2_PRE_VALIDATION_ENABLED=False        # Skip pre-validation
    export PHASE2_APPROVAL_GATES_ENABLED=False        # Execute immediately
    export PHASE2_CLARIFICATION_ENABLED=False         # No clarification questions
    
    Can disable any combination independently

Adjust Thresholds (before disabling):
    export HIGH_CONFIDENCE_THRESHOLD=0.80              # Lower from 0.85
    export MEDIUM_CONFIDENCE_THRESHOLD=0.50            # Lower from 0.55
    export APPROVAL_TIMEOUT_SECONDS=600                # Increase from 300

Increase Timeout (if Soul is slow):
    export APPROVAL_TIMEOUT_SECONDS=900                # 15 minutes

Full Debugging:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    # Now all Phase 2 operations logged with DEBUG level
""")

print()

# ============================================================================
# VERIFICATION CHECKLIST
# ============================================================================

print("=" * 70)
print("VERIFICATION CHECKLIST")
print("=" * 70)
print()

checklist = [
    ("Phase 2 files present", phase2_files),
    ("Environment variables configured", [
        "PHASE2_ENABLED",
        "HIGH_CONFIDENCE_THRESHOLD",
        "MEDIUM_CONFIDENCE_THRESHOLD",
    ]),
    ("Imports added to backend/main.py", ["phase2_confidence"]),
    ("Systems initialized in startup", ["confidence_calculator"]),
    ("/reasoning/execute updated", ["Pre-validation", "Confidence calculation"]),
    ("/approval/respond endpoint added", ["ApprovalResponse"]),
    ("Response schema updated", ["approval_state", "execution_path"]),
    ("Tests passing", ["test_phase2_all.py"]),
    ("Local testing complete", ["high confidence", "medium confidence"]),
    ("Monitoring configured", ["confidence_distribution", "approval_rate"]),
]

for check_name, items in checklist:
    print(f"[ ] {check_name}")
    for item in items:
        print(f"    - {item}")

print()

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

print("=" * 70)
print("COMMON ISSUES & SOLUTIONS")
print("=" * 70)
print()

issues = {
    "ImportError: No module named 'phase2_*'": [
        "1. Verify phase2_*.py files are in same directory as main.py",
        "2. Check sys.path includes current directory",
        "3. Run: python -c \"import phase2_confidence; print('OK')\"",
    ],
    "confidence is always 1.0 (too high)": [
        "1. Review ConfidenceFactors calculation in agent_reasoning()",
        "2. Check goal_understanding and tool_availability factors",
        "3. Manually set lower factors for testing: 0.5, 0.6, 0.7",
    ],
    "Approval requests never time out": [
        "1. Check APPROVAL_TIMEOUT_SECONDS is set correctly",
        "2. Verify Soul integration is working: soul_system.health_check()",
        "3. Review approval callback URL is correct",
    ],
    "Pre-validation rejecting valid goals": [
        "1. Disable PHASE2_PRE_VALIDATION_ENABLED temporarily",
        "2. Review validation rules in pre_validator.validate_goal()",
        "3. Adjust validation strictness in .env",
    ],
    "Tool selection accuracy dropped": [
        "1. Disable PHASE2_GRADED_CONFIDENCE_ENABLED",
        "2. Compare Phase 1 vs Phase 2 tool selections",
        "3. Check confidence weights - may need tuning",
    ],
}

for issue, solutions in issues.items():
    print(f"Q: {issue}")
    for solution in solutions:
        print(f"   {solution}")
    print()

# ============================================================================
# SUMMARY
# ============================================================================

print("=" * 70)
print("SUMMARY: EXPECTED TIME BREAKDOWN")
print("=" * 70)
print()

print("""
  Step 1: Environment Configuration     ~  5 min
  Step 2: Import Phase 2 Modules        ~  2 min
  Step 3: Initialize Systems            ~ 10 min
  Step 4: Update /reasoning/execute     ~ 20 min (most complex)
  Step 5: Add Approval Response         ~  5 min
  Step 6: Update Response Schema        ~  3 min
  Step 7: Local Testing                 ~ 10 min
  Step 8: Monitoring Setup              ~  5 min
  ─────────────────────────────────────────────
  Total                                 ~ 60 min

For help, refer to:
  - PHASE_2_IMPLEMENTATION_GUIDE.md (detailed explanations)
  - PHASE_2_DESIGN_DOCUMENT.md (architecture & theory)
  - Module docstrings (code-level documentation)
  - test_phase2_all.py (example usage)
""")

print()
print("=" * 70)
print("✓ Quick start guide complete!")
print("=" * 70)
print()
print("Next: Follow Step 1-8 above, then test locally before deployment.")

