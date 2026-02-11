"""
================================================================================
PHASE 2: GRADED CONFIDENCE SYSTEM
================================================================================

Purpose: Calculate deterministic, continuous confidence scores (0.0-1.0) for
goal execution, replacing Phase 1's bimodal distribution.

Reference: PHASE_2_DESIGN_DOCUMENT.md - Section 4

Confidence Calculation:
  confidence = (goal_understanding * 0.30) +
               (tool_availability * 0.30) +
               (context_richness * 0.20) +
               (tool_confidence * 0.20)

Factors:
  - Goal Understanding (30%): How clear is the user's intent?
  - Tool Availability (30%): Are required tools available?
  - Context Richness (20%): Is sufficient context provided?
  - Tool Confidence (20%): Are tools deterministic/safe?

Output: confidence ∈ [0.0, 1.0] (continuous)
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class ConfidenceFactors:
    """Container for all confidence calculation factors."""
    goal_understanding: float  # [0.0, 1.0]
    tool_availability: float   # [0.0, 1.0]
    context_richness: float    # [0.0, 1.0]
    tool_confidence: float     # [0.0, 1.0]

    def __post_init__(self):
        """Validate all factors are in [0.0, 1.0] range."""
        for field_name in ['goal_understanding', 'tool_availability', 
                          'context_richness', 'tool_confidence']:
            value = getattr(self, field_name)
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"{field_name} must be in [0.0, 1.0], got {value}")


class GradedConfidenceCalculator:
    """
    Deterministic confidence calculator for goal execution.
    
    Key Properties:
    - Deterministic: Same inputs → same output (no randomness)
    - Continuous: Full [0.0, 1.0] range possible
    - Weighted: Four factors with configurable weights
    - Tunable: Weights can be adjusted for calibration
    
    Example Usage:
        calculator = GradedConfidenceCalculator()
        
        # Atomic goal (clear, tools available)
        factors = ConfidenceFactors(
            goal_understanding=1.0,  # "click button #submit" is clear
            tool_availability=1.0,   # button interaction tool exists
            context_richness=0.5,    # first goal, no history
            tool_confidence=1.0      # tool is deterministic
        )
        confidence = calculator.calculate(factors)
        # Expected: ~0.90 (HIGH CONFIDENCE)
        
        # Ambiguous goal (unclear, tools unavailable)
        factors = ConfidenceFactors(
            goal_understanding=0.2,  # "help me" is vague
            tool_availability=0.0,   # no tool to help
            context_richness=0.3,    # no prior history
            tool_confidence=0.5      # uncertain what tool would help
        )
        confidence = calculator.calculate(factors)
        # Expected: ~0.16 (LOW CONFIDENCE)
    """
    
    # Default weights (tunable for calibration)
    DEFAULT_WEIGHTS = {
        'goal_understanding': 0.30,
        'tool_availability': 0.30,
        'context_richness': 0.20,
        'tool_confidence': 0.20,
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize confidence calculator.
        
        Args:
            weights: Optional custom weights. Must sum to 1.0.
                     Defaults to DEFAULT_WEIGHTS if not provided.
        """
        if weights is None:
            self.weights = self.DEFAULT_WEIGHTS.copy()
        else:
            # Validate weights sum to 1.0
            weight_sum = sum(weights.values())
            if not (0.99 <= weight_sum <= 1.01):  # Allow small floating point error
                raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")
            self.weights = weights
    
    def calculate(self, factors: ConfidenceFactors) -> float:
        """
        Calculate graded confidence from factors.
        
        Args:
            factors: ConfidenceFactors object with all four factors
        
        Returns:
            float: Confidence score in [0.0, 1.0]
        """
        confidence = (
            factors.goal_understanding * self.weights['goal_understanding'] +
            factors.tool_availability * self.weights['tool_availability'] +
            factors.context_richness * self.weights['context_richness'] +
            factors.tool_confidence * self.weights['tool_confidence']
        )
        
        # Clamp to [0.0, 1.0] (should not be necessary, but defensive)
        return min(1.0, max(0.0, confidence))
    
    def analyze_factors(self, factors: ConfidenceFactors) -> Dict[str, Any]:
        """
        Analyze factors to help understand confidence score.
        
        Args:
            factors: ConfidenceFactors object
        
        Returns:
            Dict with factor breakdown and recommendations
        """
        confidence = self.calculate(factors)
        
        # Identify weakest factor
        factor_scores = {
            'goal_understanding': factors.goal_understanding,
            'tool_availability': factors.tool_availability,
            'context_richness': factors.context_richness,
            'tool_confidence': factors.tool_confidence,
        }
        weakest = min(factor_scores, key=factor_scores.get)
        
        return {
            'confidence': confidence,
            'factors': factor_scores,
            'weakest_factor': weakest,
            'confidence_category': self._categorize_confidence(confidence),
            'recommendations': self._generate_recommendations(factors),
        }
    
    @staticmethod
    def _categorize_confidence(confidence: float) -> str:
        """Categorize confidence into bins for human readability."""
        if confidence >= 0.85:
            return 'HIGH_CONFIDENCE'
        elif confidence >= 0.55:
            return 'MEDIUM_CONFIDENCE'
        else:
            return 'LOW_CONFIDENCE'
    
    @staticmethod
    def _generate_recommendations(factors: ConfidenceFactors) -> List[str]:
        """Generate suggestions to improve confidence."""
        recommendations = []
        
        if factors.goal_understanding < 0.5:
            recommendations.append(
                "Goal is ambiguous. Ask user for clarification: "
                "specific action, target element, expected outcome."
            )
        
        if factors.tool_availability < 0.5:
            recommendations.append(
                "Required tools may be missing. Verify tool availability "
                "or suggest alternatives."
            )
        
        if factors.context_richness < 0.5:
            recommendations.append(
                "Insufficient context. Request missing information: "
                "code, data, or configuration."
            )
        
        if factors.tool_confidence < 0.5:
            recommendations.append(
                "Selected tools have high uncertainty. Consider requesting "
                "user approval before execution."
            )
        
        return recommendations


