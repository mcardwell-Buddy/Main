"""
Iterative Goal Decomposer: Smart, adaptive goal execution
that stops early for simple goals and dynamically generates
steps for complex goals based on previous results.

Key idea: Don't create 8 predefined steps. Instead:
1. Classify complexity (simple vs complex)
2. For simple: Execute directly with appropriate tool
3. For complex: Execute iteratively, where each result informs the next query
4. Stop when confidence is high enough, not after N steps
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from Back_End.llm_client import llm_client

logger = logging.getLogger(__name__)

class IterativeDecomposer:
    """Adaptive goal decomposition with iterative refinement"""
    
    # Simple goal patterns - can be solved in 1 tool call
    SIMPLE_PATTERNS = {
        'math': r'(?:\d+[\s]*[-+*/xX][\s]*\d+|what\s+is|calculate|compute|solve|times|plus|minus|divided|multiply)',
        'definition': r'^(?:what\s+is|define|explain)\s+(?!.*(?:and|also|plus|vs|compared|background|companies|founded))[^?]*\?*$',
        'time': r'(?:what\s+time|what\s+date|current\s+time|what\s+hour)',
        'conversion': r'(?:convert|how\s+many|how\s+much).*(?:to|in)',
    }
    
    # Complex goal patterns - require multiple steps
    COMPLEX_PATTERNS = {
        'research_and_compare': r'\b(?:compare|vs|versus|against)\b.*\b(?:and|with|or)\b',
        'research_then_analyze': r'\b(?:find|research|investigate)\b.*\b(?:then|and\s+then|also)\b.*\b(?:analyze|summarize)',
        'multi_entity': r'\b(?:and|also|plus)\b.*\b(?:and|also|plus)\b',  # Multiple "and"s suggest multiple entities
        'sequential_tasks': r'\b(?:first|then|next|finally|after)\b',
        'background_and_context': r'\b(?:background|history|origins)\b.*\b(?:and|also|current)\b',
    }
    
    def __init__(self):
        self.execution_history = []
    
    def analyze_goal_complexity(self, goal: str) -> Dict:
        """
        Analyze goal to determine if it's simple or complex.
        
        Returns:
        {
            'complexity': 'simple' | 'complex',
            'confidence': float (0.0-1.0),
            'category': str (e.g., 'math', 'definition', 'research_and_compare'),
            'reasoning': str,
            'recommended_tool': str or None (for simple goals),
            'requires_iteration': bool,
            'entities': list (named things to research)
        }
        """
        goal_lower = goal.lower().strip()
        
        # Check for simple patterns first
        simple_category = self._match_simple_pattern(goal_lower)
        if simple_category:
            reasoning = f"Simple {simple_category} goal - can be solved directly"
            return {
                'complexity': 'simple',
                'confidence': 0.9,
                'category': simple_category,
                'reasoning': reasoning,
                'recommended_tool': self._get_simple_tool(simple_category),
                'requires_iteration': False,
                'entities': self._extract_entities(goal)
            }
        
        # Check for complex patterns
        complex_category = self._match_complex_pattern(goal_lower)
        if complex_category:
            reasoning = f"Complex {complex_category} goal - requires iterative research"
            return {
                'complexity': 'complex',
                'confidence': 0.85,
                'category': complex_category,
                'reasoning': reasoning,
                'recommended_tool': None,
                'requires_iteration': True,
                'entities': self._extract_entities(goal)
            }
        
        # Use LLM for ambiguous cases
        if llm_client.enabled:
            llm_analysis = self._analyze_with_llm(goal)
            if llm_analysis:
                return llm_analysis
        
        # Default: assume complex if uncertain
        return {
            'complexity': 'complex',
            'confidence': 0.6,
            'category': 'unknown',
            'reasoning': 'Unable to classify - treating as complex',
            'recommended_tool': None,
            'requires_iteration': True,
            'entities': self._extract_entities(goal)
        }
    
    def generate_first_step(self, goal: str, entities: List[str]) -> Dict:
        """
        Generate the first step for iterative execution.
        
        Returns:
        {
            'step': str,
            'search_query': str,
            'tool': str,
            'purpose': str,
            'expected_output': str
        }
        """
        if not entities:
            entities = self._extract_entities(goal)
        
        # Use LLM to generate intelligent first query
        if llm_client.enabled:
            prompt = f"""Given this goal: "{goal}"
            
And these entities to research: {entities}

Generate the FIRST search query that should be executed. This query should find:
- The primary information needed
- Will lead to natural follow-up searches

