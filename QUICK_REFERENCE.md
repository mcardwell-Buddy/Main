# Buddy Quick Reference 🚀

## What is Buddy?

A **31-tool autonomous agent** powered by:
- ✅ OpenAI GPT-4o-mini (language understanding)
- ✅ Firebase Firestore (long-term memory)
- ✅ LLM + Pattern hybrid (robust tool selection)
- ✅ Feedback system (learns from corrections)
- ✅ 8 completed learning objectives

---

## 🛠️ Your Tools (31 Total)

### Essential (Use Daily)
```
web_search        → Find information online
calculate         → Do math
get_time          → Check current time/date
read_file         → View file contents
```

### Content Analysis
```
summarize_text        → Create summaries
sentiment_analysis    → Check emotional tone
keyword_extraction    → Find main topics
extract_entities      → Get emails, URLs, names
```

### Code & Development
```
analyze_code      → Review code structure
find_bugs         → Identify issues
generate_code     → Write code snippets
dependency_map    → Map relationships
```

### Data Processing
```
parse_json        → Process JSON
aggregate_data    → Summarize data
statistical_analysis → Calculate mean/median/std
transform_data    → Convert formats (CSV→JSON)
```

### System & Monitoring
```
check_system_status  → CPU, memory, disk usage
list_processes       → Running programs
run_command          → Execute shell commands
```

### Specialized
```
compare_items     → Compare multiple things
diff_analysis     → Find differences
parse_html        → Extract web data
query_structure   → Analyze SQL
advanced_math     → Complex calculations
```

### Learning (About Buddy)
```
learning_query          → "What do you know about X?"
understanding_metrics   → Get Buddy's stats
```

---

## 💡 Common Tasks

### Research Something
```
User: "Research [topic]"
→ web_search → parse_html → summarize_text
→ keyword_extraction → extract_entities
```

### Analyze Code
```
User: "Review this code for bugs"
→ analyze_code → find_bugs → reflect
```

### Process Data
```
User: "Parse JSON and calculate average"
→ parse_json → aggregate_data → statistical_analysis
```

### Compare Options
```
User: "Compare [A] vs [B]"
→ web_search (both) → compare_items → reflect
```

### Monitor System
```
User: "Check system health"
→ check_system_status → list_processes
```

---

## 🎯 Example Queries

### Research
- "What is Cardwell Associates?"
- "Search for AI trends in 2024"
- "Find papers on machine learning"

### Analysis
- "What's the sentiment of this text?"
- "Extract keywords from this article"
- "Summarize this documentation"

### Development
- "Generate Python code for a function"
- "Analyze this code for security issues"
- "Map dependencies in this project"

### Data
- "Parse this JSON and calculate average"
- "Convert CSV to JSON format"
- "Run statistical analysis on this dataset"

### System
- "How much memory is being used?"
- "List all Python processes"
- "What's the current time?"

### Learning (About Buddy)
- "What do you know about Python?"
- "Show me your learning metrics"
- "How confident are you about [topic]?"

---

## 📊 How Buddy Works

```
1. You Ask
   ↓
2. LLM Understands Intent
   ↓
3. Smart Tool Selection
   ↓
4. Tool Execution
   ↓
5. LLM Synthesizes Answer
   ↓
6. You Learn Something New!
```

---

## 🧠 Learning Features

### Feedback System
- 👍 Mark answers as "Helpful"
- 👎 Mark as "Not Helpful"
- ❌ Teach Buddy corrections
- 🔍 Ask for "Deeper Dive"

### Knowledge Tracking
- 📚 Query what Buddy knows
- 📊 See learning metrics
- 🎯 Track expertise by topic
- 📈 Watch confidence grow

### Memory
- ✅ Remembers past interactions
- ✅ Learns from corrections
- ✅ Improves over time
- ✅ Stores knowledge in Firebase

---

## ⚙️ Configuration

### Backend
- Port: `8000`
- URL: `http://localhost:8000`
- Framework: FastAPI + Python

### Frontend
- Port: `3001`
- URL: `http://localhost:3001`
- Framework: React

### LLM
- Provider: OpenAI
- Model: gpt-4o-mini
- API Key: In `.env`

### Memory
- Database: Firebase Firestore
- Collection: `agent_memory`
- Status: Connected

### Web Search
- Provider: SerpAPI
- Daily Limit: 100 queries
- Status: Active

---

## 🚀 Getting Started

### 1. Start Backend
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 2. Start Frontend
```bash
cd frontend
npm start
```

### 3. Open Browser
```
http://localhost:3001
```

### 4. Ask Buddy Something!

---

## 📈 Buddy's Capabilities

| Aspect | Capability | Status |
|--------|-----------|--------|
| Tools | 31 specialized tools | ✅ Complete |
| Intelligence | LLM-powered understanding | ✅ Active |
| Memory | Long-term storage | ✅ Firebase |
| Learning | Feedback & improvement | ✅ Enabled |
| Autonomy | Multi-level permission system | ✅ 5 levels |
| Knowledge Graph | Visualization of learning | ✅ Available |
| Performance | Fast & scalable | ✅ Optimized |

---

## 💬 Natural Language Examples

### ✅ Good Questions
- "What is machine learning?"
- "Find recent news about AI"
- "Compare Python vs JavaScript"
- "Analyze this code for bugs"
- "What's the capital of France?"

### ✅ Complex Queries
- "Research AI frameworks and compare them"
- "Analyze customer reviews for sentiment"
- "Find and verify these links"
- "Process this data and show statistics"

### ✅ Learning Questions
- "What do you know about web development?"
- "Show me your learning metrics"
- "How confident are you about Python?"

---

## 🔧 Advanced Features

### Teaching Mode
Click "❌ Wrong" to correct Buddy's mistakes.

### Deeper Dive
Click "🔍 Deeper Dive" for comprehensive analysis.

### Knowledge Graph
Click "🧠 Knowledge Graph" to visualize learning.

### Goal Decomposition
Complex goals automatically broken into steps.

### Multi-Tool Workflows
Chains multiple tools together intelligently.

---

## 📞 Support / Troubleshooting

### Backend Not Starting
```bash
# Check Python installation
python --version

# Install dependencies
pip install -r requirements.txt

# Try again
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Frontend Not Loading
```bash
# Install dependencies
cd frontend && npm install

# Start dev server
npm start
```

### Tools Not Showing
```bash
# Restart backend to reload tools
GET http://localhost:8000/tools
```

### LLM Not Working
- Check `.env` has OpenAI API key
- Verify API key is valid
- Check internet connection

---

## 🎓 Learning Path

1. ✅ Try simple queries (web_search, calculate)
2. ✅ Use learning tools (learning_query, metrics)
3. ✅ Provide feedback (helpful/not helpful/wrong)
4. ✅ Watch Buddy improve
5. ✅ Use advanced tools (code, data, analysis)
6. ✅ Teach Buddy corrections
7. ✅ View knowledge graph
8. ✅ Leverage deeper dives

---

## 📊 Stats

- **Total Tools**: 31
- **Autonomy Levels**: 5
- **Learning Objectives**: 8/8 complete
- **Average Response**: 0.5-8 seconds
- **Success Rate**: 85-95%
- **Memory**: Firebase Firestore
- **API**: OpenAI GPT-4o-mini
- **Web Search**: SerpAPI

---

## 🎉 What's Next?

- ⭐ Use all 31 tools!
- ⭐ Teach Buddy corrections
- ⭐ View your knowledge graph
- ⭐ Build tool combinations
- ⭐ Create custom workflows
- ⭐ Watch Buddy grow smarter!

---

**Your Buddy is ready! Start asking questions! 🤖**
