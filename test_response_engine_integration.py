"""Live-ish integration test for Response Engine components.

Run:
  python test_response_engine_integration.py
"""

import sys
sys.path.insert(0, r"c:\Users\micha\Buddy")

from backend.response_engine import (
    ResponseBuilder,
    ResponseType,
    ApprovalManager,
    ApprovalDecision,
    ErrorRecoveryManager,
    ResponseCacheManager,
    PersonalityEngine,
    PersonalityRegistry,
    Button,
    Link,
    ExpandableSection,
    ProgressIndicator,
    interactive_to_dict,
)


def run():
    builder = ResponseBuilder(mission_id="mission_test_full")
    builder.set_primary_content("Generated response content.")
    builder.add_content(
        content="Executive summary for the plan.",
        response_type=ResponseType.BUSINESS_PLAN,
        title="Executive Summary",
        description="High level plan summary",
    )

    builder.set_requires_approval(True, reason="User approval required")
    builder.add_interactive_element(interactive_to_dict(Button("btn1", "Approve", "approve")))
    builder.add_interactive_element(interactive_to_dict(Link("lnk1", "View Docs", "https://example.com")))
    builder.add_interactive_element(interactive_to_dict(ExpandableSection("exp1", "Details", "More info here")))
    builder.add_interactive_element(interactive_to_dict(ProgressIndicator("prog1", "Processing", 0.5)))

    recovery = ErrorRecoveryManager()
    response = recovery.safe_build(builder)

    manager = ApprovalManager()
    manager.create_request(response, reason="Test approval")
    manager.apply_decision(response, ApprovalDecision(approved=True, decided_by="tester"))

    cache_manager = ResponseCacheManager()
    cache_manager.cache_response(response, ttl_seconds=10)
    cached = cache_manager.get_cached_response(response.response_id)

    registry = PersonalityRegistry()
    engine = PersonalityEngine(profile=registry.get("friendly"))
    engine.apply(response)

    formatted = builder.format("business_plan")

    assert response.approval_status == "approved"
    assert cached is not None
    assert "Business Plan" in formatted
    assert response.primary_content.startswith("Hey!")
    assert len(response.interactive_elements) == 4

    print("ALL RESPONSE ENGINE TESTS PASSED")


if __name__ == "__main__":
    run()