Respond with ONLY the search query, nothing else."""
            
            first_query = llm_client.complete(prompt, max_tokens=100, temperature=0.3)
            if first_query:
                return {
                    'step': 'initial_research',
                    'search_query': first_query.strip(),
                    'tool': 'web_search',
                    'purpose': 'Find primary information to inform next searches',
                    'expected_output': 'Web results about the main entity/topic'
                }
        
        # Fallback: basic query
        primary_entity = entities[0] if entities else goal.split()[0]
        return {
            'step': 'initial_research',
            'search_query': primary_entity,
            'tool': 'web_search',
            'purpose': 'Find information about primary entity',
            'expected_output': 'Web results about the entity'
        }
    
    def generate_next_step(self, goal: str, previous_results: List[Dict], 
                          current_findings: Dict) -> Optional[Dict]:
        """
        Based on previous results and current findings, generate the next step.
        
        Returns next step dict or None if research is sufficient.
        
        Args:
            goal: Original goal
            previous_results: List of {query, tool, results, timestamp}
            current_findings: {entities_found: dict, confidence: float, gaps: list}
        
        Returns:
        {
            'step': str,
            'search_query': str,
            'tool': str,
            'purpose': str,
            'expected_output': str,
            'stop_iteration': bool (if True, no more steps needed)
        }
        """
        
        # Check if we have sufficient information
        if current_findings.get('confidence', 0) >= 0.85:
            logger.info("Confidence level sufficient, stopping iteration")
            return {
                'step': 'synthesize',
                'search_query': None,
                'tool': None,
                'purpose': 'Sufficient information gathered',
                'expected_output': 'Final answer synthesis',
                'stop_iteration': True
            }
        
        # Check iteration limit (max 5 searches to avoid infinite loops)
        if len(previous_results) >= 5:
            logger.info("Reached maximum iteration count")
            return {
                'step': 'synthesize',
                'search_query': None,
                'tool': None,
                'purpose': 'Maximum iterations reached',
                'expected_output': 'Final answer from available data',
                'stop_iteration': True
            }
        
        gaps = current_findings.get('gaps', [])
        if not gaps:
            logger.info("No identified gaps in findings")
            return {
                'step': 'synthesize',
                'search_query': None,
                'tool': None,
                'purpose': 'No gaps identified',
                'expected_output': 'Final answer synthesis',
                'stop_iteration': True
            }
        
        # Use LLM to generate next intelligent query based on gaps
        if llm_client.enabled:
            prompt = f"""Goal: {goal}

Current findings:
{self._format_findings(current_findings)}

Identified information gaps: {gaps}

What should we search for next to fill these gaps? 
Respond with ONLY the next search query, nothing else."""
            
            next_query = llm_client.complete(prompt, max_tokens=100, temperature=0.3)
            if next_query:
                return {
                    'step': f'research_gap_{len(previous_results)}',
                    'search_query': next_query.strip(),
                    'tool': 'web_search',
                    'purpose': f'Research gap: {gaps[0] if gaps else "additional context"}',
                    'expected_output': 'Web results filling the identified gap',
                    'stop_iteration': False
                }
        
        # Fallback: generate next query from gap
        if gaps:
            next_query = f"{current_findings.get('primary_entity', '')} {gaps[0]}"
            return {
                'step': f'research_gap_{len(previous_results)}',
                'search_query': next_query,
                'tool': 'web_search',
                'purpose': f'Fill gap: {gaps[0]}',
                'expected_output': 'Web results about the gap',
                'stop_iteration': False
            }
        
        # No clear next step
        return {
            'step': 'synthesize',
            'search_query': None,
            'tool': None,
            'purpose': 'No clear next step identified',
            'expected_output': 'Final answer synthesis',
            'stop_iteration': True
        }
    
    def analyze_search_results(self, search_results: str, goal: str,
                               current_findings: Dict) -> Dict:
        """
        Analyze search results to identify:
        - What we've learned
        - What gaps remain
        - What to search for next
        
        Returns:
        {
            'entities_found': {entity: info},
            'key_facts': [fact1, fact2, ...],
            'gaps': ['missing info 1', 'missing info 2'],
            'confidence': float (0.0-1.0),
            'ready_to_synthesize': bool
        }
        """
        
        # Use LLM to analyze results
        if llm_client.enabled:
            prompt = f"""Goal: {goal}

Search results:
{search_results[:1000]}  # Limit to first 1000 chars

From these results, identify:
1. Key entities found (e.g., people, companies, dates)
2. Key facts established
3. What information is STILL MISSING to fully answer the goal
4. Overall confidence in the answer (0-100%)

