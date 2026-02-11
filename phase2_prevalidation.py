"""
================================================================================
PHASE 2: PRE-VALIDATION SYSTEM
================================================================================

Purpose: Detect impossible or risky goals BEFORE reasoning, reducing wasted
computation and providing clearer error messages.

Reference: PHASE_2_DESIGN_DOCUMENT.md - Section 6

Six Pre-Validation Checks:
  1. Required Tool Availability
  2. Element Existence (Frontend Goals)
  3. Context Availability
  4. Contradiction Detection
  5. Scope Validation
  6. Complexity Warning

Key Principle: Read-only checks only. No tool execution during validation.

Output: pre_validation_result with status, failures, confidence_delta, and
         suggested clarification questions.
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class SeverityLevel(Enum):
    """Severity levels for pre-validation failures."""
    LOW = 0.1
    MEDIUM = 0.2
    HIGH = 0.3
    CRITICAL = 0.4


@dataclass
class ValidationFailure:
    """Single pre-validation check failure."""
    check_name: str
    severity: SeverityLevel
    message: str
    confidence_delta: float  # How much to reduce confidence


@dataclass
class PreValidationResult:
    """Result of all pre-validation checks."""
    validation_status: str  # "pre_validation_passed" | "pre_validation_failed"
    checks_passed: int
    checks_failed: int
    failures: List[ValidationFailure] = field(default_factory=list)
    total_confidence_delta: float = 0.0
    final_confidence: float = 0.5  # Will be set by caller
    recommendation: str = ""  # "proceed" | "clarify" | "reject"
    suggested_questions: List[str] = field(default_factory=list)


class PreValidator:
    """
    Execute all six pre-validation checks.
    
    Usage:
        validator = PreValidator(available_tools=['button_clicker', 'element_finder'])
        result = validator.validate_goal(goal="click the button")
        
        if result.validation_status == "pre_validation_passed":
            print("Goal is valid, proceed to reasoning")
        else:
            print(f"Issues found: {result.failures}")
            print(f"Reduce confidence by: {result.total_confidence_delta}")
    """
    
    SYSTEM_SCOPE_KEYWORDS = {
        'software', 'code', 'button', 'element', 'file', 'function',
        'variable', 'database', 'api', 'test', 'debug', 'ui', 'screen',
        'interface', 'click', 'find', 'analyze', 'parse', 'compile'
    }
    
    OUT_OF_SCOPE_KEYWORDS = {
        'rocket', 'launch', 'physical', 'hardware', 'robot', 'car',
        'house', 'building', 'nuclear', 'weapon', 'dangerous'
    }
    
    def __init__(
        self,
        available_tools: List[str] = None,
        ui_schema: Dict[str, Any] = None,
    ):
        """
        Initialize pre-validator.
        
        Args:
            available_tools: List of available tool names
            ui_schema: Dict of available UI elements (for element existence check)
        """
        self.available_tools = set(available_tools or [])
        self.ui_schema = ui_schema or {}
    
    def validate_goal(
        self,
        goal: str,
        session_context: Dict[str, Any] = None,
    ) -> PreValidationResult:
        """
        Run all six pre-validation checks.
        
        Args:
            goal: User's stated goal
            session_context: Optional context dict with prior_goals, etc.
        
        Returns:
            PreValidationResult with all checks' status
        """
        session_context = session_context or {}
        result = PreValidationResult(
            validation_status="pre_validation_passed",
            checks_passed=0,
            checks_failed=0,
        )
        
        # Check 1: Required Tool Availability
        tool_failure = self._check_required_tool_availability(goal)
        if tool_failure:
            result.failures.append(tool_failure)
            result.checks_failed += 1
        else:
            result.checks_passed += 1
        
        # Check 2: Element Existence
        element_failure = self._check_element_existence(goal)
        if element_failure:
            result.failures.append(element_failure)
            result.checks_failed += 1
        else:
            result.checks_passed += 1
        
        # Check 3: Context Availability
        context_failure = self._check_context_availability(goal, session_context)
        if context_failure:
            result.failures.append(context_failure)
            result.checks_failed += 1
        else:
            result.checks_passed += 1
        
        # Check 4: Contradiction Detection
        contradiction_failure = self._check_contradictions(goal)
        if contradiction_failure:
            result.failures.append(contradiction_failure)
            result.checks_failed += 1
        else:
            result.checks_passed += 1
        
        # Check 5: Scope Validation
        scope_failure = self._check_scope_validation(goal)
        if scope_failure:
            result.failures.append(scope_failure)
            result.checks_failed += 1
        else:
            result.checks_passed += 1
        
        # Check 6: Complexity Warning
        complexity_failure = self._check_complexity_warning(goal)
        if complexity_failure:
            result.failures.append(complexity_failure)
            result.checks_failed += 1
        else:
            result.checks_passed += 1
        
        # Calculate total confidence delta
        result.total_confidence_delta = sum(f.confidence_delta for f in result.failures)
        
        # Determine overall status and recommendation
        if result.checks_failed > 0:
            result.validation_status = "pre_validation_failed"
            result.recommendation = self._determine_recommendation(result)
            result.suggested_questions = self._generate_suggested_questions(result)
        
        return result
    
    def _check_required_tool_availability(self, goal: str) -> ValidationFailure or None:
        """
        Check 1: Required Tool Availability
        
        Detect: If goal explicitly mentions a tool name with "tool" or "using", verify it exists.
        Example: "Use the ImageEditor tool" → check if ImageEditor exists
                 "Using CompilerTool" → check if CompilerTool exists
        """
        goal_lower = goal.lower()
        
        # Only check for tool names when goal explicitly mentions using a tool
        tool_indicators = ['tool', 'using', 'with the', 'use the']
        if not any(indicator in goal_lower for indicator in tool_indicators):
            return None
        
        # Extract tool names (capitalized words that come after tool indicators)
        words = goal.split()
        for i, word in enumerate(words):
            word_lower = word.lower()
            if word_lower in ['tool', 'using', 'use']:
                # Check next few words for capitalized tool names
                for j in range(i + 1, min(i + 4, len(words))):
                    potential_tool = words[j].rstrip('.,;:!?')
                    # Must be capitalized, not a common word, and look like a tool name
                    if (potential_tool and potential_tool[0].isupper() and 
                        len(potential_tool) > 3 and
                        potential_tool not in {'The', 'This', 'That', 'Click', 'Find', 'Get', 'Set'}):
                        if potential_tool not in self.available_tools:
                            return ValidationFailure(
                                check_name="required_tool_availability",
                                severity=SeverityLevel.HIGH,
                                message=f"Tool '{potential_tool}' is not available",
                                confidence_delta=-0.3,
                            )
        
        return None
    
    def _check_element_existence(self, goal: str) -> ValidationFailure or None:
        """
        Check 2: Element Existence
        
        Detect: If goal targets UI elements, verify they can be found.
        Example: "click the ImageEditor button" → check if button exists
        """
        element_keywords = {
            'button': [], 'input': [], 'field': [], 'element': [],
            'text': [], 'checkbox': [], 'dropdown': [], 'modal': []
        }
        
        goal_lower = goal.lower()
        
        for element_type in element_keywords:
            if element_type in goal_lower:
                # Check if element exists in UI schema
                if element_type not in self.ui_schema:
                    return ValidationFailure(
                        check_name="element_existence",
                        severity=SeverityLevel.MEDIUM,
                        message=f"Target element type '{element_type}' not found in UI",
                        confidence_delta=-0.2,
                    )
        
        return None
    
    def _check_context_availability(
        self,
        goal: str,
        session_context: Dict[str, Any],
    ) -> ValidationFailure or None:
        """
        Check 3: Context Availability
        
        Detect: If goal requires code/data context, verify it's available.
        Example: "Refactor this function" → check if function code provided
        """
        context_required_keywords = {
            'refactor': 'code',
            'analyze': 'data',
            'debug': 'code',
            'compile': 'code',
            'test': 'test_data',
        }
        
        goal_lower = goal.lower()
        
        for keyword, required_context in context_required_keywords.items():
            if keyword in goal_lower:
                # Check if context is in goal or session
                if required_context not in session_context:
                    # Context might be in goal itself, so this is a MEDIUM issue
                    if required_context not in goal_lower:
                        return ValidationFailure(
                            check_name="context_availability",
                            severity=SeverityLevel.MEDIUM,
                            message=f"Required context '{required_context}' not provided",
                            confidence_delta=-0.2,
                        )
        
        return None
    
    def _check_contradictions(self, goal: str) -> ValidationFailure or None:
        """
        Check 4: Contradiction Detection
        
        Detect: Contradictory instructions in goal.
        Example: "Click button X and do NOT click button Y" → conflict
        """
        contradiction_pairs = [
            ('click', 'not click'),
            ('enable', 'disable'),
            ('add', 'remove'),
            ('start', 'stop'),
            ('open', 'close'),
            ('create', 'delete'),
            ('allow', 'block'),
        ]
        
        goal_lower = goal.lower()
        
        for positive, negative in contradiction_pairs:
            if positive in goal_lower and negative in goal_lower:
                return ValidationFailure(
                    check_name="contradiction_detection",
                    severity=SeverityLevel.HIGH,
                    message=f"Goal contains contradictory instructions: '{positive}' and '{negative}'",
                    confidence_delta=-0.3,
                )
        
        return None
    
    def _check_scope_validation(self, goal: str) -> ValidationFailure or None:
        """
        Check 5: Scope Validation
        
        Detect: Goal is outside system scope.
        Example: "Launch a rocket" → not a software task
        """
        goal_lower = goal.lower()
        
        # Check if out-of-scope keywords present
        for keyword in self.OUT_OF_SCOPE_KEYWORDS:
            if keyword in goal_lower:
                return ValidationFailure(
                    check_name="scope_validation",
                    severity=SeverityLevel.CRITICAL,
                    message=f"Goal mentions '{keyword}', which is outside system scope",
                    confidence_delta=-0.4,
                )
        
        # Check if in-scope keywords present (optional boost)
        has_scope_keyword = any(
            keyword in goal_lower
            for keyword in self.SYSTEM_SCOPE_KEYWORDS
        )
        
        if not has_scope_keyword and len(goal) > 5:
            # Goal doesn't mention any in-scope keywords (weak signal)
            return ValidationFailure(
                check_name="scope_validation",
                severity=SeverityLevel.MEDIUM,
                message="Goal doesn't clearly mention software/code tasks",
                confidence_delta=-0.1,
            )
        
        return None
    
    def _check_complexity_warning(self, goal: str) -> ValidationFailure or None:
        """
        Check 6: Complexity Warning
        
        Detect: Overly complex goals that might fail.
        Example: Multi-step goal requiring 5+ tools
        """
        # Simple heuristic: count action verbs
        action_verbs = {
            'click', 'find', 'analyze', 'refactor', 'generate', 'test',
            'debug', 'fix', 'parse', 'validate', 'extract', 'transform',
        }
        
        goal_lower = goal.lower()
        action_count = sum(
            1 for verb in action_verbs if verb in goal_lower
        )
        
        # If goal mentions 4+ actions, it's complex
        if action_count >= 4:
            return ValidationFailure(
                check_name="complexity_warning",
                severity=SeverityLevel.LOW,
                message=f"Goal involves {action_count} actions and may be complex",
                confidence_delta=-0.1,
            )
        
        return None
    
    @staticmethod
    def _determine_recommendation(result: PreValidationResult) -> str:
        """Determine overall recommendation based on failures."""
        if result.checks_failed == 0:
            return "proceed"
        elif result.total_confidence_delta <= -0.3:
            return "reject"
        else:
            return "clarify"
    
    @staticmethod
    def _generate_suggested_questions(result: PreValidationResult) -> List[str]:
        """Generate clarification questions based on failures."""
        questions = []
        
        for failure in result.failures:
            if failure.check_name == "required_tool_availability":
                questions.append(
                    "Do you want to use a different tool, or can I suggest alternatives?"
                )
            
            elif failure.check_name == "element_existence":
                questions.append(
                    "Can you provide more details about the element location? "
                    "(e.g., 'button in the top-right corner')"
                )
            
            elif failure.check_name == "context_availability":
                questions.append(
                    "Please provide the code or data you want me to work with."
                )
            
            elif failure.check_name == "contradiction_detection":
                questions.append(
                    "Your goal contains conflicting instructions. "
                    "Can you clarify what you'd like me to do?"
                )
            
            elif failure.check_name == "scope_validation":
                questions.append(
                    "This task may be outside my capabilities. "
                    "Can you rephrase it as a software/code task?"
                )
            
            elif failure.check_name == "complexity_warning":
                questions.append(
                    "This is a complex task. Can you break it down into simpler steps?"
                )
        
        return questions


# =============================================================================
# EXAMPLES FOR TESTING
# =============================================================================

def example_passing_validation():
    """Example: Goal passes all validation checks."""
    validator = PreValidator(
        available_tools=['button_clicker', 'element_finder'],
        ui_schema={'button': {}, 'input': {}}
    )
    
    result = validator.validate_goal("Click the submit button")
    
    print("PASSING VALIDATION EXAMPLE:")
    print(f"  Status: {result.validation_status}")
    print(f"  Checks Passed: {result.checks_passed}")
    print(f"  Checks Failed: {result.checks_failed}")
    print(f"  Recommendation: {result.recommendation}")
    return result


def example_failing_validation():
    """Example: Goal fails validation checks."""
    validator = PreValidator(
        available_tools=['button_clicker'],
        ui_schema={'button': {}}
    )
    
    result = validator.validate_goal(
        "Refactor the ImageEditor tool and click the button"
    )
    
    print("\nFAILING VALIDATION EXAMPLE:")
    print(f"  Status: {result.validation_status}")
    print(f"  Checks Passed: {result.checks_passed}")
    print(f"  Checks Failed: {result.checks_failed}")
    print(f"  Confidence Delta: {result.total_confidence_delta}")
    print(f"  Recommendation: {result.recommendation}")
    print(f"  Failures:")
    for failure in result.failures:
        print(f"    - {failure.check_name}: {failure.message} (delta: {failure.confidence_delta})")
    print(f"  Suggested Questions:")
    for q in result.suggested_questions:
        print(f"    - {q}")
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("PRE-VALIDATION SYSTEM - EXAMPLES")
    print("=" * 70)
    
    example_passing_validation()
    example_failing_validation()

