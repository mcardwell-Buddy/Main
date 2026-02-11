"""
Mission Proposal Emitter

Writes proposed missions to Firebase MissionStore and emits learning signals.

HARD CONSTRAINTS:
- NO execution
- NO automatic approval
- All proposals logged to Firebase
- All proposals emit signals
- Full audit trail
"""

from datetime import datetime, timezone
from typing import Optional

from Back_End.mission_control.mission_draft_builder import MissionDraft
from Back_End.mission_store import get_mission_store, Mission
from Back_End.memory_manager import memory


class MissionProposalEmitter:
    """
    Emits mission proposals to Firebase MissionStore and signals.
    
    NO execution. NO autonomy. Pure logging.
    """
    
    def __init__(self):
        self.mission_store = get_mission_store()
        self.memory = memory
    
    def emit_proposal(self, draft: MissionDraft) -> dict:
        """
        Emit a mission proposal to Firebase and signals.
        
        Args:
            draft: MissionDraft to emit
            
        Returns:
            dict with emission results
        """
        # Create mission object
        mission = Mission(
            mission_id=draft.mission_id,
            event_type='mission_proposed',
            status='proposed',
            objective={
                'type': draft.objective_type,
                'description': draft.objective_description,
                'target_count': draft.target_count,
            },
            scope={
                'allowed_domains': draft.allowed_domains,
                'max_pages': draft.max_pages,
                'max_duration_seconds': draft.max_duration_seconds,
            },
            metadata={
                'created_at': draft.created_at,
                'raw_chat_message': draft.raw_chat_message,
                'intent_keywords': draft.intent_keywords,
                'awaiting_approval': True,
                'source': 'chat',
            }
        )
        
        # Write to Firebase mission store
        self.mission_store.write_mission_event(mission)
        
        # Emit learning signal to Firebase memory
        signal = self._create_proposal_signal(draft)
        signal_key = f"mission_proposed:{draft.mission_id}"
        self.memory.safe_call("set", signal_key, signal)
        
        # WIRING FIX 2: Emit mission_status_update signal so whiteboard can see it
        status_update = self._create_status_update_signal(draft, 'proposed')
        status_key = f"mission_status:{draft.mission_id}:proposed"
        self.memory.safe_call("set", status_key, status_update)
        
        return {
            'success': True,
            'mission_id': draft.mission_id,
            'status': 'proposed',
            'storage': 'firebase:missions',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _create_proposal_signal(self, draft: MissionDraft) -> dict:
        """
        Create learning signal for mission proposal.
        
        Signal type: mission_proposed
        """
        return {
            'signal_type': 'mission_proposed',
            'signal_layer': 'mission',
            'signal_source': 'chat_intake',
            'mission_id': draft.mission_id,
            'objective_type': draft.objective_type,
            'objective_description': draft.objective_description,
            'source': 'chat',
            'status': 'proposed',
            'awaiting_approval': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _create_status_update_signal(self, draft: MissionDraft, status: str) -> dict:
        """
        Create mission_status_update signal for whiteboard reconstruction.
        
        WIRING FIX 2: This signal is required for whiteboard to see missions.
        Whiteboard reconstructs mission history by reading mission_status_update events.
        
        Signal type: mission_status_update
        """
        return {
            'signal_type': 'mission_status_update',
            'signal_layer': 'mission',
            'signal_source': 'orchestrator',
            'mission_id': draft.mission_id,
            'status': status,
            'source': 'chat',
            'objective_type': draft.objective_type,
            'objective_description': draft.objective_description,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def get_proposed_missions(self) -> list:
        """
        Load all proposed missions from Firebase MissionStore.
        
        Returns list of proposed missions awaiting approval.
        """
        missions = self.mission_store.list_missions(status='proposed')
        return [m.to_dict() for m in missions]


# Convenience function
def emit_mission_proposal(draft: MissionDraft) -> dict:
    """Emit a mission proposal."""
    emitter = MissionProposalEmitter()
    return emitter.emit_proposal(draft)