class GoalUnderstandingCalculator:
    """
    Calculate goal_understanding factor (0.0-1.0).
    
    Signals:
    - Action verb present: +0.1
    - Target element specified: +0.1
    - Context provided: +0.1
    - Expected outcome stated: +0.1
    - No contradictions: +0.1
    
    Max: 1.0, Min: 0.0
    """
    
    ACTION_VERBS = {
        'click', 'find', 'analyze', 'refactor', 'generate', 'test',
        'debug', 'fix', 'parse', 'validate', 'extract', 'transform',
        'list', 'search', 'compare', 'create', 'modify', 'delete',
        'execute', 'run', 'compile', 'build', 'deploy', 'check'
    }
    
    def calculate(self, goal: str) -> float:
        """
        Calculate goal understanding from goal string.
        
        Args:
            goal: User's stated goal
        
        Returns:
            float in [0.0, 1.0]
        """
        if not goal or not isinstance(goal, str):
            return 0.0
        
        goal_lower = goal.lower()
        score = 0.0
        
        # Check for action verb
        if any(verb in goal_lower for verb in self.ACTION_VERBS):
            score += 0.1
        
        # Check for specific target (has noun-like specificity)
        if self._has_target_specificity(goal):
            score += 0.1
        
        # Check for context clues
        if self._has_context_clues(goal):
            score += 0.1
        
        # Check for expected outcome
        if self._has_outcome_statement(goal):
            score += 0.1
        
        # Check for contradictions (subtract if found)
        if self._has_contradictions(goal):
            score -= 0.2
        else:
            score += 0.1  # Bonus for no contradictions
        
        return min(1.0, max(0.0, score))
    
    @staticmethod
    def _has_target_specificity(goal: str) -> bool:
        """Check if goal specifies a target (e.g., 'button', 'function', 'element')."""
        target_keywords = {
            'button', 'input', 'function', 'variable', 'file', 'element',
            'line', 'section', 'class', 'method', 'field', 'attribute'
        }
        return any(keyword in goal.lower() for keyword in target_keywords)
    
    @staticmethod
    def _has_context_clues(goal: str) -> bool:
        """Check if goal provides context (e.g., 'in the modal', 'on line 5')."""
        context_keywords = {'in', 'on', 'at', 'within', 'inside', 'from', 'to'}
        words = goal.lower().split()
        return any(kw in words for kw in context_keywords)
    
    @staticmethod
    def _has_outcome_statement(goal: str) -> bool:
        """Check if goal states expected outcome (e.g., 'should', 'must', 'expect')."""
        outcome_keywords = {'should', 'must', 'expect', 'will', 'return', 'result'}
        return any(keyword in goal.lower() for keyword in outcome_keywords)
    
    @staticmethod
    def _has_contradictions(goal: str) -> bool:
        """Check if goal contains contradictions (e.g., 'click and don't click')."""
        contradiction_pairs = [
            ('click', 'not click'),
            ('enable', 'disable'),
            ('add', 'remove'),
            ('start', 'stop'),
            ('open', 'close'),
        ]
        goal_lower = goal.lower()
        for pos, neg in contradiction_pairs:
            if pos in goal_lower and neg in goal_lower:
                return True
        return False


