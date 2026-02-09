# How the Agent Knows What to Save

## The Intelligence Layer

### Before (Dumb):
```
Every step → Save everything to Firebase
```
- No intelligence
- Wastes storage
- Hard to find important insights

### After (Smart):
```
Every step → Calculate Importance → Save only if >= 0.6
```

## Importance Scoring (0.0 to 1.0)

### Factors That Increase Importance:

1. **High Effectiveness** (0.7+)
   - Agent succeeded at the task
   - Tools worked well
   - Result: +0.3 to importance

2. **Large Confidence Change** (±0.15+)
   - Significant learning moment
   - Major success or failure
   - Result: +0.5 to importance

3. **Specific Strategy Advice** (long, actionable)
   - Not generic advice
   - Concrete next steps
   - Result: +0.2 to importance

4. **Tool Failures** (usefulness < 0.3)
   - Don't repeat mistakes
   - Critical to remember
   - Result: +0.3 to importance

5. **Errors** (any error in observation)
   - Always important
   - Result: +0.4 to importance

6. **Goal Completions** (always)
   - Track successful patterns
   - Result: 1.0 importance (always save)

## Example Scenarios

### ❌ NOT Saved (Importance 0.50)
```json
{
  "effectiveness_score": 0.5,
  "confidence_adjustment": 0.0,
  "strategy_adjustment": "Try again",
  "tool_feedback": {}
}
```
**Why?** Neutral, no learning, generic advice

### ✅ SAVED (Importance 0.88)
```json
{
  "effectiveness_score": 0.85,
  "confidence_adjustment": 0.15,
  "strategy_adjustment": "Web search was very effective. Use targeted queries for technical topics.",
  "tool_feedback": {
    "web_search": {"usefulness": 0.9}
  }
}
```
**Why?** High success, confidence boost, specific strategy

### ✅ SAVED (Importance 0.99)
```json
{
  "effectiveness_score": 0.2,
  "confidence_adjustment": -0.15,
  "strategy_adjustment": "This tool consistently fails. Avoid using it.",
  "tool_feedback": {
    "calculate": {"usefulness": 0.1}
  }
}
```
**Why?** Critical failure - must remember to avoid

## What Gets Saved

| Type | Always? | Threshold | Reason |
|------|---------|-----------|--------|
| Goal Completions | ✅ | 1.0 | Track success patterns |
| Tool Failures | ✅ | 0.9 | Don't repeat mistakes |
| Errors | ✅ | 0.9 | Debug and learn |
| High Effectiveness | ✅ | 0.7+ | Successful strategies |
| Neutral Reflections | ❌ | 0.5 | No value |
| Generic Advice | ❌ | 0.5 | Not actionable |

## Firebase Structure

```
agent_memory/
  ├── last_reflection:search for autonomous agents
  │   └── {
  │        "data": { reflection data },
  │        "metadata": {
  │          "importance": 0.88,
  │          "type": "reflection",
  │          "timestamp": "2026-02-03T12:34:56",
  │          "context": { goal, steps, tools }
  │        }
  │      }
  ├── observation:goal:step3
  │   └── { saved only if error or significant }
  └── goal_completion:calculate 15 + 27
      └── { always saved }
```

## New API Endpoint

**GET /memory/insights?goal=search**

Returns what the agent has learned about similar goals:
- Strategies that worked
- Tools to avoid
- Average effectiveness
- Confidence level

## Configuration

In `.env`:
```bash
# Save everything for learning (ignore importance)
DEBUG=true

# Production mode (only save important items)
DEBUG=false
```

## Benefits

✅ **Smarter Storage** - Only important data in Firebase  
✅ **Faster Learning** - Easy to find key insights  
✅ **Cost Efficient** - Less storage usage  
✅ **Better Decisions** - Agent learns from failures  
✅ **Traceable** - All saves have importance metadata  
