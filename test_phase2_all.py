"""
================================================================================
PHASE 2: UNIT TESTS
================================================================================

Test coverage for all Phase 2 modules:
  - test_graded_confidence
  - test_pre_validation
  - test_approval_gates
  - test_clarification
  - test_soul_integration
  - test_response_schema

Run with: python -m pytest test_phase2_*.py -v

Reference: PHASE_2_DESIGN_DOCUMENT.md - Section 9
"""

import pytest
from phase2_confidence import (
    ConfidenceFactors, GradedConfidenceCalculator,
    GoalUnderstandingCalculator, ToolAvailabilityCalculator
)
from phase2_prevalidation import (
    PreValidator, PreValidationResult, SeverityLevel
)
from phase2_approval_gates import (
    ApprovalGates, ApprovalRequest, ExecutionPath, ApprovalState
)
from phase2_clarification import (
    ClarificationGenerator, ClarificationResponse,
    ClarificationProcessor, ClarificationPattern
)
from phase2_soul_integration import (
    MockSoulSystem, ConversationContext
)
from phase2_response_schema import (
    Phase2ResponseBuilder, ResponseValidator, ReasoningResult
)


# =============================================================================
# GRADED CONFIDENCE TESTS
# =============================================================================

class TestGradedConfidence:
    """Test graded confidence calculation."""
    
    def test_high_confidence_atomic(self):
        """Test high confidence for clear atomic goal."""
        calculator = GradedConfidenceCalculator()
        
        factors = ConfidenceFactors(
            goal_understanding=1.0,
            tool_availability=1.0,
            context_richness=0.5,
            tool_confidence=1.0,
        )
        
        confidence = calculator.calculate(factors)
        
        assert confidence >= 0.85, "Atomic goal should have high confidence"
        assert confidence <= 1.0, "Confidence should not exceed 1.0"
    
    def test_low_confidence_ambiguous(self):
        """Test low confidence for ambiguous goal."""
        calculator = GradedConfidenceCalculator()
        
        factors = ConfidenceFactors(
            goal_understanding=0.1,
            tool_availability=0.0,
            context_richness=0.3,
            tool_confidence=0.5,
        )
        
        confidence = calculator.calculate(factors)
        
        assert confidence < 0.55, "Ambiguous goal should have low confidence"
        assert confidence >= 0.0, "Confidence should not be negative"
    
    def test_medium_confidence_missing_context(self):
        """Test medium confidence for goal missing context."""
        calculator = GradedConfidenceCalculator()
        
        factors = ConfidenceFactors(
            goal_understanding=0.9,
            tool_availability=0.8,
            context_richness=0.4,
            tool_confidence=0.7,
        )
        
        confidence = calculator.calculate(factors)
        
        assert 0.55 <= confidence < 0.85, "Should be medium confidence"
    
    def test_weights_sum_to_one(self):
        """Test that default weights sum to 1.0."""
        calculator = GradedConfidenceCalculator()
        
        weight_sum = sum(calculator.weights.values())
        
        assert 0.99 <= weight_sum <= 1.01, "Weights should sum to 1.0"
    
    def test_goal_understanding_calculation(self):
        """Test goal understanding factor calculation."""
        calc = GoalUnderstandingCalculator()
        
        # Clear goal with action and target
        score1 = calc.calculate("Click the submit button")
        assert score1 >= 0.6, "Clear goal should score high"
        
        # Vague goal
        score2 = calc.calculate("Help me")
        assert score2 < 0.4, "Vague goal should score low"
    
    def test_contradictions_detected(self):
        """Test that contradictions reduce understanding."""
        calc = GoalUnderstandingCalculator()
        
        # Goal with contradiction
        score_contradiction = calc.calculate("Click the button and don't click the button")
        
        # Goal without contradiction
        score_clear = calc.calculate("Click the button")
        
        assert score_contradiction < score_clear, "Contradictions should reduce understanding"


# =============================================================================
# PRE-VALIDATION TESTS
# =============================================================================

class TestPreValidation:
    """Test pre-validation checks."""
    
    def test_valid_goal_passes(self):
        """Test that valid goal passes all checks."""
        validator = PreValidator(
            available_tools=['button_clicker', 'element_finder'],
            ui_schema={'button': {}, 'input': {}}
        )
        
        result = validator.validate_goal("Click the submit button")
        
        assert result.validation_status == "pre_validation_passed"
        assert result.checks_failed == 0
    
    def test_missing_tool_detected(self):
        """Test that missing tool is detected."""
        validator = PreValidator(
            available_tools=['button_clicker'],
        )
        
        result = validator.validate_goal("Use the ImageEditor tool to crop image")
        
        assert result.validation_status == "pre_validation_failed"
        assert result.checks_failed > 0
        assert any(
            f.check_name == "required_tool_availability"
            for f in result.failures
        )
    
    def test_contradiction_detected(self):
        """Test that contradictions are detected."""
        validator = PreValidator(available_tools=['button_clicker'])
        
        result = validator.validate_goal("Click button X and do NOT click button Y")
        
        assert result.validation_status == "pre_validation_failed"
        assert any(
            f.check_name == "contradiction_detection"
            for f in result.failures
        )
    
    def test_out_of_scope_detected(self):
        """Test that out-of-scope goals are detected."""
        validator = PreValidator(available_tools=['button_clicker'])
        
        result = validator.validate_goal("Launch a rocket")
        
        assert result.validation_status == "pre_validation_failed"
        assert any(
            f.check_name == "scope_validation"
            for f in result.failures
        )
    
    def test_complexity_warning(self):
        """Test that complex goals trigger warning."""
        validator = PreValidator(available_tools=['button_clicker'])
        
        result = validator.validate_goal(
            "Click the button, find the element, analyze the code, test the function"
        )
        
        # Complex goal should have at least one failure
        assert result.checks_failed > 0


