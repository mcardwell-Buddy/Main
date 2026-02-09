# Autonomous Agent - Full Stack

A production-ready autonomous AI agent with reflection, memory, and extensible tools.

## Architecture

**Backend (Python/FastAPI)**
- Bounded, observable agent runtime
- Tool registry with performance tracking
- Firebase-backed persistent memory
- Reflection system for self-improvement
- WebSocket streaming support

**Frontend (React)**
- Real-time agent monitoring
- Tool performance dashboard
- HTTP and WebSocket modes
- Beautiful, responsive UI

## Quick Start

### Backend

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment (copy `.env.example` to `.env`):
```bash
FIREBASE_ENABLED=true
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
SERPAPI_KEY=your-key-here
MOCK_MODE=false
```

3. Run the server:
```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm start
```

3. Open http://localhost:3000

## Available Tools

- **web_search**: Search the web using SerpAPI
- **reflect**: Self-evaluate recent actions and suggest improvements
- **calculate**: Evaluate mathematical expressions safely
- **read_file**: Read file contents (bounded, safe)
- **list_directory**: List directory contents
- **get_time**: Get current date and time

## API Endpoints

- `GET /` - Health check
- `GET /tools` - List all tools with performance metrics
- `POST /chat?goal=<goal>` - Run agent (HTTP, returns all steps)
- `WebSocket /ws` - Run agent (streaming, real-time updates)

## Key Features

✅ **Safety First**
- Bounded execution (max steps, timeouts)
- No infinite loops or hangs
- All tools are sandboxed

✅ **Observable**
- Structured JSON output per step
- WebSocket streaming for real-time monitoring
- Tool performance tracking

✅ **Self-Improving**
- Reflection after each step
- Memory-backed learning
- Confidence adjustment

✅ **Production Ready**
- Firebase persistence
- CORS enabled
- Error handling throughout
- Performance metrics

## Adding New Tools

```python
# backend/additional_tools.py or backend/tools.py
def my_tool(input_data):
    # Your logic here
    return {'result': 'data'}

tool_registry.register(
    'my_tool',
    my_tool,
    mock_func=lambda x: {'result': 'mock'},
    description='What your tool does'
)
```

## Testing

```bash
# Test memory
python -m backend.test_memory

# Test agent
python -m backend.test_run

# Test API
python test_api.py
```

## Next Steps

- Add more tools (database, APIs, etc.)
- Implement vector search for semantic memory
- Add user authentication
- Deploy to cloud (AWS, GCP, Azure)
- Add tool chaining and composition
- Implement circuit breakers for failing tools

---

Built with ❤️ using FastAPI, React, and Firebase
