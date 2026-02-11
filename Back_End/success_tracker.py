"""
Success Tracker: Measures whether Buddy's solutions actually work.

This is the critical feedback loop that drives improvement.
Success = does the solution actually solve the user's problem?
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from Back_End.memory import memory

logger = logging.getLogger(__name__)


class SuccessTracker:
    """Tracks goal success with multiple dimensions of measurement"""
    
    def __init__(self):
        self.collection_key = "goal_success"
    
    def record_goal(self, goal: str, domain: str = "general", initial_confidence: float = 0.5) -> Dict:
        """
        Record a new goal being attempted.
        
        Returns goal_id for tracking through completion.
        """
        goal_id = f"goal_{datetime.utcnow().timestamp()}"
        
        record = {
            "id": goal_id,
            "goal": goal,
            "domain": domain,
            "created_at": datetime.utcnow().isoformat(),
            "initial_confidence": initial_confidence,
            "status": "in_progress",  # in_progress, completed, abandoned
            "agent_response": None,
            "response_received_at": None,
            "user_feedback": None,
            "user_feedback_at": None,
            "success_score": None,  # 0-1: aggregate success rating
            "success_metrics": {
                "helpfulness": None,  # 1-5: was response helpful?
                "accuracy": None,     # 1-5: was response accurate?
                "completeness": None, # 1-5: did it fully answer the question?
                "actionability": None,# 1-5: can user act on it?
                "code_quality": None, # 1-5: (for builds) was code working?
            },
            "notes": ""
        }
        
        # Store in memory
        key = f"{self.collection_key}"
        goals = memory.safe_call('get', key) or []
        goals.append(record)
        memory.safe_call('set', key, goals)
        
        logger.info(f"✓ Recorded goal: {goal_id} - {goal[:50]}")
        return record
    
    def record_response(self, goal_id: str, response: str, 
                       tools_used: List[str], tools_count: int) -> Dict:
        """
        Record Buddy's response to a goal.
        """
        goals = memory.safe_call('get', f"{self.collection_key}") or []
        
        for goal in goals:
            if goal['id'] == goal_id:
                goal['agent_response'] = response
                goal['response_received_at'] = datetime.utcnow().isoformat()
                goal['response_metadata'] = {
                    'tools_used': tools_used,
                    'tools_count': tools_count,
                    'response_length': len(response),
                    'has_code': '<code>' in response or '```' in response,
                    'has_links': 'http' in response.lower()
                }
                memory.safe_call('set', f"{self.collection_key}", goals)
                logger.info(f"✓ Recorded response for goal {goal_id}")
                return goal
        
        return None
    
    def submit_feedback(self, goal_id: str, 
                       helpfulness: int = None,
                       accuracy: int = None,
                       completeness: int = None,
                       actionability: int = None,
                       code_quality: int = None,
                       notes: str = "") -> Dict:
        """
        Submit user feedback on a response (1-5 scale).
        
        This is the KEY FEEDBACK LOOP for improvement!
        """
        goals = memory.safe_call('get', f"{self.collection_key}") or []
        
        for goal in goals:
            if goal['id'] == goal_id:
                # Record feedback
                goal['success_metrics'] = {
                    "helpfulness": helpfulness,
                    "accuracy": accuracy,
                    "completeness": completeness,
                    "actionability": actionability,
                    "code_quality": code_quality,
                }
                goal['user_feedback'] = {
                    "helpfulness": helpfulness,
                    "accuracy": accuracy,
                    "completeness": completeness,
                    "actionability": actionability,
                    "code_quality": code_quality,
                    "notes": notes,
                    "submitted_at": datetime.utcnow().isoformat()
                }
                goal['user_feedback_at'] = datetime.utcnow().isoformat()
                goal['status'] = 'completed'
                
                # Calculate aggregate success score
                scores = []
                if helpfulness is not None: scores.append(helpfulness)
                if accuracy is not None: scores.append(accuracy)
                if completeness is not None: scores.append(completeness)
                if actionability is not None: scores.append(actionability)
                if code_quality is not None: scores.append(code_quality)
                
                if scores:
                    goal['success_score'] = sum(scores) / (len(scores) * 5.0)  # 0-1 scale
                    
                    # Log the outcome
                    outcome = "✓ SUCCESS" if goal['success_score'] >= 0.7 else "✗ FAILED"
                    logger.info(f"{outcome} {goal_id}: score {goal['success_score']:.2%}")
                
                memory.safe_call('set', f"{self.collection_key}", goals)
                return goal
        
        return None
    
    def get_success_stats(self, domain: str = None) -> Dict:
        """Get overall success statistics"""
        goals = memory.safe_call('get', f"{self.collection_key}") or []
        
        if domain:
            goals = [g for g in goals if g.get('domain') == domain]
        
        completed = [g for g in goals if g.get('status') == 'completed']
        
        if not completed:
            return {
                'total_goals': len(goals),
                'completed': 0,
                'success_rate': 0.0,
                'avg_helpfulness': 0.0,
                'avg_accuracy': 0.0,
                'avg_completeness': 0.0,
                'avg_actionability': 0.0,
                'avg_code_quality': 0.0,
            }
        
        success_scores = [g.get('success_score', 0) for g in completed if g.get('success_score') is not None]
        successful = len([s for s in success_scores if s >= 0.7])
        
        # Calculate averages for each metric
        helpfulness = [g['success_metrics'].get('helpfulness', 0) for g in completed if g['success_metrics'].get('helpfulness')]
        accuracy = [g['success_metrics'].get('accuracy', 0) for g in completed if g['success_metrics'].get('accuracy')]
        completeness = [g['success_metrics'].get('completeness', 0) for g in completed if g['success_metrics'].get('completeness')]
        actionability = [g['success_metrics'].get('actionability', 0) for g in completed if g['success_metrics'].get('actionability')]
        code_quality = [g['success_metrics'].get('code_quality', 0) for g in completed if g['success_metrics'].get('code_quality')]
        
        return {
            'total_goals': len(goals),
            'completed': len(completed),
            'success_rate': successful / len(success_scores) if success_scores else 0.0,
            'avg_score': sum(success_scores) / len(success_scores) if success_scores else 0.0,
            'avg_helpfulness': sum(helpfulness) / len(helpfulness) if helpfulness else 0.0,
            'avg_accuracy': sum(accuracy) / len(accuracy) if accuracy else 0.0,
            'avg_completeness': sum(completeness) / len(completeness) if completeness else 0.0,
            'avg_actionability': sum(actionability) / len(actionability) if actionability else 0.0,
            'avg_code_quality': sum(code_quality) / len(code_quality) if code_quality else 0.0,
        }
    
    def get_failed_goals(self, domain: str = None, limit: int = 5) -> List[Dict]:
        """Get goals that failed (score < 0.7) for analysis"""
        goals = memory.safe_call('get', f"{self.collection_key}") or []
        
        if domain:
            goals = [g for g in goals if g.get('domain') == domain]
        
        failed = [g for g in goals if g.get('success_score') and g['success_score'] < 0.7]
        
        # Sort by most recent
        failed.sort(key=lambda g: g.get('user_feedback_at', ''), reverse=True)
        
        return failed[:limit]
    
    def get_high_success_goals(self, domain: str = None, limit: int = 5) -> List[Dict]:
        """Get goals that succeeded (score >= 0.8) - learn from successes!"""
        goals = memory.safe_call('get', f"{self.collection_key}") or []
        
        if domain:
            goals = [g for g in goals if g.get('domain') == domain]
        
        successful = [g for g in goals if g.get('success_score') and g['success_score'] >= 0.8]
        
        # Sort by most recent
        successful.sort(key=lambda g: g.get('user_feedback_at', ''), reverse=True)
        
        return successful[:limit]
    
    def analyze_failure_patterns(self, domain: str = None) -> Dict:
        """
        Analyze what causes failures.
        
        Used by self-improvement to fix problems.
        """
        failed_goals = self.get_failed_goals(domain, limit=20)
        
        if not failed_goals:
            return {'patterns': [], 'total_failures': 0}
        
        patterns = {
            'low_helpfulness': 0,
            'low_accuracy': 0,
            'incomplete': 0,
            'not_actionable': 0,
            'bad_code': 0,
        }
        
        for goal in failed_goals:
            metrics = goal.get('success_metrics', {})
            
            if metrics.get('helpfulness') and metrics['helpfulness'] < 2.5:
                patterns['low_helpfulness'] += 1
            if metrics.get('accuracy') and metrics['accuracy'] < 2.5:
                patterns['low_accuracy'] += 1
            if metrics.get('completeness') and metrics['completeness'] < 2.5:
                patterns['incomplete'] += 1
            if metrics.get('actionability') and metrics['actionability'] < 2.5:
                patterns['not_actionable'] += 1
            if metrics.get('code_quality') and metrics['code_quality'] < 2.5:
                patterns['bad_code'] += 1
        
        return {
            'patterns': patterns,
            'total_failures': len(failed_goals),
            'failed_goals': failed_goals
        }


# Global instance
success_tracker = SuccessTracker()

