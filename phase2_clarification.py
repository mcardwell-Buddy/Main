"""
================================================================================
PHASE 2: CLARIFICATION HANDLING SYSTEM
================================================================================

Purpose: For ambiguous goals (<0.55 confidence), generate clarification
questions to help user provide missing context.

Reference: PHASE_2_DESIGN_DOCUMENT.md - Section 5

Clarification Flow:
  1. Detect ambiguous goal (confidence < 0.55 OR goal_understanding < 0.3)
  2. Generate targeted clarification questions
  3. Validate questions with Soul
  4. Send to user
  5. Process response and recalculate confidence
  6. Proceed with approval gates if confidence improves

Question Patterns:
  - Action Identification: What specific action?
  - Target Identification: What to target?
  - Context Identification: What context needed?
  - Success Criteria: How to know if it worked?
  - Constraints: Any constraints/preferences?
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid


class ClarificationPattern(Enum):
    """Types of clarification question patterns."""
    ACTION_IDENTIFICATION = "action_identification"
    TARGET_IDENTIFICATION = "target_identification"
    CONTEXT_IDENTIFICATION = "context_identification"
    SUCCESS_CRITERIA = "success_criteria"
    CONSTRAINTS = "constraints"


@dataclass
class ClarificationQuestion:
    """Single clarification question."""
    index: int
    question: str
    pattern: ClarificationPattern
    required: bool = True
    examples: List[str] = field(default_factory=list)


@dataclass
class ClarificationRequest:
    """Request for clarification sent to user."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_goal: str = ""
    ambiguity_reason: str = ""
    questions: List[ClarificationQuestion] = field(default_factory=list)
    time_limit_seconds: int = 300
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            'request_id': self.request_id,
            'original_goal': self.original_goal,
            'ambiguity_reason': self.ambiguity_reason,
            'questions': [
                {
                    'index': q.index,
                    'question': q.question,
                    'pattern': q.pattern.value,
                    'required': q.required,
                    'examples': q.examples,
                }
                for q in self.questions
            ],
            'time_limit_seconds': self.time_limit_seconds,
        }


@dataclass
class ClarificationResponse:
    """Response to clarification questions from user."""
    request_id: str
    answers: Dict[int, str] = field(default_factory=dict)  # question_index -> answer
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            'request_id': self.request_id,
            'answers': self.answers,
        }


