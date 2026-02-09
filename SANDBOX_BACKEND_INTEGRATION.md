# Backend Integration: Sandbox Workshop

## How the Backend Powers Sandbox

The Sandbox Workshop uses the same `/reasoning/execute` endpoint as Chat, but with different prompt patterns to trigger analysis vs. building.

---

## API Integration

### Endpoint Used
```
POST /reasoning/execute
Content-Type: application/json

{
  "goal": "Review the ChatInterface code and suggest improvements",
  "context": {}
}
```

### Response Format
```json
{
  "success": true,
  "result": {
    "message": "I reviewed ChatInterface...",
    "key_findings": ["Finding 1", "Finding 2", ...],
    "recommendations": ["Rec 1", "Rec 2", ...],
    "reasoning_steps": [...],
    "confidence": 0.85
  }
}
```

---

## Intent Detection

The Sandbox Workshop detects what you want by analyzing your message:

### Code Review Pattern
```javascript
const isCodeReview = /review|improve|analyze|suggest|what|wrong|better|refactor/i.test(userInput);

// Matches:
// "Review the ChatInterface code"
// "Suggest improvements to the reasoning system"
// "What could we improve?"
// "Analyze the CSS organization"
// "How could we refactor this?"
```

When detected:
- Calls `analyzeOwnCode()`
- Gets findings and recommendations
- Shows them in the message feed
- Waits for "build" request to show preview

### Build Pattern
```javascript
const isBuildRequest = /build|create|make|implement|show|test/i.test(userInput);

// Matches:
// "Build the keyboard shortcuts overlay"
// "Create a dark mode toggle"
// "Implement the memoization optimization"
// "Show me how this would look"
// "Test the new component"
```

When detected:
- Calls `buildImprovement()`
- Creates a live preview
- Shows in right panel
- Enables Approve/Iterate/Reject actions

### Conversation Pattern
```javascript
// Anything else
// Matches:
// "Why is it designed that way?"
// "Tell me more about..."
// "How does the codebase structure?"
```

When detected:
- Calls `conversationalResponse()`
- Returns helpful dialogue
- Suggests next steps

---

## Data Flow in Sandbox

### Phase 1: Analysis
```
User Input: "Review the ChatInterface code and suggest improvements"
    ↓
Frontend: Detects /review|improve|analyze/ pattern
    ↓
Frontend: POST /reasoning/execute {goal: "Analyze Buddy's codebase..."}
    ↓
Backend: AgentReasoning.reason_about_goal()
    • Stage 1: Understand the goal (analyze codebase)
    • Stage 2: Plan approach (which files to check)
    • Stage 3: Execute iteration (read files, analyze)
    • Stage 4: Reflect on progress (findings/recommendations)
    • Stage 5: Should continue? (yes, gathered enough)
    • Stage 6: Compile response (format findings)
    ↓
Backend Returns: {message, key_findings, recommendations, confidence}
    ↓
Frontend: Displays message with findings in feed
    ↓
Frontend: Shows "What we could improve:" list
    ↓
User: "Build the keyboard shortcuts overlay"
```

### Phase 2: Building
```
User Input: "Build the keyboard shortcuts overlay"
    ↓
Frontend: Detects /build|create|make/ pattern
    ↓
Frontend: Simulates buildImprovement() (currently)
    ↓
Frontend: Creates livePreview {title, code, description}
    ↓
Frontend: Shows live preview on right panel
    ↓
Frontend: Shows Approve/Iterate/Reject buttons
    ↓
User: Clicks ✅ Approve
    ↓
Frontend: Posts confirmation message
    ↓
Backend: Would merge code to actual files (Phase 2)
```

---

## Real Implementation (Phase 2)

Currently, `buildImprovement()` simulates the build:

```javascript
const buildImprovement = async (prompt) => {
  addMessage('🔨 Building... Let me create this for you.', 'agent');
  
  setTimeout(() => {
    // Simulated build - in Phase 2, this will actually:
    // 1. POST /build/component with prompt
    // 2. Get back actual generated code
    // 3. Preview the component in a sandbox
    // 4. Show real live demo
  }, 800);
};
```

