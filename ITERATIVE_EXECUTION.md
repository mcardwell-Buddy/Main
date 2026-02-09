# Iterative Goal Execution: Smart, Adaptive Deep Thought

## Problem: 8-Step Plans Are Too Generic

The original approach decomposed **every** goal into predefined steps:
- "What is 2+2?" → 8 steps
- "Find CEO of Company X's background" → 8 steps
- Simple and complex goals treated the same

This is inefficient because:
1. **Simple goals waste time** (why 8 steps for a math problem?)
2. **Complex goals need flexibility** (static steps can't adapt to new information)
3. **No feedback loop** (each step is predetermined, not informed by previous results)

## Solution: Iterative Decomposition with Adaptive Refinement

The new **IterativeExecutor** system is intelligent about goal complexity:

### 1. Classify Complexity Upfront

```python
analysis = iterative_decomposer.analyze_goal_complexity(goal)
# Returns: complexity="simple" or "complex"
```

**Simple patterns** (solved in 1 tool call):
- Math: "What is 2+2?" → calculate tool, done
- Definition: "What is Python?" → web_search, done  
- Time: "What time is it?" → system tool, done
- Conversion: "How many MB in GB?" → calculate, done

**Complex patterns** (require iteration):
- Research + Compare: "Research Python and JavaScript, compare them"
- Sequential tasks: "Find X's background, then their companies"
- Multi-entity: "Find A, B, and C's connection"

### 2. For Simple Goals: Execute Directly

```
Goal: "What is 2+2?"
  ↓
Classify: simple (math)
  ↓
Execute: calculate("2+2")
  ↓
Answer: "The result is 4"
  ✓ DONE (1 step)
```

### 3. For Complex Goals: Iterate with Feedback Loop

```
Goal: "Find Sam Altman's background and companies"
  ↓
Classify: complex (research_then_analyze)
  ↓
Step 1: Search "Sam Altman CEO"
  Results: Finds he's OpenAI CEO, founded Y Combinator
  Analyze: Need more about background/education
  ↓
Step 2: Search "Sam Altman background Stanford education"
  Results: Stanford dropout, founded Loopt
  Analyze: Need company history
  ↓
Step 3: Search "Sam Altman Y Combinator Loopt companies"
  Results: Complete company timeline
  Confidence: 85% - sufficient
  ↓
STOP iteration - information sufficient
  ✓ Synthesize answer (3 steps, not predefined)
```

**Key difference**: Each result informs the next query. The system:
- Analyzes what info was found
- Identifies what's still missing (gaps)
- Formulates next search query based on gaps
- Stops when confidence ≥ 85% OR max 5 iterations

## Architecture

### Module: `iterative_decomposer.py`

```python
class IterativeDecomposer:
    
    # Classifies goal complexity
    def analyze_goal_complexity(goal) → {
        'complexity': 'simple' | 'complex',
        'category': str,
        'requires_iteration': bool,
        'entities': [list of things to research]
    }
    
    # Generates first intelligent search
    def generate_first_step(goal, entities) → {
        'search_query': str,
        'tool': 'web_search',
        'purpose': str
    }
    
    # Analyzes search results and identifies gaps
    def analyze_search_results(results, goal) → {
        'entities_found': {entity: info},
        'key_facts': [facts],
        'gaps': ['missing info 1', 'missing info 2'],
        'confidence': 0.0-1.0
    }
    
    # Generates next search query based on gaps
    def generate_next_step(goal, results, findings) → {
        'search_query': str,
        'stop_iteration': bool  # True if done
    }
```

### Module: `iterative_executor.py`

```python
class IterativeExecutor:
    
    def execute() → {
        'execution_type': 'simple' | 'iterative',
        'total_iterations': int,
        'final_answer': str,
        'confidence': 0.0-1.0,
        'execution_log': [details of each iteration]
    }
```

### New API Endpoints

**1. `/chat` (original static decomposition)**
```
POST /chat?goal=Find%20Python%20vs%20JavaScript
Returns: 3-4 predefined subgoals
```

**2. `/chat/iterative` (NEW - smart adaptive)**
```
POST /chat/iterative?goal=Find%20Python%20vs%20JavaScript
Returns: Actual iterations performed, how each informed the next
```

**3. `/chat/analyze-complexity` (NEW - preview only)**
```
GET /chat/analyze-complexity?goal=What%20is%202+2
Returns: {
  "complexity": "simple",
  "category": "math",
  "recommended_tool": "calculate",
  "requires_iteration": false
}
```

## Examples

### Example 1: Simple Goal (Math)

```
Request: POST /chat/iterative?goal=What+is+15+*+3+plus+12
Response: {
  "execution_type": "simple",
  "category": "math",
  "total_iterations": 1,
  "final_answer": "The result is: 57",
  "confidence": 1.0
}
```

### Example 2: Simple Goal (Definition)

```
Request: POST /chat/iterative?goal=Define+photosynthesis
Response: {
  "execution_type": "simple",
  "category": "definition",
  "tool_used": "web_search",
  "total_iterations": 1,
  "final_answer": "Photosynthesis is the process by which plants...",
  "confidence": 0.92
}
```

### Example 3: Complex Goal (Iterative Research)

```
Request: POST /chat/iterative?goal=Who+is+Sam+Altman+and+what+companies+has+he+founded
Response: {
  "execution_type": "iterative",
  "total_iterations": 3,
  "final_answer": "Sam Altman is the CEO of OpenAI. He co-founded Y Combinator...",
  "confidence": 0.87,
  "execution_log": [
    {
      "iteration": 0,
      "query": "Sam Altman CEO founder",
      "purpose": "Find primary information about entity",
      "gaps_filled": ["Who is Sam Altman"],
      "entities_found": ["Sam Altman", "OpenAI", "Y Combinator"]
    },
    {
      "iteration": 1,
      "query": "Sam Altman background education Stanford",
      "purpose": "Research gap: background and history",
      "gaps_filled": ["Background", "Education"],
      "entities_found": ["Stanford", "Loopt"]
    },
    {
      "iteration": 2,
      "query": "Sam Altman companies founded Loopt",
      "purpose": "Research gap: company information",
      "gaps_filled": ["Company history"],
      "entities_found": ["Y Combinator", "Loopt", "OpenAI"]
    }
  ]
}
```

## Stopping Conditions

The iterative executor stops when:

1. **Confidence ≥ 85%**: Sufficient information gathered
2. **Max iterations = 5**: Safety limit to prevent infinite loops
3. **No gaps identified**: All required info found
4. **Next step returns `stop_iteration=True`**: Engine decides done

## LLM Integration

Uses OpenAI GPT-4o-mini to:

1. **Classify complexity** with natural language understanding
2. **Generate first query** intelligently from goal text
3. **Analyze search results** to identify entities, facts, gaps
4. **Formulate next query** based on identified gaps
5. **Synthesize answer** naturally from findings

Falls back to pattern matching if LLM unavailable.

## Comparison: `/chat` vs `/chat/iterative`

| Aspect | `/chat` (Static) | `/chat/iterative` (Dynamic) |
|--------|------------------|---------------------------|
| Simple goal | 3-4 steps | 1 step ✓ |
| Complex goal | 3-4 predefined steps | N steps (1-5, adaptive) |
| First query | Predetermined | LLM-generated ✓ |
| Next query | Predetermined | Based on results ✓ |
| Stopping | After N steps | When sufficient ✓ |
| Feedback loop | No | Yes ✓ |
| Can adapt | No | Yes ✓ |

## Usage in Frontend

Update React to use new endpoint:

```javascript
// Simple goals - use iterative for efficiency
const response = await axios.post(
  'http://localhost:8000/chat/iterative', 
  null, 
  { params: { goal: userQuestion } }
);

if (response.data.execution_type === 'simple') {
  // Show answer directly
  setAnswer(response.data.final_answer);
  setIterations(1);
} else {
  // Show iteration log for transparency
  setAnswer(response.data.final_answer);
  setIterations(response.data.total_iterations);
  setExecutionLog(response.data.execution_log);
}
```

## Testing the System

```powershell
# Test 1: Simple goal (should be 1 iteration)
curl "http://localhost:8000/chat/iterative?goal=What+is+5+times+4"

# Test 2: Complex goal (should be 2-3 iterations)
curl "http://localhost:8000/chat/iterative?goal=Who+is+Elon+Musk+and+what+companies+has+he+founded"

# Test 3: Analyze complexity only
curl "http://localhost:8000/chat/analyze-complexity?goal=Define+AI"
```

## Benefits Over Static Decomposition

1. **Efficiency**: Simple goals solved in 1 step instead of 3-4
2. **Adaptability**: Complex goals adapt to results, not predetermined
3. **Intelligence**: Each search informs the next, creating a feedback loop
4. **Transparency**: Execution log shows exactly how it found the answer
5. **Scalability**: Works equally well for simple definitions or complex research
6. **Learning**: Can be enhanced over time with user feedback on quality

## Future Enhancements

1. **Caching**: Store findings from repeated searches
2. **Parallel iteration**: Search multiple gaps simultaneously
3. **Tool diversity**: Use different tools for different gaps (web_search, code analysis, etc.)
4. **Confidence scoring**: Return confidence per finding, not just overall
5. **Source attribution**: Track which search result each fact came from
6. **User refinement**: Allow users to steer iteration mid-execution
