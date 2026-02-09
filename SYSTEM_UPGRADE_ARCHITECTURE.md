# System Architecture Upgrade Design
**Date:** February 3, 2026  
**Status:** Design Phase (Implementation Follows)

---

## OVERVIEW

This document designs 5 major system upgrades for the autonomous agent. Each upgrade maintains:
- ✅ Clean architecture (no circular dependencies)
- ✅ Deterministic behavior (explainable decisions)
- ✅ Full observability (every decision auditable)
- ✅ Backward compatibility (old code still works during migration)
- ✅ Bounded scope (no infinite expansion, no retraining)

---

## UPGRADE #1: DOMAIN CAPSULES

### PROBLEM
Current system tracks tool performance globally:
```
web_search: success_rate=0.93, usefulness=0.88
```

But web_search for "marketing research" ≠ web_search for "crypto analysis".
This causes:
- False confidence transfer (crypto success inflates marketing expectations)
- Wrong penalties (crypto failure penalizes marketing research)
- Lost contextual learning (can't distinguish use patterns by domain)

### SOLUTION
Isolate performance metrics by domain while reusing tool implementations.

### DATA MODEL

**Current Structure (Global):**
```
firebase: tool_performance:web_search
{
  tool_name: "web_search",
  total_calls: 45,
  success_rate: 0.93,
  usefulness: 0.88,
  avg_latency: 1.2
}
```

**New Structure (Domain-Scoped):**
```
firebase: tool_performance:web_search:marketing
{
  tool: "web_search",
  domain: "marketing",
  total_calls: 28,
  success_rate: 0.96,
  usefulness: 0.92,
  avg_latency: 1.1,
  failure_modes: ["too_generic", "outdated"]  // capture failure patterns
}

firebase: tool_performance:web_search:crypto
{
  tool: "web_search",
  domain: "crypto",
  total_calls: 17,
  success_rate: 0.82,
  usefulness: 0.76,
  avg_latency: 1.5,
  failure_modes: ["missing_recent_news", "too_technical"]
}

firebase: tool_performance:web_search:_global  // Fallback
{
  tool: "web_search",
  domain: "_global",
  total_calls: 45,
  success_rate: 0.89,
  usefulness: 0.85,
  avg_latency: 1.2
}
```

### INTEGRATION POINTS

#### 1. AgentState (agent.py)
**Add domain tracking:**
```python
class AgentState:
    def __init__(self, goal, domain=None):
        self.goal = goal
        self.domain = domain or self._infer_domain(goal)  # Auto-detect if not provided
        self.context = {}
        self.memory = {}
        self.confidence = 1.0
        self.steps = 0
        self.observations = []
    
    def _infer_domain(self, goal: str) -> str:
        """Infer domain from goal or return '_global' (neutral default)"""
        # Simple keyword matching; can be enhanced with ML later
        goal_lower = goal.lower()
        if any(kw in goal_lower for kw in ["market", "campaign", "customer", "brand"]):
            return "marketing"
        if any(kw in goal_lower for kw in ["bitcoin", "eth", "crypto", "blockchain"]):
            return "crypto"
        if any(kw in goal_lower for kw in ["code", "debug", "api", "python", "backend"]):
            return "engineering"
        if any(kw in goal_lower for kw in ["schedule", "budget", "resource", "timeline"]):
            return "operations"
        return "_global"  # Fallback: unknown domain
```

#### 2. ToolPerformanceTracker (tool_performance.py)
**Modify to track by domain:**

**Current:**
```python
def record_usage(self, tool_name: str, success: bool, latency_ms: float):
    key = f"{self.collection_key}:{tool_name}"
```

**New:**
```python
def record_usage(self, tool_name: str, success: bool, latency_ms: float, 
                 domain: str = "_global", failure_mode: str = None):
    """Track tool performance scoped to domain"""
    # Domain-specific record
    domain_key = f"{self.collection_key}:{tool_name}:{domain}"
    domain_data = memory.safe_call('get', domain_key) or self._init_record(tool_name, domain)
    
    # Update domain-specific metrics
    domain_data['total_calls'] += 1
    if success:
        domain_data['successful_calls'] += 1
    else:
        domain_data['failed_calls'] += 1
        if failure_mode:
            domain_data['failure_modes'].append(failure_mode)
    
    # Update domain-specific latency
    domain_data['avg_latency_ms'] = self._update_running_average(
        domain_data['avg_latency_ms'],
        latency_ms,
        domain_data['total_calls']
    )
    
    # Save domain-specific record
    memory.safe_call('set', domain_key, domain_data)
    
    # ALSO update global aggregate (for fallback)
    global_key = f"{self.collection_key}:{tool_name}:_global"
    global_data = memory.safe_call('get', global_key) or self._init_record(tool_name, "_global")
    global_data['total_calls'] += 1
    if success:
        global_data['successful_calls'] += 1
    else:
        global_data['failed_calls'] += 1
    global_data['avg_latency_ms'] = self._update_running_average(
        global_data['avg_latency_ms'],
        latency_ms,
        global_data['total_calls']
    )
    memory.safe_call('set', global_key, global_data)

def get_stats(self, tool_name: str, domain: str = "_global"):
    """Get stats for tool in specific domain (or global if domain has no history)"""
    domain_key = f"{self.collection_key}:{tool_name}:{domain}"
    stats = memory.safe_call('get', domain_key)
    
    # If no domain-specific history and not requesting global, fall back to global
    if not stats and domain != "_global":
        logging.debug(f"No history for {tool_name} in domain '{domain}', using global fallback")
        global_key = f"{self.collection_key}:{tool_name}:_global"
        stats = memory.safe_call('get', global_key)
    
    return stats

def get_usefulness_score(self, tool_name: str, domain: str = "_global") -> float:
    """Get usefulness for tool in domain (or global if no domain history)"""
    stats = self.get_stats(tool_name, domain)
    if not stats or stats['total_calls'] == 0:
        return 0.5  # neutral
    
    success_rate = stats['successful_calls'] / stats['total_calls']
    confidence = min(1.0, stats['total_calls'] / 10.0)
    return (success_rate * 0.7 + 0.5 * 0.3) * confidence
```

#### 3. ToolSelector (tool_selector.py)
**Domain-aware tool selection:**

**Current:**
```python
def select_tool(self, goal: str, context: Dict = None):
    performance_scores = {}
    for tool_name in tool_registry.tools.keys():
        performance_scores[tool_name] = self.get_tool_usefulness(tool_name)
```

**New:**
```python
def select_tool(self, goal: str, context: Dict = None):
    domain = context.get('domain', '_global') if context else '_global'
    
    # Get pattern scores (domain-agnostic)
    pattern_scores = self.analyze_goal(goal)
    
    # Get domain-specific performance
    performance_scores = {}
    for tool_name in tool_registry.tools.keys():
        performance_scores[tool_name] = tracker.get_usefulness_score(tool_name, domain)
    
    # Combine as before
    final_scores = {}
    for tool_name in tool_registry.tools.keys():
        pattern_conf = pattern_scores.get(tool_name, 0.0)
        perf_conf = performance_scores.get(tool_name, 0.5)
        final_scores[tool_name] = (pattern_conf * 0.8) + (perf_conf * 0.2)
    
    # Domain-specific memory penalties
    learnings = memory_manager.summarize_learnings(goal, domain=domain)
    tools_to_avoid = learnings.get('tools_to_avoid', [])
    
    for tool_name in tools_to_avoid:
        if tool_name in final_scores:
            final_scores[tool_name] *= 0.3
            logging.info(f"Penalizing {tool_name} in domain '{domain}'")
    
    # Select as before
    max_score = max(final_scores.values()) if final_scores else 0.0
    if max_score < 0.15:
        return None, None, max_score
    
    best_tool = max(final_scores.items(), key=lambda x: x[1])
    return best_tool[0], self.prepare_input(best_tool[0], goal, context), best_tool[1]
```

#### 4. Agent Loop (agent.py)
**Pass domain through execution:**

**Current:**
```python
tool_name, tool_input, confidence = tool_selector.select_tool(
    self.state.goal,
    context={'refined': self.state.context.get('refined')}
)

observation = tool_registry.call(action['tool'], action['input'])
```

**New:**
```python
# Pass domain to tool selector
tool_name, tool_input, confidence = tool_selector.select_tool(
    self.state.goal,
    context={
        'refined': self.state.context.get('refined'),
        'domain': self.state.domain,  # NEW
        'step': self.state.steps
    }
)

# Tool execution captures domain
if action['tool']:
    observation = tool_registry.call(action['tool'], action['input'])
    
    # Record with domain context
    success = not observation.get('error')
    failure_mode = observation.get('failure_type') if not success else None
    tracker.record_usage(
        action['tool'],
        success=success,
        latency_ms=observation.get('latency_ms', 0),
        domain=self.state.domain,  # NEW
        failure_mode=failure_mode
    )
```

#### 5. MemoryManager (memory_manager.py)
**Domain-aware memory queries:**

**Current:**
```python
def summarize_learnings(self, goal: str) -> dict:
    memories = self.get_important_memories(goal)
```

**New:**
```python
def summarize_learnings(self, goal: str, domain: str = "_global") -> dict:
    """Summarize learnings for specific domain"""
    memories = self.get_important_memories(goal, domain=domain)
    
    # Extract domain-specific insights
    strategies = []
    tools_to_avoid = []
    avg_effectiveness = 0.0
    
    for mem in memories:
        data = mem.get('data', {})
        
        # Only extract if memory's domain matches (or is global)
        mem_domain = mem.get('metadata', {}).get('domain', '_global')
        if mem_domain != '_global' and mem_domain != domain:
            continue  # Skip memories from other domains
        
        if 'strategy_adjustment' in data:
            strategies.append(data['strategy_adjustment'])
        
        if 'tool_feedback' in data:
            for tool, feedback in data['tool_feedback'].items():
                if feedback.get('usefulness', 0.5) < 0.3:
                    tools_to_avoid.append(tool)
        
        if 'effectiveness_score' in data:
            avg_effectiveness += data['effectiveness_score']
    
    if len(memories) > 0:
        avg_effectiveness /= len(memories)
    
    return {
        'domain': domain,
        'summary': f"Learned from {len(memories)} similar goals in domain '{domain}'",
        'strategies': strategies,
        'tools_to_avoid': list(set(tools_to_avoid)),
        'avg_effectiveness': avg_effectiveness,
        'confidence': min(1.0, len(memories) / 5.0)
    }
```

### MIGRATION STRATEGY

**Phase 1 (Backward Compatible):**
- Add domain tracking to AgentState (default: `_global`)
- Modify ToolPerformanceTracker to accept optional domain parameter
- Update agent loop to pass domain
- All old code continues working (domain defaults to `_global`)

**Phase 2 (Validation):**
- Run tests with domain awareness
- Verify global aggregate still works as fallback
- Check Firebase structure

**Phase 3 (Cutover):**
- Domain inference becomes default
- UI updated to show domain-scoped performance

### RISK MITIGATION

| Risk | Mitigation |
|------|-----------|
| Breaking old queries | Global aggregate `_global` domain maintains backward compat |
| Domain inference errors | Default to `_global` if uncertain; human can override |
| Memory explosion | Limit failure_modes history to last 10 per domain |
| Query complexity | Simple string concatenation for keys, no complex lookups |

### BENEFITS

✅ Marketing research doesn't contaminate crypto tool selection  
✅ Agent learns specialized patterns (web_search for marketing ≠ crypto)  
✅ Penalties are domain-specific (failures don't cascade globally)  
✅ Fallback to global when domain has no history (graceful degradation)  
✅ Completely observable (can audit why tool was chosen for domain)  

---

## UPGRADE #2: LIGHTWEIGHT GOAL DECOMPOSITION

### PROBLEM

Current agent treats all goals as atomic:
```
"Design a marketing campaign for quantum computing startups"
→ No decomposition
→ Agent tries web_search once
→ Gets generic results
→ Stops
```

Should decompose to:
```
1. Research quantum computing market trends
2. Analyze target audience for startups
3. Identify key marketing channels
4. Draft campaign positioning
5. Synthesize into actionable plan
```

### SOLUTION

Add a lightweight goal classifier and decomposer (no recursion, no planning trees).

### DATA MODEL

**Goal Classification:**
```python
{
  "goal": "Design a marketing campaign for quantum computing startups",
  "is_composite": True,
  "subgoals": [
    {
      "index": 0,
      "goal": "Research current quantum computing market trends and opportunities",
      "type": "research",
      "confidence": 0.9
    },
    {
      "index": 1,
      "goal": "Analyze the target audience: early-stage quantum computing startups",
      "type": "analysis",
      "confidence": 0.9
    },
    {
      "index": 2,
      "goal": "Identify the most effective marketing channels for this audience",
      "type": "strategy",
      "confidence": 0.85
    },
    {
      "index": 3,
      "goal": "Draft key messaging and positioning for the campaign",
      "type": "synthesis",
      "confidence": 0.8
    }
  ],
  "total_subgoals": 4,
  "complexity_score": 0.72
}
```

**Execution Record:**
```python
{
  "original_goal": "Design a marketing campaign...",
  "domain": "marketing",
  "subgoal_results": [
    {
      "subgoal_index": 0,
      "subgoal": "Research current quantum computing market trends...",
      "steps": 3,
      "confidence": 0.88,
      "key_findings": ["Market growing 25% YoY", "Enterprise adoption increasing"],
      "effectiveness": 0.84
    },
    {
      "subgoal_index": 1,
      "subgoal": "Analyze target audience...",
      "steps": 2,
      "confidence": 0.85,
      "key_findings": ["Avg team size: 12-50", "Funding stage: Series A/B"],
      "effectiveness": 0.82
    },
    // ... more subgoals
  ],
  "synthesis": {
    "combined_findings": "...",
    "overall_confidence": 0.845,
    "final_response": "..."
  }
}
```

### IMPLEMENTATION

#### 1. Create GoalDecomposer (backend/goal_decomposer.py)

```python
import re
import logging
from typing import List, Dict, Tuple

class GoalDecomposer:
    """Lightweight goal classifier and decomposer"""
    
    # Patterns that indicate composite goals
    COMPOSITE_PATTERNS = [
        r'\b(design|build|plan|develop|create)\b.*\b(and|then|also)\b',  # "design X and implement Y"
        r'\b(analyze|research|compare)\b.*\b(and|with|vs)\b',  # "compare X with Y"
        r'\b(first|then|next|finally)\b',  # Sequential goals
        r'\b(before|after|once)\b.*\b(then)\b',  # Dependency chain
    ]
    
    # Keywords for subgoal types
    RESEARCH_KEYWORDS = ["research", "investigate", "explore", "find out", "discover", "analyze"]
    ANALYSIS_KEYWORDS = ["analyze", "evaluate", "assess", "compare", "contrast"]
    STRATEGY_KEYWORDS = ["strategy", "recommend", "suggest", "plan", "approach"]
    SYNTHESIS_KEYWORDS = ["synthesize", "combine", "summarize", "conclude"]
    
    def classify_goal(self, goal: str) -> Dict:
        """Classify goal as atomic or composite"""
        is_composite = any(
            re.search(pattern, goal, re.IGNORECASE) 
            for pattern in self.COMPOSITE_PATTERNS
        )
        
        if is_composite:
            subgoals = self.decompose(goal)
            return {
                "goal": goal,
                "is_composite": True,
                "subgoals": subgoals,
                "total_subgoals": len(subgoals),
                "complexity_score": min(1.0, len(subgoals) * 0.15)  # More subgoals = more complex
            }
        else:
            return {
                "goal": goal,
                "is_composite": False,
                "subgoals": [],
                "total_subgoals": 0,
                "complexity_score": 0.1
            }
    
    def decompose(self, goal: str) -> List[Dict]:
        """Decompose a composite goal into 2-4 subgoals"""
        # CONSTRAINT: Max 4 subgoals (prevents explosion)
        subgoals = []
        
        # Simple heuristic-based decomposition
        # (In production, could use NLP, but must remain deterministic and auditable)
        
        if any(kw in goal.lower() for kw in ["design", "plan", "build"]):
            subgoals.append(self._create_subgoal(
                0, 
                f"Research background and context for: {goal}",
                "research",
                0.9
            ))
            subgoals.append(self._create_subgoal(
                1,
                f"Analyze requirements and constraints for: {goal}",
                "analysis",
                0.85
            ))
            subgoals.append(self._create_subgoal(
                2,
                f"Draft a plan for: {goal}",
                "strategy",
                0.8
            ))
        
        elif any(kw in goal.lower() for kw in ["compare", "analyze"]):
            subgoals.append(self._create_subgoal(
                0,
                f"Research details on first subject in: {goal}",
                "research",
                0.9
            ))
            subgoals.append(self._create_subgoal(
                1,
                f"Research details on second subject in: {goal}",
                "research",
                0.9
            ))
            subgoals.append(self._create_subgoal(
                2,
                f"Compare and synthesize findings from: {goal}",
                "synthesis",
                0.85
            ))
        
        # Fallback: treat as atomic (just return original as single subgoal)
        if not subgoals:
            subgoals.append(self._create_subgoal(0, goal, "general", 0.9))
        
        # CONSTRAINT: Never exceed 4 subgoals
        return subgoals[:4]
    
    def _create_subgoal(self, index: int, subgoal_text: str, subgoal_type: str, confidence: float) -> Dict:
        return {
            "index": index,
            "goal": subgoal_text,
            "type": subgoal_type,
            "confidence": confidence
        }
    
    def validate_decomposition(self, goal: str, subgoals: List[Dict]) -> bool:
        """Validate that decomposition is sound"""
        # CONSTRAINT: Max 4 subgoals
        if len(subgoals) > 4:
            logging.warning(f"Decomposition exceeds 4 subgoals: {len(subgoals)}")
            return False
        
        # CONSTRAINT: Subgoals should be distinct
        seen_keywords = set()
        for sg in subgoals:
            keywords = set(sg['goal'].lower().split())
            overlap = seen_keywords & keywords
            if len(overlap) > len(keywords) * 0.5:
                logging.warning(f"Subgoal overlap detected: {sg['goal']}")
        
        return True
```

#### 2. Modify Agent to Handle Composite Goals (agent.py)

**New flow:**
```python
from backend.goal_decomposer import GoalDecomposer

class Agent:
    def __init__(self, goal):
        self.decomposer = GoalDecomposer()
        self.goal_classification = self.decomposer.classify_goal(goal)
        
        if self.goal_classification['is_composite']:
            # Composite goal: run subgoals sequentially
            self.subgoals = self.goal_classification['subgoals']
            self.subgoal_results = []
            self.current_subgoal_index = 0
        else:
            # Atomic goal: single execution
            self.subgoals = []
            self.current_subgoal_index = 0
        
        self.state = AgentState(goal)
    
    def execute(self):
        """Main execution loop"""
        if self.goal_classification['is_composite']:
            return self._execute_composite()
        else:
            return self._execute_atomic()
    
    def _execute_atomic(self):
        """Execute single-goal as before"""
        steps = []
        while self.current_subgoal_index < Config.MAX_AGENT_STEPS and not self.state.done:
            state = self.step()
            steps.append(state)
            if state['done']:
                break
        
        return {
            'goal_type': 'atomic',
            'goal': self.state.goal,
            'steps': steps,
            'final_confidence': self.state.confidence
        }
    
    def _execute_composite(self):
        """Execute composite goal (subgoals in sequence)"""
        subgoal_results = []
        combined_findings = []
        
        for subgoal_idx, subgoal in enumerate(self.subgoals):
            logging.info(f"Executing subgoal {subgoal_idx + 1}/{len(self.subgoals)}: {subgoal['goal']}")
            
            # Create new agent state for each subgoal
            subgoal_agent = Agent(subgoal['goal'])
            subgoal_agent.state.domain = self.state.domain  # Inherit domain
            
            # Execute subgoal
            subgoal_steps = []
            while not subgoal_agent.state.done and len(subgoal_steps) < Config.MAX_AGENT_STEPS:
                state = subgoal_agent.step()
                subgoal_steps.append(state)
                if state['done']:
                    break
            
            # Capture result
            subgoal_result = {
                'subgoal_index': subgoal_idx,
                'subgoal': subgoal['goal'],
                'steps': len(subgoal_steps),
                'confidence': subgoal_agent.state.confidence,
                'effectiveness': self._compute_subgoal_effectiveness(subgoal_steps),
                'key_findings': self._extract_key_findings(subgoal_steps)
            }
            subgoal_results.append(subgoal_result)
            combined_findings.append(subgoal_result['key_findings'])
        
        # Synthesis step: combine all findings
        synthesis = self._synthesize_results(subgoal_results)
        
        return {
            'goal_type': 'composite',
            'original_goal': self.state.goal,
            'domain': self.state.domain,
            'subgoals': self.subgoals,
            'subgoal_results': subgoal_results,
            'synthesis': synthesis,
            'final_confidence': self._compute_final_confidence(subgoal_results)
        }
    
    def _compute_subgoal_effectiveness(self, steps: List[Dict]) -> float:
        """Compute how effective subgoal execution was"""
        if not steps:
            return 0.0
        
        successes = sum(1 for s in steps if s.get('decision', {}).get('tool') is not None)
        return min(1.0, successes / max(1, len(steps)))
    
    def _extract_key_findings(self, steps: List[Dict]) -> List[str]:
        """Extract key findings from step observations"""
        findings = []
        for step in steps:
            obs = step.get('observation', {})
            if 'results' in obs and isinstance(obs['results'], list):
                # Extract first 2-3 results as findings
                findings.extend([
                    str(r)[:100] for r in obs['results'][:3]  # Truncate to 100 chars
                ])
        return findings[:5]  # Max 5 findings per subgoal
    
    def _synthesize_results(self, subgoal_results: List[Dict]) -> Dict:
        """Synthesize results from all subgoals"""
        combined_text = "\n".join([
            f"Subgoal {r['subgoal_index']}: {r['key_findings']}"
            for r in subgoal_results
        ])
        
        return {
            'combined_findings': combined_text,
            'overall_effectiveness': sum(r['effectiveness'] for r in subgoal_results) / len(subgoal_results),
            'final_response': f"Completed composite goal with {len(subgoal_results)} subgoals. Overall effectiveness: {sum(r['effectiveness'] for r in subgoal_results) / len(subgoal_results):.2f}"
        }
    
    def _compute_final_confidence(self, subgoal_results: List[Dict]) -> float:
        """Compute final confidence as average of subgoal confidences"""
        if not subgoal_results:
            return 0.0
        return sum(r['confidence'] for r in subgoal_results) / len(subgoal_results)
```

#### 3. Update FastAPI Endpoints (main.py)

**Existing /chat endpoint handles both:**
```python
@app.post("/chat")
async def chat(goal: str):
    agent = Agent(goal)
    
    # Classification happens automatically
    if agent.goal_classification['is_composite']:
        result = agent._execute_composite()
    else:
        result = agent._execute_atomic()
    
    return JSONResponse(content=result)
```

### CONSTRAINTS & SAFETY

1. **Max 4 subgoals:** Prevents explosion
2. **Single-level only:** No recursive decomposition
3. **Sequential execution:** Subgoals run one-by-one (no parallel, simpler to debug)
4. **Same domain:** All subgoals inherit parent domain
5. **Audit trail:** Every subgoal result recorded
6. **Step limits respected:** Each subgoal still limited to MAX_AGENT_STEPS

### OBSERVABILITY

User sees:
```json
{
  "goal_type": "composite",
  "original_goal": "Design a marketing campaign for quantum computing startups",
  "subgoals": [
    {"index": 0, "goal": "Research..."},
    {"index": 1, "goal": "Analyze..."},
    ...
  ],
  "subgoal_results": [
    {"subgoal_index": 0, "steps": 2, "confidence": 0.88},
    {"subgoal_index": 1, "steps": 3, "confidence": 0.82},
    ...
  ],
  "synthesis": {
    "combined_findings": "...",
    "overall_effectiveness": 0.84
  },
  "final_confidence": 0.845
}
```

**No black magic — every subgoal, every step visible.**

---

## UPGRADE #3: READ-ONLY CODEBASE AWARENESS

### PROBLEM

Agent currently has no understanding of project structure. Can't propose:
- New tools intelligently
- Refactorings that fit architecture
- Missing modules that would help

Should provide read-only analysis WITHOUT write access.

### SOLUTION

Add three new tools (read-only, no execution):
1. **repo_index** - List files and structure
2. **file_summary** - Understand file purpose
3. **dependency_map** - See how files relate

### DATA MODEL

**Repository Index:**
```json
{
  "type": "repo_index",
  "timestamp": "2026-02-03T...",
  "structure": {
    "backend/": {
      "files": ["agent.py", "main.py", "tool_registry.py", ...],
      "subdirs": [],
      "total_files": 14,
      "description": "Core agent logic and tools"
    },
    "frontend/": {
      "files": ["App.js", "App.css", ...],
      "subdirs": ["src/"],
      "total_files": 4,
      "description": "React UI dashboard"
    }
  },
  "total_lines_of_code": 3247,
  "languages": ["python", "javascript"],
  "entry_points": ["backend/main.py", "frontend/src/index.js"]
}
```

**File Summary:**
```json
{
  "type": "file_summary",
  "file": "backend/agent.py",
  "lines_of_code": 156,
  "docstring": "Core agent loop with step execution, reflection, and memory integration",
  "classes": ["AgentState", "Agent"],
  "functions": ["step", "_emit_state", ...],
  "imports": [
    "backend.memory",
    "backend.memory_manager",
    "backend.tool_registry",
    ...
  ],
  "purpose": "Main agent execution engine. Orchestrates tool selection, execution, reflection, and memory saving.",
  "integration_points": ["tool_selector.select_tool()", "tool_registry.call()", "memory_manager.save_if_important()"],
  "dependencies_on_me": ["main.py"]
}
```

**Dependency Map:**
```json
{
  "type": "dependency_map",
  "analysis": {
    "main.py": {
      "imports": ["agent", "tool_registry", "tool_performance", "memory_manager"],
      "is_imported_by": ["test_api.py"]
    },
    "agent.py": {
      "imports": ["memory", "memory_manager", "tool_registry", "tool_selector", "tools"],
      "is_imported_by": ["main.py"]
    },
    "tool_selector.py": {
      "imports": ["tool_registry", "tool_performance", "memory_manager"],
      "is_imported_by": ["agent.py"]
    }
  },
  "circular_dependencies": [],
  "orphaned_files": [],
  "core_modules": ["agent.py", "tool_registry.py", "tool_selector.py", "memory.py"]
}
```

### IMPLEMENTATION

#### 1. Create CodebaseAnalyzer (backend/codebase_analyzer.py)

```python
import os
import re
import logging
from typing import Dict, List, Tuple
from pathlib import Path

class CodebaseAnalyzer:
    """Read-only codebase analysis (no modifications)"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.python_files = list(self.root_path.rglob("*.py"))
        self.js_files = list(self.root_path.rglob("*.js"))
    
    def get_repo_index(self) -> Dict:
        """Analyze overall repository structure"""
        structure = {}
        total_lines = 0
        
        # Scan top-level directories
        for item in self.root_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                files = list(item.glob("*.*"))
                subdirs = [d.name for d in item.iterdir() if d.is_dir()]
                
                # Count lines in directory
                dir_lines = sum(self._count_lines(f) for f in files if f.suffix in ['.py', '.js'])
                total_lines += dir_lines
                
                structure[item.name] = {
                    'files': [f.name for f in files if f.suffix in ['.py', '.js']],
                    'subdirs': subdirs,
                    'total_files': len(files),
                    'description': self._infer_dir_description(item.name)
                }
        
        return {
            'type': 'repo_index',
            'structure': structure,
            'total_lines_of_code': total_lines,
            'languages': self._detect_languages(),
            'entry_points': self._find_entry_points()
        }
    
    def get_file_summary(self, filepath: str) -> Dict:
        """Summarize a specific file without executing it"""
        path = self.root_path / filepath
        
        if not path.exists():
            return {'error': f'File not found: {filepath}'}
        
        if path.suffix == '.py':
            return self._summarize_python_file(path)
        elif path.suffix == '.js':
            return self._summarize_js_file(path)
        else:
            return {'error': f'Unsupported file type: {path.suffix}'}
    
    def _summarize_python_file(self, path: Path) -> Dict:
        """Analyze Python file"""
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Extract classes
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        
        # Extract functions
        functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
        
        # Extract imports
        imports = re.findall(r'^(?:from|import)\s+(\w+(?:\.\w+)?)', content, re.MULTILINE)
        
        # Extract docstring
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        docstring = docstring_match.group(1).strip() if docstring_match else "No docstring"
        
        return {
            'type': 'file_summary',
            'file': str(path.relative_to(self.root_path)),
            'lines_of_code': len(lines),
            'docstring': docstring[:200],  # First 200 chars
            'classes': classes,
            'functions': functions,
            'imports': list(set(imports)),
            'purpose': self._infer_file_purpose(str(path), classes, functions),
            'integration_points': self._find_integration_points(str(path), content),
            'dependencies_on_me': self._find_dependents(str(path))
        }
    
    def _summarize_js_file(self, path: Path) -> Dict:
        """Analyze JavaScript file"""
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Extract components/classes
        components = re.findall(r'(?:class|function)\s+(\w+)', content)
        
        # Extract imports
        imports = re.findall(r'(?:import|from)\s+[\'"]([\w/.-]+)[\'"]', content)
        
        return {
            'type': 'file_summary',
            'file': str(path.relative_to(self.root_path)),
            'lines_of_code': len(lines),
            'components': components,
            'imports': list(set(imports)),
            'purpose': self._infer_file_purpose(str(path), [], []),
            'integration_points': self._find_integration_points(str(path), content)
        }
    
    def get_dependency_map(self) -> Dict:
        """Analyze how modules depend on each other"""
        dependency_graph = {}
        
        for py_file in self.python_files:
            filepath = str(py_file.relative_to(self.root_path))
            
            with open(py_file, 'r', errors='ignore') as f:
                content = f.read()
            
            # Find imports
            imports = re.findall(r'^(?:from|import)\s+([\w.]+)', content, re.MULTILINE)
            imports = [imp.split('.')[0] for imp in imports]  # Normalize
            
            dependency_graph[filepath] = {
                'imports': list(set(imports)),
                'is_imported_by': []
            }
        
        # Build reverse dependency map
        for filepath, deps in dependency_graph.items():
            for dep in deps['imports']:
                # Find which files define this module
                for other_file, other_deps in dependency_graph.items():
                    if other_file.replace('/', '.').replace('.py', '') == dep.replace('.', ''):
                        dependency_graph[other_file]['is_imported_by'].append(filepath)
        
        return {
            'type': 'dependency_map',
            'analysis': dependency_graph,
            'circular_dependencies': self._detect_circular_deps(dependency_graph),
            'orphaned_files': self._find_orphaned_files(dependency_graph),
            'core_modules': self._identify_core_modules(dependency_graph)
        }
    
    # Helper methods
    def _count_lines(self, filepath: Path) -> int:
        """Count lines in a file"""
        try:
            with open(filepath, 'r', errors='ignore') as f:
                return len(f.readlines())
        except:
            return 0
    
    def _infer_dir_description(self, dirname: str) -> str:
        """Infer directory purpose from name"""
        descriptions = {
            'backend': 'Core agent logic and tools',
            'frontend': 'React UI dashboard',
            'tests': 'Test scripts',
            'docs': 'Documentation'
        }
        return descriptions.get(dirname, f'{dirname} module')
    
    def _infer_file_purpose(self, filepath: str, classes: List[str], functions: List[str]) -> str:
        """Infer file purpose from name and content"""
        if 'agent.py' in filepath:
            return "Main agent execution engine"
        elif 'tool_selector' in filepath:
            return "Intelligent tool selection logic"
        # ... more rules
        return f"Module with {len(classes)} classes and {len(functions)} functions"
    
    def _find_integration_points(self, filepath: str, content: str) -> List[str]:
        """Find where this file is used"""
        # Simple: look for function/class definitions that are called elsewhere
        points = []
        if 'agent.py' in filepath:
            points.append("Called by main.py endpoints")
        if 'tool_registry' in filepath:
            points.append("Used by agent.step()")
        return points
    
    def _find_dependents(self, filepath: str) -> List[str]:
        """Find which files import this one"""
        # Would scan all files for imports of this module
        return []
    
    def _detect_circular_deps(self, graph: Dict) -> List:
        """Detect circular dependencies (simple detection)"""
        return []
    
    def _find_orphaned_files(self, graph: Dict) -> List:
        """Find files that aren't imported anywhere"""
        orphaned = []
        for filepath, deps in graph.items():
            if not deps['is_imported_by'] and 'test' not in filepath:
                orphaned.append(filepath)
        return orphaned
    
    def _identify_core_modules(self, graph: Dict) -> List[str]:
        """Identify core modules (highly imported)"""
        core = []
        for filepath, deps in graph.items():
            if len(deps['is_imported_by']) >= 2:
                core.append(filepath)
        return core
```

#### 2. Register as Read-Only Tools (tools.py)

```python
def register_code_awareness_tools(registry):
    """Register read-only codebase analysis tools"""
    
    analyzer = CodebaseAnalyzer(root_path=".")
    
    def repo_index_impl(input_str: str = ""):
        """List repository structure"""
        return analyzer.get_repo_index()
    
    def file_summary_impl(input_str: str):
        """Summarize a specific file"""
        if not input_str:
            return {'error': 'file_summary requires a filepath parameter'}
        return analyzer.get_file_summary(input_str)
    
    def dependency_map_impl(input_str: str = ""):
        """Show how modules depend on each other"""
        return analyzer.get_dependency_map()
    
    # Register as tools
    registry.register(
        'repo_index',
        repo_index_impl,
        description='Analyze repository structure (read-only)',
        mock_func=repo_index_impl
    )
    
    registry.register(
        'file_summary',
        file_summary_impl,
        description='Summarize a Python or JS file (read-only)',
        mock_func=file_summary_impl
    )
    
    registry.register(
        'dependency_map',
        dependency_map_impl,
        description='Show module dependencies (read-only)',
        mock_func=dependency_map_impl
    )
```

#### 3. Add to Tool Patterns (tool_selector.py)

```python
self.tool_patterns['repo_index'] = [
    r'\b(repository|repo|structure|architecture|organization)\b',
    r'\b(what files|what modules|project layout)\b',
]

self.tool_patterns['file_summary'] = [
    r'\b(summarize|understand|what does|analyze)\b.*\b(file|module)\b',
    r'\.(py|js)\b',
]

self.tool_patterns['dependency_map'] = [
    r'\b(dependencies|imports|relationships|how do.*relate)\b',
    r'\b(circular|orphaned|core modules)\b',
]
```

### SAFETY GUARANTEES

✅ **NO write access** - All methods read-only  
✅ **NO code execution** - Analysis only, no exec()  
✅ **NO sensitive data** - No .env, .keys files analyzed  
✅ **NO external calls** - Pure local analysis  
✅ **Bounded scope** - Analyzes root_path only  

### USAGE EXAMPLES

**User:** "What's the project structure?"
→ Agent selects repo_index
→ Shows directory tree, entry points, LOC

**User:** "I'm thinking about adding a goal persistence module. Where should it go?"
→ Agent selects file_summary on agent.py, memory.py
→ Agent selects dependency_map
→ Proposes: "Create backend/goal_persistence.py, import by agent.py and main.py"

**User:** "Are there any orphaned modules?"
→ Agent selects dependency_map
→ Lists unused files

---

## UPGRADE #4: HUMAN FEEDBACK INJECTION

### PROBLEM

Automated reflection is good, but wrong sometimes. Humans need to:
- Correct mistakes
- Override learned preferences
- Inject domain knowledge
- Set hard constraints

### SOLUTION

Create feedback injection system that:
- Ranks human feedback highest (importance ≥ 0.9)
- Applies immediate overrides
- Creates audit trail
- Prevents conflicts

### DATA MODEL

**Feedback Record:**
```json
{
  "type": "human_feedback",
  "timestamp": "2026-02-03T14:23:45Z",
  "human_id": "user_123",  // For future multi-user
  "goal_pattern": "marketing campaign",  // Or specific goal
  "tool": "web_search",  // Or null for goal-level feedback
  "domain": "marketing",
  "verdict": "negative" | "positive" | "correction",
  "reason": "Results were too generic, lacked specifics",
  "evidence": "Expected 5+ actionable insights, got 3 vague ones",
  "importance": 0.95,  // Always high
  "action": "penalize" | "boost" | "constraint",
  "impact": {
    "tool_adjustment": 0.5,  // Multiply tool usefulness by 0.5
    "penalty_duration": "permanent" | "session" | "7days",
    "hard_constraint": null | "never_use_for_marketing"
  },
  "applied_to_memories": 3  // How many affected
}
```

**Feedback Query:**
```python
# Example: Get negative feedback on web_search for marketing
GET /feedback?tool=web_search&domain=marketing&verdict=negative
→ [
    {timestamp: 2026-02-03T..., reason: "...", impact: {...}},
    {timestamp: 2026-02-02T..., reason: "...", impact: {...}}
]
```

### IMPLEMENTATION

#### 1. Create FeedbackManager (backend/feedback_manager.py)

```python
import logging
from datetime import datetime
from typing import Dict, List
from backend.memory import memory

class FeedbackManager:
    """Manage human feedback and apply it to agent decisions"""
    
    def __init__(self):
        self.collection_prefix = "human_feedback"
    
    def submit_feedback(self, goal: str, tool: str = None, domain: str = "_global", 
                       verdict: str = "negative", reason: str = "", 
                       action: str = "penalize", evidence: str = "") -> Dict:
        """
        Submit feedback from human.
        
        verdict: "positive", "negative", "correction"
        action: "penalize", "boost", "constraint", "correct"
        """
        feedback = {
            'type': 'human_feedback',
            'timestamp': datetime.utcnow().isoformat(),
            'goal_pattern': goal,
            'tool': tool,
            'domain': domain,
            'verdict': verdict,
            'reason': reason,
            'evidence': evidence,
            'importance': 0.95,  # Human feedback always high importance
            'action': action,
            'impact': self._compute_impact(verdict, action)
        }
        
        # Save feedback
        key = f"{self.collection_prefix}:{goal}:{tool}:{domain}:{datetime.utcnow().timestamp()}"
        memory.safe_call('set', key, feedback)
        
        # Apply to existing tool performance metrics
        applied_count = self._apply_feedback_to_metrics(tool, domain, feedback)
        feedback['applied_to_memories'] = applied_count
        
        # Save updated feedback with applied count
        memory.safe_call('set', key, feedback)
        
        logging.info(f"Human feedback submitted: {tool} in {domain} - {reason}")
        return feedback
    
    def _compute_impact(self, verdict: str, action: str) -> Dict:
        """Compute how to adjust metrics based on feedback"""
        if verdict == "negative":
            if action == "penalize":
                return {
                    'tool_adjustment': 0.3,  # Multiply usefulness by 0.3
                    'confidence_adjustment': -0.2,
                    'penalty_duration': 'permanent'
                }
            elif action == "constraint":
                return {
                    'hard_constraint': 'never_use',
                    'penalty_duration': 'permanent'
                }
        
        elif verdict == "positive":
            return {
                'tool_adjustment': 1.2,  # Boost usefulness by 20%
                'confidence_adjustment': 0.15,
                'penalty_duration': 'permanent'
            }
        
        elif verdict == "correction":
            return {
                'replace_with': action,  # "use X instead"
                'penalty_duration': 'permanent'
            }
        
        return {}
    
    def _apply_feedback_to_metrics(self, tool: str, domain: str, feedback: Dict) -> int:
        """Apply feedback to existing tool performance records"""
        if not tool:
            return 0  # Goal-level feedback doesn't directly modify tool metrics
        
        # Load tool performance
        key = f"tool_performance:{tool}:{domain}"
        stats = memory.safe_call('get', key)
        
        if not stats:
            return 0
        
        # Apply adjustment
        impact = feedback['impact']
        if 'tool_adjustment' in impact:
            old_usefulness = stats.get('usefulness', 0.5)
            stats['usefulness'] = min(1.0, max(0.0, old_usefulness * impact['tool_adjustment']))
            stats['human_feedback_applied'] = True
            stats['last_feedback_timestamp'] = feedback['timestamp']
            
            # Save updated stats
            memory.safe_call('set', key, stats)
            
            logging.info(f"Adjusted {tool} usefulness: {old_usefulness:.2f} → {stats['usefulness']:.2f}")
            return 1
        
        return 0
    
    def get_feedback_for_tool(self, tool: str, domain: str = "_global", 
                             verdict: str = None) -> List[Dict]:
        """Get all feedback for a tool in a domain"""
        # This is simplified; in production, you'd query Firebase with filters
        # For now, return from memory or implement proper querying
        
        feedback_list = []
        # Query would filter by tool, domain, optional verdict
        # This is a placeholder for proper Firebase querying
        
        return feedback_list
    
    def apply_feedback_to_selection(self, tool_name: str, domain: str, 
                                    confidence: float) -> Tuple[float, bool]:
        """
        Apply feedback penalties to tool selection confidence.
        
        Returns: (adjusted_confidence, should_skip)
        """
        feedback_list = self.get_feedback_for_tool(tool_name, domain)
        
        if not feedback_list:
            return confidence, False
        
        # Get most recent negative feedback
        negative_feedback = [f for f in feedback_list if f['verdict'] == 'negative']
        
        if not negative_feedback:
            return confidence, False
        
        most_recent = max(negative_feedback, key=lambda x: x['timestamp'])
        
        if most_recent['impact'].get('hard_constraint') == 'never_use':
            return 0.0, True  # Skip this tool entirely
        
        # Apply adjustment factor
        adjustment = most_recent['impact'].get('tool_adjustment', 1.0)
        adjusted = confidence * adjustment
        
        logging.info(f"Applied human feedback to {tool_name}: {confidence:.2f} → {adjusted:.2f}")
        return adjusted, False
```

#### 2. Add Feedback Endpoints (main.py)

```python
@app.post("/feedback/submit")
async def submit_feedback(
    goal: str,
    tool: str = None,
    domain: str = "_global",
    verdict: str = "negative",
    reason: str = "",
    action: str = "penalize",
    evidence: str = ""
):
    """
    Submit human feedback to override agent decisions.
    
    verdict: "positive", "negative", "correction"
    action: "penalize", "boost", "constraint"
    """
    feedback = feedback_manager.submit_feedback(
        goal=goal,
        tool=tool,
        domain=domain,
        verdict=verdict,
        reason=reason,
        action=action,
        evidence=evidence
    )
    return JSONResponse(content=feedback)

@app.get("/feedback/history")
async def get_feedback_history(tool: str = None, domain: str = "_global"):
    """Get human feedback history for a tool/domain"""
    feedback_list = feedback_manager.get_feedback_for_tool(tool, domain)
    return JSONResponse(content={'feedback': feedback_list})

@app.get("/feedback/stats")
async def get_feedback_stats():
    """Get statistics on human feedback"""
    return JSONResponse(content={
        'total_feedback': 42,
        'by_verdict': {'positive': 8, 'negative': 28, 'correction': 6},
        'by_tool': {'web_search': 15, 'calculate': 8, 'read_file': 19}
    })
```

#### 3. Integrate into Tool Selector (tool_selector.py)

```python
def select_tool(self, goal: str, context: Dict = None):
    domain = context.get('domain', '_global') if context else '_global'
    
    # ... existing pattern + performance scoring ...
    
    # NEW: Apply human feedback penalties
    final_scores_with_feedback = {}
    for tool_name, confidence in final_scores.items():
        adjusted_conf, should_skip = feedback_manager.apply_feedback_to_selection(
            tool_name, domain, confidence
        )
        
        if should_skip:
            final_scores_with_feedback[tool_name] = 0.0  # Exclude from selection
        else:
            final_scores_with_feedback[tool_name] = adjusted_conf
    
    final_scores = final_scores_with_feedback
    
    # ... rest of selection logic ...
```

### USAGE FLOW

**User:** "The search results were too generic. I needed specific competitor analysis."
```
POST /feedback/submit
{
  "goal": "analyze competitors",
  "tool": "web_search",
  "domain": "marketing",
  "verdict": "negative",
  "reason": "Results lacked specific competitor details",
  "evidence": "Returned 3 general articles, needed 5+ company-specific analyses",
  "action": "penalize"
}
```

**Agent's next decision:**
- web_search confidence in marketing domain: 0.60
- Human feedback applied: 0.60 × 0.3 = 0.18 (penalized)
- Agent tries different tool or refines query

**Over time:**
- Multiple negative feedbacks on web_search for "competitor analysis"
- Eventually: hard constraint "never_use_for_competitor_analysis"

### AUDIT TRAIL

Every piece of human feedback:
- Saved to Firebase with timestamp
- Linked to metrics it changed
- Reversible (can query "what if I remove this feedback?")
- Inspectable ("show me all negative feedback in Q1")

---

## UPGRADE #5: AUTONOMY LADDERS (Design Only)

### PROBLEM

Currently, agent is:
- Suggest only (level 1)
- Human must approve every step

Future could be:
- Draft + queue (level 2)
- Execute safe tools automatically (level 3)
- Schedule tasks (level 4)
- Cross-goal optimization (level 5)

### REQUIREMENT

Design structures now, DON'T enable yet.

### SOLUTION

Add autonomy level flags and prepare data structures.

### DATA MODEL

**Autonomy Configuration:**
```json
{
  "autonomy_level": 1,  // 1-5
  "level_descriptions": {
    "1": "Suggest only - human approves every action",
    "2": "Draft + queue - agent proposes, human queues",
    "3": "Execute safe tools - runs read-only tools auto, asks before write",
    "4": "Scheduled tasks - can schedule future tasks",
    "5": "Cross-goal optimization - can chain multiple goals"
  },
  "safe_tools_for_level_3": [
    "web_search",
    "repo_index",
    "file_summary",
    "get_time"
  ],
  "unsafe_tools_for_level_3": [
    "write_file",
    "modify_config",
    "deploy"
  ],
  "current_level": 1,
  "can_escalate_to": 2,  // Human-approved path
  "escalation_requirements": {
    "2": "10 successful session, <10% error rate",
    "3": "50 successful sessions, <5% error rate, zero unsafe tool requests",
    "4": "100 successful sessions, demonstrated goal chaining"
  }
}
```

**Autonomy Request (when agent wants to escalate):**
```json
{
  "type": "autonomy_escalation_request",
  "current_level": 1,
  "requested_level": 2,
  "justification": "10 successful sessions completed, error rate 3%",
  "metrics": {
    "total_sessions": 10,
    "successful_sessions": 10,
    "error_rate": 0.03,
    "human_approval_rate": 1.0,
    "avg_confidence": 0.82
  },
  "risks": "None identified"
}
```

### IMPLEMENTATION (Structures Only, No Enablement)

#### 1. Create AutonomyManager (backend/autonomy_manager.py)

```python
import logging
from datetime import datetime
from typing import Dict, Tuple
from backend.memory import memory

class AutonomyManager:
    """
    Manage agent autonomy levels.
    
    CRITICAL: This is DESIGN ONLY. No actual escalation happens.
    All decisions stay at level 1 unless explicitly approved.
    """
    
    LEVELS = {
        1: "suggest_only",
        2: "draft_and_queue",
        3: "execute_safe_tools",
        4: "schedule_tasks",
        5: "cross_goal_optimization"
    }
    
    LEVEL_REQUIREMENTS = {
        1: {},  # Default, no requirements
        2: {
            'min_successful_sessions': 10,
            'max_error_rate': 0.10,
            'min_confidence': 0.70
        },
        3: {
            'min_successful_sessions': 50,
            'max_error_rate': 0.05,
            'min_confidence': 0.75,
            'unsafe_tool_requests': 0  # Must never request unsafe tools
        },
        4: {
            'min_successful_sessions': 100,
            'max_error_rate': 0.05,
            'demonstrated_goal_chaining': True
        },
        5: {
            'min_successful_sessions': 200,
            'max_error_rate': 0.03,
            'demonstrated_cross_goal': True
        }
    }
    
    SAFE_TOOLS = {
        1: ['web_search', 'calculate', 'read_file', 'list_directory', 'get_time', 'repo_index', 'file_summary', 'dependency_map', 'reflect'],
        2: ['web_search', 'calculate', 'read_file', 'list_directory', 'get_time', 'repo_index', 'file_summary', 'dependency_map', 'reflect'],
        3: ['web_search', 'calculate', 'read_file', 'list_directory', 'get_time', 'repo_index', 'file_summary', 'dependency_map', 'reflect'],
        4: ['web_search', 'calculate', 'read_file', 'list_directory', 'get_time', 'repo_index', 'file_summary', 'dependency_map', 'reflect'],
        5: ['web_search', 'calculate', 'read_file', 'list_directory', 'get_time', 'repo_index', 'file_summary', 'dependency_map', 'reflect']
    }
    
    def __init__(self):
        self.current_level = 1  # Always start at level 1
        self.session_stats = self._load_session_stats()
    
    def get_current_level(self) -> int:
        """Get current autonomy level (always auditable)"""
        return self.current_level
    
    def can_tool_execute_at_level(self, tool_name: str, level: int) -> bool:
        """Check if tool is allowed at autonomy level"""
        return tool_name in self.SAFE_TOOLS.get(level, [])
    
    def evaluate_escalation(self, target_level: int) -> Tuple[bool, str, Dict]:
        """
        Evaluate if agent meets requirements for escalation.
        
        Returns: (can_escalate, reason, metrics)
        """
        if target_level <= self.current_level:
            return False, "Target level must be higher than current", {}
        
        if target_level > 5:
            return False, "Maximum autonomy level is 5", {}
        
        requirements = self.LEVEL_REQUIREMENTS.get(target_level, {})
        metrics = self.session_stats
        
        # Check each requirement
        for req_key, req_value in requirements.items():
            if req_key == 'min_successful_sessions':
                if metrics.get('successful_sessions', 0) < req_value:
                    return False, f"Need {req_value} successful sessions, have {metrics.get('successful_sessions', 0)}", metrics
            
            elif req_key == 'max_error_rate':
                error_rate = 1.0 - metrics.get('success_rate', 0.0)
                if error_rate > req_value:
                    return False, f"Error rate {error_rate:.1%} exceeds limit {req_value:.1%}", metrics
            
            elif req_key == 'min_confidence':
                if metrics.get('avg_confidence', 0.0) < req_value:
                    return False, f"Avg confidence {metrics.get('avg_confidence', 0.0):.2f} below {req_value:.2f}", metrics
            
            elif req_key == 'unsafe_tool_requests':
                if metrics.get('unsafe_requests', 0) > req_value:
                    return False, f"Unsafe tool requests: {metrics.get('unsafe_requests', 0)}", metrics
        
        return True, "Meets all requirements", metrics
    
    def request_escalation(self, target_level: int, reason: str = "") -> Dict:
        """
        Agent requests escalation (but humans must approve).
        
        Returns: escalation request for human review
        """
        can_escalate, reason_msg, metrics = self.evaluate_escalation(target_level)
        
        request = {
            'type': 'autonomy_escalation_request',
            'timestamp': datetime.utcnow().isoformat(),
            'current_level': self.current_level,
            'requested_level': target_level,
            'meets_requirements': can_escalate,
            'justification': reason,
            'reason_if_not_met': reason_msg,
            'metrics': metrics,
            'status': 'pending_human_review',
            'requires_human_approval': True
        }
        
        # Save for human review
        key = f"autonomy_escalation_request:{datetime.utcnow().timestamp()}"
        memory.safe_call('set', key, request)
        
        logging.warning(f"Agent requested escalation to level {target_level}: {reason}")
        logging.info(f"Escalation request saved for human review: {key}")
        
        return request
    
    def approve_escalation(self, request_key: str, approved: bool, 
                          human_comment: str = "") -> Dict:
        """
        Human approves or denies escalation request.
        
        CRITICAL: Only humans can approve escalation.
        """
        request = memory.safe_call('get', request_key)
        
        if not request:
            return {'error': 'Request not found'}
        
        if approved:
            # Escalate
            old_level = self.current_level
            self.current_level = request['requested_level']
            
            action = {
                'type': 'autonomy_escalation_approved',
                'timestamp': datetime.utcnow().isoformat(),
                'old_level': old_level,
                'new_level': self.current_level,
                'human_comment': human_comment,
                'approved_by': 'human_reviewer'
            }
            
            logging.warning(f"AUTONOMY ESCALATION APPROVED: Level {old_level} → {self.current_level}")
            logging.info(f"Human comment: {human_comment}")
        else:
            # Deny
            action = {
                'type': 'autonomy_escalation_denied',
                'timestamp': datetime.utcnow().isoformat(),
                'requested_level': request['requested_level'],
                'human_comment': human_comment,
                'denied_by': 'human_reviewer'
            }
            
            logging.info(f"AUTONOMY ESCALATION DENIED: Level {request['requested_level']}")
            logging.info(f"Human comment: {human_comment}")
        
        # Save decision
        decision_key = f"autonomy_decision:{datetime.utcnow().timestamp()}"
        memory.safe_call('set', decision_key, action)
        
        return action
    
    def _load_session_stats(self) -> Dict:
        """Load accumulated session statistics"""
        # Simplified; in production, query Firebase
        return {
            'total_sessions': 0,
            'successful_sessions': 0,
            'success_rate': 1.0,
            'avg_confidence': 0.8,
            'unsafe_requests': 0,
            'total_tools_used': 0
        }
```

#### 2. Add Escalation Endpoints (main.py)

```python
@app.get("/autonomy/status")
async def get_autonomy_status():
    """Get current autonomy level and requirements"""
    level = autonomy_manager.get_current_level()
    return JSONResponse(content={
        'current_level': level,
        'level_name': autonomy_manager.LEVELS[level],
        'next_level': level + 1 if level < 5 else None,
        'requirements_for_next': autonomy_manager.LEVEL_REQUIREMENTS.get(level + 1, {}),
        'current_metrics': autonomy_manager.session_stats
    })

@app.post("/autonomy/request_escalation")
async def request_escalation(target_level: int, reason: str = ""):
    """
    Agent requests autonomy escalation.
    
    CRITICAL: Humans must review and approve.
    """
    request = autonomy_manager.request_escalation(target_level, reason)
    return JSONResponse(content=request)

@app.post("/autonomy/approve_escalation")
async def approve_escalation(request_key: str, approved: bool, 
                            human_comment: str = ""):
    """
    Human approves or denies escalation.
    
    ONLY humans can call this endpoint.
    """
    result = autonomy_manager.approve_escalation(request_key, approved, human_comment)
    return JSONResponse(content=result)

@app.get("/autonomy/requests")
async def get_pending_escalations():
    """Get all pending escalation requests"""
    # Query Firebase for pending requests
    return JSONResponse(content={
        'pending': [
            {
                'id': 'req_123',
                'from_level': 1,
                'to_level': 2,
                'reason': '10 successful sessions',
                'timestamp': '2026-02-03T12:00:00Z'
            }
        ]
    })
```

### GUARDRAILS

**NEVER auto-escalate:**
```python
# WRONG - Don't do this
if stats['success_rate'] > 0.9:
    autonomy_manager.current_level = 2  # ❌ NO!

# RIGHT - Always require human approval
if stats['success_rate'] > 0.9:
    autonomy_manager.request_escalation(2)  # ✅ Request for review
```

**Tools always respect autonomy level:**
```python
# In agent loop
if not autonomy_manager.can_tool_execute_at_level(tool_name, autonomy_manager.get_current_level()):
    logging.error(f"Tool {tool_name} not allowed at level {autonomy_manager.get_current_level()}")
    return  # Don't execute
```

**All escalation decisions are auditable:**
```
All escalation requests saved to Firebase
All approvals/denials logged with timestamp and human ID
Can query: "Show me all escalations from Feb 2026"
```

### FUTURE CAPABILITY (Not Implemented)

When humans decide to enable higher autonomy:

**Level 2: Draft + Queue**
- Agent preposes tool sequence
- Humans queue it
- Agent executes when approved

**Level 3: Execute Safe Tools**
- web_search, calculate, read operations auto-execute
- Reflection and memory still automatic
- Unsafe tools still require approval

**Level 4: Scheduled Tasks**
- "Remind me about crypto news every Monday"
- Agent schedules and executes autonomously

**Level 5: Cross-Goal Optimization**
- "Complete all 3 marketing subgoals efficiently"
- Agent chains subgoals, reuses results

---

## INTEGRATION ROADMAP

### Phase 1 (Week 1): Domain Capsules
1. Modify ToolPerformanceTracker
2. Update ToolSelector
3. Add domain inference to AgentState
4. Test with domain-specific queries

### Phase 2 (Week 1-2): Goal Decomposition
1. Create GoalDecomposer
2. Modify Agent loop
3. Update endpoints
4. Test with composite goals

### Phase 3 (Week 2): Codebase Awareness
1. Create CodebaseAnalyzer
2. Register new tools
3. Add patterns to ToolSelector
4. Test code analysis queries

### Phase 4 (Week 2-3): Human Feedback
1. Create FeedbackManager
2. Add feedback endpoints
3. Integrate into ToolSelector
4. Test feedback override

### Phase 5 (Week 3): Autonomy Ladders
1. Create AutonomyManager (structures only)
2. Add monitoring endpoints
3. Document escalation requirements
4. NO enablement yet

---

## RISKS & MITIGATION

| Risk | Mitigation |
|------|-----------|
| Domain inference wrong | Default to `_global` if uncertain, human can override |
| Decomposition explodes | Hard limit: 4 subgoals max, single level only |
| Code analysis breaks | Read-only, errors logged, gracefully returns empty |
| Human feedback lost | Every piece saved to Firebase with timestamp |
| Autonomy escalates silently | Requires explicit human approval, all logged |

---

## SUCCESS CRITERIA

✅ All upgrades backward compatible (old system still works)  
✅ Domain capsules reduce tool contamination by 60%+  
✅ Composite goals complete faster than sequential manual runs  
✅ Code awareness enables 5+ new use cases  
✅ Human feedback overrides work 100% of the time  
✅ Autonomy system ready but disabled  

---

## QUESTIONS FOR CLARIFICATION

Before implementing, I need answers to:

1. **Domain Inference:** Should domain be inferred from goal, provided by user, or both?
2. **Decomposition:** Should subgoals run in parallel (faster) or sequential (simpler debugging)?
3. **Feedback Scope:** Should feedback apply to individual goals or all goals of that type?
4. **Autonomy Timeline:** When should autonomy escalation be enabled? (Q1? Q2? Later?)
5. **Firebase Limits:** Any concerns about query cost as domain-scoped records grow?

Ready to implement any or all of these. Where should we start?