When integrated with backend:

```javascript
const buildImprovement = async (prompt) => {
  const response = await fetch('http://localhost:8000/build/component', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      description: prompt,
      context: analysisResults // Use previous analysis
    })
  });
  
  const data = await response.json();
  
  setLivePreview({
    title: data.component_name,
    code: data.code,
    description: data.description,
    preview: data.preview_url // Actual component running
  });
};
```

---

## Supporting Backend Endpoints

### Current Endpoints Used
```
POST /reasoning/execute
├─ Input: {goal, context}
└─ Output: {success, result: {message, key_findings, recommendations, confidence}}

GET /reasoning/todos
├─ Output: {success, todos, current_goal, confidence}

POST /reasoning/understand
├─ Input: {goal}
└─ Output: {success, understanding, todos}

GET /reasoning/reset
├─ Output: {success, message}
```

### Future Endpoints for Sandbox
```
POST /build/component
├─ Input: {description, context}
├─ Process: Generate code based on requirements
└─ Output: {success, code, preview_url, test_results}

POST /analyze/codebase
├─ Input: {focus_area}
├─ Process: Deep analysis of specified code area
└─ Output: {findings, recommendations, metrics}

POST /refactor/code
├─ Input: {file_path, strategy}
├─ Process: Refactor code with specific strategy
└─ Output: {original_code, refactored_code, changes, tests}

PUT /approve/improvement
├─ Input: {improvement_id, component_path}
├─ Process: Merge improvement into actual codebase
└─ Output: {success, merged_file, commit_hash}

POST /test/component
├─ Input: {component_code}
├─ Process: Run tests on new component
└─ Output: {passed, failed, coverage, results}
```

---

## LLM Integration Points

The Sandbox Workshop leverages AgentReasoning in these ways:

### 1. Code Analysis (Using LLM)
```python
# backend/agent_reasoning.py

def analyze_codebase(self, focus_area):
    """Uses LLM to analyze own codebase"""
    response = llm_client.call({
        'system': 'You are analyzing Buddy\'s Python and React codebase. Provide specific, actionable improvements.',
        'prompt': f'Analyze {focus_area} and suggest improvements',
        'context': {
            'python_files': read_backend_files(),
            'react_files': read_frontend_files(),
            'architecture': current_architecture
        }
    })
    return extract_findings(response)
```

### 2. Recommendation Generation (Using LLM)
```python
def generate_recommendations(self, findings):
    """Uses LLM to turn findings into actionable recommendations"""
    response = llm_client.call({
        'system': 'Generate clear, prioritized recommendations based on these findings',
        'prompt': f'Findings: {findings}. Suggest 3-5 improvements we could make.',
    })
    return parse_recommendations(response)
```

### 3. Code Generation (Phase 2 with LLM)
```python
def generate_component_code(self, description, context):
    """Uses LLM to generate new component code"""
    response = llm_client.call({
        'system': 'Generate React components that match Buddy\'s style and architecture',
        'prompt': f'Generate a React component: {description}',
        'context': {
            'existing_components': get_component_examples(),
            'design_system': get_design_guidelines(),
            'requirements': context
        }
    })
    return extract_code(response)
```

---

## State Management in Sandbox

### Frontend State
```javascript
// SandboxWorkshop.js

// Messages history
const [messages, setMessages] = useState([
  {type: 'agent'|'user', content, timestamp, todos}
]);

// Current interaction state
const [input, setInput] = useState(''); // Textarea content
const [isAnalyzing, setIsAnalyzing] = useState(false); // Loading state
const [livePreview, setLivePreview] = useState(null); // Shown on right panel
```

