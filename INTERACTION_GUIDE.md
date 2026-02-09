# How to Interact with Your Agent: Training & Long-term Goals

## Quick Start

### 1. Start the Backend
```bash
cd C:\Users\micha\Buddy
.venv\Scripts\activate
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend
```bash
cd frontend
npm start
```

Visit: http://localhost:3000

## Interaction Methods

### Method 1: Chat API (Simple)
```python
import requests

response = requests.post('http://localhost:8000/chat', json={
    'message': 'Search for the latest developments in quantum computing'
})

print(response.json())
```

### Method 2: WebSocket (Real-time Streaming)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`Step ${data.step}:`, data);
};

ws.send(JSON.stringify({
    message: 'Calculate the compound interest on $1000 at 5% for 10 years'
}));
```

### Method 3: Frontend UI (Visual)
The React app at http://localhost:3000 provides:
- 📊 Tool dashboard with performance metrics
- 🔍 Real-time step visualization
- 💭 Thought process display
- 📈 Confidence tracking

## How the Agent Learns

### 1. Tool Performance Learning

**Automatic Learning:**
Every time the agent uses a tool, it records:
- Success or failure
- Execution time
- Usefulness (based on reflection)

```python
# After each tool use, this happens automatically:
tracker.record_usage(
    tool_name='web_search',
    success=True,
    latency=1.234,
    usefulness=0.85  # From reflection
)
```

