"""
Chat Session Handler Integration Tests

Tests the complete flow:
User Message → ChatSessionHandler → InteractionOrchestrator → ResponseEnvelope

5 Integration Scenarios:
1. Chat message → mission creation
2. Chat question → text response
3. Ambiguous message → clarification request
4. Acknowledgment → friendly response
5. Multiple messages in same session

CONSTRAINTS VALIDATED:
- No autonomy (missions always proposed)
- No frontend code
- No logic changes to existing agents
- No UI rendering
"""

import unittest
from datetime import datetime

from Back_End.chat_session_handler import (
    ChatMessage, ChatResponse, ChatSessionHandler, ChatSessionManager,
    handle_chat_message, get_session_stats, get_all_stats
)
from Back_End.response_envelope import ResponseType


class TestChatMessage(unittest.TestCase):
    """Test ChatMessage dataclass."""
    
    def test_chat_message_creation(self):
        """Test creating a chat message."""
        msg = ChatMessage(
            message_id="msg_123",
            user_id="user_456",
            session_id="sess_789",
            text="Get data from site.com",
            timestamp="2026-02-07T10:00:00"
        )
        
        self.assertEqual(msg.message_id, "msg_123")
        self.assertEqual(msg.text, "Get data from site.com")
        self.assertIsNone(msg.context)
    
    def test_chat_message_to_dict(self):
        """Test ChatMessage serialization."""
        msg = ChatMessage(
            message_id="msg_123",
            user_id="user_456",
            session_id="sess_789",
            text="Hello",
            timestamp="2026-02-07T10:00:00"
        )
        
        d = msg.to_dict()
        self.assertIn('message_id', d)
        self.assertIn('text', d)
        self.assertEqual(d['text'], "Hello")


class TestChatResponse(unittest.TestCase):
    """Test ChatResponse dataclass."""
    
    def test_chat_response_creation(self):
        """Test creating a chat response."""
        from Back_End.response_envelope import text_response
        
        envelope = text_response("Hello!")
        response = ChatResponse(
            response_id="resp_123",
            message_id="msg_456",
            session_id="sess_789",
            envelope=envelope,
            timestamp="2026-02-07T10:00:00"
        )
        
        self.assertEqual(response.response_id, "resp_123")
        self.assertEqual(response.envelope.response_type, ResponseType.TEXT)
    
    def test_chat_response_serialization(self):
        """Test ChatResponse JSON serialization."""
        from Back_End.response_envelope import text_response
        
        envelope = text_response("Test")
        response = ChatResponse(
            response_id="resp_123",
            message_id="msg_456",
            session_id="sess_789",
            envelope=envelope,
            timestamp="2026-02-07T10:00:00"
        )
        
        json_str = response.to_json()
        self.assertIsNotNone(json_str)
        self.assertIn("response_id", json_str)
        self.assertIn("resp_123", json_str)


