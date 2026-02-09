# Learning System Quick Reference

## TL;DR - How Your Agent Learns

**Before**: Single web search → copy-paste snippet → maybe save
**Now**: 4-5 searches → LLM synthesis → structured knowledge → always saved

## The 3 Learning Commands

### 1. 🔍 Introspection: "What do YOU know?"
```
"what do you know about Python?"
"tell me what you've learned about Docker"
```
→ Checks memory, doesn't search
→ Tool: `learning_query`
→ Returns what agent already knows

### 2. 📚 Active Learning: "Learn about X"
```
"learn about Python decorators"
"study quantum computing"
"teach yourself Docker"
```
→ Does 4-5 web searches
→ Tool: `store_knowledge`  
→ Stores structured knowledge
→ **This is the deep learning!**

### 3. 🔎 Research: "What is X?"
```
"what is quantum computing?"
"explain Docker containers"
```
→ Single web search
→ Tool: `web_search`
→ Doesn't save to memory

## What Happens During "learn about X"

```
📝 Generate 4 queries
   ├─ "what is X"
   ├─ "how does X work"
   ├─ "X examples and use cases"
   └─ "X pros and cons"

🔍 Execute 4 searches (12-15 results total)

🧠 LLM Synthesis
   ├─ Extract key concepts (5-7)
   ├─ Summarize definition
   ├─ Explain mechanism
   ├─ List applications
   └─ Calculate confidence

💾 Store in Memory (importance = 1.0)
   ├─ Structured knowledge
   ├─ Key concepts
   ├─ Facts (8+)
   └─ Sources (10 URLs)

✅ Return learning summary
```

## What Gets Saved to Memory

| Type | Importance | Always Saved? |
|------|------------|---------------|
| **Active Learning** | **0.95-1.0** | ✅ YES |
| Goal Completion | 1.0 | ✅ YES |
| Tool Failure | 0.9 | ✅ YES |
| High-Quality Reflection | 0.8+ | ✅ YES |
| Normal Reflection | 0.5 | ❌ NO |
| Error Observation | 0.9 | ✅ YES |

**Threshold**: 0.6 (only items ≥ 0.6 are saved)

## Steps Allowed

- **Max steps per goal**: 8
- **Learning goals**: Use 1 step (but 4-5 searches internally)
- **Composite goals**: Split 8 steps across subgoals

## Test It

```bash
# Learn something
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"goal": "learn about Python decorators"}'

# Check what it learned
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"goal": "what do you know about Python decorators?"}'
```

## Expected Results

**Learning Output**:
```json
{
  "topic": "Python decorators",
  "status": "learned",
  "confidence": 0.90,
  "key_concepts": [
    "Higher-Order Function",
    "Syntactic Sugar",
    "Function Wrapping",
    "Reusability",
    "Chaining"
  ],
  "facts_learned": 8,
  "searches_performed": 4,
  "results_analyzed": 12,
  "stored": true
}
```

**Introspection Output**:
```json
{
  "topic": "Python decorators",
  "confidence": 0.90,
  "expertise_level": "Proficient",
  "knowledge_summary": {
    "key_concepts": ["..."],
    "total_observations": 1,
    "data_points": 12
  },
  "knowledge_gaps": [],
  "learning_suggestions": ["Continue practicing"]
}
```

## Files Changed

1. **backend/learning_tools.py**
   - Rewrote `store_knowledge()` for deep learning
   - Added `_generate_learning_queries()`
   - Added `_synthesize_knowledge()` with LLM
   - Added `_extract_bullet_points()`, `_extract_key_terms()`, `_extract_facts()`

2. **backend/memory_manager.py**
   - Added `item_type='learning'` with importance 0.95-1.0
   - Boosts for multi-search and high confidence

3. **backend/llm_client.py**
   - Updated tool selection prompt with learning distinctions
   - Updated goal decomposition prompt for learning instructions

4. **backend/tool_selector.py**
   - Added `store_knowledge` patterns

5. **backend/goal_decomposer.py**
   - Added learning patterns to `ATOMIC_PATTERNS`
   - Reordered to check patterns BEFORE LLM

## Key Insight

The agent doesn't just scrape web pages anymore. It:
1. **Researches** comprehensively (4-5 searches)
2. **Synthesizes** across sources (LLM-powered)
3. **Structures** knowledge (concepts, facts, sources)
4. **Stores** permanently (high importance)
5. **Retrieves** intelligently (when asked)

**This is real learning, not carnival answers.**