class ClarificationGenerator:
    """
    Generate targeted clarification questions based on ambiguity type.
    
    Usage:
        generator = ClarificationGenerator()
        
        request = generator.generate_clarification(
            goal="Help me",
            confidence=0.2,
            goal_understanding=0.1,
        )
        
        # User responds
        response = ClarificationResponse(
            request_id=request.request_id,
            answers={
                0: "Click the save button",
                1: "The button is in the bottom right",
            }
        )
        
        # Clarification is processed and goal is re-evaluated
    """
    
    def generate_clarification(
        self,
        goal: str,
        confidence: float = 0.0,
        goal_understanding: float = 0.0,
    ) -> ClarificationRequest:
        """
        Generate clarification questions for ambiguous goal.
        
        Args:
            goal: User's ambiguous goal
            confidence: Current confidence score
            goal_understanding: Goal understanding factor
        
        Returns:
            ClarificationRequest with targeted questions
        """
        questions = []
        reason = self._analyze_ambiguity(goal, goal_understanding)
        
        # Always ask what action
        questions.append(
            ClarificationQuestion(
                index=0,
                question=(
                    "What specific action would you like me to perform? "
                    "(e.g., click a button, analyze code, generate text)"
                ),
                pattern=ClarificationPattern.ACTION_IDENTIFICATION,
                required=True,
                examples=[
                    "Click the submit button",
                    "Analyze this code for bugs",
                    "Generate a test case",
                ],
            )
        )
        
        # Ask for target/context
        if not self._has_target_specificity(goal):
            questions.append(
                ClarificationQuestion(
                    index=1,
                    question=(
                        "What is the target? Please provide location or context. "
                        "(e.g., 'the button in the top-right', 'the function on line 42')"
                    ),
                    pattern=ClarificationPattern.TARGET_IDENTIFICATION,
                    required=True,
                    examples=[
                        "The button in the bottom right corner",
                        "The function at the top of the file",
                        "The text input labeled 'Email'",
                    ],
                )
            )
        
        # Ask for missing context
        if not self._has_context_provided(goal):
            questions.append(
                ClarificationQuestion(
                    index=2,
                    question=(
                        "What context should I use? "
                        "Please provide code, data, or other relevant information."
                    ),
                    pattern=ClarificationPattern.CONTEXT_IDENTIFICATION,
                    required=False,
                    examples=[
                        "Here's the function to refactor: def foo(): ...",
                        "The data to analyze is in this CSV: ...",
                    ],
                )
            )
        
        # Ask for expected outcome
        questions.append(
            ClarificationQuestion(
                index=3,
                question=(
                    "How will I know if it's working correctly? "
                    "What's the expected result?"
                ),
                pattern=ClarificationPattern.SUCCESS_CRITERIA,
                required=False,
                examples=[
                    "The button should become highlighted",
                    "Should return a list of bugs found",
                    "The error message should disappear",
                ],
            )
        )
        
        # Ask for constraints
        questions.append(
            ClarificationQuestion(
                index=4,
                question=(
                    "Are there any constraints or preferences? "
                    "(e.g., use specific library, don't modify certain files)"
                ),
                pattern=ClarificationPattern.CONSTRAINTS,
                required=False,
                examples=[
                    "Use only built-in Python libraries",
                    "Don't modify the config file",
                    "Must work offline",
                ],
            )
        )
        
        return ClarificationRequest(
            original_goal=goal,
            ambiguity_reason=reason,
            questions=questions,
        )
    
    @staticmethod
    def _analyze_ambiguity(goal: str, goal_understanding: float) -> str:
        """Determine why goal is ambiguous."""
        goal_lower = goal.lower()
        
        if goal_understanding < 0.2:
            return "Goal is very vague with no clear action or target"
        elif goal_understanding < 0.4:
            return "Goal is unclear - missing specific action or target"
        elif goal_understanding < 0.6:
            return "Goal has ambiguity - could be interpreted multiple ways"
        else:
            return "Goal needs additional context for execution"
    
    @staticmethod
    def _has_target_specificity(goal: str) -> bool:
        """Check if goal specifies a target."""
        target_keywords = {
            'button', 'input', 'function', 'variable', 'file', 'element',
            'line', 'section', 'class', 'method', 'field', 'attribute'
        }
        return any(keyword in goal.lower() for keyword in target_keywords)
    
    @staticmethod
    def _has_context_provided(goal: str) -> bool:
        """Check if goal provides context (code, data, etc.)."""
        # Simple heuristic: if goal has code-like syntax
        if '{' in goal or '(' in goal or '=' in goal:
            return True
        return False


class ClarificationProcessor:
    """
    Process clarification responses and update goal.
    
    Usage:
        processor = ClarificationProcessor()
        
        response = ClarificationResponse(
            request_id="req_123",
            answers={
                0: "Click the save button",
                1: "Button is in bottom right",
            }
        )
        
        updated_goal = processor.build_clarified_goal(
            original_goal="Help me",
            response=response,
        )
        # Returns: "Click the save button that is in the bottom right"
    """
    
    def build_clarified_goal(
        self,
        original_goal: str,
        response: ClarificationResponse,
    ) -> str:
        """
        Rebuild goal using user's clarification answers.
        
        Args:
            original_goal: Original ambiguous goal
            response: User's answers to clarification questions
        
        Returns:
            Clarified goal string
        """
        parts = []
        
        # Action (usually index 0)
        if 0 in response.answers:
            parts.append(response.answers[0])
        
        # Target (usually index 1)
        if 1 in response.answers:
            target = response.answers[1]
            if target and len(parts) > 0:
                parts[-1] += f" {target}"  # Append to action
        
        # Constraints (usually index 4)
        if 4 in response.answers:
            constraints = response.answers[4]
            if constraints:
                parts.append(f"with constraints: {constraints}")
        
        # Join into coherent goal
        clarified_goal = " ".join(parts) if parts else original_goal
        
        return clarified_goal
    
    def merge_context(
        self,
        goal: str,
        response: ClarificationResponse,
    ) -> Dict[str, Any]:
        """
        Extract context from clarification response.
        
        Args:
            goal: Current goal
            response: User's answers
        
        Returns:
            Dict with context_data and updated_goal
        """
        context_data = {}
        
        # Context (usually index 2)
        if 2 in response.answers:
            context_data['provided_context'] = response.answers[2]
        
        # Success criteria (usually index 3)
        if 3 in response.answers:
            context_data['success_criteria'] = response.answers[3]
        
        # Build clarified goal
        clarified_goal = self.build_clarified_goal(goal, response)
        
        return {
            'goal': clarified_goal,
            'context': context_data,
        }


