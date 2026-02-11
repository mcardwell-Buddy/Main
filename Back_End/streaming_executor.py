"""
Streaming execution wrapper that provides real-time progress updates via WebSocket.
"""
import logging
import asyncio
import json
from typing import Dict, List, Optional, Callable
from Back_End.agent import Agent
from Back_End.goal_decomposer import goal_decomposer
from Back_End.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamingExecutor:
    """
    Wraps agent execution to provide real-time progress updates.
    """
    
    def __init__(self, websocket=None):
        self.websocket = websocket
        
    async def send_update(self, update: Dict):
        """Send progress update via WebSocket"""
        if self.websocket:
            try:
                await self.websocket.send_json(update)
            except Exception as e:
                logger.error(f"Failed to send WebSocket update: {e}")
    
    async def execute_with_streaming(self, goal: str, domain: Optional[str] = None) -> Dict:
        """
        Execute goal with real-time streaming updates.
        
        Sends updates for:
        - Goal classification
        - Subgoal decomposition
        - Each tool execution
        - Reflections
        - Final synthesis
        """
        
        # Step 1: Classify goal
        await self.send_update({
            'type': 'classification',
            'status': 'analyzing',
            'message': 'Analyzing your question...'
        })
        
        classification = goal_decomposer.classify_goal(goal)
        
        await self.send_update({
            'type': 'classification',
            'status': 'complete',
            'is_composite': classification['is_composite'],
            'goal_type': classification.get('type', 'unknown'),
            'subgoals_count': len(classification.get('subgoals', []))
        })
        
        if not classification['is_composite']:
            # Atomic goal - single agent execution
            return await self._execute_atomic_streaming(goal, domain)
        else:
            # Composite goal - decompose and execute
            return await self._execute_composite_streaming(goal, domain, classification)
    
    async def _execute_atomic_streaming(self, goal: str, domain: Optional[str]) -> Dict:
        """Execute atomic goal with streaming updates"""
        
        await self.send_update({
            'type': 'execution_start',
            'goal': goal,
            'mode': 'atomic'
        })
        
        agent = Agent(goal, domain=domain)
        steps = []
        step_num = 0
        
        while not agent.state.done and step_num < Config.MAX_AGENT_STEPS:
            step_num += 1
            
            # Send "thinking" update
            await self.send_update({
                'type': 'step_start',
                'step_number': step_num,
                'status': 'thinking',
                'message': f'Step {step_num}: Deciding next action...'
            })
            
            # Execute step
            state = agent.step()
            steps.append(state)
            
            # Extract tool from decision (correct structure)
            tool_used = state.get('decision', {}).get('tool', 'none')
            
            # Send step result
            await self.send_update({
                'type': 'step_complete',
                'step_number': step_num,
                'tool_used': tool_used,
                'observation': self._summarize_observation(state.get('observation')),
                'confidence': agent.state.confidence,
                'done': state.get('done', False)
            })
            
            if state.get('done'):
                break
        
        # Final answer
        final_answer = self._extract_answer(steps)
        
        await self.send_update({
            'type': 'execution_complete',
            'goal_type': 'atomic',
            'final_answer': final_answer,
            'confidence': agent.state.confidence,
            'total_steps': len(steps)
        })
        
        return {
            'goal_type': 'atomic',
            'goal': goal,
            'steps': steps,
            'final_answer': final_answer,
            'final_confidence': agent.state.confidence
        }
    
    async def _execute_composite_streaming(self, goal: str, domain: Optional[str], 
                                          classification: Dict) -> Dict:
        """Execute composite goal with streaming updates"""
        
        subgoals = classification['subgoals']
        
        await self.send_update({
            'type': 'decomposition',
            'subgoals': subgoals,
            'count': len(subgoals),
            'message': f'Breaking down into {len(subgoals)} steps...'
        })
        
        subgoal_results = []
        
        for idx, subgoal in enumerate(subgoals):
            # Start subgoal
            await self.send_update({
                'type': 'subgoal_start',
                'subgoal_index': idx,
                'subgoal_total': len(subgoals),
                'subgoal': subgoal['goal'],
                'subgoal_type': subgoal.get('type', 'general')
            })
            
            # Execute subgoal
            agent = Agent(subgoal['goal'], domain=domain)
            subgoal_steps = []
            step_num = 0
            
            while not agent.state.done and step_num < Config.MAX_AGENT_STEPS:
                step_num += 1
                
                await self.send_update({
                    'type': 'subgoal_step',
                    'subgoal_index': idx,
                    'step_number': step_num,
                    'status': 'executing'
                })
                
                state = agent.step()
                subgoal_steps.append(state)
                
                # Extract tool from decision (correct structure)
                tool_used = state.get('decision', {}).get('tool', 'none')
                
                await self.send_update({
                    'type': 'subgoal_step_complete',
                    'subgoal_index': idx,
                    'step_number': step_num,
                    'tool_used': tool_used,
                    'confidence': agent.state.confidence,
                    'message': f'Used {tool_used}'
                })
                
                # Check if done or has good result
                if state.get('done') or agent.state.done:
                    logger.info(f"Subgoal {idx} complete after {step_num} steps")
                    break
                    
                # Early stop if we have a good observation
                obs = state.get('observation', {})
                if obs and 'error' not in obs and agent.state.confidence > 0.7:
                    logger.info(f"Subgoal {idx} early stop - good confidence")
                    break
            
            # Subgoal complete
            findings = self._extract_findings(subgoal_steps)
            
            await self.send_update({
                'type': 'subgoal_complete',
                'subgoal_index': idx,
                'confidence': agent.state.confidence,
                'findings_count': len(findings)
            })
            
            subgoal_results.append({
                'subgoal_index': idx,
                'subgoal': subgoal['goal'],
                'steps': len(subgoal_steps),
                'confidence': agent.state.confidence,
                'key_findings': findings
            })
        
        # Synthesis
        await self.send_update({
            'type': 'synthesis_start',
            'message': 'Combining results...'
        })
        
        synthesis = self._synthesize_results(subgoal_results, goal)
        
        await self.send_update({
            'type': 'execution_complete',
            'goal_type': 'composite',
            'synthesis': synthesis,
            'subgoals_completed': len(subgoals)
        })
        
        return {
            'goal_type': 'composite',
            'original_goal': goal,
            'subgoals': subgoals,
            'subgoal_results': subgoal_results,
            'synthesis': synthesis,
            'final_confidence': self._compute_final_confidence(subgoal_results)
        }
    
    def _summarize_observation(self, observation) -> str:
        """Summarize observation for streaming (limit length)"""
        if not observation:
            return "No result"
        
        obs_str = str(observation)
        if len(obs_str) > 200:
            return obs_str[:200] + "..."
        return obs_str
    
    def _extract_answer(self, steps: List[Dict]) -> str:
        """Extract final answer from steps"""
        for step in reversed(steps):
            obs = step.get('observation')
            if obs and not step.get('error'):
                if isinstance(obs, dict) and obs.get('answer'):
                    return obs['answer']
                elif isinstance(obs, str):
                    return obs[:500]
        return "Unable to determine answer"
    
    def _extract_findings(self, steps: List[Dict]) -> List[str]:
        """Extract key findings from steps"""
        findings = []
        for step in steps:
            obs = step.get('observation')
            if obs and not step.get('error'):
                if isinstance(obs, dict):
                    if obs.get('results'):
                        findings.extend(obs['results'][:2])
                    elif obs.get('answer'):
                        findings.append(obs['answer'])
                elif isinstance(obs, str):
                    findings.append(obs[:200])
        return findings[:5]
    
    def _synthesize_results(self, subgoal_results: List[Dict], original_goal: str) -> Dict:
        """Synthesize subgoal results"""
        from Back_End.llm_client import llm_client
        
        if not llm_client.enabled:
            return {
                'synthesis_narrative': "Results compiled from subgoals.",
                'key_points': [r['subgoal'] for r in subgoal_results],
                'summary': f"Completed {len(subgoal_results)} steps"
            }
        
        # Use LLM to synthesize
        try:
            prompt = f"""Synthesize these research findings for: "{original_goal}"

Findings:
{json.dumps([{'subgoal': r['subgoal'], 'findings': r['key_findings'][:3]} for r in subgoal_results], indent=2)}

Provide a comprehensive synthesis in JSON:
{{
  "synthesis_narrative": "<cohesive answer>",
  "key_points": ["<point 1>", "<point 2>", ...],
  "summary": "<brief summary>"
}}"""

            response = llm_client.complete(prompt, max_tokens=600)
            return json.loads(response)
        except:
            return {
                'synthesis_narrative': f"Completed {len(subgoal_results)} research steps.",
                'key_points': [r['subgoal'] for r in subgoal_results],
                'summary': "Synthesis unavailable"
            }
    
    def _compute_final_confidence(self, subgoal_results: List[Dict]) -> float:
        """Compute overall confidence from subgoals"""
        if not subgoal_results:
            return 0.0
        
        confidences = [r.get('confidence', 0.0) for r in subgoal_results]
        return sum(confidences) / len(confidences)