**How to help it learn:**
- ✅ Give it varied tasks that exercise different tools
- ✅ Let it complete tasks (don't interrupt)
- ✅ Review its reflections in the UI

**What gets learned:**
```json
{
  "web_search": {
    "total_calls": 45,
    "success_rate": 0.93,
    "avg_latency": 1.2,
    "avg_usefulness": 0.82,
    "usefulness_score": 0.88
  }
}
```

### 2. Memory Learning (What's Important)

**Automatic Filtering:**
Not everything gets saved to Firebase. Only important memories:

| Importance Score | Saves? | Examples |
|------------------|--------|----------|
| < 0.60 | ❌ No | Routine observations, neutral reflections |
| 0.60 - 0.79 | ✅ Yes | Successful completions, useful insights |
| 0.80 - 0.89 | ✅ Yes | High-value learnings, pattern discoveries |
| 0.90+ | ✅ Yes | Critical failures, breakthrough insights |

**How importance is calculated:**
```python
importance = 0.5  # Base

# Boost factors:
if effectiveness >= 0.8:
    importance += 0.3  # Very effective action

if confidence_delta > 0.2:
    importance += 0.2  # Big confidence increase

if tool_failed:
    importance += 0.4  # Learn from failures!

if 'completed' in observation.lower():
    importance += 0.3  # Goal completion
```

**How to help it learn:**
- ✅ Give it challenging tasks (learns more from failures)
- ✅ Provide goals that require multiple steps
- ✅ Let it reflect after each action

### 3. Tool Selection Learning

**Pattern + Performance:**
- **First time:** Uses pattern matching (80% weight)
- **After experience:** Adds historical performance (20% weight)
- **After failures:** Avoids tools that failed (0.3× penalty)

**How to help it learn:**
- ✅ Start with clear goals: "search for X", "calculate Y", "read file Z"
- ✅ Gradually introduce ambiguous goals as it gains experience
- ✅ Let it try tools and fail - it learns from mistakes

## Training Strategies

### Strategy 1: Basic Tool Training

**Goal:** Teach the agent when to use each tool

**Training sequence:**
```python
training_goals = [
    # Web search training
    "search for the capital of France",
    "find the latest news about AI",
    "research best practices for Python testing",
    
    # Calculator training
    "calculate 15 + 27",
    "what is 123 * 456",
    "solve (100 - 25) / 5",
    
    # File operations training
    "read the file backend/config.py",
    "list files in the backend directory",
    "show me the contents of README.md",
    
    # Time queries
    "what time is it",
    "what's the current date",
]

for goal in training_goals:
    requests.post('http://localhost:8000/chat', json={'message': goal})
    time.sleep(2)  # Let it complete
```

**After training:** Check tool performance at `GET /tools`

### Strategy 2: Multi-Step Problem Solving

**Goal:** Teach the agent to break down complex goals

**Training sequence:**
```python
complex_goals = [
    "Search for Python best practices, then summarize the top 3",
    "Read the file requirements.txt and tell me if numpy is installed",
    "Calculate 50 * 20, then tell me what that amount could buy",
    "List all Python files in backend, then read main.py",
]
```

**What the agent learns:**
- Which tool to use first
- When to use multiple tools in sequence
- How to combine tool outputs

### Strategy 3: Error Recovery

**Goal:** Teach resilience and alternative approaches

**Training sequence:**
```python
error_scenarios = [
    "read the file nonexistent.txt",  # File not found
    "calculate abc + xyz",  # Invalid expression
    "search for [corrupted input]",  # Bad query
]
```

**What the agent learns:**
- Which tools fail in which situations
- To avoid tools that recently failed
- To try alternative approaches

## Long-Term Goal Tracking

### Current Capabilities

The agent currently supports **session-based goals**:
- You give it a goal
- It works until completion or max steps
- Memory persists across sessions

### Setting Long-Term Goals

Let me add a goal tracking system...

**New feature: Goal Registry**

```python
# Set a long-term goal
POST /goals
{
    "goal": "Learn to build and deploy web applications",
    "milestones": [
        "Understand Flask/FastAPI basics",
        "Create a REST API",
        "Add database integration",
        "Deploy to production"
    ],
    "deadline": "2026-03-01"
}

# Check progress
GET /goals
{
    "goals": [{
        "id": "goal_123",
        "goal": "Learn to build and deploy web applications",
        "progress": 0.5,
        "completed_milestones": 2,
        "total_milestones": 4,
        "next_action": "Add database integration"
    }]
}
```

Would you like me to implement this?

## Feedback Mechanisms

### Current: Implicit Feedback
The agent learns from:
- ✅ Tool success/failure (automatic)
- ✅ Execution time (automatic)
- ✅ Reflection effectiveness (self-assessed)

### Potential: Explicit Feedback
I can add endpoints for you to give direct feedback:

```python
# Rate an agent action
POST /feedback
{
    "step_id": "step_123",
    "rating": 0.9,  # 0.0 to 1.0
    "comment": "Good job finding relevant information"
}

# Correct a mistake
POST /feedback/correction
{
    "goal": "calculate 2 + 2",
    "wrong_tool": "web_search",
    "correct_tool": "calculate",
    "reason": "This is a math problem, not a search query"
}
```

This would:
- Boost/penalize tool selection scores
- Save to memory with high importance
- Adjust confidence more aggressively

Would you like me to add this?

## Best Practices

### ✅ DO:
1. **Start simple, increase complexity**
   - Begin with single-tool tasks
   - Progress to multi-step problems
   - Introduce edge cases gradually

2. **Let it complete tasks**
   - Don't interrupt mid-execution
   - Allow full reflection cycle
   - Review the complete thought process

3. **Review its memory**
   - Check `GET /memory/insights` regularly
   - See what it learned
   - Understand its decision patterns

4. **Monitor tool performance**
   - Check `GET /tools` for metrics
   - Identify underused tools
   - Create training tasks for weak areas

5. **Give diverse tasks**
   - Mix search, calculation, file operations
   - Combine different tool types
   - Create realistic scenarios

### ❌ DON'T:
1. **Don't give contradictory goals**
   - Bad: "Search for X but don't use web_search"
   - This confuses the tool selector

2. **Don't expect perfection immediately**
   - It needs experience to learn
   - Early mistakes are learning opportunities

3. **Don't spam the same goal**
   - Variety helps it generalize
   - Repeated identical tasks don't add value

4. **Don't ignore failures**
   - Review why tools failed
   - Adjust patterns if needed
   - Consider if the tool needs improvement

## Monitoring Learning Progress

### Check Tool Performance
```bash
curl http://localhost:8000/tools
```

Look for:
- **Success rate** trending up (target: > 0.80)
- **Avg usefulness** improving (target: > 0.75)
- **Total calls** increasing (more experience)

### Check Memory Insights
```bash
curl http://localhost:8000/memory/insights
```

Look for:
- Important learnings being saved
- Patterns in what works/doesn't work
- Tool preferences emerging

### Check Reflection Quality
In the UI or WebSocket output, look for:
- Specific reflections (not generic)
- Confidence adjustments that make sense
- Recognition of failures and successes

## Example Training Session

```python
import requests
import time

API = 'http://localhost:8000'

def train_agent(goal):
    print(f"\n🎯 Training: {goal}")
    response = requests.post(f'{API}/chat', json={'message': goal})
    result = response.json()
    print(f"   Confidence: {result.get('confidence', 0):.2f}")
    print(f"   Steps: {result.get('step', 0)}")
    time.sleep(1)

# Day 1: Basic training
print("=== DAY 1: BASIC TOOLS ===")
train_agent("search for Python documentation")
train_agent("calculate 100 + 200")
train_agent("what time is it")

# Day 2: File operations
print("\n=== DAY 2: FILE OPERATIONS ===")
train_agent("list files in the backend directory")
train_agent("read the file backend/main.py")
train_agent("show me the contents of README.md")

# Day 3: Complex tasks
print("\n=== DAY 3: MULTI-STEP ===")
train_agent("search for Flask tutorials, then summarize them")
train_agent("list Python files, then read the first one")

# Check progress
print("\n=== PROGRESS CHECK ===")
tools = requests.get(f'{API}/tools').json()
for tool in tools['tools']:
    print(f"{tool['name']}: {tool['total_calls']} calls, "
          f"{tool['success_rate']:.0%} success, "
          f"{tool['usefulness_score']:.2f} usefulness")
```

## Next Steps

1. **Now:** Start training with the current system
2. **Soon:** I can add explicit feedback endpoints
3. **Later:** Implement long-term goal tracking with milestones

Want me to implement any of these features?
