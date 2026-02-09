"""
Chat Intake Coordinator

Main entry point for chat → mission flow.

Orchestrates:
1. Intent routing
2. Draft building
3. Proposal emission
4. Chat feedback

NO execution. NO autonomy. Pure coordination.
"""

from typing import Dict, Any
from dataclasses import asdict

from backend.mission_control.chat_intent_router import ChatIntentRouter, ChatIntent
from backend.mission_control.mission_draft_builder import MissionDraftBuilder, MissionDraft
from backend.mission_control.mission_proposal_emitter import MissionProposalEmitter


class ChatIntakeCoordinator:
    """
    Coordinates chat message intake and mission proposal.
    
    Flow:
    1. Chat message arrives
    2. Route to intent
    3. If actionable, build draft
    4. Emit proposal
    5. Return feedback for chat response
    
    NO execution happens here.
    """
    
    def __init__(self):
        self.router = ChatIntentRouter()
        self.builder = MissionDraftBuilder()
        self.emitter = MissionProposalEmitter()
    
    def process_chat_message(self, message: str, user_id: str = 'default') -> Dict[str, Any]:
        """
        Process a chat message and return feedback.
        
        Args:
            message: Raw chat message text
            user_id: User identifier (optional)
            
        Returns:
            dict with:
            - intent_classification
            - actionable (bool)
            - mission_draft (if actionable)
            - emission_result (if emitted)
            - chat_feedback (message for user)
        """
        # Step 1: Route intent
        intent = self.router.route(message)
        
        result = {
            'intent_classification': intent.to_dict(),
            'actionable': intent.actionable,
            'user_id': user_id,
        }
        
        # Step 2: Handle non-actionable
        if not intent.actionable:
            result['chat_feedback'] = self._create_non_actionable_feedback(intent)
            return result
        
        # Step 3: Build draft
        draft = self.builder.build_draft(
            raw_message=message,
            intent_type=intent.intent_type,
            intent_keywords=intent.keywords_matched
        )
        
        result['mission_draft'] = draft.to_dict()
        
        # Step 4: Emit proposal
        emission = self.emitter.emit_proposal(draft)
        result['emission_result'] = emission
        
        # Step 5: Create feedback
        result['chat_feedback'] = self._create_actionable_feedback(draft, emission)
        
        return result
    
    def _create_non_actionable_feedback(self, intent: ChatIntent) -> Dict[str, Any]:
        """
        Create feedback for non-actionable messages.
        
        Returns friendly message explaining why not actionable.
        """
        intent_type = intent.intent_type
        
        if intent_type == 'informational_question':
            return {
                'type': 'informational_response',
                'message': "I'll need to collect that data for you. Can you specify what information you'd like me to get and from where? For example: 'Get the services list from example.com'",
                'can_convert_to_action': True,
                'suggestion': 'Rephrase as a data collection request'
            }
        
        if intent_type == 'non_actionable':
            return {
                'type': 'non_actionable_response',
                'message': "I understand. What would you like me to help with?",
                'can_convert_to_action': False,
                'suggestion': None
            }
        
        return {
            'type': 'unknown_response',
            'message': "I'm not sure how to help with that. Try: 'Get [data] from [website]'",
            'can_convert_to_action': False,
            'suggestion': 'Provide more details'
        }
    
    def _create_actionable_feedback(self, draft: MissionDraft, emission: dict) -> Dict[str, Any]:
        """
        Create feedback for actionable messages.
        
        Returns mission summary and approval request.
        """
        return {
            'type': 'mission_proposed',
            'message': self._format_mission_summary(draft),
            'mission_id': draft.mission_id,
            'status': 'proposed',
            'awaiting_approval': True,
            'approval_required': True,
            'next_steps': [
                'Review the mission details',
                'Approve to execute',
                'Mission will appear in Whiteboard'
            ]
        }
    
    def _format_mission_summary(self, draft: MissionDraft) -> str:
        """
        Format mission draft into human-readable summary.
        
        Returns clear description of what the mission would do.
        """
        lines = []
        lines.append("📋 Mission Proposed:")
        lines.append(f"• Objective: {draft.objective_description}")
        lines.append(f"• Type: {draft.objective_type}")
        
        if draft.target_count:
            lines.append(f"• Target: {draft.target_count} items")
        
        if draft.allowed_domains:
            domains_str = ', '.join(draft.allowed_domains)
            lines.append(f"• Domains: {domains_str}")
        
        lines.append(f"• Max Pages: {draft.max_pages}")
        lines.append(f"• Max Duration: {draft.max_duration_seconds}s")
        lines.append("")
        lines.append("⚠️ Status: PROPOSED (awaiting approval)")
        lines.append("✅ Review in Whiteboard to approve")
        
        return '\n'.join(lines)
    
    def get_pending_proposals(self) -> list:
        """Get all pending mission proposals."""
        return self.emitter.get_proposed_missions()


# Convenience function
def process_chat_message(message: str, user_id: str = 'default') -> Dict[str, Any]:
    """Process a chat message and return feedback."""
    coordinator = ChatIntakeCoordinator()
    return coordinator.process_chat_message(message, user_id)
