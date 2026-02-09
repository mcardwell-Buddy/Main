"""
================================================================================
PHASE 2: SOUL INTEGRATION SYSTEM
================================================================================

Purpose: Interface for Soul system (user-facing approval and memory system).
Provides callbacks for:
  - Approval request validation
  - Clarification question validation
  - Conversation context retrieval
  - Approval decision storage

Reference: PHASE_2_DESIGN_DOCUMENT.md - Section 2

Integration Pattern:
  - Non-blocking callbacks (async)
  - Full audit trail
  - Persistent storage
  - Timeout handling

This module includes:
  1. SoulInterface (abstract base)
  2. MockSoulSystem (for testing)
  3. HTTPSoulClient (for production - stub)
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
import asyncio


@dataclass
class ConversationContext:
    """Context from prior conversation."""
    session_id: str
    prior_goals: List[Dict[str, Any]] = field(default_factory=list)
    prior_approvals: List[Dict[str, Any]] = field(default_factory=list)
    context_summary: str = ""


class SoulInterface(ABC):
    """
    Abstract interface for Soul system integration.
    
    Implementations:
      - MockSoulSystem (for testing)
      - HTTPSoulClient (for production)
    """
    
    @abstractmethod
    def validate_approval_request(
        self,
        approval_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate approval request before sending to user.
        
        Args:
            approval_request: Request dict with goal, confidence, etc.
        
        Returns:
            {
                'valid': bool,
                'feedback': str,
                'approved': bool (optional, if Soul pre-approves)
            }
        """
        pass
    
    @abstractmethod
    def validate_clarification(
        self,
        clarification_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate clarification questions before sending to user.
        
        Args:
            clarification_request: Request dict with questions
        
        Returns:
            {
                'valid': bool,
                'approved_indices': List[int],
                'feedback': str
            }
        """
        pass
    
    @abstractmethod
    def get_conversation_context(
        self,
        session_id: str,
    ) -> ConversationContext:
        """
        Retrieve prior conversation context.
        
        Args:
            session_id: User session ID
        
        Returns:
            ConversationContext with prior goals, approvals, etc.
        """
        pass
    
    @abstractmethod
    def store_approval_decision(
        self,
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Store approval decision for audit trail.
        
        Args:
            decision: {
                'request_id': str,
                'approved': bool,
                'feedback': str,
                'timestamp': str,
                'approver_id': str,
            }
        
        Returns:
            {
                'stored': bool,
                'decision_id': str
            }
        """
        pass


class MockSoulSystem(SoulInterface):
    """
    Mock Soul system for testing Phase 2 without real Soul integration.
    
    Features:
    - In-memory storage
    - Deterministic responses
    - Simulated delays
    - Approval history tracking
    
    Usage:
        soul = MockSoulSystem()
        result = soul.validate_approval_request({...})
        context = soul.get_conversation_context("session_123")
    """
    
    def __init__(self, simulate_delays: bool = False):
        """
        Initialize mock Soul system.
        
        Args:
            simulate_delays: Add small delays to simulate network latency
        """
        self.simulate_delays = simulate_delays
        
        # In-memory storage
        self._approval_decisions: Dict[str, Dict] = {}
        self._conversation_history: Dict[str, List[Dict]] = {}
        self._clarification_history: Dict[str, List[Dict]] = {}
    
    def validate_approval_request(
        self,
        approval_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Mock approval request validation.
        Always returns valid unless confidence is suspiciously high/low.
        """
        if self.simulate_delays:
            # Simulate network delay
            import time
            time.sleep(0.01)
        
        confidence = approval_request.get('confidence', 0.5)
        goal = approval_request.get('goal', '')
        
        # Validation rules (mock)
        issues = []
        
        if confidence < 0 or confidence > 1:
            issues.append("Confidence out of range [0, 1]")
        
        if not goal or len(goal) < 3:
            issues.append("Goal must be at least 3 characters")
        
        if len(approval_request.get('tools_proposed', [])) == 0:
            issues.append("No tools proposed")
        
        # In mock: we approve by default (would be user decision in real Soul)
        pre_approved = confidence >= 0.85
        
        return {
            'valid': len(issues) == 0,
            'feedback': "; ".join(issues) if issues else "Request is valid",
            'approved': pre_approved,  # Mock pre-approves high confidence
        }
    
    def validate_clarification(
        self,
        clarification_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Mock clarification question validation.
        Validates that questions are clear and not excessive.
        """
        if self.simulate_delays:
            import time
            time.sleep(0.01)
        
        questions = clarification_request.get('questions', [])
        
        # Validation rules (mock)
        issues = []
        approved_indices = []
        
        if len(questions) == 0:
            issues.append("No questions provided")
        elif len(questions) > 5:
            issues.append("Too many questions (max 5)")
        
        for q in questions:
            if isinstance(q, dict):
                question_text = q.get('question', '')
                q_index = q.get('index', -1)
            else:
                continue
            
            if len(question_text) < 5:
                issues.append(f"Q{q_index}: Question too short")
            else:
                approved_indices.append(q_index)
        
        return {
            'valid': len(issues) == 0,
            'approved_indices': approved_indices,
            'feedback': "; ".join(issues) if issues else "All questions approved",
        }
    
    def get_conversation_context(
        self,
        session_id: str,
    ) -> ConversationContext:
        """
        Mock conversation context retrieval.
        Returns empty context for new sessions, prior history for existing.
        """
        if self.simulate_delays:
            import time
            time.sleep(0.01)
        
        history = self._conversation_history.get(session_id, [])
        
        return ConversationContext(
            session_id=session_id,
            prior_goals=history[:5],  # Last 5 goals
            prior_approvals=[
                h for h in history if h.get('type') == 'approval'
            ][:5],
            context_summary=f"Session {session_id} with {len(history)} prior interactions",
        )
    
    def store_approval_decision(
        self,
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Mock approval decision storage.
        Stores in memory and generates decision ID.
        """
        if self.simulate_delays:
            import time
            time.sleep(0.01)
        
        request_id = decision.get('request_id', 'unknown')
        session_id = decision.get('session_id', 'unknown')
        
        # Generate decision ID
        import uuid
        decision_id = f"approval_{uuid.uuid4().hex[:8]}"
        
        # Store
        self._approval_decisions[decision_id] = {
            **decision,
            'decision_id': decision_id,
            'stored_at': datetime.utcnow().isoformat(),
        }
        
        # Add to conversation history
        if session_id not in self._conversation_history:
            self._conversation_history[session_id] = []
        
        self._conversation_history[session_id].append({
            'type': 'approval',
            'request_id': request_id,
            'decision_id': decision_id,
            'approved': decision.get('approved', False),
            'timestamp': datetime.utcnow().isoformat(),
        })
        
        return {
            'stored': True,
            'decision_id': decision_id,
        }
    
    def add_goal_to_history(self, session_id: str, goal: str):
        """Helper to manually add goal to conversation history."""
        if session_id not in self._conversation_history:
            self._conversation_history[session_id] = []
        
        self._conversation_history[session_id].append({
            'type': 'goal',
            'goal': goal,
            'timestamp': datetime.utcnow().isoformat(),
        })
    
    def get_approval_history(self, session_id: str) -> List[Dict]:
        """Get all approval decisions for a session."""
        history = self._conversation_history.get(session_id, [])
        return [h for h in history if h.get('type') == 'approval']


class HTTPSoulClient(SoulInterface):
    """
    HTTP client for Soul system (production stub).
    
    In production, this would make real HTTP requests to Soul API.
    For now: stub implementation.
    
    Configuration:
        soul_url: Base URL of Soul API
        timeout: Request timeout in seconds
        api_key: API key for authentication
    """
    
    def __init__(
        self,
        soul_url: str = "http://localhost:8001",
        timeout: float = 5.0,
        api_key: str = "test-key",
    ):
        """Initialize HTTP Soul client."""
        self.soul_url = soul_url
        self.timeout = timeout
        self.api_key = api_key
    
    def validate_approval_request(
        self,
        approval_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Stub: would make HTTP POST to /soul/validate-approval"""
        # TODO: Implement real HTTP call
        # response = requests.post(
        #     f"{self.soul_url}/validate-approval",
        #     json=approval_request,
        #     timeout=self.timeout,
        #     headers={'Authorization': f'Bearer {self.api_key}'}
        # )
        # return response.json()
        return {'valid': True, 'feedback': 'STUB'}
    
    def validate_clarification(
        self,
        clarification_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Stub: would make HTTP POST to /soul/validate-clarification"""
        return {'valid': True, 'approved_indices': [], 'feedback': 'STUB'}
    
    def get_conversation_context(
        self,
        session_id: str,
    ) -> ConversationContext:
        """Stub: would make HTTP GET to /soul/context/{session_id}"""
        return ConversationContext(session_id=session_id)
    
    def store_approval_decision(
        self,
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Stub: would make HTTP POST to /soul/store-decision"""
        return {'stored': True, 'decision_id': 'stub-id'}


# =============================================================================
# EXAMPLES FOR TESTING
# =============================================================================

def example_mock_soul_validation():
    """Example: Mock Soul validates approval request."""
    soul = MockSoulSystem()
    
    approval_request = {
        'goal': 'Click the submit button',
        'confidence': 0.72,
        'tools_proposed': ['button_clicker'],
    }
    
    result = soul.validate_approval_request(approval_request)
    
    print("MOCK SOUL - APPROVAL VALIDATION:")
    print(f"  Valid: {result['valid']}")
    print(f"  Feedback: {result['feedback']}")
    print(f"  Pre-approved: {result.get('approved', False)}")
    return result


def example_mock_soul_clarification():
    """Example: Mock Soul validates clarification questions."""
    soul = MockSoulSystem()
    
    clarification_request = {
        'original_goal': 'Help me',
        'questions': [
            {'index': 0, 'question': 'What action do you want?'},
            {'index': 1, 'question': 'What is the target?'},
        ]
    }
    
    result = soul.validate_clarification(clarification_request)
    
    print("\nMOCK SOUL - CLARIFICATION VALIDATION:")
    print(f"  Valid: {result['valid']}")
    print(f"  Approved Question Indices: {result['approved_indices']}")
    print(f"  Feedback: {result['feedback']}")
    return result


def example_mock_soul_context():
    """Example: Mock Soul retrieves conversation context."""
    soul = MockSoulSystem()
    
    # Add some history
    soul.add_goal_to_history('session_123', 'Click button')
    soul.add_goal_to_history('session_123', 'Find element')
    
    context = soul.get_conversation_context('session_123')
    
    print("\nMOCK SOUL - CONVERSATION CONTEXT:")
    print(f"  Session ID: {context.session_id}")
    print(f"  Prior Goals: {len(context.prior_goals)}")
    print(f"  Context Summary: {context.context_summary}")
    return context


def example_mock_soul_storage():
    """Example: Mock Soul stores approval decision."""
    soul = MockSoulSystem()
    
    decision = {
        'request_id': 'req_123',
        'session_id': 'session_123',
        'approved': True,
        'feedback': 'Go ahead, this looks right',
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    result = soul.store_approval_decision(decision)
    
    print("\nMOCK SOUL - APPROVAL STORAGE:")
    print(f"  Stored: {result['stored']}")
    print(f"  Decision ID: {result['decision_id']}")
    
    # Verify it's in history
    history = soul.get_approval_history('session_123')
    print(f"  Approval History Entries: {len(history)}")
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("SOUL INTEGRATION SYSTEM - EXAMPLES")
    print("=" * 70)
    
    example_mock_soul_validation()
    example_mock_soul_clarification()
    example_mock_soul_context()
    example_mock_soul_storage()
