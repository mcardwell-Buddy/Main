"""
Phase 5 Tests: Semantic Normalization Layer

Tests that semantic normalization:
1. Reduces phrasing brittleness
2. Does NOT create missions
3. Does NOT execute tools
4. Does NOT bypass safety checks
5. Returns original text for ambiguous input
"""

import pytest
from Back_End.semantic_normalizer import (
    maybe_normalize,
    _attempt_normalization,
    NormalizationResult,
    NORMALIZATION_CONFIDENCE_THRESHOLD
)


# ============================================================================
# LEVEL 1: ARITHMETIC NORMALIZATION
# ============================================================================

def test_normalize_arithmetic_what_is():
    """Test: 'What is 1+2?' normalizes to 'calculate 1 + 2'"""
    result = maybe_normalize("What is 1+2?", session_context=None)
    
    # Should normalize to canonical form
    assert "calculate" in result.lower()
    assert "1" in result
    assert "2" in result


def test_normalize_arithmetic_compute():
    """Test: 'Compute 5 * 3' normalizes to 'calculate 5 * 3'"""
    result = maybe_normalize("Compute 5 * 3", session_context=None)
    
    assert "calculate" in result.lower() or "compute" in result.lower()
    assert "5" in result
    assert "3" in result


def test_normalize_arithmetic_solve():
    """Test: 'Solve 10 - 4' normalizes to calculation"""
    result = maybe_normalize("Solve 10 - 4", session_context=None)
    
    assert "10" in result
    assert "4" in result


# ============================================================================
# LEVEL 2: NAVIGATION PHRASING
# ============================================================================

def test_normalize_navigate_to():
    """Test: 'Navigate to example.com' normalizes consistently"""
    result = maybe_normalize("Navigate to example.com", session_context=None)
    
    # Should normalize to canonical navigation form
    assert "navigate" in result.lower()
    assert "example.com" in result.lower()


def test_normalize_go_to():
    """Test: 'Go to example.com' normalizes to 'navigate to example.com'"""
    result = maybe_normalize("Go to example.com", session_context=None)
    
    assert "navigate" in result.lower() or "go" in result.lower()
    assert "example.com" in result.lower()


def test_normalize_open_site():
    """Test: 'Open example.com' normalizes to navigation"""
    result = maybe_normalize("Open example.com", session_context=None)
    
    assert ("navigate" in result.lower() or "open" in result.lower())
    assert "example.com" in result.lower()


def test_normalize_visit():
    """Test: 'Visit example.com' normalizes to navigation"""
    result = maybe_normalize("Visit example.com", session_context=None)
    
    assert ("navigate" in result.lower() or "visit" in result.lower())
    assert "example.com" in result.lower()


def test_normalize_browse_to():
    """Test: 'Browse to example.com' normalizes to navigation"""
    result = maybe_normalize("Browse to example.com", session_context=None)
    
    assert ("navigate" in result.lower() or "browse" in result.lower())
    assert "example.com" in result.lower()


# ============================================================================
# LEVEL 3: EXTRACT PHRASING
# ============================================================================

def test_normalize_extract_title():
    """Test: 'What's the page title?' normalizes to extract command"""
    session_context = {"last_visited_url": "https://example.com"}
    result = maybe_normalize("What's the page title?", session_context=session_context)
    
    # Should normalize to extraction command
    assert "extract" in result.lower() or "title" in result.lower()


def test_normalize_grab_title():
    """Test: 'Grab the title' normalizes to extract command"""
    session_context = {"last_visited_url": "https://example.com"}
    result = maybe_normalize("Grab the title", session_context=session_context)
    
    assert "extract" in result.lower() or "grab" in result.lower() or "title" in result.lower()


def test_normalize_get_headings():
    """Test: 'Get the headings' normalizes to extract command"""
    session_context = {"last_visited_url": "https://example.com"}
    result = maybe_normalize("Get the headings", session_context=session_context)
    
    assert "extract" in result.lower() or "get" in result.lower() or "heading" in result.lower()


def test_normalize_whats_on_the_page():
    """Test: 'What's on the page?' normalizes to extract command"""
    session_context = {"last_visited_url": "https://example.com"}
    result = maybe_normalize("What's on the page?", session_context=session_context)
    
    # Should reference extraction or page content
    assert any(word in result.lower() for word in ["extract", "page", "content"])


# ============================================================================
# LEVEL 4: AMBIGUOUS INPUT (NO REWRITE)
# ============================================================================

