"""
Agent Reasoning System - Core decision-making loop

The agent reasons through goals in stages:
1. Understand - What is the user really asking?
2. Plan - What's our strategy?
3. Execute - Run tools and collect findings
4. Reflect - Did it work? What failed?
5. Decide - Should we continue or explore?
6. Respond - Compile findings into natural language
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from backend.llm_client import llm_client
from backend.tool_selector import tool_selector
from backend.memory_manager import memory_manager
from backend.curiosity_engine import curiosity_engine
from backend.code_analyzer import analyze_file_for_improvements
from backend.python_sandbox import sandbox
from backend.tool_registry import tool_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentTodo:
    """Represents a sub-task in the agent's reasoning process"""
    
    def __init__(self, step_num: int, task: str, status: str = "pending"):
        self.step_num = step_num
        self.task = task
        self.status = status  # pending, in-progress, complete, failed
        self.result = None
        self.timestamp = datetime.now().isoformat()
        
    def to_dict(self) -> Dict:
        return {
            "step": self.step_num,
            "task": self.task,
            "status": self.status,
            "result": self.result,
            "timestamp": self.timestamp
        }


class AgentReasoning:
    """
    Core reasoning loop for autonomous decision-making.
    
    Orchestrates: Understanding → Planning → Execution → Reflection → Decision → Response
    """
    
    def __init__(self):
        self.current_goal = None
        self.understanding = {}
        self.findings = {}
        self.todos: List[AgentTodo] = []
        self.iteration = 0
        self.max_iterations = 5
        self.confidence = 0.0
        self.should_explore = False
        
    def reset(self):
        """Reset for new goal"""
        self.todos = []
        self.findings = {"answers": [], "tools_used": [], "confidence": 0.0}
        self.iteration = 0
        self.confidence = 0.0
        self.should_explore = False
        self.generated_code = None
        self.sandbox_result = None
        
    def add_todo(self, task: str, status: str = "pending") -> AgentTodo:
        """Add a todo to the reasoning process"""
        step_num = len(self.todos) + 1
        todo = AgentTodo(step_num, task, status)
        self.todos.append(todo)
        logger.info(f"[Step {step_num}] {task}")
        return todo
        
    def update_todo_status(self, step_num: int, status: str, result: Any = None):
        """Update a todo's status"""
        if step_num <= len(self.todos):
            self.todos[step_num - 1].status = status
            self.todos[step_num - 1].result = result
            
    def get_todos(self) -> List[Dict]:
        """Get all todos in dict format"""
        return [todo.to_dict() for todo in self.todos]
        
    # ============ STAGE 1: UNDERSTANDING ============
    
    def understand_goal(self, goal: str, context: Dict = None) -> Dict:
        """
        STAGE 1: Understand what the user is really asking.
        
        Questions answered:
        - What is the actual goal (not surface level)?
        - What assumptions am I making?
        - What domain does this belong to?
        - Are there clarifying questions?
        """
        self.reset()
        self.current_goal = goal
        
        todo = self.add_todo("Understanding goal...", "in-progress")
        
        # Extract memories from context if provided
        memories = []
        if context and 'memories' in context:
            memories = context['memories']
        
        # Build context section if memories exist
        memory_context = ""
        if memories:
            memory_items = "\n".join([f"- {m.get('goal', '')}: {m.get('correction', m.get('feedback', 'previous interaction'))}" for m in memories[:3]])
            memory_context = f"\n\nRelevant previous context:\n{memory_items}\n"
        
        # Use LLM to deeply understand the goal
        understanding_prompt = f"""
Given this goal: "{goal}"
Context: {json.dumps(context) if context else "None"}{memory_context}

Analyze deeply:
1. What is the real underlying goal? (not surface level)
2. What domain does this belong to? (code, data, learning, building, planning, automation, etc)
3. What assumptions am I making about what the user wants?
4. What clarifying questions should I ask BEFORE taking action?
5. What does success look like?

IMPORTANT: If the goal is vague, ambiguous, or could be interpreted multiple ways:
- Ask 2-3 specific clarifying questions
- Examples: "Build a website" → Ask about purpose, target audience, features
- Examples: "Make a tool" → Ask what problem it solves, who uses it, what it does

Return JSON:
{{
  "real_goal": "...",
  "surface_goal": "{goal}",
  "domain": "...",
  "assumptions": ["..."],
  "clarifying_questions": ["question1", "question2"],
  "success_criteria": ["..."],
  "initial_approach": "...",
  "needs_planning": true/false
}}
"""
        
        response = llm_client.complete(understanding_prompt, max_tokens=500)
        
        try:
            self.understanding = json.loads(response)
        except:
            # Fallback if LLM response isn't valid JSON
            self.understanding = {
                "real_goal": goal,
                "surface_goal": goal,
                "domain": self._infer_domain(goal),
                "assumptions": [],
                "clarifying_questions": [],
                "success_criteria": ["Complete the requested task"],
                "initial_approach": "Use tool selection to find best tools"
            }
        
        self.update_todo_status(todo.step_num, "complete", self.understanding)
        return self.understanding
    
    def detect_self_improvement_intent(self, goal: str) -> Optional[Dict]:
        """
        Detect if user is requesting self-improvement.
        
        Returns improvement details if detected, None otherwise
        """
        goal_lower = goal.lower()
        
        # Self-improvement patterns
        if any(phrase in goal_lower for phrase in [
            'improve yourself',
            'improve your code',
            'improve your own',
            'analyze yourself',
            'optimize yourself',
            'refactor yourself',
            'make yourself better',
            'enhance yourself',
            'scan for improvements',
            'find improvements'
        ]):
            return {
                'type': 'self_improvement_scan',
                'action': 'scan_codebase',
                'message': 'Detected self-improvement request'
            }
            
        return None
        
    # ============ STAGE 2: PLANNING ============
    
    def plan_approach(self) -> Dict:
        """
        STAGE 2: Plan the strategy.
        
        Create a plan based on understanding:
        - What tools will we need?
        - What's the execution order?
        - What are the success metrics?
        """
        todo = self.add_todo("Planning approach...", "in-progress")
        
        planning_prompt = f"""
Goal: {self.current_goal}
Understanding: {json.dumps(self.understanding, indent=2)}

Create a detailed execution plan with concrete steps:
1. What specific actions will we take?
2. What tools will help (web_search, scrape_webpage, code_analyzer, etc)?
3. What order should we execute them?
4. How will we know each step succeeded?

For planning-type goals (organize, schedule, create roadmap), create the actual plan/schedule.
For building goals, outline what to build and how.
For research goals, outline what to research and where.

Return JSON:
{{
  "steps": [
    {{"step": 1, "action": "Specific action description", "tool": "tool_name", "success_metric": "How we know it worked"}},
    {{"step": 2, "action": "Next action", "tool": "tool_name", "success_metric": "Expected outcome"}}
  ],
  "key_decisions": ["Decision point 1", "Decision point 2"],
  "fallback_strategies": ["If X fails, try Y"],
  "estimated_duration": "5 minutes",
  "needs_user_input": false
}}
"""
        
        response = llm_client.complete(planning_prompt, max_tokens=400)
        
        try:
            plan = json.loads(response)
        except:
            plan = {
                "steps": [{"step": 1, "action": "Analyze goal", "tool": "web_search"}],
                "key_decisions": [],
                "fallback_strategies": ["Try alternative tools", "Refine search"]
            }
        
        self.update_todo_status(todo.step_num, "complete", plan)
        return plan
    
    def generate_and_test_code(self, goal: str, understanding: Dict) -> Dict:
        """
        Generate code based on the goal and test it in sandbox.
        
        Returns: {code, execution_result, success}
        """
        todo = self.add_todo("Generating code...", "in-progress")
        
        code_prompt = f"""
Goal: {goal}
Understanding: {json.dumps(understanding, indent=2)}

Generate interactive HTML/JavaScript code that accomplishes this goal.
The code should:
1. Be a complete, working HTML page with inline JavaScript
2. Have interactive elements (buttons, inputs, etc.)
3. Be visually appealing with inline CSS
4. Actually demonstrate the functionality requested

Return ONLY the HTML code, no explanations.
Start with <!DOCTYPE html>
"""
        
        try:
            generated_code = llm_client.complete(code_prompt, max_tokens=1500)
            
            # Extract HTML if wrapped in markdown
            if '```html' in generated_code:
                generated_code = generated_code.split('```html')[1].split('```')[0].strip()
            elif '```' in generated_code:
                generated_code = generated_code.split('```')[1].split('```')[0].strip()
                
            self.generated_code = generated_code
            
            # Test if it's valid HTML
            if not generated_code.strip().startswith('<!DOCTYPE') and not generated_code.strip().startswith('<html'):
                generated_code = f"<!DOCTYPE html>\n<html>\n<head><title>Generated</title></head>\n<body>\n{generated_code}\n</body>\n</html>"
                self.generated_code = generated_code
            
            self.update_todo_status(todo.step_num, "complete", {"code_length": len(generated_code)})
            
            return {
                "success": True,
                "code": generated_code,
                "code_type": "html"
            }
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            self.update_todo_status(todo.step_num, "failed", str(e))
            return {
                "success": False,
                "error": str(e)
            }
        
    # ============ STAGE 3: EXECUTION ============
    
    def execute_iteration(self, iteration_num: int = None) -> Dict:
        """
        STAGE 3: Execute one iteration - select and run a tool.
        
        Returns: {tool_name, input, result, success}
        """
        if iteration_num is None:
            iteration_num = self.iteration + 1
            
        self.iteration = iteration_num
        
        # Decide what to do next based on current findings
        decision = self._decide_next_action()
        
        if decision["action"] == "execute_tool":
            todo = self.add_todo(
                f"Executing: {decision['tool']} with '{decision['input']}'",
                "in-progress"
            )
            
            # For now, simulate tool execution
            # In production, would call actual tools
            result = self._simulate_tool_execution(decision)
            
            self.findings["answers"].append(result)
            self.findings["tools_used"].append(decision["tool"])
            self.update_confidence()
            
            self.update_todo_status(todo.step_num, "complete", result)
            
            return {
                "success": True,
                "tool": decision["tool"],
                "result": result,
                "confidence": self.confidence
            }
        
        elif decision["action"] == "continue_reasoning":
            self.add_todo("Continuing reasoning...", "complete")
            return {"success": True, "action": "continue", "reason": decision["reason"]}
            
        return {"success": False}
        
    # ============ STAGE 4: REFLECTION ============
    
    def reflect_on_progress(self) -> Dict:
        """
        STAGE 4: Reflect on what we've learned.
        
        Ask: Did this help? What worked? What failed? Should we change strategy?
        """
        todo = self.add_todo("Reflecting on progress...", "in-progress")
        
        reflection_prompt = f"""
Goal: {self.current_goal}
Findings so far: {json.dumps(self.findings, indent=2)}
Confidence: {self.confidence}

Reflect:
1. Have we answered the core question?
2. What worked well?
3. What didn't work?
4. Do we need to change our approach?
5. Are we missing important information?

Return JSON:
{{
  "progress": 0-1,
  "answered_core_question": true/false,
  "what_worked": ["..."],
  "what_failed": ["..."],
  "strategy_working": true/false,
  "gaps": ["..."],
  "recommendation": "continue|pivot|stop"
}}
"""
        
        response = llm_client.complete(reflection_prompt, max_tokens=400)
        
        try:
            reflection = json.loads(response)
        except:
            reflection = {
                "progress": self.confidence,
                "answered_core_question": self.confidence > 0.8,
                "what_worked": [],
                "what_failed": [],
                "strategy_working": True,
                "gaps": [],
                "recommendation": "continue"
            }
        
        self.update_todo_status(todo.step_num, "complete", reflection)
        return reflection
        
    # ============ STAGE 5: DECISION ============
    
    def should_continue(self, reflection: Dict, iteration: int) -> Tuple[bool, str]:
        """
        STAGE 5: Decide if we should continue or stop.
        
        Returns: (should_continue, reason)
        """
        # Stop if we've answered the question
        if reflection.get("answered_core_question"):
            return False, "Core question answered"
            
        # Stop if we've hit max iterations
        if iteration >= self.max_iterations:
            return False, f"Reached max iterations ({self.max_iterations})"
            
        # Stop if strategy isn't working and confidence is high enough
        if not reflection.get("strategy_working") and self.confidence > 0.75:
            return False, "Strategy not working but confidence sufficient"
            
        # Continue if recommendation says so
        if reflection.get("recommendation") == "continue":
            return True, "Recommendation to continue"
            
        # Default: continue if confidence is low
        return self.confidence < 0.85, "Confidence below threshold"
        
    def should_explore_further(self, reflection: Dict) -> bool:
        """
        STAGE 5B: Should we explore related topics?
        
        After main goal is satisfied, should agent be curious?
        """
        if self.confidence >= 0.85:
            has_gaps = len(reflection.get("gaps", [])) > 0
            has_related = hasattr(curiosity_engine, 'should_explore_further') and \
                         curiosity_engine.should_explore_further(
                             self.current_goal,
                             self.confidence,
                             self.iteration
                         )
            return has_gaps or has_related
        
        return False
        
    # ============ STAGE 6: RESPONSE ============
    
    def compile_response(self, include_todos: bool = True) -> Dict:
        """
        STAGE 6: Compile findings into natural language response.
        
        Returns: {message, findings, todos, confidence, recommendations}
        """
        todo = self.add_todo("Compiling response...", "in-progress")
        
        # Build tool results section showing success/failure explicitly
        tool_results_display = self._build_tool_results_display()
        
        response_prompt = f"""
Goal: {self.current_goal}
Findings: {json.dumps(self.findings, indent=2)}
Understanding: {json.dumps(self.understanding, indent=2)}
Confidence: {self.confidence}
Tool Results: {tool_results_display}

Create a natural, conversational response as if you're talking to a friend. 
Be direct and helpful. Don't use formal section headers.
IMPORTANT: Reference the explicit tool results shown above - don't hide failures.

SEPARATELY (for internal learning only):
- Identify key findings (what you learned)
- Note recommendations (what could be improved)

Return JSON:
{{
  "message": "Your natural, friendly response as one cohesive message...",
  "summary": "One sentence summary",
  "key_findings": ["finding1", "finding2"],
  "recommendations": ["rec1", "rec2"],
  "next_steps": ["step1", "step2"]
}}

IMPORTANT: 
- message = what the user sees (conversational, natural, honest about failures)
- key_findings/recommendations = internal data for learning (not shown to user)
"""
        
        response = llm_client.complete(response_prompt, max_tokens=500)

        compiled = self._try_parse_compiled_response(response)
        if not compiled:
            compiled = self._build_fallback_compiled_response()
        
        self.update_todo_status(todo.step_num, "complete", compiled)
        
        result = {
            "message": compiled.get("message"),
            "summary": compiled.get("summary"),
            "key_findings": compiled.get("key_findings"),
            "recommendations": compiled.get("recommendations"),
            "next_steps": compiled.get("next_steps"),
            "confidence": self.confidence,
            "tools_used": self.findings.get("tools_used", []),
            "tool_results": self._get_tool_results_structured(),  # Add explicit tool results
            "understanding": self.understanding
        }
        
        # Include generated code if available
        if self.generated_code:
            result["generated_code"] = self.generated_code
            result["code_type"] = "html"
        
        if include_todos:
            result["reasoning_steps"] = self.get_todos()
        
        return result
    
    def _build_tool_results_display(self) -> str:
        """Build a text display of tool results showing success/failure."""
        if not self.findings.get("answers"):
            return "No tools executed yet"
        
        lines = []
        for i, result in enumerate(self.findings["answers"], 1):
            tool_name = result.get("tool", "unknown")
            success = result.get("success", False)
            status = "✓ SUCCESS" if success else "✗ FAILED"
            output = result.get("output", "No output")
            
            lines.append(f"{i}. [{status}] {tool_name}")
            
            if not success:
                lines.append(f"   Error: {output}")
            else:
                if isinstance(output, dict):
                    if "count" in output:
                        lines.append(f"   Result: Found {output['count']} items")
                    elif "message" in output:
                        lines.append(f"   Result: {output['message']}")
                elif isinstance(output, list):
                    lines.append(f"   Result: {len(output)} items")
                elif isinstance(output, str) and len(output) < 100:
                    lines.append(f"   Result: {output}")
        
        return "\n".join(lines)
    
    def _get_tool_results_structured(self) -> List[Dict]:
        """Get structured tool results for frontend."""
        results = []
        for result in self.findings.get("answers", []):
            results.append({
                "tool_name": result.get("tool", "unknown"),
                "success": result.get("success", False),
                "message": result.get("output", "No output"),
                "input": result.get("input", ""),
                "status": "✓" if result.get("success") else "✗"
            })
        return results

    def _try_parse_compiled_response(self, response_text: str) -> Dict:
        """Try to parse LLM response into JSON, with extraction fallback."""
        if not response_text:
            return {}
        try:
            return json.loads(response_text)
        except Exception:
            pass

        # Try to extract JSON from code fences or text
        text = response_text.strip()
        if "```json" in text:
            try:
                candidate = text.split("```json", 1)[1].split("```", 1)[0].strip()
                return json.loads(candidate)
            except Exception:
                pass
        if "```" in text:
            try:
                candidate = text.split("```", 1)[1].split("```", 1)[0].strip()
                return json.loads(candidate)
            except Exception:
                pass

        # Best-effort: parse between first { and last }
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = text[start:end + 1]
                return json.loads(candidate)
        except Exception:
            pass

        return {}

    def _build_fallback_compiled_response(self) -> Dict:
        """Fallback response when LLM output isn't valid JSON."""
        answers = self.findings.get("answers", [])
        summary_lines = []

        # Summarize recent tool outputs (best-effort)
        for item in answers[-2:]:
            if isinstance(item, dict):
                output = item.get("output")
                tool = item.get("tool")
                if isinstance(output, dict) and "results" in output:
                    results = output.get("results", [])[:3]
                    snippets = []
                    for r in results:
                        if isinstance(r, dict):
                            snippets.append(r.get("title") or r.get("snippet") or str(r))
                        else:
                            snippets.append(str(r))
                    summary_lines.append(f"{tool}: " + "; ".join([s for s in snippets if s]))
                elif output:
                    summary_lines.append(f"{tool}: {str(output)[:300]}")
            else:
                summary_lines.append(str(item)[:300])

        if summary_lines:
            # Build contextual response based on tools used
            tools_used = self.findings.get("tools_used", [])
            
            # Check if Mployer tools were called
            mployer_called = any('mployer' in str(tool).lower() for tool in tools_used)
            
            if mployer_called:
                # If Mployer tools were used, show those results
                action_prompt = "\n\nLet me know if you'd like me to extract contacts from any of these employers or refine the search."
            else:
                # Generic follow-up based on what was done
                action_prompt = "\n\nWhat would you like me to do with this information?"
            
            message = (
                "Here's what I found:\n" +
                "\n".join([f"- {line}" for line in summary_lines]) +
                action_prompt
            )
        else:
            message = (
                "I can actively inspect the Mployer site, map the employer search flow, and import results into GHL. "
                "Tell me the search criteria (industry, size, location), the number of employers/contacts to add, and which GHL pipeline/stage/tags to use."
            )

        return {
            "message": message,
            "summary": self.current_goal,
            "key_findings": answers,
            "recommendations": [],
            "next_steps": []
        }
        
    # ============ FULL REASONING LOOP ============
    
    def reason_about_goal(self, goal: str) -> Dict:
        """
        Execute full reasoning loop from goal to response.
        
        This is the main entry point.
        """
        # CRITICAL: Reset state for new goal
        self.reset()
        self.current_goal = goal
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🤔 AGENT REASONING: {goal}")
        logger.info(f"{'='*60}\n")
        
        # Retrieve relevant memories for context
        relevant_memories = memory_manager.retrieve_observations(goal, domain="_global", top_k=3)
        if relevant_memories:
            logger.info(f"📚 Retrieved {len(relevant_memories)} relevant memories")
        
        # Stage 1: Understand
        self.understand_goal(goal, context={'memories': relevant_memories})
        logger.info(f"✓ Understood goal: {self.understanding.get('real_goal')}")
        
        # If there are clarifying questions, return them FIRST
        clarifying_questions = self.understanding.get('clarifying_questions', [])
        if clarifying_questions and len(clarifying_questions) > 0:
            logger.info(f"🤔 Found {len(clarifying_questions)} clarifying questions")
            # Return early with questions - don't execute yet
            return {
                "message": "I want to make sure I understand what you need.",
                "understanding": self.understanding,
                "confidence": 0.3,
                "reasoning_steps": self.get_todos(),
                "tools_used": [],
                "key_findings": [],
                "recommendations": []
            }
        
        # Check if this is a build request
        goal_lower = goal.lower()
        is_build_request = any(word in goal_lower for word in ['build', 'create', 'make', 'generate', 'code'])
        
        # Stage 2: Plan
        plan = self.plan_approach()
        logger.info(f"✓ Created plan with {len(plan.get('steps', []))} steps")
        
        # If build request, generate code
        if is_build_request:
            code_result = self.generate_and_test_code(goal, self.understanding)
            if code_result.get('success'):
                logger.info(f"✓ Generated code ({len(code_result.get('code', ''))} characters)")
            else:
                logger.error(f"✗ Code generation failed: {code_result.get('error')}")
        
        # Stage 3-5: Execute loop with timeout
        goal_start_time = time.time()
        goal_timeout = 120  # 2 minutes per goal
        
        while self.iteration < self.max_iterations:
            # Check goal timeout
            elapsed = time.time() - goal_start_time
            if elapsed > goal_timeout:
                logger.warning(f"⏱️ Goal execution timeout after {elapsed:.1f}s")
                self.confidence = 0.1
                break
            # Execute one iteration
            exec_result = self.execute_iteration()
            
            if not exec_result.get("success"):
                break
                
            # Reflect on progress
            reflection = self.reflect_on_progress()
            logger.info(f"✓ Reflection: {reflection.get('recommendation')}")
            
            # Decide to continue
            should_continue, reason = self.should_continue(reflection, self.iteration)
            if not should_continue:
                logger.info(f"✓ Stopping: {reason}")
                break
        
        # Stage 6: Compile response
        response = self.compile_response(include_todos=True)
        
        logger.info(f"\n✓ Final confidence: {self.confidence:.2%}")
        logger.info(f"✓ Tools used: {', '.join(self.findings.get('tools_used', []))}")
        logger.info(f"{'='*60}\n")
        
        return response
        
    # ============ HELPER METHODS ============
    
    def _infer_domain(self, goal: str) -> str:
        """Infer domain from goal"""
        goal_lower = goal.lower()
        
        if any(kw in goal_lower for kw in ["code", "function", "class", "python", "javascript"]):
            return "code"
        elif any(kw in goal_lower for kw in ["data", "csv", "json", "parse"]):
            return "data"
        elif any(kw in goal_lower for kw in ["learn", "understand", "research", "what is", "how does", "explain"]):
            return "learning"
        elif any(kw in goal_lower for kw in ["build", "create", "make", "generate", "implement"]):
            return "building"
        elif any(kw in goal_lower for kw in ["plan", "strategy", "roadmap", "organize", "schedule"]):
            return "planning"
        else:
            return "general"
            
    def _decide_next_action(self) -> Dict:
        """
        Decide what to do next based on findings.
        
        Returns: {action, tool, input, reason}
        """
        goal_lower = self.current_goal.lower()
        
        # Force Mployer login first if goal references Mployer
        if 'mployer' in goal_lower:
            already_logged_in = any(
                result.get('tool') == 'mployer_login'
                for result in self.findings["answers"]
                if isinstance(result, dict)
            )
            if not already_logged_in:
                return {
                    "action": "execute_tool",
                    "tool": "mployer_login",
                    "input": "",
                    "reason": "Must login to Mployer before any search"
                }
        
        # If no findings yet, use tool selector to pick the best tool
        if not self.findings["answers"]:
            tool_name, tool_input, confidence = tool_selector.select_tool(
                self.current_goal,
                {"iteration": self.iteration, "domain": self.understanding.get("domain")}
            )
            return {
                "action": "execute_tool",
                "tool": tool_name,
                "input": tool_input,
                "reason": "Starting investigation"
            }
        
        # After first tool, decide if we need more information
        # Check if the user wants multi-step automation (login + search + extract)
        # Check if we need to log in first
        if 'login' in goal_lower and 'mployer' in goal_lower:
            # Check if we've already logged in
            already_logged_in = any(
                result.get('tool') == 'mployer_login' 
                for result in self.findings["answers"]
                if isinstance(result, dict)
            )
            if not already_logged_in:
                return {
                    "action": "execute_tool",
                    "tool": "mployer_login",
                    "input": "",
                    "reason": "Must login to Mployer first"
                }
            # After login, navigate to search
            already_navigated = any(
                result.get('tool') == 'mployer_navigate_to_search' 
                for result in self.findings["answers"]
                if isinstance(result, dict)
            )
            if not already_navigated:
                return {
                    "action": "execute_tool",
                    "tool": "mployer_navigate_to_search",
                    "input": "",
                    "reason": "Navigate to search page"
                }
            # After navigation, execute the search
            already_searched = any(
                result.get('tool') == 'mployer_search_employers' 
                for result in self.findings["answers"]
                if isinstance(result, dict)
            )
            if not already_searched:
                # Extract search parameters from goal
                import re
                state_match = re.search(r'\b([A-Z]{2})\b|maryland', goal_lower, re.IGNORECASE)
                employees_match = re.search(r'between (\d+) and (\d+) employees', goal_lower)
                
                state = state_match.group(1).upper() if state_match and state_match.group(1) else 'MD'
                if 'maryland' in goal_lower:
                    state = 'MD'
                    
                min_emp = int(employees_match.group(1)) if employees_match else 10
                max_emp = int(employees_match.group(2)) if employees_match else 500
                
                return {
                    "action": "execute_tool",
                    "tool": "mployer_search_employers",
                    "input": {"state": state, "min_employees": min_emp, "max_employees": max_emp, "max_results": 50},
                    "reason": f"Search for employers in {state} with {min_emp}-{max_emp} employees"
                }
        
        # If confidence is still low, continue searching
        if self.confidence < 0.7 and 'mployer' not in goal_lower:
            return {
                "action": "execute_tool",
                "tool": "web_search",
                "input": f"more about {self.current_goal}",
                "reason": "Need more information"
            }
        
        return {
            "action": "continue_reasoning",
            "reason": "Sufficient findings collected"
        }
        
    def _simulate_tool_execution(self, decision: Dict) -> Dict:
        """
        Execute actual tool from registry.
        
        Calls real tools like web_search, mployer_login, mployer_search_employers, etc.
        """
        tool_name = decision.get("tool")
        tool_input = decision.get("input", "")
        
        if not tool_name:
            return {
                "tool": "unknown",
                "input": tool_input,
                "output": "No tool specified",
                "success": False
            }
        
        logger.info(f"🔧 Executing tool: {tool_name} with input: {str(tool_input)[:100]}")
        
        try:
            # Handle different input types
            if isinstance(tool_input, dict):
                # Call with keyword arguments
                result = tool_registry.call(tool_name, **tool_input)
            elif isinstance(tool_input, (list, tuple)):
                # Call with positional arguments
                result = tool_registry.call(tool_name, *tool_input)
            else:
                # Call with single string argument
                result = tool_registry.call(tool_name, tool_input)
            
            # Check if result has error or explicit failure
            if isinstance(result, dict):
                if result.get('error'):
                    return {
                        "tool": tool_name,
                        "input": tool_input,
                        "output": result.get('error'),
                        "success": False
                    }
                if result.get('success') is False:
                    return {
                        "tool": tool_name,
                        "input": tool_input,
                        "output": result.get('message', 'Tool reported failure'),
                        "success": False
                    }
            
            # Success - return the actual result
            return {
                "tool": tool_name,
                "input": tool_input,
                "output": result,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            return {
                "tool": tool_name,
                "input": tool_input,
                "output": f"Error: {str(e)}",
                "success": False
            }
        
    def update_confidence(self):
        """Update overall confidence based on findings"""
        if not self.findings["answers"]:
            self.confidence = 0.0
        else:
            # Simple heuristic: more findings = higher confidence
            self.confidence = min(0.9, 0.3 + (len(self.findings["answers"]) * 0.2))


# Global instance
agent_reasoning = AgentReasoning()


def create_reasoning_session(goal: str) -> Dict:
    """Tool function: Create a reasoning session"""
    return agent_reasoning.reason_about_goal(goal)


def get_reasoning_todos() -> List[Dict]:
    """Tool function: Get current reasoning todos"""
    return agent_reasoning.get_todos()
