# LLM Integration Guide

## Overview
Buddy now supports LLM integration for improved natural language understanding:
- **Tool Selection**: LLM understands intent better than regex patterns
- **Goal Decomposition**: Intelligently breaks complex goals into subgoals
- **Answer Synthesis**: Natural, conversational responses

## Setup

### 1. Install LLM Dependencies

#### For OpenAI (Recommended for simplicity):
```bash
pip install openai
```

#### For Anthropic Claude:
```bash
pip install anthropic
```

### 2. Configure .env

Add your API key to `.env`:

```env
# For OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...your-key-here...
OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo

# For Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### 3. Restart Backend
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## How It Works

### Without LLM (Pattern-Based)
- ❌ Brittle regex patterns
- ❌ "What is Cardwell Associates?" → calculate tool (wrong!)
- ❌ Complex goals poorly decomposed
- ❌ Answers are template-based

### With LLM (Intelligent)
- ✅ True language understanding
- ✅ "What is Cardwell Associates?" → web_search (correct!)
- ✅ Smart goal decomposition
- ✅ Natural, conversational answers

## Fallback System

Buddy uses a **graceful degradation** approach:

1. **LLM Available**: Uses LLM for intelligent understanding
2. **LLM Fails**: Falls back to pattern-based heuristics
3. **LLM Disabled**: Works 100% offline with patterns

Set `LLM_PROVIDER=none` to disable LLM entirely.

## Cost Optimization

### Recommended Models:
- **OpenAI**: `gpt-4o-mini` (~$0.15 per 1M tokens)
- **Anthropic**: `claude-3-5-haiku` (fast, cheap)
- **Local**: Run llama.cpp or Ollama (free, no API)

### Token Usage:
- Tool selection: ~200-300 tokens per query
- Goal decomposition: ~300-400 tokens
- Answer synthesis: ~400-500 tokens

**Average cost per interaction**: $0.001-0.002 with gpt-4o-mini

## Benefits

### Tool Selection Example:

**Question**: "What is Cardwell Associates?"

**Pattern-Based** (Old):
- Sees "What is"
- Triggers calculate tool ❌
- Wrong result

**LLM-Based** (New):
- Understands: "asking about a company/organization"
- Selects web_search tool ✅
- Correct result

### Answer Synthesis Example:

**Pattern-Based**:
```
{'title': 'Cardwell Associates', 'link': 'https://...', 'snippet': '...'}
```
Hard to read, raw JSON.

**LLM-Based**:
```
Cardwell Associates is a benefits consulting firm that helps companies 
reduce insurance costs by an average of 20% while maintaining quality 
coverage. They specialize in healthcare plan optimization. Learn more 
at cardwellassociates.com
```
Natural, informative, well-formatted.

## Testing

Test the LLM integration:

```bash
# Tool selection
curl -X POST "http://localhost:8000/chat?goal=What%20is%20Cardwell%20Associates"

# Goal decomposition  
curl -X POST "http://localhost:8000/chat?goal=Research%20and%20compare%20Python%20vs%20JavaScript"

# Answer synthesis
curl -X POST "http://localhost:8000/chat?goal=What%20is%202%20plus%202"
```

Check logs for:
- `LLM selected web_search (confidence: 0.95)`
- `LLM classified goal as composite`
- `Using LLM-synthesized answer`

## Troubleshooting

### "LLM library not installed"
```bash
pip install openai  # or anthropic
```

### "OpenAI initialization failed"
- Check API key in .env
- Verify key has credits: https://platform.openai.com/usage

### "LLM selection failed, falling back to patterns"
- This is normal! Fallback ensures Buddy keeps working
- Check logs for specific error

### Disable LLM
Set in .env:
```env
LLM_PROVIDER=none
```

## Next Steps

1. **Add your API key** to `.env`
2. **Restart backend** 
3. **Test queries** and watch the logs
4. **Compare results** with/without LLM

Buddy will automatically use LLM when available and fall back to patterns when needed!