Respond in JSON format:
{{
    "entities": {{"entity_name": "description", ...}},
    "key_facts": ["fact1", "fact2", ...],
    "gaps": ["gap1", "gap2", ...],
    "confidence": 85,
    "ready_to_synthesize": false
}}"""
            
            analysis_json = llm_client.complete(prompt, max_tokens=500, temperature=0.3)
            if analysis_json:
                try:
                    import json
                    analysis = json.loads(analysis_json)
                    return {
                        'entities_found': analysis.get('entities', {}),
                        'key_facts': analysis.get('key_facts', []),
                        'gaps': analysis.get('gaps', []),
                        'confidence': analysis.get('confidence', 0) / 100.0,
                        'ready_to_synthesize': analysis.get('ready_to_synthesize', False),
                        'primary_entity': list(analysis.get('entities', {}).keys())[0] if analysis.get('entities') else None
                    }
                except Exception as e:
                    logger.warning(f"Failed to parse LLM analysis: {e}")
        
        # Fallback: basic analysis
        entities = self._extract_entities_from_text(search_results)
        facts = self._extract_facts(search_results)
        
        return {
            'entities_found': {e: 'found in search results' for e in entities},
            'key_facts': facts[:5],
            'gaps': self._identify_gaps(goal, entities, facts),
            'confidence': 0.5 if entities else 0.3,
            'ready_to_synthesize': len(entities) > 0,
            'primary_entity': entities[0] if entities else None
        }
    
    # ==================== PRIVATE HELPERS ====================
    
    def _match_simple_pattern(self, goal: str) -> Optional[str]:
        """Check if goal matches a simple pattern. Returns category name or None."""
        for category, pattern in self.SIMPLE_PATTERNS.items():
            if re.search(pattern, goal, re.IGNORECASE):
                return category
        return None
    
    def _match_complex_pattern(self, goal: str) -> Optional[str]:
        """Check if goal matches a complex pattern. Returns category name or None."""
        for category, pattern in self.COMPLEX_PATTERNS.items():
            if re.search(pattern, goal, re.IGNORECASE):
                return category
        return None
    
    def _get_simple_tool(self, category: str) -> str:
        """Return the appropriate tool for a simple goal category."""
        tool_map = {
            'math': 'calculate',
            'definition': 'web_search',
            'time': 'web_search',
            'conversion': 'calculate'
        }
        return tool_map.get(category, 'web_search')
    
    def _extract_entities(self, goal: str) -> List[str]:
        """Extract main entities (nouns) from goal."""
        # Simple extraction: split by 'and' and 'vs'
        parts = re.split(r'\b(?:and|vs|versus|with|or)\b', goal, flags=re.IGNORECASE)
        entities = [p.strip() for p in parts if p.strip()]
        return entities[:3]  # Max 3 entities
    
    def _extract_entities_from_text(self, text: str) -> List[str]:
        """Extract entities from search results text."""
        # Basic: extract capitalized words that look like proper nouns
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return list(set(words))[:5]
    
    def _extract_facts(self, text: str) -> List[str]:
        """Extract factual statements from text."""
        sentences = re.split(r'[\.!?]+', text)
        facts = [s.strip() for s in sentences if len(s.strip()) > 20]
        return facts[:5]
    
    def _identify_gaps(self, goal: str, entities: List[str], facts: List[str]) -> List[str]:
        """Identify what information is missing."""
        gaps = []
        
        goal_lower = goal.lower()
        if 'background' in goal_lower and not any('born' in f.lower() or 'background' in f.lower() for f in facts):
            gaps.append('background and history')
        if 'current' in goal_lower and not any('now' in f.lower() or 'currently' in f.lower() for f in facts):
            gaps.append('current status')
        if 'company' in goal_lower or 'work' in goal_lower and not any('company' in f.lower() or 'work' in f.lower() for f in facts):
            gaps.append('company information')
        
        return gaps if gaps else ['additional context and details']
    
    def _format_findings(self, findings: Dict) -> str:
        """Format findings for LLM prompt."""
        lines = []
        for entity, info in findings.get('entities_found', {}).items():
            lines.append(f"- {entity}: {info}")
        for fact in findings.get('key_facts', []):
            lines.append(f"- {fact}")
        return '\n'.join(lines) if lines else 'No findings yet'
    
    def _analyze_with_llm(self, goal: str) -> Optional[Dict]:
        """Use LLM to analyze goal complexity."""
        if not llm_client.enabled:
            return None
        
        prompt = f"""Analyze this goal for complexity:
"{goal}"

Is this a simple goal (can be answered in 1 tool call) or complex (requires multiple searches)?

Respond in JSON:
{{
    "complexity": "simple" or "complex",
    "category": "category name",
    "confidence": 0.8,
    "reasoning": "explanation"
}}"""
        
        try:
            response = llm_client.complete(prompt, max_tokens=200, temperature=0.3)
            if response:
                import json
                data = json.loads(response)
                return {
                    'complexity': data.get('complexity', 'complex'),
                    'confidence': data.get('confidence', 0.6),
                    'category': data.get('category', 'unknown'),
                    'reasoning': data.get('reasoning', ''),
                    'recommended_tool': None,
                    'requires_iteration': data.get('complexity') == 'complex',
                    'entities': self._extract_entities(goal)
                }
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")
        
        return None


# Singleton instance
iterative_decomposer = IterativeDecomposer()

