"""
Composite Agent Executor: Handles both atomic and composite goals.
Wraps the standard Agent to add decomposition support.
"""

import logging
from typing import Dict, List, Tuple
from Back_End.agent import Agent as AtomicAgent
from Back_End.goal_decomposer import goal_decomposer
from Back_End.config import Config
from Back_End.memory_manager import memory_manager
from Back_End.llm_client import llm_client


class CompositeAgentExecutor:
    """
    Executes both atomic and composite goals.
    
    - Atomic goals: Run through standard agent loop
    - Composite goals: Decompose, execute subgoals sequentially, synthesize results
    """
    
    def __init__(self, goal: str, domain: str = None):
        self.goal = goal
        self.domain = domain
        self.classification = goal_decomposer.classify_goal(goal)
        self.is_composite = self.classification['is_composite']
        self.subgoals = self.classification['subgoals']
    
    def execute(self) -> Dict:
        """
        Execute goal (atomic or composite) and return results.
        
        Returns:
        - Atomic: {'goal_type': 'atomic', 'steps': [...], ...}
        - Composite: {'goal_type': 'composite', 'subgoals': [...], 'synthesis': {...}, ...}
        """
        if not self.is_composite:
            return self._execute_atomic()
        else:
            return self._execute_composite()
    
    def _execute_atomic(self) -> Dict:
        """Execute single-goal (standard agent loop)"""
        agent = AtomicAgent(self.goal, domain=self.domain)
        steps = []
        
        while not agent.state.done and len(steps) < Config.MAX_AGENT_STEPS:
            state = agent.step()
            steps.append(state)
            if state.get('done'):
                break
        
        # Extract final answer from the last successful observation
        final_answer = self._extract_answer(steps)
        
        # Extract list of tools that were actually used
        tools_used = list(set(
            s.get('decision', {}).get('tool') 
            for s in steps 
            if s.get('decision', {}).get('tool')
        ))
        
        return {
            'goal_type': 'atomic',
            'goal': self.goal,
            'domain': agent.state.domain,
            'steps': steps,
            'final_confidence': agent.state.confidence,
            'total_steps': len(steps),
            'final_answer': final_answer,
            'tools_used': tools_used
        }
    
    def _execute_composite(self) -> Dict:
        """
        Execute composite goal: decompose → run subgoals → synthesize
        """
        logging.info(f"Executing composite goal with {len(self.subgoals)} subgoals")
        
        subgoal_results = []
        combined_findings = []
        
        for subgoal_idx, subgoal in enumerate(self.subgoals):
            logging.info(f"Subgoal {subgoal_idx + 1}/{len(self.subgoals)}: {subgoal['goal'][:60]}...")
            
            # Execute each subgoal through standard agent loop
            subgoal_agent = AtomicAgent(subgoal['goal'], domain=self.domain)
            subgoal_steps = []
            
            while not subgoal_agent.state.done and len(subgoal_steps) < Config.MAX_AGENT_STEPS:
                state = subgoal_agent.step()
                subgoal_steps.append(state)
                if state.get('done'):
                    break
            
            # Capture subgoal result
            subgoal_result = {
                'subgoal_index': subgoal_idx,
                'subgoal': subgoal['goal'],
                'subgoal_type': subgoal.get('type', 'general'),
                'steps': len(subgoal_steps),
                'confidence': subgoal_agent.state.confidence,
                'effectiveness': self._compute_effectiveness(subgoal_steps),
                'key_findings': self._extract_findings(subgoal_steps)
            }
            subgoal_results.append(subgoal_result)
            combined_findings.extend(subgoal_result['key_findings'])
            
            logging.info(f"  ✓ Completed (confidence: {subgoal_agent.state.confidence:.2f})")
        
        # Synthesis step: combine all findings
        synthesis = self._synthesize_results(subgoal_results)
        
        return {
            'goal_type': 'composite',
            'original_goal': self.goal,
            'domain': self.domain or '_global',
            'subgoals': self.subgoals,
            'subgoal_results': subgoal_results,
            'synthesis': synthesis,
            'final_confidence': self._compute_final_confidence(subgoal_results),
            'total_subgoals': len(self.subgoals),
            'total_steps': sum(r['steps'] for r in subgoal_results)
        }
    
    def _extract_answer(self, steps: List[Dict]) -> str:
        """
        Extract final answer from step observations.
        Priority: user corrections > LLM synthesis > successful observations > fallback
        """
        # First, check if user has provided a correction for this question
        correction = self._check_user_corrections()
        if correction:
            logging.info(f"Using user correction for '{self.goal}'")
            return f"[Learned from correction] {correction}"
        
        # Try LLM-based answer synthesis if available
        if llm_client.enabled and steps:
            llm_answer = llm_client.synthesize_answer(self.goal, steps)
            if llm_answer:
                logging.info("Using LLM-synthesized answer")
                return llm_answer
        
        # Fallback to pattern-based extraction
        # Look for the first successful tool observation
        for step in reversed(steps):  # Start from most recent
            obs = step.get('observation', {})
            if obs and 'error' not in obs:
                # For time-related queries, be smart about what to return
                if 'date' in obs and 'time' in obs:
                    # Check what they actually asked for
                    goal_lower = self.goal.lower()
                    if 'date' in goal_lower and 'time' not in goal_lower:
                        return f"The date is {obs.get('date')}"
                    elif 'time' in goal_lower and 'date' not in goal_lower:
                        return f"The current time is {obs.get('time')}"
                    else:
                        return f"The current date and time is {obs.get('date')} at {obs.get('time')}"
                
                # For calculation results
                if 'result' in obs:
                    return f"The result is: {obs.get('result')}"
                
                # For web search results - synthesize into readable format
                if 'results' in obs and isinstance(obs['results'], list) and obs['results']:
                    return self._synthesize_search_results(obs['results'])
                
                # For learning query results
                if 'topic' in obs and 'confidence' in obs:
                    return self._format_learning_query(obs)
                
                # For understanding metrics
                if 'overall_confidence' in obs and 'tool_mastery' in obs:
                    return self._format_understanding_metrics(obs)
                
                # For file contents
                if 'content' in obs:
                    return obs.get('content', '')[:500]  # Truncate long content
                
                # Generic observation
                return str(obs)
        
        return "Unable to complete the task. No successful observations."
    
    def _check_user_corrections(self) -> str:
        """Check if user has provided a correction for this goal"""
        try:
            # Query memory for user corrections matching this goal
            observations = memory_manager.retrieve_observations(
                goal_pattern=self.goal,
                domain=self.domain or "_global",
                top_k=1
            )
            
            # Look for corrections
            for obs in observations:
                if obs.get('type') == 'user_correction' and obs.get('original_goal') == self.goal:
                    return obs.get('correction')
            
            return None
        except Exception as e:
            logging.warning(f"Failed to check user corrections: {e}")
            return None
    
    def _synthesize_search_results(self, results: List[Dict]) -> str:
        """Convert raw search results into a readable summary"""
        if not results:
            return "No search results found."
        
        # Get the top result
        top_result = results[0]
        
        # Extract key information
        title = top_result.get('title', 'Untitled')
        link = top_result.get('link', '')
        snippet = top_result.get('snippet', '')
        source = top_result.get('source', top_result.get('displayed_link', ''))
        
        # Build readable answer
        answer_parts = []
        
        # Start with the snippet (main info)
        if snippet:
            answer_parts.append(snippet)
        
        # Add source information
        if source:
            answer_parts.append(f"\n\nSource: {source}")
        
        # Add link if available
        if link:
            answer_parts.append(f"Learn more: {link}")
        
        # If there are multiple relevant results, mention them
        if len(results) > 1:
            additional_sources = []
            for result in results[1:4]:  # Include up to 3 more sources
                if 'title' in result:
                    additional_sources.append(f"- {result.get('title')} ({result.get('source', 'source')})")
            
            if additional_sources:
                answer_parts.append("\n\nAdditional sources:")
                answer_parts.extend(additional_sources)
        
        return '\n'.join(answer_parts)
    
    def _format_learning_query(self, obs: Dict) -> str:
        """Format learning query results into readable text"""
        topic = obs.get('topic', 'Unknown')
        confidence = obs.get('confidence', 0)
        expertise = obs.get('expertise_level', 'Unknown')
        data_points = obs.get('data_points', 0)
        gaps = obs.get('knowledge_gaps', [])
        suggestions = obs.get('learning_suggestions', [])
        
        parts = [
            f"📚 Knowledge about '{topic}':",
            f"• Expertise Level: {expertise} ({int(confidence * 100)}% confident)",
            f"• Based on {data_points} data points",
        ]
        
        if gaps:
            parts.append(f"\n🔍 Knowledge Gaps:")
            parts.extend([f"  - {gap}" for gap in gaps[:3]])
        
        if suggestions:
            parts.append(f"\n💡 Suggestions:")
            parts.extend([f"  - {sug}" for sug in suggestions[:3]])
        
        return '\n'.join(parts)
    
    def _format_understanding_metrics(self, obs: Dict) -> str:
        """Format understanding metrics into readable text"""
        confidence = obs.get('overall_confidence', 0)
        level = obs.get('confidence_level', 'Unknown')
        total_calls = obs.get('total_tool_calls', 0)
        success_rate = obs.get('overall_success_rate', 0)
        mastery = obs.get('tool_mastery', {})
        growth = obs.get('growth_indicators', [])
        
        parts = [
            f"📊 Learning Metrics:",
            f"• Overall Level: {level} ({int(confidence * 100)}% confident)",
            f"• Total Experience: {total_calls} tool calls with {int(success_rate * 100)}% success",
            f"\n🏆 Tool Mastery:",
            f"  Expert: {', '.join(mastery.get('expert', ['None']))}",
            f"  Learning: {', '.join(mastery.get('learning', ['None']))}",
        ]
        
        if mastery.get('novice'):
            parts.append(f"  Improving: {', '.join(mastery.get('novice', []))}")
        
        if growth:
            parts.append(f"\n📈 Growth:")
            parts.extend([f"  - {g}" for g in growth[:3]])
        
        return '\n'.join(parts)
        
        return {
            'goal_type': 'composite',
            'original_goal': self.goal,
            'domain': self.domain or '_global',
            'subgoals': self.subgoals,
            'subgoal_results': subgoal_results,
            'synthesis': synthesis,
            'final_confidence': self._compute_final_confidence(subgoal_results),
            'total_subgoals': len(self.subgoals),
            'total_steps': sum(r['steps'] for r in subgoal_results)
        }
    
    def _compute_effectiveness(self, steps: List[Dict]) -> float:
        """Compute how effective subgoal execution was (0.0-1.0)"""
        if not steps:
            return 0.0
        
        # Count steps where a tool was used
        tool_steps = sum(1 for s in steps if s.get('decision', {}).get('tool') is not None)
        # Count steps with observations
        obs_steps = sum(1 for s in steps if s.get('observation') is not None)
        
        if len(steps) == 0:
            return 0.0
        
        return min(1.0, (tool_steps + obs_steps) / (len(steps) * 2.0))
    
    def _extract_findings(self, steps: List[Dict]) -> List[str]:
        """Extract key findings from step observations"""
        findings = []
        
        for step in steps:
            obs = step.get('observation', {})
            
            # Extract from search results
            if 'results' in obs and isinstance(obs['results'], list):
                for result in obs['results'][:2]:  # First 2 results
                    result_str = str(result)
                    if len(result_str) > 200:
                        result_str = result_str[:200] + "..."
                    findings.append(result_str)
            
            # Extract from reflections
            if 'reflection' in step and step['reflection']:
                refl = step['reflection']
                if 'strategy_adjustment' in refl:
                    findings.append(f"Strategy: {refl['strategy_adjustment'][:100]}")
        
        # Return unique findings, max 5
        return list(dict.fromkeys(findings))[:5]
    
    def _synthesize_results(self, subgoal_results: List[Dict]) -> Dict:
        """Synthesize results from all subgoals"""
        findings_by_type = {}
        
        for result in subgoal_results:
            sg_type = result['subgoal_type']
            if sg_type not in findings_by_type:
                findings_by_type[sg_type] = []
            findings_by_type[sg_type].extend(result['key_findings'])
        
        # Build synthesis narrative
        synthesis_lines = []
        for subgoal_result in subgoal_results:
            synthesis_lines.append(
                f"• {subgoal_result['subgoal_type'].title()}: {', '.join(subgoal_result['key_findings'][:2])}"
            )
        
        overall_effectiveness = sum(r['effectiveness'] for r in subgoal_results) / len(subgoal_results) if subgoal_results else 0.0
        
        return {
            'findings_by_type': findings_by_type,
            'synthesis_narrative': '\n'.join(synthesis_lines),
            'overall_effectiveness': overall_effectiveness,
            'recommendation': self._generate_recommendation(overall_effectiveness)
        }
    
    def _compute_final_confidence(self, subgoal_results: List[Dict]) -> float:
        """Compute final confidence as weighted average of subgoal confidences"""
        if not subgoal_results:
            return 0.0
        
        # Weight later subgoals higher (synthesis is most important)
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for idx, result in enumerate(subgoal_results):
            weight = 1.0 + (idx / len(subgoal_results))  # Increasing weight
            weighted_confidence += result['confidence'] * weight
            total_weight += weight
        
        return min(1.0, weighted_confidence / total_weight if total_weight > 0 else 0.0)
    
    def _generate_recommendation(self, overall_effectiveness: float) -> str:
        """Generate recommendation based on synthesis effectiveness"""
        if overall_effectiveness >= 0.8:
            return "High confidence in synthesis. Findings are well-supported."
        elif overall_effectiveness >= 0.6:
            return "Moderate confidence. May need additional research on specific areas."
        else:
            return "Low confidence. Recommend deeper analysis of key findings."


def execute_goal(goal: str, domain: str = None) -> Dict:
    """
    Execute a goal (atomic or composite).
    
    Automatically detects if goal is composite and handles accordingly.
    """
    executor = CompositeAgentExecutor(goal, domain=domain)
    return executor.execute()

