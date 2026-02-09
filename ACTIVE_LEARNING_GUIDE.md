# Active Learning System

## What Was Added

Your agent now understands **3 types of knowledge queries**:

| Query Type | Pattern | Tool Used | What It Does |
|------------|---------|-----------|--------------|
| **Introspection** | "what do YOU know about X?" | `learning_query` | Checks agent's memory (self-reflection) |
| **Active Learning** | "learn about X" | `store_knowledge` | Researches topic AND saves to memory |
| **Research** | "what is X?" | `web_search` | Just researches (no saving) |

## How to Use

### 1. Introspection (Check What Agent Knows)
```
"what do you know about Python?"
"tell me what you've learned about Docker"
"show me your understanding of machine learning"
```
→ Uses `learning_query` tool to check agent's memory

### 2. Active Learning (Instruct Agent to Learn)
```
"learn about Python decorators"
"study quantum computing"
"research and remember Docker best practices"
"teach yourself TypeScript"
```
→ Uses `store_knowledge` tool to research AND save information

### 3. Research (Just Get Information)
```
"what is quantum computing?"
"explain Docker containers"
"define machine learning"
```
→ Uses `web_search` tool to research (no memory storage)

## Examples

### Before (Wrong Behavior)
```
User: "what do you know about machine learning?"
Agent: [Does 4 web searches, decomposes into subgoals]  ❌ WRONG
```

### After (Correct Behavior)
```
User: "what do you know about machine learning?"
Agent: [Checks memory] "Based on X data points, confidence 0.65..."  ✅ Introspection

User: "learn about Python decorators"
Agent: [Researches + saves] "Successfully learned about Python decorators"  ✅ Learning

User: "what is quantum computing?"
Agent: [Web search] "Quantum computing is..."  ✅ Research
```

## Technical Details

### New Tool: `store_knowledge`

**Located**: `backend/learning_tools.py`

**Function**: Actively researches a topic and stores information in agent memory

**Parameters**:
- `topic` (str): What to learn about
- `information` (str): Information to store
- `source` (str): Where knowledge came from

**Returns**:
```json
{
  "topic": "Python decorators",
  "status": "learned",
  "stored": true,
  "message": "Successfully learned about Python decorators"
}
```

### Pattern Recognition

**Atomic Patterns** (never decomposed):
- `\b(what do you know|tell me what you know)\b` → Introspection
- `\b(learn about|study|research and remember)\b` → Active learning

**Tool Selection**:
1. LLM checks critical distinctions first
2. Falls back to pattern matching
3. Patterns prioritized: `learning_query` > `store_knowledge` > `web_search`

### Files Modified

1. **backend/learning_tools.py**
   - Added `store_knowledge()` function
   - Updated tool descriptions for clarity
   - Registered new tool

2. **backend/tool_selector.py**
   - Added `store_knowledge` patterns
   - Patterns ordered by priority

3. **backend/goal_decomposer.py**
   - Added learning instruction patterns to `ATOMIC_PATTERNS`
   - Reordered to check patterns BEFORE LLM

4. **backend/llm_client.py**
   - Updated decompose_goal prompt to recognize learning instructions
   - Updated select_tool prompt with critical distinctions

## Testing

Run `python test_learning.py` to verify all patterns work correctly.

## Integration with Memory System

The `store_knowledge` tool automatically:
- ✅ Saves with high importance (active learning is valuable)
- ✅ Stores in Firebase with metadata
- ✅ Makes information retrievable via `learning_query`
- ✅ Builds knowledge graph connections

## Next Steps

Now you can:
1. **Instruct agent to learn**: "learn about Docker security"
2. **Check what it learned**: "what do you know about Docker?"
3. **Build curriculum**: Give it sequential learning tasks
4. **Track progress**: Use knowledge graph to see what it knows

The agent now has a proper distinction between:
- 🔍 **Introspection**: Checking existing knowledge
- 📚 **Learning**: Actively acquiring new knowledge
- 🔎 **Research**: Just getting information
