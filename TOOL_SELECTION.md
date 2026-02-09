# How the Agent Knows to Search (and Use Other Tools)

## The Problem Before

```python
# Old code - VERY dumb
if 'search' in self.state.goal.lower():
    action = {'tool': 'web_search', 'input': query}
```

**Issues:**
- Only works if goal contains the exact word "search"
- Can't use other tools
- No learning from past experience
- No confidence scoring

## The Solution Now

### 1. Pattern Matching (Regex + Keywords)

Each tool has patterns that indicate when it should be used:

```python
'web_search': [
    r'\b(search|find|look up|research|investigate)\b',
    r'\b(latest|current|recent|news|information about)\b',
    r'\b(best practices|how to|tutorial|guide)\b',
]

'calculate': [
    r'\b(calculate|compute|solve|math)\b',
    r'[\d\s\+\-\*\/\(\)]+',  # Math expressions
]

'read_file': [
    r'\b(read|show|display)\b.*\b(file|document)\b',
    r'\.(txt|py|js|json|md)',  # File extensions
]
```

### 2. Intelligent Scoring

For each goal, the agent:

1. **Pattern Match** (0.0 to 1.0)
   - Checks regex patterns for each tool
   - Adds +0.3 for each matching pattern
   - Capped at 1.0

2. **Historical Performance** (0.0 to 1.0)
   - Looks at past success rate
   - Defaults to 0.5 for unused tools

3. **Combined Score**
   ```
   final_score = (pattern * 80%) + (performance * 20%)
   ```

4. **Memory Penalties**
   - If a tool failed before for this goal type: **×0.3 penalty**

### 3. Smart Input Extraction

Once a tool is selected, the agent extracts the relevant input:

| Tool | Extraction Logic |
|------|------------------|
| `web_search` | Remove command words ("search for", "find"), keep the query |
| `calculate` | Extract math expression (`15 + 27`) |
| `read_file` | Extract filename or path (`config.json`) |
| `list_directory` | Extract directory path |
| `get_time` | No input needed |

## Real Examples

### Example 1: Web Search
**Goal:** `"search for best practices for autonomous agents"`

1. Pattern matching:
   - "search" → +0.3 for web_search
   - "best practices" → +0.3 for web_search
   - **Pattern score: 0.60**

2. Performance: 0.50 (neutral, no history)

3. Final: `(0.60 * 0.8) + (0.50 * 0.2) = 0.58`

4. ✅ **Selected:** web_search  
   **Input:** `"best practices for autonomous agents"`  
   **Confidence:** 0.58

### Example 2: Calculator
**Goal:** `"calculate 15 + 27"`

1. Pattern matching:
   - "calculate" → +0.3
   - "15 + 27" (math expr) → +0.3
   - **Pattern score: 0.60**

2. Performance: 0.50

3. Final: 0.58

4. ✅ **Selected:** calculate  
   **Input:** `"15 + 27"`  
   **Confidence:** 0.58

### Example 3: Ambiguous Goal
**Goal:** `"what is 2 * (3 + 5)"`

1. Pattern matching:
   - "what is" → +0.3 for web_search
   - "2 * (3 + 5)" → +0.3 for calculate
   - **Multiple matches!**

2. Final scores:
   - web_search: 0.34
   - calculate: 0.34

3. ✅ **Selected:** web_search (first in tie)  
   **Input:** `"what is 2 * (3 + 5)"`  
   **Confidence:** 0.34 (lower due to ambiguity)

### Example 4: Learning from Failures
**Goal:** `"search for tutorials"`  
**Previous history:** web_search failed 3 times for this goal type

1. Pattern: 0.60
2. Performance: 0.50
3. Combined: 0.58
4. **Memory penalty:** 0.58 × 0.3 = 0.17
5. ❌ **Below threshold (0.15)** - tries a different tool or does nothing

## Configuration

### Confidence Threshold (in agent.py)
```python
if confidence >= 0.15:  # Adjustable
    use_tool()
```

- **0.15**: Moderate - tries tools when reasonably confident
- **0.30**: Conservative - only very confident matches
- **0.05**: Aggressive - tries tools on weak signals

### Pattern Weight vs Performance Weight
```python
final = (pattern * 80%) + (performance * 20%)
```

- Early in life: Pattern matching dominates (no history)
- Over time: Performance weight increases as tool usage history grows

## Benefits

✅ **Multi-tool support** - Not just search, but 6+ tools  
✅ **Intelligent matching** - Understands synonyms and patterns  
✅ **Learns from failures** - Avoids tools that didn't work  
✅ **Confidence scoring** - Knows when it's uncertain  
✅ **Smart input extraction** - Parses what the tool needs  
✅ **Extensible** - Add new tools by just adding patterns  

## API Endpoints

### Get Tool Selection Explanation
```http
GET /tools/explain?goal=search%20for%20tutorials
```

Returns:
```json
{
  "goal": "search for tutorials",
  "pattern_scores": {
    "web_search": 0.60,
    "calculate": 0.0
  },
  "selected": "web_search",
  "confidence": 0.58,
  "reasoning": "Pattern match: 'search' + 'for tutorials'"
}
```

## Adding New Tool Patterns

To teach the agent when to use a new tool:

```python
# In tool_selector.py
self.tool_patterns['my_new_tool'] = [
    r'\b(keyword1|keyword2|keyword3)\b',
    r'specific_pattern_here',
]
```

That's it! The agent automatically learns when to use it.
