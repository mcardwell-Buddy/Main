"""
Mission Approval Service

Implements approval gate for mission lifecycle.

Responsibility:
- Transition missions from proposed → approved
- Write exactly ONE status update event to Firebase
- NO execution, NO tool selection, NO side effects

Invariant:
Each approval call writes ONE event to Firebase MissionStore
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from backend.mission_store import get_mission_store, Mission

logger = logging.getLogger(__name__)


class MissionApprovalService:
    """
    Approves missions, transitioning proposed → approved.
    
    Does NOT execute, does NOT select tools.
    Pure state transition.
    """
    
    def __init__(self):
        self.mission_store = get_mission_store()
    
    def approve_mission(self, mission_id: str) -> Dict[str, Any]:
        """
        Approve a mission, transitioning from proposed → approved.
        
        Args:
            mission_id: Mission to approve
            
        Returns:
            {
                'success': bool,
                'mission_id': str,
                'status': str,
                'message': str
            }
        """
        logger.info(f"[APPROVAL] Approving mission: {mission_id}")
        
        # Step 1: Verify mission exists and is in proposed state
        mission_record = self.mission_store.find_mission(mission_id)
        
        if not mission_record:
            logger.error(f"[APPROVAL] Mission not found: {mission_id}")
            return {
                'success': False,
                'mission_id': mission_id,
                'status': 'error',
                'message': f'Mission {mission_id} not found'
            }
        
        current_status = mission_record.status
        if current_status != 'proposed':
            logger.error(
                f"[APPROVAL] Mission {mission_id} is not in proposed state. "
                f"Current status: {current_status}"
            )
            return {
                'success': False,
                'mission_id': mission_id,
                'status': 'error',
                'message': f'Mission is in state "{current_status}", not "proposed"'
            }
        
        # Step 2: Write status update event (exactly ONE) to Firebase
        try:
            approval_event = Mission(
                mission_id=mission_id,
                event_type='mission_status_update',
                status='approved',
                objective=mission_record.objective,
                metadata={'reason': 'user_approval'},
                scope=mission_record.scope
            )
            
            self.mission_store.write_mission_event(approval_event)
            logger.info(f"[APPROVAL] Mission {mission_id} approved")
            
            return {
                'success': True,
                'mission_id': mission_id,
                'status': 'approved',
                'message': f'Mission {mission_id} approved successfully'
            }
        
        except Exception as e:
            logger.error(f"[APPROVAL] Error approving mission {mission_id}: {e}", exc_info=True)
            return {
                'success': False,
                'mission_id': mission_id,
                'status': 'error',
                'message': f'Error approving mission: {str(e)}'
            }


# Singleton instance
_approval_service = None


def get_approval_service():
    """Get or create approval service singleton."""
    global _approval_service
    if _approval_service is None:
        _approval_service = MissionApprovalService()
    return _approval_service


def approve_mission(mission_id: str) -> Dict[str, Any]:
    """
    Approve a mission via singleton service.
    
    Args:
        mission_id: Mission to approve
        
    Returns:
        Result dict
    """
    service = get_approval_service()
    return service.approve_mission(mission_id)
