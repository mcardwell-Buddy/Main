# Phase 3C Invariants (Safety Contract)

## 1) READY missions are always approvable
- Prevents: READY missions from being stranded without an approval path.
- Enforced by: `set_pending_mission()` storing READY missions in session context and approval handler consuming that pending entry.
- Test: [backend/tests/test_ready_to_approval_bridge.py](backend/tests/test_ready_to_approval_bridge.py#L63)

## 2) Approval executes exactly once
- Prevents: duplicate execution from repeated approvals.
- Enforced by: pending mission cleared after successful execution; subsequent approvals return “nothing to approve.”
- Test: [backend/tests/test_ready_to_approval_bridge.py](backend/tests/test_ready_to_approval_bridge.py#L96)

## 3) No approval without READY
- Prevents: approvals from triggering execution when no READY mission exists.
- Enforced by: approval handler returning “There’s nothing to approve yet” when no pending mission is set.
- Test: [backend/tests/test_ready_to_approval_bridge.py](backend/tests/test_ready_to_approval_bridge.py#L138)

## 4) No bypass of ActionReadinessEngine
- Prevents: missions executing without readiness validation.
- Enforced by: readiness gating before mission creation; INCOMPLETE requests never create missions or approvals.
- Tests: [backend/tests/test_readiness_sole_gate.py](backend/tests/test_readiness_sole_gate.py#L64), [backend/tests/test_readiness_sole_gate.py](backend/tests/test_readiness_sole_gate.py#L86), [backend/tests/test_clarification_ux_invariants.py](backend/tests/test_clarification_ux_invariants.py#L195)

## 5) No regression of Phase 3A or 3B guarantees
- Prevents: regressions in readiness gating, session context safety, or targeted clarifications.
- Enforced by: regression guard tests across Phase 3A and 3B suites.
- Tests: [backend/tests/test_session_context_safety.py](backend/tests/test_session_context_safety.py#L420), [backend/tests/test_clarification_ux_invariants.py](backend/tests/test_clarification_ux_invariants.py#L391), [backend/tests/test_clarification_ux_invariants.py](backend/tests/test_clarification_ux_invariants.py#L414)