### Flow
```
User types in textarea → setInput()
    ↓
User hits Enter → handleSendMessage()
    ↓
Detect intent → analyzeOwnCode() | buildImprovement() | conversationalResponse()
    ↓
setIsAnalyzing(true)
    ↓
API call to backend
    ↓
Receive response → addMessage()
    ↓
If building → setLivePreview()
    ↓
setIsAnalyzing(false)
    ↓
User: Approve/Iterate/Reject → handleApprove() | handleIterate() | handleReject()
```

---

## Error Handling

### Frontend Error Handling
```javascript
try {
  const response = await fetch('http://localhost:8000/reasoning/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal: prompt })
  });
  
  const data = await response.json();
  
  if (data.success) {
    addMessage(data.result.message, 'agent');
    setLivePreview({...});
  } else {
    addMessage(`Error: ${data.error}`, 'agent');
  }
} catch (error) {
  addMessage(`Couldn't analyze: ${error.message}`, 'agent');
}
```

### Backend Error Handling (in main.py)
```python
@app.post("/reasoning/execute")
async def reason_about_goal(request: ReasoningRequest):
    try:
        result = agent_reasoning.reason_about_goal(
            request.goal, 
            request.context or {}
        )
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": 500
        }
```

---

## Performance Considerations

### Caching
```python
# Cache analysis results to avoid re-analyzing same code
@lru_cache(maxsize=10)
def analyze_code_section(file_path: str) -> dict:
    # Read and analyze file
    return findings
```

### Streaming (Phase 2)
```javascript
// WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8000/reasoning/stream');

ws.onmessage = (event) => {
  const step = JSON.parse(event.data);
  // Update todos in real-time
  updateTodoProgress(step.step_num, step.status);
};
```

---

## Testing the Integration

### Test 1: Code Review
```bash
# Terminal 1: Backend is running
python -m uvicorn backend.main:app --port 8000

# Terminal 2: Frontend is running
cd frontend && npm start

# Browser: http://localhost:3000
# Go to Sandbox Workshop tab
# Type: "Review the ChatInterface code and suggest improvements"
# Should see analysis in 2-3 seconds
```

### Test 2: Building
```bash
# Type: "Build a keyboard shortcuts overlay"
# Should see live preview appear on right panel
```

### Test 3: Iteration
```bash
# Click 🔄 Iterate
# Type: "Make the overlay smaller"
# Should update preview
```

---

## Debugging Tips

### Check Backend Connection
```javascript
// In browser console
fetch('http://localhost:8000/docs')
  .then(r => r.ok ? console.log('✅ Backend OK') : console.log('❌ Error'))
  .catch(e => console.log('❌ Backend not reachable:', e));
```

### Monitor Messages
```javascript
// Add to SandboxWorkshop.js
useEffect(() => {
  console.log('Messages:', messages);
  console.log('Live Preview:', livePreview);
}, [messages, livePreview]);
```

### Check Reasoning Todos
```
GET http://localhost:8000/reasoning/todos
```

Returns current progress:
```json
{
  "success": true,
  "todos": [
    {"step_num": 1, "task": "Understand goal", "status": "complete"},
    {"step_num": 2, "task": "Plan approach", "status": "complete"},
    {"step_num": 3, "task": "Execute", "status": "in_progress"}
  ],
  "current_goal": "Review ChatInterface code",
  "confidence": 0.65
}
```

---

## Summary

The Sandbox Workshop connects to the existing backend `/reasoning/execute` endpoint and uses intent detection to trigger different behaviors:

- **Review intent** → `analyzeOwnCode()` → Shows findings in messages
- **Build intent** → `buildImprovement()` → Shows preview on right
- **Other intent** → `conversationalResponse()` → Natural dialogue

The backend's AgentReasoning class handles all the heavy lifting:
- Analyzing codebase with LLM
- Generating recommendations
- Storing todos/progress
- Tracking confidence

Future phases will add:
- Actual code generation in preview
- Real component rendering
- File writing/git integration
- WebSocket streaming for real-time updates

This creates a seamless, natural collaborative development experience where you guide Buddy to improve itself! 🚀