class ClarificationValidator:
    """
    Validate clarification questions before sending to user.
    
    Used to ensure questions are:
    - Clear and actionable
    - Not redundant
    - Appropriate for the ambiguity
    """
    
    def validate_questions(
        self,
        questions: List[ClarificationQuestion],
        goal: str,
    ) -> Dict[str, Any]:
        """
        Validate clarification questions.
        
        Args:
            questions: List of questions to validate
            goal: Original goal for context
        
        Returns:
            Dict with valid=True/False, approved_indices, feedback
        """
        approved_indices = []
        issues = []
        
        for q in questions:
            # Check question is not empty
            if not q.question or len(q.question) < 10:
                issues.append(f"Q{q.index}: Question is too short")
                continue
            
            # Check question is not redundant
            if self._is_redundant(q.question, questions[:q.index]):
                issues.append(f"Q{q.index}: Question is redundant")
                continue
            
            # Check question is appropriate for goal
            if not self._is_appropriate(q.pattern, goal):
                issues.append(f"Q{q.index}: Question may not be appropriate for goal")
                continue
            
            approved_indices.append(q.index)
        
        return {
            'valid': len(issues) == 0,
            'approved_indices': approved_indices,
            'issues': issues,
            'feedback': "All questions are valid" if not issues else f"{len(issues)} issues found",
        }
    
    @staticmethod
    def _is_redundant(question: str, prior_questions: List[ClarificationQuestion]) -> bool:
        """Check if question is redundant with prior ones."""
        for prior in prior_questions:
            # Simple: check if patterns are same
            if prior.pattern == ClarificationPattern.ACTION_IDENTIFICATION:
                if 'action' in question.lower():
                    return True
        return False
    
    @staticmethod
    def _is_appropriate(
        pattern: ClarificationPattern,
        goal: str,
    ) -> bool:
        """Check if question pattern is appropriate for goal."""
        # All patterns are generally appropriate; could add heuristics here
        return True


# =============================================================================
# EXAMPLES FOR TESTING
# =============================================================================

def example_clarification_generation():
    """Example: Generate clarification for ambiguous goal."""
    generator = ClarificationGenerator()
    
    request = generator.generate_clarification(
        goal="Help me",
        confidence=0.2,
        goal_understanding=0.1,
    )
    
    print("CLARIFICATION REQUEST GENERATED:")
    print(f"  Request ID: {request.request_id}")
    print(f"  Original Goal: {request.original_goal}")
    print(f"  Ambiguity Reason: {request.ambiguity_reason}")
    print(f"  Questions:")
    for q in request.questions:
        print(f"    {q.index}. {q.question}")
        if q.examples:
            print(f"       Examples: {', '.join(q.examples)}")
    return request


def example_clarification_response():
    """Example: Process clarification response."""
    processor = ClarificationProcessor()
    
    response = ClarificationResponse(
        request_id="req_123",
        answers={
            0: "Click the save button",
            1: "The button is in the bottom right corner",
            3: "The button should become highlighted",
        }
    )
    
    result = processor.merge_context(
        goal="Help me",
        response=response,
    )
    
    print("\nCLARIFICATION RESPONSE PROCESSED:")
    print(f"  Original Goal: Help me")
    print(f"  Clarified Goal: {result['goal']}")
    print(f"  Context:")
    for key, value in result['context'].items():
        print(f"    {key}: {value}")
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("CLARIFICATION HANDLING SYSTEM - EXAMPLES")
    print("=" * 70)
    
    example_clarification_generation()
    example_clarification_response()

