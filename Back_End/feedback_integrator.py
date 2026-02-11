"""
Feedback Integrator: Connect mission outcomes to tool selection learning.

Tracks which tools work best for different mission types, applies learnings
to improve future tool selection confidence scores.

PHASE 3: Feedback → Tool Selection

Example:
- Mission 1: Find Python tutorials → web_search (success ✅)
- Mission 2: Find Python tutorials → web_search (success ✅)
→ Future Python tutorial queries: +15% confidence for web_search
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class MissionFeedback:
    """Captures outcome feedback from a completed mission."""
    
    def __init__(
        self,
        mission_id: str,
        tool_used: str,
        mission_type: str,  # e.g., 'web_search_tutorial', 'code_calculation', etc.
        success: bool,
        confidence_before: float,
        execution_time_seconds: float,
        user_satisfaction: Optional[float] = None,  # 0-5 scale
        notes: Optional[str] = None
    ):
        self.mission_id = mission_id
        self.tool_used = tool_used
        self.mission_type = mission_type
        self.success = success
        self.confidence_before = confidence_before
        self.execution_time_seconds = execution_time_seconds
        self.user_satisfaction = user_satisfaction
        self.notes = notes
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'mission_id': self.mission_id,
            'tool_used': self.tool_used,
            'mission_type': self.mission_type,
            'success': self.success,
            'confidence_before': self.confidence_before,
            'execution_time_seconds': self.execution_time_seconds,
            'user_satisfaction': self.user_satisfaction,
            'notes': self.notes,
            'timestamp': self.timestamp
        }


class FeedbackIntegrator:
    """
    Integrate mission outcomes back into tool selection.
    
    Maintains tool success rates by mission type:
    - web_search: [success_rate: 0.92, avg_time: 2.5s, count: 50]
    - calculate: [success_rate: 0.99, avg_time: 0.8s, count: 150]
    - etc.
    
    Applies learnings to tool_selector via multiplier:
    - High success rate (>90%) → +20% confidence boost
    - Medium success rate (70-90%) → +5% confidence boost
    - Low success rate (<70%) → -15% confidence penalty
    """
    
    def __init__(self, mission_store, feedback_manager):
        self.mission_store = mission_store
        self.feedback_manager = feedback_manager
        self._stats_cache: Dict[str, Dict[str, Any]] = {}  # mission_type → stats
    
    def record_mission_outcome(
        self,
        mission_id: str,
        tool_used: str,
        mission_type: str,
        success: bool,
        confidence: float,
        execution_time: float,
        user_satisfaction: Optional[float] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Record outcome of a completed mission.
        
        Args:
            mission_id: Mission that completed
            tool_used: Tool that was selected
            mission_type: Type of mission (extracted from objective)
            success: Whether execution succeeded
            confidence: Original tool confidence before execution
            execution_time: Time mission took in seconds
            user_satisfaction: Optional user rating (0-5)
            notes: Optional notes about the outcome
        
        Returns:
            True if successfully recorded
        """
        try:
            feedback = MissionFeedback(
                mission_id=mission_id,
                tool_used=tool_used,
                mission_type=mission_type,
                success=success,
                confidence_before=confidence,
                execution_time_seconds=execution_time,
                user_satisfaction=user_satisfaction,
                notes=notes
            )
            
            # Save to Firestore
            self.mission_store.save_mission_feedback(feedback)
            
            # Clear stats cache for this type (will be recalculated on next access)
            self._stats_cache.pop(mission_type, None)
            
            logger.info(
                f"[FEEDBACK] Recorded outcome for {mission_id}: "
                f"{tool_used} on {mission_type} ({'✅' if success else '❌'})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to record mission outcome: {e}")
            return False
    
    def get_tool_confidence_multiplier(
        self,
        tool_name: str,
        mission_type: str
    ) -> float:
        """
        Get confidence multiplier for a tool based on historical success.
        
        Returns:
            1.0: No adjustment
            > 1.0: Boost confidence (e.g., 1.15 = +15%)
            < 1.0: Reduce confidence (e.g., 0.85 = -15%)
        
        Example:
            multiplier = integrator.get_tool_confidence_multiplier(
                'web_search', 'python_tutorial'
            )
            new_confidence = 0.80 * multiplier  # Adjust confidence
        """
        try:
            stats = self.get_tool_stats(tool_name, mission_type)
            
            if stats['count'] < 3:
                # Not enough data yet, no adjustment
                return 1.0
            
            success_rate = stats['success_rate']
            
            # Confidence multiplier based on success rate
            if success_rate >= 0.95:
                # Very high success: strong boost
                return 1.25
            elif success_rate >= 0.90:
                # High success: moderate boost
                return 1.20
            elif success_rate >= 0.80:
                # Good success: small boost
                return 1.10
            elif success_rate >= 0.70:
                # Acceptable success: minimal boost
                return 1.05
            elif success_rate >= 0.50:
                # Below average: slight penalty
                return 0.90
            else:
                # Poor success: strong penalty
                return 0.70
        
        except Exception as e:
            logger.warning(f"Failed to calculate multiplier: {e}")
            return 1.0  # Default: no adjustment
    
    def get_tool_stats(
        self,
        tool_name: str,
        mission_type: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get statistics for a tool on a mission type (recent data).
        
        Returns:
        {
            'tool': 'web_search',
            'mission_type': 'python_tutorial',
            'count': 12,
            'success_count': 11,
            'success_rate': 0.917,
            'avg_execution_time': 2.3,
            'avg_satisfaction': 4.2,
            'period_days': 30,
            'last_used': '2026-02-11T14:30:00Z'
        }
        """
        cache_key = f"{tool_name}:{mission_type}"
        if cache_key in self._stats_cache:
            return self._stats_cache[cache_key]
        
        try:
            feedbacks = self.mission_store.get_mission_feedbacks(
                tool=tool_name,
                mission_type=mission_type,
                days=days
            )
            
            if not feedbacks:
                result = {
                    'tool': tool_name,
                    'mission_type': mission_type,
                    'count': 0,
                    'success_count': 0,
                    'success_rate': 0.5,  # Neutral default
                    'avg_execution_time': 0.0,
                    'avg_satisfaction': None,
                    'period_days': days,
                    'last_used': None
                }
            else:
                success_count = sum(1 for f in feedbacks if f.get('success'))
                total_count = len(feedbacks)
                total_time = sum(f.get('execution_time_seconds', 0) for f in feedbacks)
                satisfactions = [f.get('user_satisfaction') for f in feedbacks 
                               if f.get('user_satisfaction') is not None]
                
                result = {
                    'tool': tool_name,
                    'mission_type': mission_type,
                    'count': total_count,
                    'success_count': success_count,
                    'success_rate': success_count / total_count if total_count > 0 else 0.5,
                    'avg_execution_time': total_time / total_count if total_count > 0 else 0.0,
                    'avg_satisfaction': sum(satisfactions) / len(satisfactions) if satisfactions else None,
                    'period_days': days,
                    'last_used': feedbacks[-1].get('timestamp') if feedbacks else None
                }
            
            # Cache result for 5 minutes
            self._stats_cache[cache_key] = result
            return result
        
        except Exception as e:
            logger.error(f"Failed to get tool stats: {e}")
            return {
                'tool': tool_name,
                'mission_type': mission_type,
                'count': 0,
                'success_rate': 0.5,
                'error': str(e)
            }
    
    def get_top_tools_for_mission_type(
        self,
        mission_type: str,
        limit: int = 3,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get highest-performing tools for a mission type.
        
        Returns:
            List of tools sorted by success rate, ranked by performance
        """
        try:
            # Get all tool feedback for this mission type
            feedbacks = self.mission_store.get_mission_feedbacks(
                mission_type=mission_type,
                days=days
            )
            
            # Group by tool and calculate stats
            tool_stats: Dict[str, Dict[str, Any]] = {}
            for f in feedbacks:
                tool = f.get('tool_used')
                if tool not in tool_stats:
                    tool_stats[tool] = {
                        'tool': tool,
                        'count': 0,
                        'success_count': 0,
                        'total_time': 0.0,
                        'satisfactions': []
                    }
                
                tool_stats[tool]['count'] += 1
                if f.get('success'):
                    tool_stats[tool]['success_count'] += 1
                tool_stats[tool]['total_time'] += f.get('execution_time_seconds', 0)
                if f.get('user_satisfaction'):
                    tool_stats[tool]['satisfactions'].append(f['user_satisfaction'])
            
            # Calculate rates and convert to results
            results = []
            for tool, stats in tool_stats.items():
                results.append({
                    'tool': tool,
                    'success_rate': stats['success_count'] / stats['count'] if stats['count'] > 0 else 0,
                    'usage_count': stats['count'],
                    'avg_execution_time': stats['total_time'] / stats['count'] if stats['count'] > 0 else 0,
                    'avg_satisfaction': (
                        sum(stats['satisfactions']) / len(stats['satisfactions'])
                        if stats['satisfactions'] else None
                    )
                })
            
            # Sort by success rate descending
            results.sort(key=lambda x: x['success_rate'], reverse=True)
            
            logger.info(
                f"[FEEDBACK] Top tools for '{mission_type}': "
                f"{[r['tool'] for r in results[:limit]]}"
            )
            
            return results[:limit]
        
        except Exception as e:
            logger.error(f"Failed to get top tools: {e}")
            return []
    
    def clear_cache(self) -> None:
        """Clear stats cache (useful for testing)."""
        self._stats_cache.clear()
        logger.debug("[FEEDBACK] Cleared stats cache")


def get_feedback_integrator():
    """Get singleton FeedbackIntegrator instance."""
    from Back_End.mission_store import get_mission_store
    from Back_End.feedback_manager import feedback_manager
    
    if not hasattr(get_feedback_integrator, '_instance'):
        get_feedback_integrator._instance = FeedbackIntegrator(
            mission_store=get_mission_store(),
            feedback_manager=feedback_manager
        )
    
    return get_feedback_integrator._instance
