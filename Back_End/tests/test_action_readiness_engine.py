import pytest

from Back_End.action_readiness_engine import (
    ActionReadinessEngine,
    ConfidenceTier,
    IntentCandidate,
    ReadinessDecision,
)


def evaluate_message(message: str, candidates, session_context=None):
    engine = ActionReadinessEngine(session_context=session_context)
    return engine.evaluate(message, candidates)


def test_ready_extract_emails_from_linkedin():
    candidates = [IntentCandidate(intent="extract", confidence=0.92)]
    result = evaluate_message("Extract emails from linkedin.com", candidates)
    assert result.decision == ReadinessDecision.READY


def test_ready_navigate_to_github():
    candidates = [IntentCandidate(intent="navigate", confidence=0.90)]
    result = evaluate_message("Navigate to github.com", candidates)
    assert result.decision == ReadinessDecision.READY


def test_ready_calculate_expression():
    candidates = [IntentCandidate(intent="calculate", confidence=0.95)]
    result = evaluate_message("Calculate 12 + 5", candidates)
    assert result.decision == ReadinessDecision.READY


def test_incomplete_extract_missing_source():
    candidates = [IntentCandidate(intent="extract", confidence=0.80)]
    result = evaluate_message("Extract emails", candidates)
    assert result.decision == ReadinessDecision.INCOMPLETE
    assert "source_url" in result.missing_fields


def test_incomplete_navigate_there_without_session_url():
    candidates = [IntentCandidate(intent="navigate", confidence=0.80)]
    result = evaluate_message("Navigate there", candidates, session_context={"recent_urls": []})
    assert result.decision == ReadinessDecision.INCOMPLETE
    assert "source_url" in result.missing_fields


def test_incomplete_search_and_collect_information():
    candidates = [IntentCandidate(intent="search", confidence=0.72)]
    result = evaluate_message("Search and collect information", candidates)
    assert result.decision == ReadinessDecision.INCOMPLETE
    assert "action_object" in result.missing_fields


def test_question_how_do_i_extract():
    candidates = [IntentCandidate(intent="extract", confidence=0.80)]
    result = evaluate_message("How do I extract data?", candidates)
    assert result.decision == ReadinessDecision.QUESTION


def test_meta_what_can_you_do():
    candidates = [IntentCandidate(intent="search", confidence=0.40)]
    result = evaluate_message("What can you do?", candidates)
    assert result.decision == ReadinessDecision.META


def test_ambiguous_get_data():
    candidates = [
        IntentCandidate(intent="extract", confidence=0.55),
        IntentCandidate(intent="search", confidence=0.50),
    ]
    result = evaluate_message("Get data", candidates)
    assert result.decision == ReadinessDecision.AMBIGUOUS
    assert result.clarification_options == ["extract", "search"]


def test_ambiguous_two_intents_within_delta():
    candidates = [
        IntentCandidate(intent="navigate", confidence=0.60),
        IntentCandidate(intent="search", confidence=0.52),
    ]
    result = evaluate_message("Go there", candidates)
    assert result.decision == ReadinessDecision.AMBIGUOUS


@pytest.mark.parametrize(
    "confidence,expected_tier",
    [
        (0.91, ConfidenceTier.CERTAIN),
        (0.75, ConfidenceTier.HIGH),
        (0.60, ConfidenceTier.MEDIUM),
        (0.35, ConfidenceTier.LOW),
        (0.10, ConfidenceTier.UNKNOWN),
    ],
)
def test_confidence_tier_mapping(confidence, expected_tier):
    candidates = [IntentCandidate(intent="search", confidence=confidence)]
    result = evaluate_message("Search for python", candidates)
    assert result.confidence_tier == expected_tier