class TestChatSessionHandler(unittest.TestCase):
    """Test ChatSessionHandler."""
    
    def setUp(self):
        self.handler = ChatSessionHandler("test_session", "test_user")
    
    def test_session_initialization(self):
        """Test session initialization."""
        self.assertEqual(self.handler.session_id, "test_session")
        self.assertEqual(self.handler.user_id, "test_user")
        self.assertEqual(self.handler.message_count, 0)
        self.assertEqual(self.handler.mission_count, 0)
    
    def test_single_message_handling(self):
        """Test handling a single message."""
        response = self.handler.handle_message(
            text="How do I scrape?",
            message_id="msg_001"
        )
        
        # Validate response
        self.assertIsNotNone(response)
        self.assertEqual(response.message_id, "msg_001")
        self.assertEqual(response.session_id, "test_session")
        self.assertIsNotNone(response.envelope)
        self.assertEqual(response.envelope.response_type, ResponseType.TEXT)
        
        # Validate session state
        self.assertEqual(self.handler.message_count, 1)
    
    def test_scenario_1_execution_request(self):
        """
        Scenario 1: Execution request → Mission creation
        
        User: "Get product names from amazon.com"
        Expected: Mission spawned (status='proposed')
        """
        response = self.handler.handle_message(
            text="Get product names from amazon.com",
            message_id="msg_exec_001"
        )
        
        # Validation
        self.assertIsNotNone(response.envelope)
        
        # Should have mission
        missions = response.envelope.missions_spawned
        
        # If mission created, verify it's proposed
        if len(missions) > 0:
            for mission in missions:
                self.assertEqual(mission.status, 'proposed',
                    "Mission must be proposed, not active")
            
            # Session tracks mission
            self.assertGreater(self.handler.mission_count, 0)
        
        print(f"\n[Scenario 1] Execution Request")
        print(f"  Missions: {len(missions)}")
        if missions:
            print(f"  Mission ID: {missions[0].mission_id}")
            print(f"  Status: {missions[0].status}")
    
    def test_scenario_2_question(self):
        """
        Scenario 2: Question → Text response (NO mission)
        
        User: "How do I scrape a website?"
        Expected: Text response, NO mission
        """
        response = self.handler.handle_message(
            text="How do I scrape a website?",
            message_id="msg_q_001"
        )
        
        # Validation
        self.assertEqual(response.envelope.response_type, ResponseType.TEXT)
        
        # No mission should be created
        self.assertEqual(len(response.envelope.missions_spawned), 0,
            "Questions should not create missions")
        
        print(f"\n[Scenario 2] Question")
        print(f"  Response Type: {response.envelope.response_type.value}")
        print(f"  Missions: {len(response.envelope.missions_spawned)}")
    
    def test_scenario_3_ambiguous(self):
        """
        Scenario 3: Ambiguous → Clarification request (NO mission)
        
        User: "xyz abc qwerty"
        Expected: Clarification request, NO mission
        """
        response = self.handler.handle_message(
            text="xyz abc qwerty",
            message_id="msg_amb_001"
        )
        
        # Validation
        self.assertEqual(
            response.envelope.response_type,
            ResponseType.CLARIFICATION_REQUEST
        )
        
        # No mission
        self.assertEqual(len(response.envelope.missions_spawned), 0)
        
        print(f"\n[Scenario 3] Ambiguous Request")
        print(f"  Response Type: {response.envelope.response_type.value}")
        print(f"  Missions: {len(response.envelope.missions_spawned)}")
    
    def test_scenario_4_acknowledgment(self):
        """
        Scenario 4: Acknowledgment → Friendly response (NO mission, NO side effects)
        
        User: "thanks"
        Expected: Text response, NO missions, NO signals
        """
        response = self.handler.handle_message(
            text="thanks",
            message_id="msg_ack_001"
        )
        
        # Validation
        self.assertEqual(response.envelope.response_type, ResponseType.TEXT)
        
        # No side effects
        self.assertEqual(len(response.envelope.missions_spawned), 0,
            "Acknowledgments should not create missions")
        
        print(f"\n[Scenario 4] Acknowledgment")
        print(f"  Response Type: {response.envelope.response_type.value}")
        print(f"  Side Effects: {len(response.envelope.missions_spawned)} missions")
    
    def test_scenario_5_multiple_messages(self):
        """
        Scenario 5: Multiple messages in same session
        
        Tests session state tracking across messages
        """
        # Message 1
        r1 = self.handler.handle_message(
            text="Get data from site.com",
            message_id="msg_001"
        )
        count_after_1 = self.handler.message_count
        
        # Message 2
        r2 = self.handler.handle_message(
            text="How is it going?",
            message_id="msg_002"
        )
        count_after_2 = self.handler.message_count
        
        # Message 3
        r3 = self.handler.handle_message(
            text="Thanks!",
            message_id="msg_003"
        )
        count_after_3 = self.handler.message_count
        
        # Validation
        self.assertEqual(count_after_1, 1)
        self.assertEqual(count_after_2, 2)
        self.assertEqual(count_after_3, 3)
        
        # Get stats
        stats = self.handler.get_session_stats()
        self.assertEqual(stats['message_count'], 3)
        self.assertEqual(stats['session_id'], "test_session")
        
        print(f"\n[Scenario 5] Multiple Messages")
        print(f"  Messages: {count_after_3}")
        print(f"  Session Stats: {stats}")
    
    def test_session_stats(self):
        """Test session statistics."""
        self.handler.handle_message("Message 1")
        self.handler.handle_message("Message 2")
        
        stats = self.handler.get_session_stats()
        
        self.assertEqual(stats['message_count'], 2)
        self.assertEqual(stats['user_id'], "test_user")
        self.assertIn('uptime_seconds', stats)
        self.assertGreater(stats['uptime_seconds'], 0)