class ToolAvailabilityCalculator:
    """
    Calculate tool_availability factor (0.0-1.0).
    
    For each required tool:
    - Tool exists: +0.15
    - Tool has required capabilities: +0.15
    - Tool is healthy: +0.05
    
    Capped at 1.0.
    """
    
    def __init__(self, available_tools: List[str] = None):
        """
        Initialize with list of available tools.
        
        Args:
            available_tools: List of tool names available in system
        """
        self.available_tools = set(available_tools or [])
    
    def calculate(self, goal: str, tools_proposed: List[str] = None) -> float:
        """
        Calculate tool availability.
        
        Args:
            goal: User's goal (to extract tool names if not provided)
            tools_proposed: Pre-identified list of tools needed
        
        Returns:
            float in [0.0, 1.0]
        """
        if tools_proposed is None:
            tools_proposed = self._extract_tool_names(goal)
        
        if not tools_proposed:
            # If no tools proposed, assume not needed (neutral)
            return 0.5
        
        score = 0.0
        
        for tool in tools_proposed:
            if tool in self.available_tools:
                score += 0.15  # Tool exists
                score += 0.15  # Assume capabilities available
                score += 0.05  # Assume tool is healthy
            else:
                # Tool missing, reduce confidence
                score -= 0.3
        
        # Normalize by number of tools
        # (we want to encourage tool reuse but penalize missing tools)
        return min(1.0, max(0.0, score / len(tools_proposed)))
    
    @staticmethod
    def _extract_tool_names(goal: str) -> List[str]:
        """
        Extract tool names from goal string.
        Looks for patterns like "use the ToolName tool" or "with ImageEditor".
        """
        # Simple heuristic: look for capitalized words that might be tool names
        words = goal.split()
        tools = [
            word.rstrip('.,;:!?') 
            for word in words 
            if word[0].isupper() and 3 <= len(word) <= 30
        ]
        return tools


class ContextRichnessCalculator:
    """
    Calculate context_richness factor (0.0-1.0).
    
    Signals:
    - Prior conversation history: +0.1
    - Session state available: +0.05
    - User preferences known: +0.05
    - Same tool used recently: +0.05
    """
    
    def calculate(
        self,
        has_prior_goals: bool = False,
        has_session_state: bool = False,
        has_user_preferences: bool = False,
        tool_recently_used: bool = False,
    ) -> float:
        """
        Calculate context richness.
        
        Args:
            has_prior_goals: User has prior conversation history
            has_session_state: System has session state
            has_user_preferences: System knows user preferences
            tool_recently_used: Target tool used in recent goals
        
        Returns:
            float in [0.0, 1.0]
        """
        score = 0.0
        
        if has_prior_goals:
            score += 0.1
        
        if has_session_state:
            score += 0.05
        
        if has_user_preferences:
            score += 0.05
        
        if tool_recently_used:
            score += 0.05
        
        # Base: minimal context
        score += 0.3
        
        return min(1.0, max(0.0, score))


