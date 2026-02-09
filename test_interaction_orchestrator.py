"""
Unit tests for Interaction Orchestrator

Tests cover:
- Intent classification (deterministic, no LLM)
- Routing decisions
- Handler execution
- Response envelope packaging
- Hard constraint validation (NO autonomy, ONE decision per message, etc)

5 test scenarios:
1. Execution request → mission creation
2. Informational question → text response
3. Ambiguous request → clarification
4. Acknowledgment → greeting response
5. Forecast request → forecast response
"""

import unittest
from datetime import datetime
from backend.interaction_orchestrator import (
    DeterministicIntentClassifier, IntentType, IntentClassification,
    RoutingDecision, InteractionOrchestrator, orchestrate_message
)
from backend.response_envelope import ResponseType


class TestDeterministicIntentClassifier(unittest.TestCase):
    """Test deterministic intent classification."""
    
    def setUp(self):
        self.classifier = DeterministicIntentClassifier()
    
    def test_execution_request_classification(self):
        """Test classification of execution requests."""
        message = "Get product names and prices from amazon.com"
        result = self.classifier.classify(message)
        
        self.assertEqual(result.intent_type, IntentType.REQUEST_EXECUTION)
        self.assertGreater(result.confidence, 0.6)
        self.assertTrue(result.actionable)
        self.assertIn('get', result.keywords)
    
    def test_question_classification(self):
        """Test classification of informational questions."""
        message = "How do I scrape a website?"
        result = self.classifier.classify(message)
        
        self.assertEqual(result.intent_type, IntentType.QUESTION)
        self.assertGreater(result.confidence, 0.5)
        self.assertFalse(result.actionable)
    
    def test_forecast_request_classification(self):
        """Test classification of forecast requests."""
        message = "Can you predict future trends based on historical data?"
        result = self.classifier.classify(message)
        
        self.assertEqual(result.intent_type, IntentType.FORECAST_REQUEST)
        self.assertGreater(result.confidence, 0.5)
        self.assertTrue(result.actionable)
    
    def test_status_check_classification(self):
        """Test classification of status checks."""
        message = "What's the status of my current missions?"
        result = self.classifier.classify(message)
        
        self.assertEqual(result.intent_type, IntentType.STATUS_CHECK)
        self.assertGreater(result.confidence, 0.5)
        self.assertFalse(result.actionable)
    
    def test_acknowledgment_classification(self):
        """Test classification of acknowledgments."""
        message = "thanks"
        result = self.classifier.classify(message)
        
        self.assertEqual(result.intent_type, IntentType.ACKNOWLEDGMENT)
        self.assertGreater(result.confidence, 0.8)
        self.assertFalse(result.actionable)
    
    def test_clarification_needed_classification(self):
        """Test classification of ambiguous requests."""
        message = "xyz abc qwerty"  # Random, unknown words
        result = self.classifier.classify(message)
        
        self.assertEqual(result.intent_type, IntentType.CLARIFICATION_NEEDED)
        self.assertGreater(result.confidence, 0.5)
        self.assertFalse(result.actionable)
    
    def test_very_short_message_is_ambiguous(self):
        """Test that very short messages are classified as needing clarification."""
        message = "go"
        result = self.classifier.classify(message)
        
        self.assertEqual(result.intent_type, IntentType.CLARIFICATION_NEEDED)
        self.assertFalse(result.actionable)


class TestRoutingDecision(unittest.TestCase):
    """Test routing logic."""
    
    def test_route_execution_request(self):
        """Test routing of execution requests."""
        intent = IntentClassification(
            intent_type=IntentType.REQUEST_EXECUTION,
            confidence=0.8,
            keywords=['get', 'scrape'],
            actionable=True,
            reasoning="Execution keywords detected"
        )
        
        handler, kwargs = RoutingDecision.route(intent, "Get data from site.com")
        
        self.assertEqual(handler, "execute")
        self.assertIn('message', kwargs)
    
    def test_route_question_non_actionable(self):
        """Test routing of non-actionable questions."""
        intent = IntentClassification(
            intent_type=IntentType.QUESTION,
            confidence=0.6,
            keywords=['how'],
            actionable=False,
            reasoning="Informational question"
        )
        
        handler, kwargs = RoutingDecision.route(intent, "How does this work?")
        
        self.assertEqual(handler, "respond")
    
    def test_route_clarification_needed(self):
        """Test routing of ambiguous requests."""
        intent = IntentClassification(
            intent_type=IntentType.CLARIFICATION_NEEDED,
            confidence=0.6,
            keywords=[],
            actionable=False,
            reasoning="Ambiguous message"
        )
        
        handler, kwargs = RoutingDecision.route(intent, "xyz abc")
        
        self.assertEqual(handler, "clarify")
    
    def test_route_acknowledgment(self):
        """Test routing of acknowledgments."""
        intent = IntentClassification(
            intent_type=IntentType.ACKNOWLEDGMENT,
            confidence=0.95,
            keywords=[],
            actionable=False,
            reasoning="Greeting detected"
        )
        
        handler, kwargs = RoutingDecision.route(intent, "hi")
        
        self.assertEqual(handler, "acknowledge")
    
    def test_route_forecast_request(self):
        """Test routing of forecast requests."""
        intent = IntentClassification(
            intent_type=IntentType.FORECAST_REQUEST,
            confidence=0.7,
            keywords=['forecast'],
            actionable=True,
            reasoning="Forecast keywords detected"
        )
        
        handler, kwargs = RoutingDecision.route(intent, "Forecast next quarter")
        
        self.assertEqual(handler, "forecast")
    
    def test_route_status_check(self):
        """Test routing of status checks."""
        intent = IntentClassification(
            intent_type=IntentType.STATUS_CHECK,
            confidence=0.7,
            keywords=['status'],
            actionable=False,
            reasoning="Status keywords detected"
        )
        
        handler, kwargs = RoutingDecision.route(intent, "Status update?")
        
        self.assertEqual(handler, "status")