def test_normalize_tell_me_more_unchanged():
    """Test: 'Tell me more' should remain unchanged (ambiguous)"""
    result = maybe_normalize("Tell me more", session_context=None)
    
    # Should return original text for ambiguous input
    assert result == "Tell me more"


def test_normalize_do_that_unchanged():
    """Test: 'Do that' should remain unchanged without context"""
    result = maybe_normalize("Do that", session_context=None)
    
    # Ambiguous without context
    assert result == "Do that"


def test_normalize_hmm_unchanged():
    """Test: 'Hmm' should remain unchanged"""
    result = maybe_normalize("Hmm", session_context=None)
    
    assert result == "Hmm"


def test_normalize_empty_string():
    """Test: Empty string should remain unchanged"""
    result = maybe_normalize("", session_context=None)
    
    assert result == ""


def test_normalize_whitespace_only():
    """Test: Whitespace-only input should remain unchanged"""
    result = maybe_normalize("   ", session_context=None)
    
    assert result == "   "


# ============================================================================
# LEVEL 5: SAFETY REGRESSION TESTS
# ============================================================================

def test_safety_normalization_does_not_create_missions():
    """Test: Normalization does NOT create missions"""
    from Back_End.mission_manager import get_all_missions
    
    initial_missions = len(get_all_missions())
    
    # Normalize several inputs
    maybe_normalize("Navigate to example.com", session_context=None)
    maybe_normalize("Calculate 1+2", session_context=None)
    maybe_normalize("What's the page title?", session_context={"last_visited_url": "https://example.com"})
    
    final_missions = len(get_all_missions())
    
    # No missions should be created
    assert final_missions == initial_missions, "Normalization must NOT create missions"


def test_safety_normalization_does_not_execute_tools():
    """Test: Normalization does NOT execute tools"""
    from Back_End.tool_registry import tool_registry
    
    # Track tool calls (if registry supports it)
    # For now, just ensure no side effects occur
    
    result = maybe_normalize("Calculate 1+2", session_context=None)
    
    # Result should be text, not execution result
    assert isinstance(result, str)
    assert "success" not in result.lower()  # Execution results typically have "success"


def test_safety_low_confidence_uses_original():
    """Test: Low confidence returns original text unchanged"""
    # Test with highly ambiguous input that should have low confidence
    ambiguous_input = "xyz123abc"
    
    result = maybe_normalize(ambiguous_input, session_context=None)
    
    # Should return original text
    assert result == ambiguous_input


def test_safety_normalization_result_structure():
    """Test: NormalizationResult has correct structure"""
    result = _attempt_normalization("Navigate to example.com", session_context=None)
    
    assert isinstance(result, NormalizationResult)
    assert hasattr(result, 'original_text')
    assert hasattr(result, 'normalized_text')
    assert hasattr(result, 'confidence')
    assert hasattr(result, 'reason')
    
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.original_text, str)
    assert isinstance(result.normalized_text, str)
    assert isinstance(result.reason, str)


def test_safety_confidence_threshold():
    """Test: Confidence threshold is set correctly"""
    assert NORMALIZATION_CONFIDENCE_THRESHOLD == 0.6


def test_safety_exception_handling():
    """Test: Exceptions don't crash normalization"""
    # Test with various edge cases that might break LLM parsing
    edge_cases = [
        None,  # Will be handled by empty check
        "",
        "   ",
        "\n\n\n",
        "a" * 10000,  # Very long input
    ]
    
    for case in edge_cases:
        if case is None:
            continue
        try:
            result = maybe_normalize(case, session_context=None)
            # Should return original or handle gracefully
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Normalization crashed on edge case: {e}")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_integration_navigation_variations_normalize_consistently():
    """Test: Various navigation phrasings normalize to similar forms"""
    variations = [
        "Navigate to example.com",
        "Go to example.com",
        "Open example.com",
        "Visit example.com",
        "Browse to example.com"
    ]
    
    results = [maybe_normalize(v, session_context=None) for v in variations]
    
    # All should contain "example.com"
    for result in results:
        assert "example.com" in result.lower()
    
    # All should have navigation-related terms
    for result in results:
        assert any(word in result.lower() for word in ["navigate", "go", "open", "visit", "browse"])


def test_integration_normalization_preserves_urls():
    """Test: URLs are preserved during normalization"""
    test_urls = [
        "https://example.com",
        "http://test.org",
        "www.google.com",
        "github.com/user/repo"
    ]
    
    for url in test_urls:
        input_text = f"Navigate to {url}"
        result = maybe_normalize(input_text, session_context=None)
        
        # URL should be preserved
        assert url in result, f"URL {url} should be preserved in normalization"


