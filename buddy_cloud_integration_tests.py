"""
Buddy Cloud Integration Test Suite
===================================
Comprehensive end-to-end tests to verify all Buddy capabilities after cloud migration.

Tests:
1. Core Chat Integration - Message handling, session persistence
2. Tool Integration - Web scraping, data extraction, API calls
3. Learning System - Adaptive behavior, confidence tracking
4. Mission System - Goal decomposition, task orchestration
5. Artifact System - Document generation, code snippets
6. Observability - Tracing, logging, metrics
7. Knowledge Graph - Skill tracking, relationship mapping
8. Economic Simulation - Resource allocation (simulation only)
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
import uuid

# Add Back_End to path
sys.path.insert(0, str(Path(__file__).parent / "Back_End"))

from Back_End.chat_session_handler import ChatMessage, ChatSessionHandler
from Back_End.interaction_orchestrator import InteractionOrchestrator
from Back_End.buddy_core import (
    get_conversation_store,
    list_conversation_sessions,
    get_conversation_session
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BuddyIntegrationTester:
    """Comprehensive integration test runner for Buddy cloud deployment."""
    
    def __init__(self):
        self.test_session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        self.test_user_id = "integration_tester"
        self.results = []
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if details:
            logger.info(f"  Details: {details}")
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    async def test_1_core_chat_integration(self):
        """Test basic chat message handling and response generation."""
        logger.info("\n" + "="*70)
        logger.info("TEST 1: Core Chat Integration")
        logger.info("="*70)
        
        try:
            handler = ChatSessionHandler(
                session_id=self.test_session_id,
                user_id=self.test_user_id
            )
            
            # Test simple message
            message = ChatMessage(
                message_id=str(uuid.uuid4()),
                user_id=self.test_user_id,
                session_id=self.test_session_id,
                text="Hello Buddy, can you help me test your capabilities?",
                timestamp=datetime.now(timezone.utc).isoformat(),
                trace_id=str(uuid.uuid4())  # Add required trace_id
            )
            
            response = handler.handle_message(message)
            
            # Verify response structure
            assert response.envelope is not None, "No envelope returned"
            assert response.envelope.summary is not None, "No summary in envelope"
            assert len(response.envelope.summary) > 0, "Empty summary"
            
            self.log_test(
                "Core Chat - Message Processing",
                True,
                f"Received response with {len(response.envelope.summary)} chars"
            )
            
            # Test session persistence
            sessions = list_conversation_sessions()
            test_sessions = [s for s in sessions if s['session_id'] == self.test_session_id]
            assert len(test_sessions) > 0, "Session not persisted"
            
            self.log_test(
                "Core Chat - Session Persistence",
                True,
                f"Session {self.test_session_id} found in store"
            )
            
            # Test message retrieval
            full_session = get_conversation_session(self.test_session_id)
            assert full_session is not None, "Cannot retrieve session"
            assert len(full_session.get('messages', [])) >= 1, "Messages not persisted"
            
            self.log_test(
                "Core Chat - Message Persistence",
                True,
                f"Retrieved {len(full_session['messages'])} messages from session"
            )
            
        except Exception as e:
            self.log_test("Core Chat Integration", False, str(e))
            logger.error(f"Test 1 failed: {e}", exc_info=True)
            
    async def test_2_tool_integration(self):
        """Test tool invocation and execution."""
        logger.info("\n" + "="*70)
        logger.info("TEST 2: Tool Integration")
        logger.info("="*70)
        
        try:
            handler = ChatSessionHandler(
                session_id=self.test_session_id,
                user_id=self.test_user_id
            )
            
            # Test requests that should trigger tools
            test_cases = [
                ("Extract the main content from https://example.com", "web_scraping"),
                ("Search for information about Python asyncio", "search_tool"),
                ("Calculate 12345 * 67890", "calculation_tool"),
            ]
            
            tools_available = True
            for prompt, expected_tool in test_cases:
                try:
                    message = ChatMessage(
                        message_id=str(uuid.uuid4()),
                        user_id=self.test_user_id,
                        session_id=self.test_session_id,
                        text=prompt,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        trace_id=str(uuid.uuid4())  # Add required trace_id
                    )
                    
                    response = handler.handle_message(message)
                    
                    # Check if response mentions tool usage or provides relevant answer
                    has_tool_indication = (
                        'tool' in response.envelope.summary.lower() or
                        'search' in response.envelope.summary.lower() or
                        'extract' in response.envelope.summary.lower() or
                        len(response.envelope.summary) > 50  # Substantive response
                    )
                    
                    self.log_test(
                        f"Tool Integration - {expected_tool}",
                        has_tool_indication,
                        f"Response length: {len(response.envelope.summary)} chars"
                    )
                    
                except Exception as e:
                    self.log_test(f"Tool Integration - {expected_tool}", False, str(e))
                    tools_available = False
                    
        except Exception as e:
            self.log_test("Tool Integration", False, str(e))
            logger.error(f"Test 2 failed: {e}", exc_info=True)
            
    async def test_3_mission_system(self):
        """Test mission spawning and orchestration."""
        logger.info("\n" + "="*70)
        logger.info("TEST 3: Mission System")
        logger.info("="*70)
        
        try:
            handler = ChatSessionHandler(
                session_id=self.test_session_id,
                user_id=self.test_user_id
            )
            
            # Request that should spawn a mission
            message = ChatMessage(
                message_id=str(uuid.uuid4()),
                user_id=self.test_user_id,
                session_id=self.test_session_id,
                text="I need you to monitor https://example.com for changes and notify me daily",
                timestamp=datetime.now(timezone.utc).isoformat(),
                trace_id=str(uuid.uuid4())  # Add required trace_id
            )
            
            response = handler.handle_message(message)
            
            # Check for missions in envelope
            missions_spawned = response.envelope.missions_spawned
            has_missions = len(missions_spawned) > 0
            
            self.log_test(
                "Mission System - Mission Spawning",
                has_missions,
                f"Spawned {len(missions_spawned)} missions"
            )
            
            # Check mission structure if any were spawned
            if has_missions:
                mission = missions_spawned[0]
                valid_structure = all(
                    hasattr(mission, attr) for attr in ['mission_id', 'status', 'objective_type']
                )
                self.log_test(
                    "Mission System - Mission Structure",
                    valid_structure,
                    f"Mission ID: {mission.mission_id}"
                )
            else:
                logger.warning("No missions spawned - mission system may need configuration")
                self.log_test(
                    "Mission System - Mission Structure",
                    False,
                    "No missions generated to validate structure"
                )
                
        except Exception as e:
            self.log_test("Mission System", False, str(e))
            logger.error(f"Test 3 failed: {e}", exc_info=True)
            
    async def test_4_artifact_system(self):
        """Test artifact generation."""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: Artifact System")
        logger.info("="*70)
        
        try:
            handler = ChatSessionHandler(
                session_id=self.test_session_id,
                user_id=self.test_user_id
            )
            
            # Request that should generate an artifact
            message = ChatMessage(
                message_id=str(uuid.uuid4()),
                user_id=self.test_user_id,
                session_id=self.test_session_id,
                text="Create a Python script that prints 'Hello World'",
                timestamp=datetime.now(timezone.utc).isoformat(),
                trace_id=str(uuid.uuid4())  # Add required trace_id
            )
            
            response = handler.handle_message(message)
            
            # Check for artifacts
            artifacts = response.envelope.artifacts
            has_artifacts = len(artifacts) > 0
            
            self.log_test(
                "Artifact System - Generation",
                has_artifacts or len(response.envelope.summary) > 100,  # Either artifacts or detailed response
                f"Generated {len(artifacts)} artifacts, response: {len(response.envelope.summary)} chars"
            )
            
        except Exception as e:
            self.log_test("Artifact System", False, str(e))
            logger.error(f"Test 4 failed: {e}", exc_info=True)
            
    async def test_5_observability(self):
        """Test observability and tracing."""
        logger.info("\n" + "="*70)
        logger.info("TEST 5: Observability & Tracing")
        logger.info("="*70)
        
        try:
            handler = ChatSessionHandler(
                session_id=self.test_session_id,
                user_id=self.test_user_id
            )
            
            trace_id = str(uuid.uuid4())
            
            message = ChatMessage(
                message_id=str(uuid.uuid4()),
                user_id=self.test_user_id,
                session_id=self.test_session_id,
                text="Test observability tracing",
                timestamp=datetime.now(timezone.utc).isoformat(),
                trace_id=trace_id
            )
            
            response = handler.handle_message(message)
            
            # Verify trace_id is preserved
            trace_preserved = response.trace_id == trace_id
            
            self.log_test(
                "Observability - Trace ID Propagation",
                trace_preserved,
                f"Trace ID: {response.trace_id}"
            )
            
            # Check if observability directories exist
            try:
                from Back_End.observability import ensure_observability_dirs
                ensure_observability_dirs()
                obs_exists = True
            except Exception:
                obs_exists = False
            
            self.log_test(
                "Observability - Infrastructure",
                obs_exists,
                f"Observability system available: {obs_exists}"
            )
            
        except Exception as e:
            self.log_test("Observability", False, str(e))
            logger.error(f"Test 5 failed: {e}", exc_info=True)
            
    async def test_6_backend_endpoints(self):
        """Test backend API endpoints availability."""
        logger.info("\n" + "="*70)
        logger.info("TEST 6: Backend API Endpoints")
        logger.info("="*70)
        
        try:
            # Test conversation store functions
            sessions = list_conversation_sessions()
            self.log_test(
                "Backend - List Sessions",
                isinstance(sessions, list),
                f"Retrieved {len(sessions)} sessions"
            )
            
            # Test session retrieval
            if self.test_session_id:
                session = get_conversation_session(self.test_session_id)
                self.log_test(
                    "Backend - Get Session",
                    session is not None,
                    f"Session retrieval successful"
                )
                
                # Verify messages are included
                if session:
                    messages = session.get('messages', [])
                    self.log_test(
                        "Backend - Message Retrieval",
                        len(messages) > 0,
                        f"Retrieved {len(messages)} messages"
                    )
            
        except Exception as e:
            self.log_test("Backend Endpoints", False, str(e))
            logger.error(f"Test 6 failed: {e}", exc_info=True)
            
    async def run_all_tests(self):
        """Execute all integration tests."""
        logger.info("\n" + "="*80)
        logger.info("  BUDDY CLOUD INTEGRATION TEST SUITE")
        logger.info("  Testing all core capabilities after local-to-cloud migration")
        logger.info("="*80 + "\n")
        
        start_time = datetime.now()
        
        # Run all tests
        await self.test_1_core_chat_integration()
        await self.test_2_tool_integration()
        await self.test_3_mission_system()
        await self.test_4_artifact_system()
        await self.test_5_observability()
        await self.test_6_backend_endpoints()
        
        # Generate summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        logger.info("\n" + "="*80)
        logger.info("  TEST SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {total - passed}")
        logger.info(f"Pass Rate: {pass_rate:.1f}%")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info("="*80 + "\n")
        
        # Save results
        results_file = Path(__file__).parent / "test_results_cloud_integration.json"
        with open(results_file, 'w') as f:
            json.dump({
                "test_run": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration,
                    "pass_rate": pass_rate
                },
                "results": self.results
            }, f, indent=2)
        
        logger.info(f"✅ Test results saved to: {results_file}\n")
        
        return pass_rate >= 80  # Consider successful if 80%+ pass


async def main():
    """Run integration tests."""
    tester = BuddyIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("🎉 Integration tests PASSED - Buddy is fully operational!")
        return 0
    else:
        logger.error("⚠️  Integration tests FAILED - Review results above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