class ToolConfidenceCalculator:
    """
    Calculate tool_confidence factor (0.0-1.0).
    
    Tool properties:
    - Deterministic (read-only): +0.1 per tool
    - Idempotent: +0.05 per tool
    - Has error handling: +0.05 per tool
    """
    
    TOOL_PROPERTIES = {
        # Example tool configurations
        'button_clicker': {
            'deterministic': True,
            'idempotent': False,  # Clicking twice has different effect
            'has_error_handling': True,
        },
        'element_finder': {
            'deterministic': True,
            'idempotent': True,
            'has_error_handling': True,
        },
        'code_analyzer': {
            'deterministic': True,
            'idempotent': True,
            'has_error_handling': True,
        },
    }
    
    def calculate(self, tools_proposed: List[str] = None) -> float:
        """
        Calculate tool confidence from tool properties.
        
        Args:
            tools_proposed: List of tool names
        
        Returns:
            float in [0.0, 1.0]
        """
        if not tools_proposed:
            return 0.5  # Neutral if no tools
        
        score = 0.0
        
        for tool in tools_proposed:
            props = self.TOOL_PROPERTIES.get(tool, {})
            
            if props.get('deterministic', False):
                score += 0.1
            
            if props.get('idempotent', False):
                score += 0.05
            
            if props.get('has_error_handling', False):
                score += 0.05
        
        # Normalize by number of tools
        return min(1.0, max(0.0, score / len(tools_proposed)))


# =============================================================================
# EXAMPLES FOR TESTING
# =============================================================================

def example_high_confidence():
    """Example: High confidence scenario (atomic goal)."""
    calculator = GradedConfidenceCalculator()
    
    # Clear goal with all tools available
    factors = ConfidenceFactors(
        goal_understanding=1.0,
        tool_availability=1.0,
        context_richness=0.5,
        tool_confidence=1.0,
    )
    
    confidence = calculator.calculate(factors)
    analysis = calculator.analyze_factors(factors)
    
    print("HIGH CONFIDENCE EXAMPLE:")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  Category: {analysis['confidence_category']}")
    print(f"  Factors: {analysis['factors']}")
    return confidence


def example_medium_confidence():
    """Example: Medium confidence scenario."""
    calculator = GradedConfidenceCalculator()
    
    # Clear but missing context
    factors = ConfidenceFactors(
        goal_understanding=0.9,
        tool_availability=0.8,
        context_richness=0.4,
        tool_confidence=0.7,
    )
    
    confidence = calculator.calculate(factors)
    analysis = calculator.analyze_factors(factors)
    
    print("\nMEDIUM CONFIDENCE EXAMPLE:")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  Category: {analysis['confidence_category']}")
    print(f"  Weakest Factor: {analysis['weakest_factor']}")
    return confidence


def example_low_confidence():
    """Example: Low confidence scenario (ambiguous)."""
    calculator = GradedConfidenceCalculator()
    
    # Vague goal with no tools
    factors = ConfidenceFactors(
        goal_understanding=0.2,
        tool_availability=0.0,
        context_richness=0.3,
        tool_confidence=0.5,
    )
    
    confidence = calculator.calculate(factors)
    analysis = calculator.analyze_factors(factors)
    
    print("\nLOW CONFIDENCE EXAMPLE:")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  Category: {analysis['confidence_category']}")
    print(f"  Recommendations:")
    for rec in analysis['recommendations']:
        print(f"    - {rec}")
    return confidence


if __name__ == '__main__':
    print("=" * 70)
    print("GRADED CONFIDENCE SYSTEM - EXAMPLES")
    print("=" * 70)
    
    example_high_confidence()
    example_medium_confidence()
    example_low_confidence()