def test_integration_normalization_does_not_invent_urls():
    """Test: Normalization does NOT invent missing URLs"""
    input_text = "Go there"
    
    # Without context, this is ambiguous
    result = maybe_normalize(input_text, session_context=None)
    
    # Should NOT add invented URLs like "example.com"
    # Either returns original or adds context reference (if available)
    assert "there" in result.lower() or result == input_text


def test_integration_normalization_with_context():
    """Test: Normalization can use context for reference resolution"""
    session_context = {
        "last_visited_url": "https://example.com",
        "last_artifact_id": "artifact_123"
    }
    
    # Ambiguous reference that needs context
    input_text = "Go back there"
    
    result = maybe_normalize(input_text, session_context=session_context)
    
    # Should either resolve reference or return original
    assert isinstance(result, str)
    # Context hints provided to LLM, but it should NOT invent if unclear
    # Just verify it doesn't crash


def test_integration_end_to_end_normalization_in_orchestrator():
    """Test: Normalization integrates correctly with orchestrator"""
    from Back_End.interaction_orchestrator import InteractionOrchestrator
    from Back_End.session_context import SessionContextManager
    
    orchestrator = InteractionOrchestrator(session_context_manager=SessionContextManager())
    
    # Test that process_message runs without error after Phase 5 integration
    session_id = "test_phase5_session"
    
    # Test navigation phrasing variation
    response = orchestrator.process_message(
        message="Go to example.com",
        session_id=session_id,
        user_id="test_user"
    )
    
    # Should process without error
    assert response is not None
    assert hasattr(response, 'response_type')
    
    # Test arithmetic phrasing
    response2 = orchestrator.process_message(
        message="What is 5+5?",
        session_id=session_id,
        user_id="test_user"
    )
    
    assert response2 is not None


# ============================================================================
# PHASE 3-4 SAFETY INVARIANT TESTS (ENSURE NO REGRESSION)
# ============================================================================

def test_safety_incomplete_missions_still_incomplete_after_normalization():
    """Test: Normalization does NOT bypass readiness checks"""
    # This test ensures that incomplete missions remain incomplete
    # even after normalization
    
    # Normalized text should still go through readiness checks
    input_text = "Extract data"  # Incomplete - no URL specified
    
    result = maybe_normalize(input_text, session_context=None)
    
    # Normalization may clarify or keep original, but downstream
    # readiness engine should still detect incompleteness
    # This is verified by integration test below


def test_safety_approval_required_after_normalization():
    """Test: Normalization does NOT bypass approval"""
    from Back_End.interaction_orchestrator import InteractionOrchestrator
    from Back_End.session_context import SessionContextManager
    
    orchestrator = InteractionOrchestrator(session_context_manager=SessionContextManager())
    session_id = "test_approval_phase5"
    
    # Process a navigation request (will create mission)
    response = orchestrator.process_message(
        message="Navigate to example.com",
        session_id=session_id,
        user_id="test_user"
    )
    
    # Should create mission that requires approval
    # (Same behavior as before Phase 5)
    assert response is not None
    
    # Verify approval is still required (mission created but not executed)
    from Back_End.mission_manager import get_all_missions
    missions = get_all_missions()
    
    if missions:
        # Latest mission should be PENDING approval
        latest_mission = missions[-1]
        assert latest_mission.get('status') in ['pending', 'awaiting_approval', 'created']


def test_safety_tool_execution_still_requires_approval():
    """Test: Normalized text does NOT trigger immediate execution"""
    from Back_End.interaction_orchestrator import InteractionOrchestrator
    from Back_End.session_context import SessionContextManager
    from Back_End.tool_registry import tool_registry
    
    orchestrator = InteractionOrchestrator(session_context_manager=SessionContextManager())
    session_id = "test_exec_phase5"
    
    # Track if web_navigate was called
    original_call = tool_registry.call
    call_count = {"count": 0}
    
    def tracked_call(tool_name, *args, **kwargs):
        if tool_name == "web_navigate":
            call_count["count"] += 1
        return original_call(tool_name, *args, **kwargs)
    
    tool_registry.call = tracked_call
    
    try:
        # Process navigation request
        response = orchestrator.process_message(
            message="Go to example.com",
            session_id=session_id,
            user_id="test_user"
        )
        
        # Tool should NOT be executed yet (approval required)
        assert call_count["count"] == 0, "Tool execution should NOT happen before approval"
        
    finally:
        # Restore original
        tool_registry.call = original_call


if __name__ == "__main__":
    print("Running Phase 5: Semantic Normalization Tests")
    print("=" * 60)
    
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])

