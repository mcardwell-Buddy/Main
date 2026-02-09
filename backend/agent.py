import logging
from backend.memory import memory
from backend.memory_manager import memory_manager
from backend.tool_registry import tool_registry
from backend.tool_selector import tool_selector
from backend.tools import register_foundational_tools, register_code_awareness_tools
from backend.additional_tools import register_additional_tools
from backend.web_tools import register_web_tools
from backend.config import Config
from backend.autonomy_manager import autonomy_manager
from backend.feedback_manager import feedback_manager

register_foundational_tools(tool_registry)
register_additional_tools(tool_registry)
register_code_awareness_tools(tool_registry)
register_web_tools(tool_registry)

class AgentState:
    def __init__(self, goal, domain=None):
        self.goal = goal
        self.domain = domain or self._infer_domain(goal)
        self.context = {}
        self.memory = {}
        self.confidence = 1.0
        self.last_action = None
        self.done = False
        self.steps = 0
        # observations will hold structured step records: {'step', 'decision', 'observation'}
        self.observations = []
    
    def _infer_domain(self, goal: str) -> str:
        """
        Infer domain from goal keywords.
        Falls back to '_global' if no match.
        """
        goal_lower = goal.lower()
        
        # Crypto/Blockchain domain (check first for priority)
        if any(kw in goal_lower for kw in ["bitcoin", "eth", "crypto", "blockchain", "defi", "coin", "nft", "token"]):
            return "crypto"
        
        # Marketing domain
        if any(kw in goal_lower for kw in ["market", "campaign", "customer", "brand", "audience"]):
            return "marketing"
        
        # Engineering domain
        if any(kw in goal_lower for kw in ["code", "debug", "api", "python", "javascript", "backend", "frontend", "deploy"]):
            return "engineering"
        
        # Operations domain
        if any(kw in goal_lower for kw in ["schedule", "budget", "resource", "timeline", "plan", "organize"]):
            return "operations"
        
        # Default: unknown/neutral domain
        return "_global"