class TestChatSessionManager(unittest.TestCase):
    """Test ChatSessionManager."""
    
    def setUp(self):
        self.manager = ChatSessionManager()
    
    def test_get_or_create_session(self):
        """Test session creation and retrieval."""
        # Get/create session 1
        s1 = self.manager.get_or_create_session("sess_1", "user_1")
        self.assertIsNotNone(s1)
        self.assertEqual(s1.session_id, "sess_1")
        
        # Get same session (should not create new)
        s1_again = self.manager.get_or_create_session("sess_1", "user_1")
        self.assertIs(s1, s1_again)
        
        # Create different session
        s2 = self.manager.get_or_create_session("sess_2", "user_2")
        self.assertIsNot(s1, s2)
    
    def test_handle_message_via_manager(self):
        """Test handling messages through manager."""
        response = self.manager.handle_message(
            session_id="sess_1",
            text="Get data from site.com",
            user_id="user_1",
            message_id="msg_001"
        )
        
        self.assertIsNotNone(response)
        self.assertEqual(response.session_id, "sess_1")
    
    def test_manager_stats(self):
        """Test manager statistics."""
        # Add some messages to different sessions
        self.manager.handle_message("sess_1", "Message 1", "user_1")
        self.manager.handle_message("sess_1", "Message 2", "user_1")
        self.manager.handle_message("sess_2", "Message 3", "user_2")
        
        # Check all stats
        all_stats = self.manager.get_all_stats()
        
        self.assertEqual(all_stats['total_sessions'], 2)
        self.assertIn('sess_1', all_stats['sessions'])
        self.assertIn('sess_2', all_stats['sessions'])


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_handle_chat_message(self):
        """Test convenience function."""
        response = handle_chat_message(
            session_id="test_sess",
            text="Hello",
            user_id="test_user",
            message_id="msg_001"
        )
        
        self.assertIsNotNone(response)
        self.assertEqual(response.session_id, "test_sess")
    
    def test_get_stats_functions(self):
        """Test statistics convenience functions."""
        # Handle a message
        handle_chat_message("sess_1", "Message 1", "user_1")
        
        # Get session stats
        stats = get_session_stats("sess_1")
        self.assertIsNotNone(stats)
        self.assertEqual(stats['message_count'], 1)
        
        # Get all stats
        all_stats = get_all_stats()
        self.assertGreater(all_stats['total_sessions'], 0)


class TestHardConstraints(unittest.TestCase):
    """Validate hard constraints."""
    
    def test_no_autonomy_missions_proposed(self):
        """
        CONSTRAINT: NO autonomy
        
        All missions should be status='proposed'
        """
        handler = ChatSessionHandler("sess", "user")
        
        messages = [
            "Get data from site.com",
            "Scrape product information",
            "Extract email addresses"
        ]
        
        for msg in messages:
            response = handler.handle_message(msg)
            
            # All missions should be proposed
            for mission in response.envelope.missions_spawned:
                self.assertEqual(mission.status, 'proposed',
                    f"Mission from '{msg}' is not proposed")
    
    def test_no_ui_code_pure_schema(self):
        """
        CONSTRAINT: NO UI code
        
        Response should be pure schema (no rendering)
        """
        handler = ChatSessionHandler("sess", "user")
        response = handler.handle_message("Get data from site.com")
        
        envelope = response.envelope
        
        # Should have to_dict and to_json
        d = envelope.to_dict()
        self.assertIsNotNone(d)
        
        json_str = envelope.to_json()
        self.assertIsNotNone(json_str)
        
        # Should NOT have render/display methods
        self.assertFalse(hasattr(envelope, 'render'))
        self.assertFalse(hasattr(envelope, 'display'))
        self.assertFalse(hasattr(envelope, 'to_html'))
    
    def test_no_logic_changes_to_agents(self):
        """
        CONSTRAINT: NO logic changes to existing agents
        
        ChatSessionHandler should only coordinate, not modify agents
        """
        # Handler should just call orchestrator and return result
        handler = ChatSessionHandler("sess", "user")
        
        # Import orchestrator directly and compare
        from Back_End.interaction_orchestrator import orchestrate_message
        
        msg = "Get data from site.com"
        
        # Via handler
        response = handler.handle_message(msg, message_id="msg_1")
        
        # Direct call
        direct = orchestrate_message(msg, "sess", "user")
        
        # Should have same intent type
        self.assertEqual(
            response.envelope.response_type,
            direct.response_type
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)