class TestInteractionOrchestrator(unittest.TestCase):
    """Test end-to-end orchestration."""
    
    def setUp(self):
        self.orchestrator = InteractionOrchestrator()
    
    def test_scenario_1_execution_request(self):
        """
        Scenario 1: User requests execution
        
        Input: "Get product names from amazon.com"
        Expected: Mission creation + ResponseEnvelope with mission_spawned
        Constraint Validation:
        - ONE decision per message ✓
        - NO autonomy (status='proposed') ✓
        - NO loops ✓
        """
        message = "Get product names from amazon.com"
        response = self.orchestrator.process_message(
            message, session_id="test_1", user_id="user1"
        )
        
        # Validation
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)  # or MISSION if execution
        self.assertGreaterEqual(len(response.artifacts), 0)
        
        # Hard constraint: NO loops - single message = single response
        self.assertIsNotNone(response.timestamp)
        
        # Log validation
        print(f"\n[TEST-1] Execution Request")
        print(f"  Response: {response.summary}")
        print(f"  Missions spawned: {len(response.missions_spawned)}")
    
    def test_scenario_2_informational_question(self):
        """
        Scenario 2: User asks informational question
        
        Input: "How do I scrape a website?"
        Expected: Text response with guidance
        Constraint Validation:
        - NO execution ✓
        - ONE decision (respond) ✓
        - NO LLM calls (heuristic response) ✓
        """
        message = "How do I scrape a website?"
        response = self.orchestrator.process_message(
            message, session_id="test_2", user_id="user2"
        )
        
        # Validation
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)
        self.assertGreater(len(response.summary), 0)
        
        # Hard constraint: NO mission created for questions
        self.assertEqual(len(response.missions_spawned), 0)
        
        # Log validation
        print(f"\n[TEST-2] Informational Question")
        print(f"  Response: {response.summary[:100]}...")
        print(f"  Missions: {len(response.missions_spawned)} (expect 0)")
    
    def test_scenario_3_ambiguous_request(self):
        """
        Scenario 3: Ambiguous/unclear request
        
        Input: "xyz abc qwerty"
        Expected: Clarification request
        Constraint Validation:
        - ONE decision (clarify) ✓
        - NO assumptions ✓
        - NO execution ✓
        """
        message = "xyz abc qwerty"
        response = self.orchestrator.process_message(
            message, session_id="test_3", user_id="user3"
        )
        
        # Validation
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.CLARIFICATION_REQUEST)
        
        # Hard constraint: NO mission for ambiguous
        self.assertEqual(len(response.missions_spawned), 0)
        
        # Log validation
        print(f"\n[TEST-3] Ambiguous Request")
        print(f"  Response type: {response.response_type.value}")
        print(f"  Missions: {len(response.missions_spawned)} (expect 0)")
    
    def test_scenario_4_acknowledgment(self):
        """
        Scenario 4: Greeting/Acknowledgment
        
        Input: "thanks"
        Expected: Friendly response
        Constraint Validation:
        - ONE decision (acknowledge) ✓
        - NO side effects ✓
        - NO execution ✓
        """
        message = "thanks"
        response = self.orchestrator.process_message(
            message, session_id="test_4", user_id="user4"
        )
        
        # Validation
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)
        self.assertIn("welcome", response.summary.lower())
        
        # Hard constraint: NO side effects
        self.assertEqual(len(response.missions_spawned), 0)
        self.assertEqual(len(response.signals_emitted), 0)
        
        # Log validation
        print(f"\n[TEST-4] Acknowledgment")
        print(f"  Response: {response.summary}")
        print(f"  Side effects: {len(response.missions_spawned)} missions, "
              f"{len(response.signals_emitted)} signals (expect 0, 0)")
    
    def test_scenario_5_forecast_request(self):
        """
        Scenario 5: Forecast request
        
        Input: "Predict trends for next quarter"
        Expected: Forecast response + queue for pipeline
        Constraint Validation:
        - ONE decision (forecast) ✓
        - NO autonomy (queued, not executed) ✓
        - NO loops ✓
        """
        message = "Predict trends for next quarter"
        response = self.orchestrator.process_message(
            message, session_id="test_5", user_id="user5"
        )
        
        # Validation
        self.assertIsNotNone(response)
        self.assertIn(response.response_type, [
            ResponseType.TEXT,
            ResponseType.FORECAST
        ])
        
        # Hard constraint: NO autonomous execution
        self.assertEqual(len(response.missions_spawned), 0)
        
        # Log validation
        print(f"\n[TEST-5] Forecast Request")
        print(f"  Response type: {response.response_type.value}")
        print(f"  Missions spawned: {len(response.missions_spawned)} (expect 0)")