class Agent:
    def __init__(self, goal, domain=None, preferred_tool=None):
        self.state = AgentState(goal, domain=domain)
        self.preferred_tool = preferred_tool  # For simple goals, hint which tool to use

    def step(self):
        if self.state.done or self.state.steps >= Config.MAX_AGENT_STEPS:
            self.state.done = True
            
            # Save goal completion summary if agent completed successfully
            if self.state.steps > 0:
                completion_data = {
                    'goal': self.state.goal,
                    'steps_taken': self.state.steps,
                    'final_confidence': self.state.confidence,
                    'tools_used': list(set(
                        (s.get('decision', {}).get('tool') for s in self.state.observations 
                         if s.get('decision', {}).get('tool'))
                    ))
                }
                memory_manager.save_if_important(
                    f"goal_completion:{self.state.goal}",
                    'goal_completion',
                    completion_data,
                    {'success': True},
                    domain=self.state.domain  # NEW: Pass domain
                )
            
            return self._emit_state('done')
        
        # INTELLIGENT TOOL SELECTION
        # For simple goals with preferred tool, use it
        if self.preferred_tool and self.state.steps == 0:
            tool_name = self.preferred_tool
            tool_input = self.state.goal
            confidence = 0.9
        else:
            # Use learned patterns + historical performance to select best tool
            tool_name, tool_input, confidence = tool_selector.select_tool(
                self.state.goal,
                context={
                    'refined': self.state.context.get('refined'),
                    'domain': self.state.domain,  # NEW: Pass domain
                    'step': self.state.steps
                }
            )
        
        if tool_name and confidence >= 0.15:  # Lower threshold for more tool usage
            action = {'tool': tool_name, 'input': tool_input}
            logging.info(f"Selected {tool_name} with confidence {confidence:.2f}")
        else:
            action = {'tool': None, 'input': None}
            logging.info(f"No suitable tool found (max confidence: {confidence:.2f})")
        
        self.state.last_action = action
        # Tool execution (pass domain to registry)
        if action['tool']:
            if not autonomy_manager.can_tool_execute_at_level(action['tool'], autonomy_manager.get_current_level()):
                observation = {
                    'error': 'tool_not_allowed',
                    'tool': action['tool'],
                    'autonomy_level': autonomy_manager.get_current_level()
                }
            else:
                observation = tool_registry.call(action['tool'], action['input'], domain=self.state.domain)
        else:
            observation = {'note': 'No tool used.'}
        # Record the step as structured data
        step_record = {'step': self.state.steps, 'decision': action, 'observation': observation}
        self.state.observations.append(step_record)
        
        # Save important observations (errors, significant results)
        if 'error' in observation or (isinstance(observation.get('results'), list) and len(observation.get('results', [])) > 3):
            memory_manager.save_if_important(
                f"observation:{self.state.goal}:{self.state.steps}",
                'observation',
                observation,
                {'goal': self.state.goal, 'step': self.state.steps},
                domain=self.state.domain  # NEW: Pass domain
            )

        # Reflection: call reflect tool safely (avoid reflecting on reflect actions)
        reflection = None
        try:
            if action.get('tool') != 'reflect':
                # prepare recent steps (last N) and tools used
                recent = self.state.observations[-3:]
                tools_used = list({(s.get('decision') or {}).get('tool') for s in recent if isinstance(s, dict) and (s.get('decision') or {}).get('tool')})
                # memory excerpt (best-effort)
                mem_excerpt = {}
                try:
                    mem_excerpt = {'last_reflection': memory.get(f"last_reflection:{self.state.goal}")}
                except Exception:
                    mem_excerpt = {}
                # Call reflect with keyword arguments for robust reflection
                reflection = tool_registry.call('reflect', 
                    steps=recent, 
                    tools_used=tools_used, 
                    goal=self.state.goal, 
                    confidence=self.state.confidence, 
                    memory_excerpt=mem_excerpt,
                    domain=self.state.domain)
                
                # INTELLIGENT MEMORY: Only save if important
                context = {
                    'goal': self.state.goal,
                    'steps_taken': self.state.steps,
                    'tools_used': tools_used
                }
                saved = memory_manager.save_if_important(
                    f"last_reflection:{self.state.goal}",
                    'reflection',
                    reflection,
                    context,
                    domain=self.state.domain  # NEW: Pass domain
                )
                
                if saved:
                    logging.info(f"Reflection saved (important): effectiveness={reflection.get('effectiveness_score')}")
                else:
                    logging.debug(f"Reflection skipped (low importance): effectiveness={reflection.get('effectiveness_score')}")
                # adjust confidence if provided
                try:
                    adj = float(reflection.get('confidence_adjustment', 0.0))
                    if adj:
                        self.state.confidence = max(0.0, min(1.0, self.state.confidence + adj))
                except Exception:
                    pass
                # Use reflection advisory to adjust strategy for next steps (non-authoritative)
                try:
                    eff = float(reflection.get('effectiveness_score', 0.0))
                    if eff < 0.6 and 'search' in self.state.goal.lower() and not self.state.context.get('refined'):
                        # simple adaptive behavior: mark refined to alter next query
                        self.state.context['refined'] = True
                except Exception:
                    pass
        except Exception as e:
            logging.error(f"Reflection call failed: {e}")
            reflection = {'error': 'reflection_failed'}
        
        self.state.steps += 1
        
        # Check if goal is complete - for simple queries, stop after first successful tool use
        if action.get('tool') and observation and 'error' not in observation:
            # Simple goals (time, calculation, single fact) - stop after success
            simple_patterns = ['time', 'date', 'calculate', 'what is', 'how much']
            if any(pattern in self.state.goal.lower() for pattern in simple_patterns):
                logging.info(f"Simple goal completed after {self.state.steps} step(s)")
                self.state.done = True
        
        # Fallback: stop at max steps
        if self.state.steps >= Config.MAX_AGENT_STEPS:
            self.state.done = True
            
        return self._emit_state('step', observation, reflection)

    def _emit_state(self, phase, observation=None, reflection=None):
        # Apply feedback-based confidence adjustment
        feedback_stats = feedback_manager.get_feedback_stats(self.state.goal, self.state.domain)
        if feedback_stats['total_feedback'] > 0:
            # Adjust confidence based on user feedback history
            feedback_adjustment = feedback_stats['confidence_adjustment']
            self.state.confidence = max(0.0, min(1.0, self.state.confidence * feedback_adjustment))
            logging.info(f"Applied feedback adjustment: {feedback_adjustment:.2f} (based on {feedback_stats['total_feedback']} feedback)")
        
        return {
            'phase': phase,
            'thought': f"Goal: {self.state.goal}",
            'decision': self.state.last_action,
            'observation': observation,
            'reflection': reflection,
            'state': {
                'steps': self.state.steps,
                'done': self.state.done,
                'confidence': self.state.confidence
            },
            'done': self.state.done
        }