# =============================================================================
# APPROVAL GATES TESTS
# =============================================================================

class TestApprovalGates:
    """Test approval gate logic."""
    
    def test_high_confidence_executes_immediately(self):
        """Test that high confidence goal executes immediately."""
        gates = ApprovalGates()
        
        decision = gates.decide(
            confidence=0.92,
            goal="Click button",
            tools_proposed=['button_clicker'],
        )
        
        assert decision.execution_path == ExecutionPath.HIGH_CONFIDENCE
        assert decision.should_execute == True
        assert decision.approval_state == ApprovalState.NONE
    
    def test_medium_confidence_requests_approval(self):
        """Test that medium confidence requests approval."""
        gates = ApprovalGates()
        
        decision = gates.decide(
            confidence=0.70,
            goal="Refactor function",
            tools_proposed=['code_refactorer'],
        )
        
        assert decision.execution_path == ExecutionPath.APPROVED
        assert decision.should_execute == False
        assert decision.approval_state == ApprovalState.AWAITING_APPROVAL
        assert decision.approval_request is not None
    
    def test_low_confidence_clarifies(self):
        """Test that low confidence requests clarification."""
        gates = ApprovalGates()
        
        decision = gates.decide(
            confidence=0.30,
            goal="Help me",
            tools_proposed=[],
            is_ambiguous=True,
        )
        
        assert decision.execution_path == ExecutionPath.CLARIFICATION
        assert decision.should_execute == False
        assert decision.clarification_needed == True
    
    def test_approval_timeout_check(self):
        """Test approval timeout detection."""
        gates = ApprovalGates(approval_timeout_seconds=1)
        
        import time
        
        approval_request = ApprovalRequest(
            goal="Test",
            confidence=0.7,
        )
        
        # Should not timeout immediately
        assert not gates.check_approval_timeout(approval_request)
        
        # Wait for timeout
        time.sleep(1.1)
        assert gates.check_approval_timeout(approval_request)


# =============================================================================
# CLARIFICATION TESTS
# =============================================================================

class TestClarification:
    """Test clarification handling."""
    
    def test_clarification_questions_generated(self):
        """Test that clarification questions are generated."""
        generator = ClarificationGenerator()
        
        request = generator.generate_clarification(
            goal="Help me",
            goal_understanding=0.1,
        )
        
        assert request.original_goal == "Help me"
        assert len(request.questions) > 0
        assert request.questions[0].pattern == ClarificationPattern.ACTION_IDENTIFICATION
    
    def test_clarification_response_processed(self):
        """Test that clarification response is processed correctly."""
        processor = ClarificationProcessor()
        
        response = ClarificationResponse(
            request_id="req_123",
            answers={
                0: "Click the save button",
                1: "In the bottom right corner",
            }
        )
        
        clarified_goal = processor.build_clarified_goal(
            original_goal="Help me",
            response=response,
        )
        
        assert "save button" in clarified_goal
        assert len(clarified_goal) > len("Help me")
    
    def test_context_merged_from_clarification(self):
        """Test that context is extracted from clarification."""
        processor = ClarificationProcessor()
        
        response = ClarificationResponse(
            request_id="req_123",
            answers={
                0: "Refactor the function",
                2: "def foo(): pass",  # Provided context
                3: "Should have unit tests",  # Success criteria
            }
        )
        
        result = processor.merge_context(
            goal="Help me",
            response=response,
        )
        
        assert 'goal' in result
        assert 'context' in result
        assert result['context'].get('provided_context') is not None


# =============================================================================
# SOUL INTEGRATION TESTS
# =============================================================================