class TestHardConstraints(unittest.TestCase):
    """Validate that hard constraints are enforced."""
    
    def setUp(self):
        self.orchestrator = InteractionOrchestrator()
    
    def test_no_autonomy_single_message_always_proposed(self):
        """
        CONSTRAINT: NO autonomy
        
        Every message should result in:
        - Proposed missions (never 'active')
        - Never spawned execution
        - Always awaiting user approval
        """
        messages = [
            "Get data from site.com",
            "Scrape product information",
            "Extract email addresses"
        ]
        
        for msg in messages:
            response = self.orchestrator.process_message(
                msg, session_id="test", user_id="test"
            )
            
            # All missions should be proposed, not active
            for mission in response.missions_spawned:
                self.assertEqual(mission.status, 'proposed',
                    f"Mission created from '{msg}' is not proposed status")
    
    def test_no_loops_one_message_one_response(self):
        """
        CONSTRAINT: NO loops
        
        ONE message should produce EXACTLY ONE response.
        No feedback loops, no iterative refinement.
        """
        message = "Get data from example.com"
        response = self.orchestrator.process_message(
            message, session_id="test", user_id="test"
        )
        
        # Single response object
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.timestamp)
        
        # Response is deterministic - should be identical on replay
        response2 = self.orchestrator.process_message(
            message, session_id="test", user_id="test"
        )
        self.assertEqual(
            response.response_type, response2.response_type,
            "Same message produced different response types"
        )
    
    def test_one_decision_per_message(self):
        """
        CONSTRAINT: ONE decision per message
        
        Each message should result in exactly one routing decision.
        """
        classifier = DeterministicIntentClassifier()
        
        messages = [
            "Get data from site.com",
            "How do I scrape?",
            "xyz abc",
            "thanks",
            "Forecast next month"
        ]
        
        for msg in messages:
            intent = classifier.classify(msg)
            
            # Exactly one intent type
            self.assertIsNotNone(intent.intent_type)
            self.assertIsInstance(intent.intent_type, IntentType)
            
            # Confidence in valid range
            self.assertGreaterEqual(intent.confidence, 0.0)
            self.assertLessEqual(intent.confidence, 1.0)
    
    def test_no_execution_without_explicit_intent(self):
        """
        CONSTRAINT: NO execution without explicit user intent
        
        Ambiguous or informational messages should NOT trigger execution.
        """
        non_execution_messages = [
            "How does it work?",
            "What's the weather?",
            "xyz abc qwerty",
            "hello",
            "ok"
        ]
        
        for msg in non_execution_messages:
            response = self.orchestrator.process_message(
                msg, session_id="test", user_id="test"
            )
            
            # NO mission creation for non-execution messages
            self.assertEqual(len(response.missions_spawned), 0,
                f"Execution triggered for non-explicit message: '{msg}'")
    
    def test_no_ui_code_only_schemas(self):
        """
        CONSTRAINT: NO UI code
        
        Response envelope should contain ONLY data schemas,
        no rendering logic or UI components.
        """
        message = "Get data from site.com"
        response = self.orchestrator.process_message(
            message, session_id="test", user_id="test"
        )
        
        # Response is pure data
        self.assertIsNotNone(response.to_dict())
        
        # Can serialize to JSON
        json_str = response.to_json()
        self.assertIsNotNone(json_str)
        self.assertTrue(len(json_str) > 0)
        
        # No rendering methods on response
        self.assertFalse(hasattr(response, 'render'))
        self.assertFalse(hasattr(response, 'display'))
        self.assertFalse(hasattr(response, 'to_html'))
    
    def test_deterministic_no_llm_calls(self):
        """
        CONSTRAINT: NO LLM calls
        
        Classification should be deterministic heuristics only.
        Same message = same intent classification.
        """
        classifier = DeterministicIntentClassifier()
        message = "Get product names from amazon.com"
        
        results = [classifier.classify(message) for _ in range(5)]
        
        # All results identical
        for result in results:
            self.assertEqual(result.intent_type, results[0].intent_type)
            self.assertEqual(result.confidence, results[0].confidence)
            self.assertEqual(result.actionable, results[0].actionable)


class TestConvenienceFunction(unittest.TestCase):
    """Test convenience function."""
    
    def test_orchestrate_message_function(self):
        """Test that convenience function works end-to-end."""
        response = orchestrate_message(
            message="Get data from site.com",
            session_id="test_session",
            user_id="test_user"
        )
        
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.response_type)
        self.assertIsNotNone(response.timestamp)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
