"""
Iterative Execution Engine: Executes goals with adaptive, iterative refinement.

Unlike composite_agent.py which predetermines all subgoals upfront,
this engine:
1. Classifies goal complexity (simple vs complex)
2. For simple: Executes directly with one tool
3. For complex: Executes iteratively, where each result informs the next search
4. Stops when sufficient information gathered, not after N steps
"""

import logging
from typing import Dict, List, Optional
from Back_End.iterative_decomposer import iterative_decomposer
from Back_End.agent import Agent as AtomicAgent
from Back_End.config import Config
from Back_End.llm_client import llm_client
from Back_End.tool_selector import tool_selector

logger = logging.getLogger(__name__)


class IterativeExecutor:
    """Adaptive goal execution with iterative refinement"""
    
    def __init__(self, goal: str, domain: str = None):
        self.goal = goal
        self.domain = domain
        self.execution_history = []
        self.current_findings = {
            'entities_found': {},
            'key_facts': [],
            'gaps': [],
            'confidence': 0.0,
            'primary_entity': None
        }
    
    def execute(self) -> Dict:
        """
        Execute goal with intelligent iteration.
        
        Returns:
        {
            'execution_type': 'simple' | 'iterative',
            'goal': str,
            'total_iterations': int,
            'final_answer': str,
            'confidence': float,
            'execution_log': [...]
        }
        """
        # Analyze goal complexity
        complexity_analysis = iterative_decomposer.analyze_goal_complexity(self.goal)
        logger.info(f"Goal complexity: {complexity_analysis['complexity']} - {complexity_analysis['reasoning']}")
        
        if complexity_analysis['complexity'] == 'simple':
            return self._execute_simple(complexity_analysis)
        else:
            return self._execute_iterative(complexity_analysis)
    
    def _execute_simple(self, analysis: Dict) -> Dict:
        """
        Execute simple goal directly.
        Example: "What is 2+2?" → use calculate tool, done
        """
        logger.info(f"Executing simple goal: {analysis['category']}")
        
        tool_name = analysis.get('recommended_tool', 'web_search')
        
        # Create and execute agent with specific tool hint
        agent = AtomicAgent(self.goal, domain=self.domain, preferred_tool=tool_name)
        steps = []
        
        # For simple goals, stop after FIRST successful result
        while not agent.state.done and len(steps) < 3:
            state = agent.step()
            steps.append(state)
            
            # Check if we got a successful result (no error in observation)
            obs = state.get('observation', {})
            if obs and 'error' not in obs and 'result' in obs:
                logger.info(f"Got successful result on step {len(steps)}, stopping")
                break  # Stop after first successful result for simple goals
            
            if state.get('done'):
                break
        
        # Extract answer
        final_answer = self._extract_answer_from_steps(steps)
        
        return {
            'execution_type': 'simple',
            'goal': self.goal,
            'category': analysis['category'],
            'tool_used': tool_name,
            'total_iterations': 1,
            'total_steps': len(steps),
            'final_answer': final_answer,
            'confidence': agent.state.confidence,
            'reasoning': 'Simple goal solved directly',
            'execution_log': steps
        }
    
    def _execute_iterative(self, analysis: Dict) -> Dict:
        """
        Execute complex goal with iterative refinement.
        Each search result informs the next query.
        """
        logger.info(f"Executing iterative goal: {analysis['category']}")
        
        entities = analysis.get('entities', [])
        iteration = 0
        max_iterations = 5
        
        # Generate and execute first step
        first_step = iterative_decomposer.generate_first_step(self.goal, entities)
        logger.info(f"First search query: {first_step['search_query']}")
        
        # Execute first search
        first_results = self._execute_search_step(first_step, iteration)
        self.execution_history.append(first_results)
        iteration += 1
        
        # Analyze results
        self.current_findings = iterative_decomposer.analyze_search_results(
            first_results.get('raw_results', ''),
            self.goal,
            self.current_findings
        )
        
        logger.info(f"After iteration 1: confidence={self.current_findings['confidence']:.2f}, gaps={self.current_findings['gaps']}")
        
        # Iteratively refine
        while iteration < max_iterations:
            # Decide if we should continue
            next_step = iterative_decomposer.generate_next_step(
                self.goal,
                self.execution_history,
                self.current_findings
            )
            
            if next_step.get('stop_iteration'):
                logger.info(f"Stopping iteration: {next_step['purpose']}")
                break
            
            # Execute next step
            logger.info(f"Iteration {iteration + 1}: {next_step['purpose']}")
            logger.info(f"  Search query: {next_step['search_query']}")
            
            next_results = self._execute_search_step(next_step, iteration)
            self.execution_history.append(next_results)
            
            # Analyze new results
            new_findings = iterative_decomposer.analyze_search_results(
                next_results.get('raw_results', ''),
                self.goal,
                self.current_findings
            )
            
            # Merge findings
            self.current_findings['entities_found'].update(new_findings['entities_found'])
            self.current_findings['key_facts'].extend(new_findings['key_facts'])
            self.current_findings['gaps'] = new_findings['gaps']
            self.current_findings['confidence'] = new_findings['confidence']
            
            logger.info(f"After iteration {iteration + 1}: confidence={self.current_findings['confidence']:.2f}, gaps={self.current_findings['gaps']}")
            
            iteration += 1
        
        # Synthesize final answer
        final_answer = self._synthesize_iterative_answer()
        
        return {
            'execution_type': 'iterative',
            'goal': self.goal,
            'category': analysis['category'],
            'total_iterations': iteration,
            'iterations': self.execution_history,
            'final_findings': self.current_findings,
            'final_answer': final_answer,
            'confidence': self.current_findings['confidence'],
            'reasoning': f'Iteratively researched using {iteration} searches, confidence={self.current_findings["confidence"]:.2f}',
            'execution_log': [
                {
                    'iteration': h.get('iteration'),
                    'query': h.get('query'),
                    'tool': h.get('tool'),
                    'gaps_filled': h.get('gaps_filled'),
                    'entities_found': h.get('entities_found')
                }
                for h in self.execution_history
            ]
        }
    
    def _execute_search_step(self, step: Dict, iteration: int) -> Dict:
        """Execute a search step and return results"""
        query = step['search_query']
        
        # Use tool selector to execute search
        if step['tool'] == 'web_search':
            from Back_End.tools import web_search
            results = web_search(query)
        else:
            logger.warning(f"Unknown tool: {step['tool']}")
            results = {'results': []}
        
        # Capture raw results for analysis
        raw_results = str(results)
        if isinstance(results, dict) and 'results' in results:
            raw_results = '\n'.join([
                f"{r.get('title', '')}: {r.get('snippet', '')}"
                for r in results.get('results', [])[:3]
            ])
        
        return {
            'iteration': iteration,
            'query': query,
            'tool': step['tool'],
            'purpose': step['purpose'],
            'raw_results': raw_results,
            'results': results,
            'gaps_filled': [],  # Will be set by caller
            'entities_found': []  # Will be set by caller
        }
    
    def _extract_answer_from_steps(self, steps: List[Dict]) -> str:
        """Extract answer from atomic execution steps"""
        # Look for the most recent successful observation
        for step in reversed(steps):
            # Handle both step format and simple dict format
            obs = step.get('observation', step) if 'observation' in step else step
            
            if obs and isinstance(obs, dict) and 'error' not in obs:
                # Format based on observation type
                if 'result' in obs:
                    return f"The result is: {obs['result']}"
                if 'results' in obs and obs['results']:
                    if isinstance(obs['results'], list) and len(obs['results']) > 0:
                        first_result = obs['results'][0]
                        if isinstance(first_result, dict):
                            snippet = first_result.get('snippet', '')
                            return snippet if snippet else str(first_result)
                        return str(first_result)
                    return str(obs['results'])
                
                # Check for direct result/answer key
                if 'answer' in obs:
                    return obs['answer']
                
                # Generic dict observation
                if obs and obs != step:
                    return str(obs)
        
        return "Unable to find answer from execution steps"
    
    def _synthesize_iterative_answer(self) -> str:
        """Synthesize final answer from iterative findings"""
        if llm_client.enabled:
            # Use LLM to create natural answer
            facts_text = '\n'.join(self.current_findings['key_facts'][:5])
            entities_text = '\n'.join([
                f"- {e}: {info}" 
                for e, info in self.current_findings['entities_found'].items()
            ])
            
            prompt = f"""Goal: {self.goal}

Key Facts Discovered:
{facts_text}

Entities Found:
{entities_text}

Create a natural, conversational answer to the goal based on these findings."""
            
            answer = llm_client.complete(prompt, max_tokens=300, temperature=0.7)
            if answer:
                return answer.strip()
        
        # Fallback: format findings as bullet points
        lines = []
        
        if self.current_findings['entities_found']:
            lines.append("Found Information:")
            for entity, info in list(self.current_findings['entities_found'].items())[:3]:
                lines.append(f"• {entity}: {info}")
        
        if self.current_findings['key_facts']:
            lines.append("\nKey Facts:")
            for fact in self.current_findings['key_facts'][:3]:
                lines.append(f"• {fact}")
        
        return '\n'.join(lines) if lines else "Research completed but no conclusive answer found"


def execute_goal_iteratively(goal: str, domain: str = None) -> Dict:
    """
    Execute goal using iterative decomposition (preferred method).
    
    This is smarter than composite_agent.py because:
    - Simple goals solved in 1 step
    - Complex goals iterate until sufficient info found
    - Each result informs the next search query
    """
    executor = IterativeExecutor(goal, domain=domain)
    return executor.execute()

