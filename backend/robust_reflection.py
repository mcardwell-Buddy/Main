"""
Robust LLM-powered reflection that analyzes content quality and generates insights.
Replaces the basic heuristic reflection with intelligent analysis.
"""
import logging
from typing import Dict, List, Optional
from backend.llm_client import llm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reflect_robust(steps: List[Dict], tools_used: List[str], goal: str, 
                   confidence: float, memory_excerpt: Optional[str] = None) -> Dict:
    """
    Intelligent reflection using LLM to analyze quality, gaps, and strategy.
    
    Args:
        steps: List of execution steps with observations
        tools_used: List of tool names used
        goal: The original goal
        confidence: Current confidence level
        memory_excerpt: Relevant memory context
        
    Returns:
        dict with effectiveness, analysis, strategy, gaps, and curiosity questions
    """
    
    # Extract observations for analysis
    observations = []
    errors = []
    for step in steps:
        if step.get('observation'):
            observations.append(step['observation'])
        if step.get('error'):
            errors.append(step['error'])
    
    # If LLM is available, use intelligent reflection
    if llm_client.enabled:
        try:
            prompt = f"""Analyze this agent's performance on a goal execution:

**Goal**: {goal}

**Steps Taken**: {len(steps)}
**Tools Used**: {', '.join(tools_used) if tools_used else 'None'}
**Current Confidence**: {confidence:.2f}

**Observations**:
{format_observations(observations[:5])}  

**Errors** (if any):
{format_errors(errors) if errors else 'None'}

**Memory Context** (if available):
{memory_excerpt if memory_excerpt else 'No prior context'}

Please provide a comprehensive analysis in JSON format:

{{
  "effectiveness_score": <float 0.0-1.0>,
  "what_worked": "<specific successes>",
  "what_did_not_work": "<specific failures>",
  "content_quality": "<assessment of information quality>",
  "relevance": "<how relevant to goal>",
  "information_gaps": ["<gap 1>", "<gap 2>", ...],
  "strategy_adjustment": "<specific next steps>",
  "confidence_adjustment": <float -0.4 to +0.4>,
  "curiosity_questions": ["<question 1>", "<question 2>", ...],
  "recommendation": "<proceed | refine | pivot>"
}}

Be specific and actionable in your analysis."""

            response = llm_client.complete(prompt, max_tokens=700, temperature=0.3)
            
            # Parse LLM response
            import json
            try:
                # Try direct parsing first
                analysis = json.loads(response)
                
            except json.JSONDecodeError:
                # Try to extract JSON from malformed response
                logger.debug(f"First parse attempt failed, trying to extract JSON from response")
                import re
                json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if json_match:
                    try:
                        analysis = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        logger.warning("Could not extract valid JSON from LLM response, falling back to heuristic")
                        return reflect_heuristic(steps, tools_used, goal, confidence, memory_excerpt)
                else:
                    logger.warning("No JSON structure found in LLM response, falling back to heuristic")
                    return reflect_heuristic(steps, tools_used, goal, confidence, memory_excerpt)
            
            try:
                # Add tool feedback based on LLM analysis
                tool_feedback = {}
                for tool in tools_used:
                    # LLM-based assessment (we could make this more sophisticated)
                    tool_feedback[tool] = {
                        'usefulness': analysis.get('effectiveness_score', 0.5),
                        'notes': f"Used in context of: {goal[:50]}..."
                    }
                
                return {
                    'method': 'llm_powered',
                    'effectiveness_score': float(analysis.get('effectiveness_score', 0.5)),
                    'what_worked': str(analysis.get('what_worked', 'Analysis pending')),
                    'what_did_not_work': str(analysis.get('what_did_not_work', 'None identified')),
                    'content_quality': str(analysis.get('content_quality', 'Unknown')),
                    'relevance': str(analysis.get('relevance', 'Unknown')),
                    'information_gaps': list(analysis.get('information_gaps', [])),
                    'strategy_adjustment': str(analysis.get('strategy_adjustment', 'Continue')),
                    'confidence_adjustment': float(analysis.get('confidence_adjustment', 0.0)),
                    'curiosity_questions': list(analysis.get('curiosity_questions', [])),
                    'recommendation': str(analysis.get('recommendation', 'proceed')),
                    'tool_feedback': tool_feedback
                }
                
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error processing LLM analysis: {e}, falling back to heuristic")
                return reflect_heuristic(steps, tools_used, goal, confidence, memory_excerpt)
                
        except Exception as e:
            logger.error(f"LLM reflection failed: {e}")
            # Fall through to heuristic
    
    # Fallback to heuristic reflection (original implementation)
    return reflect_heuristic(steps, tools_used, goal, confidence, memory_excerpt)


