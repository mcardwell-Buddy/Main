"""
Survey Collector: Capture user satisfaction after mission completion.

PHASE 4: Mission Completion Survey

Collects user feedback on:
- Result quality (Did you get what you wanted?)
- Execution speed (Was it fast enough?)
- Tool choice (Was the right tool used?)
- Overall satisfaction (Would you use again?)

Responses feed back into learning signals to improve future executions.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class SurveyQuestion:
    """Represents a single survey question."""
    
    def __init__(
        self,
        question_id: str,
        question_text: str,
        question_type: str,  # 'rating' (1-5), 'yesno', 'text', 'multiple_choice'
        required: bool = True,
        options: Optional[List[str]] = None
    ):
        self.question_id = question_id
        self.question_text = question_text
        self.question_type = question_type
        self.required = required
        self.options = options or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'question_id': self.question_id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'required': self.required,
            'options': self.options
        }


class MissionSurvey:
    """Response to a mission completion survey."""
    
    def __init__(
        self,
        mission_id: str,
        result_quality_score: int,  # 1-5
        execution_speed_score: int,  # 1-5
        tool_appropriateness_score: int,  # 1-5
        overall_satisfaction_score: int,  # 1-5
        would_use_again: bool,
        improvement_suggestions: Optional[str] = None,
        additional_notes: Optional[str] = None
    ):
        self.mission_id = mission_id
        self.result_quality_score = result_quality_score
        self.execution_speed_score = execution_speed_score
        self.tool_appropriateness_score = tool_appropriateness_score
        self.overall_satisfaction_score = overall_satisfaction_score
        self.would_use_again = would_use_again
        self.improvement_suggestions = improvement_suggestions
        self.additional_notes = additional_notes
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def get_average_score(self) -> float:
        """Calculate average satisfaction score (1-5)."""
        scores = [
            self.result_quality_score,
            self.execution_speed_score,
            self.tool_appropriateness_score,
            self.overall_satisfaction_score
        ]
        return sum(scores) / len(scores) if scores else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'mission_id': self.mission_id,
            'result_quality_score': self.result_quality_score,
            'execution_speed_score': self.execution_speed_score,
            'tool_appropriateness_score': self.tool_appropriateness_score,
            'overall_satisfaction_score': self.overall_satisfaction_score,
            'would_use_again': self.would_use_again,
            'improvement_suggestions': self.improvement_suggestions,
            'additional_notes': self.additional_notes,
            'average_score': self.get_average_score(),
            'timestamp': self.timestamp
        }


class SurveyCollector:
    """
    Manages mission completion surveys and response collection.
    
    Surveys are triggered automatically after mission execution completes.
    Responses feed into learning systems to improve tool selection and execution.
    """
    
    # Standard survey questions for all missions
    STANDARD_QUESTIONS = [
        SurveyQuestion(
            question_id='result_quality',
            question_text='How satisfied are you with the result?',
            question_type='rating',
            required=True
        ),
        SurveyQuestion(
            question_id='execution_speed',
            question_text='Was the execution speed acceptable?',
            question_type='rating',
            required=True
        ),
        SurveyQuestion(
            question_id='tool_choice',
            question_text='Was the right tool selected for this task?',
            question_type='rating',
            required=True
        ),
        SurveyQuestion(
            question_id='overall_satisfaction',
            question_text='Overall, how satisfied are you?',
            question_type='rating',
            required=True
        ),
        SurveyQuestion(
            question_id='would_use_again',
            question_text='Would you use this capability again?',
            question_type='yesno',
            required=True
        ),
        SurveyQuestion(
            question_id='improvements',
            question_text='What could we improve? (optional)',
            question_type='text',
            required=False
        ),
        SurveyQuestion(
            question_id='additional_notes',
            question_text='Any other feedback? (optional)',
            question_type='text',
            required=False
        ),
    ]
    
    def __init__(self, mission_store):
        self.mission_store = mission_store
        self._survey_cache: Dict[str, MissionSurvey] = {}
    
    def get_survey_questions(self) -> List[Dict[str, Any]]:
        """
        Get survey questions to present to user.
        
        Returns:
            List of question dictionaries
        """
        return [q.to_dict() for q in self.STANDARD_QUESTIONS]
    
    def submit_survey_response(
        self,
        mission_id: str,
        result_quality: int,
        execution_speed: int,
        tool_appropriateness: int,
        overall_satisfaction: int,
        would_use_again: bool,
        improvements: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Submit completed survey response.
        
        Args:
            mission_id: Mission being surveyed
            result_quality: 1-5 rating
            execution_speed: 1-5 rating
            tool_appropriateness: 1-5 rating
            overall_satisfaction: 1-5 rating
            would_use_again: True/False
            improvements: Optional improvement suggestions
            notes: Optional additional notes
        
        Returns:
            True if successfully saved
        """
        try:
            # Validate scores
            for score in [result_quality, execution_speed, tool_appropriateness, overall_satisfaction]:
                if not (1 <= score <= 5):
                    logger.error(f"Invalid score: {score} (must be 1-5)")
                    return False
            
            survey = MissionSurvey(
                mission_id=mission_id,
                result_quality_score=result_quality,
                execution_speed_score=execution_speed,
                tool_appropriateness_score=tool_appropriateness,
                overall_satisfaction_score=overall_satisfaction,
                would_use_again=would_use_again,
                improvement_suggestions=improvements,
                additional_notes=notes
            )
            
            # Save to Firestore
            self.mission_store.save_mission_survey(survey)
            
            # Update cache
            self._survey_cache[mission_id] = survey
            
            avg_score = survey.get_average_score()
            logger.info(
                f"[SURVEY] Saved response for {mission_id}: "
                f"avg_score={avg_score:.1f}/5.0, would_use_again={would_use_again}"
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to submit survey: {e}")
            return False
    
    def get_survey_response(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Get survey response for a mission.
        
        Returns:
            Survey response dict, or None if not completed
        """
        # Check cache first
        if mission_id in self._survey_cache:
            return self._survey_cache[mission_id].to_dict()
        
        # Query Firestore
        try:
            survey = self.mission_store.get_mission_survey(mission_id)
            if survey:
                self._survey_cache[mission_id] = survey
                return survey.to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get survey: {e}")
            return None
    
    def get_survey_summary(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get aggregate statistics from all surveys.
        
        Returns:
        {
            'total_surveys': 100,
            'avg_result_quality': 4.2,
            'avg_execution_speed': 4.5,
            'avg_tool_appropriateness': 4.1,
            'avg_overall_satisfaction': 4.3,
            'would_use_again_percentage': 92.0,
            'result_quality_distribution': {1: 2, 2: 1, 3: 5, 4: 30, 5: 62},
            '...': '...'
        }
        """
        try:
            surveys = self.mission_store.get_all_mission_surveys(limit=limit)
            
            if not surveys:
                return {
                    'total_surveys': 0,
                    'message': 'No surveys collected yet'
                }
            
            total = len(surveys)
            sum_quality = sum(s['result_quality_score'] for s in surveys)
            sum_speed = sum(s['execution_speed_score'] for s in surveys)
            sum_tool = sum(s['tool_appropriateness_score'] for s in surveys)
            sum_satisfaction = sum(s['overall_satisfaction_score'] for s in surveys)
            would_use_count = sum(1 for s in surveys if s.get('would_use_again'))
            
            # Distribution analysis
            def get_distribution(key):
                dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for s in surveys:
                    score = s.get(key, 3)
                    if score in dist:
                        dist[score] += 1
                return dist
            
            return {
                'total_surveys': total,
                'avg_result_quality': round(sum_quality / total, 2),
                'avg_execution_speed': round(sum_speed / total, 2),
                'avg_tool_appropriateness': round(sum_tool / total, 2),
                'avg_overall_satisfaction': round(sum_satisfaction / total, 2),
                'would_use_again_percentage': round(would_use_count / total * 100, 1),
                'result_quality_distribution': get_distribution('result_quality_score'),
                'execution_speed_distribution': get_distribution('execution_speed_score'),
                'tool_appropriateness_distribution': get_distribution('tool_appropriateness_score'),
                'overall_satisfaction_distribution': get_distribution('overall_satisfaction_score'),
            }
        except Exception as e:
            logger.error(f"Failed to get survey summary: {e}")
            return {'error': str(e)}
    
    def clear_cache(self) -> None:
        """Clear survey cache (useful for testing)."""
        self._survey_cache.clear()
        logger.debug("[SURVEY] Cleared cache")


def get_survey_collector():
    """Get singleton SurveyCollector instance."""
    from Back_End.mission_store import get_mission_store
    
    if not hasattr(get_survey_collector, '_instance'):
        get_survey_collector._instance = SurveyCollector(
            mission_store=get_mission_store()
        )
    
    return get_survey_collector._instance