class TestSoulIntegration:
    """Test Soul system integration."""
    
    def test_mock_soul_validates_approval(self):
        """Test that mock Soul validates approval requests."""
        soul = MockSoulSystem()
        
        result = soul.validate_approval_request({
            'goal': 'Click button',
            'confidence': 0.70,
            'tools_proposed': ['button_clicker'],
        })
        
        assert result['valid'] == True
        assert 'feedback' in result
    
    def test_mock_soul_validates_clarification(self):
        """Test that mock Soul validates clarification."""
        soul = MockSoulSystem()
        
        result = soul.validate_clarification({
            'original_goal': 'Help me',
            'questions': [
                {'index': 0, 'question': 'What action?'},
            ]
        })
        
        assert result['valid'] == True
        assert 0 in result['approved_indices']
    
    def test_mock_soul_retrieves_context(self):
        """Test that mock Soul retrieves conversation context."""
        soul = MockSoulSystem()
        
        soul.add_goal_to_history('session_123', 'Goal 1')
        soul.add_goal_to_history('session_123', 'Goal 2')
        
        context = soul.get_conversation_context('session_123')
        
        assert context.session_id == 'session_123'
        assert len(context.prior_goals) > 0
    
    def test_mock_soul_stores_approval(self):
        """Test that mock Soul stores approval decisions."""
        soul = MockSoulSystem()
        
        result = soul.store_approval_decision({
            'request_id': 'req_123',
            'session_id': 'session_123',
            'approved': True,
            'feedback': 'Approved',
            'timestamp': '2026-02-05T00:00:00Z',
        })
        
        assert result['stored'] == True
        assert result['decision_id'] is not None
        
        # Verify it's in history
        history = soul.get_approval_history('session_123')
        assert len(history) > 0


# =============================================================================
# RESPONSE SCHEMA TESTS
# =============================================================================

class TestResponseSchema:
    """Test response schema and builders."""
    
    def test_high_confidence_response_valid(self):
        """Test that high confidence response is valid."""
        builder = Phase2ResponseBuilder()
        
        response = builder.build_high_confidence_execution(
            goal="Click button",
            tools_used=['button_clicker'],
            tool_results=[
                {'tool_name': 'button_clicker', 'success': True}
            ],
            confidence=0.92,
        )
        
        validation = ResponseValidator.validate(response)
        
        assert validation['valid'] == True
        assert response.execution_path == "high_confidence"
    
    def test_awaiting_approval_response_valid(self):
        """Test that awaiting approval response is valid."""
        builder = Phase2ResponseBuilder()
        
        response = builder.build_awaiting_approval(
            goal="Refactor",
            confidence=0.70,
            approval_request_id="req_123",
        )
        
        validation = ResponseValidator.validate(response)
        
        assert validation['valid'] == True
        assert response.approval_state == "awaiting_approval"
    
    def test_response_validation_catches_invalid_confidence(self):
        """Test that validation catches invalid confidence."""
        from phase2_response_schema import Phase2Response
        
        # Create invalid response
        result = ReasoningResult(
            reasoning_summary="Test",
            tool_results=[],
            tools_used=[],
            understanding={},
            confidence=1.5,  # Invalid: > 1.0
        )
        
        response = Phase2Response(
            success=True,
            result=result,
            approval_state="none",
        )
        
        validation = ResponseValidator.validate(response)
        
        assert validation['valid'] == False
        assert len(validation['errors']) > 0
    
    def test_response_validation_catches_mismatch(self):
        """Test that validation catches tool/result mismatch."""
        from phase2_response_schema import Phase2Response
        
        # Create response with mismatch
        result = ReasoningResult(
            reasoning_summary="Test",
            tool_results=[
                {'tool_name': 'tool_a', 'success': True},
                {'tool_name': 'tool_b', 'success': False},
            ],
            tools_used=['tool_a'],  # Mismatch: 2 results, 1 tool
            understanding={},
            confidence=0.8,
        )
        
        response = Phase2Response(
            success=False,
            result=result,
            approval_state="none",
        )
        
        validation = ResponseValidator.validate(response)
        
        assert validation['valid'] == False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for multiple systems."""
    
    def test_confidence_to_approval_gate_flow(self):
        """Test flow: calculate confidence -> approval gates."""
        confidence_calc = GradedConfidenceCalculator()
        gates = ApprovalGates()
        
        # High confidence
        factors = ConfidenceFactors(1.0, 1.0, 0.5, 1.0)
        confidence = confidence_calc.calculate(factors)
        decision = gates.decide(confidence, "Click button", tools_proposed=['button_clicker'])
        
        assert decision.should_execute == True
        
        # Medium confidence
        factors = ConfidenceFactors(0.9, 0.8, 0.4, 0.7)
        confidence = confidence_calc.calculate(factors)
        decision = gates.decide(confidence, "Refactor", tools_proposed=['code_refactorer'])
        
        assert decision.should_execute == False
        assert decision.approval_state == ApprovalState.AWAITING_APPROVAL
    
    def test_clarification_then_execution_flow(self):
        """Test flow: clarification -> updated goal -> execution."""
        generator = ClarificationGenerator()
        processor = ClarificationProcessor()
        builder = Phase2ResponseBuilder()
        
        # Step 1: Generate clarification
        request = generator.generate_clarification(
            goal="Help me",
            goal_understanding=0.1,
        )
        
        # Step 2: Process response
        response = ClarificationResponse(
            request_id=request.request_id,
            answers={
                0: "Click the save button",
                1: "In the bottom right",
            }
        )
        
        result = processor.merge_context("Help me", response)
        clarified_goal = result['goal']
        
        # Step 3: Build execution response
        exec_response = builder.build_high_confidence_execution(
            goal=clarified_goal,
            tools_used=['button_clicker'],
            tool_results=[{'tool_name': 'button_clicker', 'success': True}],
            confidence=0.92,
        )
        
        assert exec_response.success == True
        assert "save button" in clarified_goal


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