def reflect_heuristic(steps: List[Dict], tools_used: List[str], goal: str,
                     confidence: float, memory_excerpt: Optional[str] = None) -> Dict:
    """
    Original heuristic-based reflection (fallback when LLM unavailable).
    """
    successes = sum(1 for step in steps if 'error' not in step.get('observation', {}))
    total = len(steps)
    effectiveness = successes / total if total > 0 else 0
    
    what_worked = 'Some tools returned usable observations.' if successes > 0 else 'No effective observations.'
    what_did_not_work = 'Several steps produced errors or incomplete data.' if successes < total else 'Minor issues only.'
    
    if effectiveness < 0.6:
        strategy_adjustment = 'Broaden queries or try different tools.'
    else:
        strategy_adjustment = 'Proceed with current strategy. Results look good.'
    
    tool_feedback = {}
    for tool in tools_used:
        found = any(step.get('tool') == tool for step in steps)
        tool_feedback[tool] = {
            'usefulness': 1.0 if found else 0.5,
            'notes': 'Heuristic usefulness score.'
        }
    
    confidence_adjustment = (effectiveness - 0.5) * 0.4  # -0.2 to +0.2
    
    return {
        'method': 'heuristic',
        'effectiveness_score': effectiveness,
        'what_worked': what_worked,
        'what_did_not_work': what_did_not_work,
        'strategy_adjustment': strategy_adjustment,
        'tool_feedback': tool_feedback,
        'confidence_adjustment': confidence_adjustment,
        'information_gaps': [],
        'curiosity_questions': []
    }


def format_observations(observations: List) -> str:
    """Format observations for LLM prompt"""
    if not observations:
        return "No observations"
    
    formatted = []
    for i, obs in enumerate(observations, 1):
        obs_str = str(obs)
        if len(obs_str) > 300:
            obs_str = obs_str[:300] + "..."
        formatted.append(f"{i}. {obs_str}")
    
    return "\n".join(formatted)


def format_errors(errors: List) -> str:
    """Format errors for LLM prompt"""
    if not errors:
        return "None"
    
    return "\n".join(f"- {error}" for error in errors)


def register_robust_reflection(tool_registry):
    """Register robust reflection tool (replaces basic reflect)"""
    
    # Keep original reflect as fallback
    if 'reflect' in tool_registry.tools:
        tool_registry.tools['reflect_basic'] = tool_registry.tools['reflect']
    
    # Register robust version as primary
    tool_registry.register(
        name='reflect',
        func=reflect_robust,
        description='Intelligent LLM-powered reflection that analyzes execution quality, identifies gaps, and generates strategic insights. Parameters: steps, tools_used, goal, confidence, memory_excerpt (optional)',
        mock_func=lambda **kwargs: {
            'method': 'mock',
            'effectiveness_score': 0.85,
            'what_worked': '[MOCK] Analysis indicates good progress',
            'what_did_not_work': '[MOCK] Some minor gaps',
            'content_quality': '[MOCK] High quality',
            'strategy_adjustment': '[MOCK] Continue current approach',
            'confidence_adjustment': 0.1,
            'information_gaps': ['[MOCK] Gap 1', '[MOCK] Gap 2'],
            'curiosity_questions': ['[MOCK] What about X?', '[MOCK] How does Y relate?'],
            'tool_feedback': {}
        }
    )
    
    logger.info("Registered robust LLM-powered reflection (replaces basic reflect)")
