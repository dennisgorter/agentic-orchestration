# Agent Orchestrator - Car Pollution Zone Eligibility Service

A proof-of-concept FastAPI service with React frontend that uses LangGraph to orchestrate car eligibility checks for city pollution zones. The service intelligently routes user queries through a deterministic workflow, using OpenAI for natural language understanding while keeping business logic rule-based.

## 🚀 Quick Start

**Want to get started immediately?** → See [QUICKSTART.md](QUICKSTART.md)

**TL;DR:**
```bash
# Terminal 1: Start Backend
export OPENAI_API_KEY="sk-your-key"
./start.sh

# Terminal 2: Start Frontend
cd frontend && npx vite

# Open browser: http://localhost:3000
```

## Features

- **🖥️ React Chat Interface**: Modern, user-friendly chat UI with example queries and available cars display
- **🌍 Automatic Language Detection**: Detects user's language and responds accordingly (English, Spanish, French, Dutch, German, Italian, Portuguese)
- **🔄 Car Context Preservation**: Maintains car context across conversation turns for follow-up questions
- **Multi-intent handling**: Single car queries, fleet queries, and policy-only questions
- **Smart disambiguation**: Automatically asks clarifying questions when multiple cars or zones match
- **Deterministic eligibility**: Rule-based decision engine (not LLM-based)
- **LangGraph workflow**: State machine controls orchestration flow
- **OpenAI integration**: Intent extraction, question phrasing, and explanation generation
- **Mock services**: In-memory car and policy data for PoC
- **Request Traceability**: Unique trace IDs for every request with structured logging

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes with step-by-step setup
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)** - Comprehensive technical documentation including:
  - Complete feature list and implementation details
  - Bug fixes (VIN context preservation, graph recursion)
  - Frontend architecture (React + Vite)
  - Language detection system (7 languages)
  - Traceability system (structured logging + trace IDs)
  - Architecture patterns and design decisions
  - Extension points for production deployment
- **[TRACEABILITY.md](TRACEABILITY.md)** - Guide to request tracing and debugging

## User Interface

The frontend provides:
- ✅ **Example Queries** - Click pre-built questions to get started
- ✅ **Available Cars Display** - See which test cars you can use
- ✅ **Interactive Disambiguation** - Click buttons to answer clarifying questions
- ✅ **Trace ID Display** - Debug requests with unique identifiers
- ✅ **Responsive Design** - Works on desktop and mobile

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         User Browser                              │
│                    http://localhost:3000                          │
│                     (React Chat Interface)                        │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTP Requests
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Backend API Server                           │
│                    http://localhost:8000                          │
│                      (FastAPI + LangGraph)                        │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
         User Query → Intent Extraction (LLM) → Car Resolution
                                                       ↓
         Final Explanation (LLM) ← Eligibility Decision (Rules) ← Zone Resolution
                                                                         ↓
                                                                   Policy Fetch
```

### Components

- **React Frontend**: Chat interface with examples and disambiguation UI
- **FastAPI**: REST API layer (`/chat`, `/chat/answer`, `/health`)
- **LangGraph**: Workflow orchestration with conditional routing
- **OpenAI GPT-4o-mini**: NLU and explanation generation
- **Pydantic**: Strict schema validation
- **Mock Services**: Stub data for cars and city policies

## Project Structure

```
agentic-orchestrator/
├── frontend/                # React chat interface
│   ├── src/
│   │   ├── App.jsx         # Main chat component
│   │   ├── App.css         # Styling
│   │   └── main.jsx        # React entry point
│   ├── index.html          # HTML template
│   ├── package.json        # Node dependencies
│   ├── vite.config.js      # Vite config with proxy
│   ├── start_frontend.sh   # Startup script
│   └── README.md           # Frontend documentation
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI endpoints
│   ├── models.py           # Pydantic models
│   ├── graph.py            # LangGraph workflow
│   ├── llm.py              # OpenAI client wrapper
│   ├── rules.py            # Eligibility decision logic
│   ├── tools.py            # Mock services (cars, policies)
│   ├── state.py            # Session management
│   └── logging_config.py   # Structured logging & traceability
├── tests/
│   ├── __init__.py
│   └── test_graph.py       # Unit tests with mocked LLM
├── requirements.txt        # Python dependencies
├── start.sh               # Backend startup script
├── test_api.sh            # API test script
├── QUICKSTART.md          # Quick start guide
├── TRACEABILITY.md        # Traceability guide
└── README.md              # This file
```

## Setup

### Prerequisites

- Python 3.9+
- OpenAI API key

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /Users/dennisgorter/Projects/agentic-orchestrator
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key:
   # OPENAI_API_KEY=sk-...
   ```

   Or export directly:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

### Running the Service

**Backend:**

Validate setup (recommended):
```bash
python validate.py
```

Start the backend server:
```bash
./start.sh
```

Server runs at: http://localhost:8000

Test the API:
```bash
./test_api.sh
```

**Frontend (React Chat UI):**

Navigate to frontend directory:
```bash
cd frontend
```

Install dependencies (first time only):
```bash
npm install
```

Start the frontend:
```bash
./start_frontend.sh
```

Frontend runs at: http://localhost:3000

Open http://localhost:3000 in your browser to use the chat interface!

### What You Can Ask (POC Scope)

The POC understands these types of queries:

**Single Car Eligibility:**
- "Is my car AB-123-CD allowed to enter Amsterdam city center?"
- "Can I drive my electric car IJ-789-KL into Amsterdam city center?"
- "Is EF-456-GH allowed in Rotterdam?"

**Fleet Queries:**
- "Which of my cars can enter Amsterdam city center?"
- "Can any of my cars access the Amsterdam logistics zone?"

**Policy Information:**
- "What are the pollution rules in Amsterdam?"
- "What are the pollution rules in Rotterdam?"
- "Tell me about the Amsterdam LEZ zone"

**Available Test Cars:**
- **AB-123-CD** - Diesel Euro 4 (❌ Banned in Amsterdam LEZ)
- **EF-456-GH** - Diesel Euro 5 (✅ Allowed in Amsterdam LEZ)
- **IJ-789-KL** - Electric (✅ Allowed everywhere)
- **MN-321-OP** - Petrol Euro 6 (✅ Allowed in Amsterdam LEZ)

**Available Cities:**
- Amsterdam (with LEZ and ZEZ zones)
- Rotterdam (with Environmental Zone)
uvicorn app.main:app --reload
# OR use the convenience script:
./start.sh
```

The service will be available at `http://localhost:8000`

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Running Tests

```bash
pytest tests/ -v
```

Tests use mocked LLM calls and don't require an API key.

## API Usage Examples

### Example 1: Single Car Eligibility Check

Check if a specific car is allowed in a zone:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user_123",
    "message": "Is my car AB-123-CD allowed to enter Amsterdam city center?"
  }'
```

**Expected Response:**
```json
{
  "session_id": "user_123",
  "reply": "Your vehicle AB-123-CD (diesel, euro4) is not allowed...",
  "pending_question": false,
  "options": null,
  "state": null
}
```

### Example 2: Fleet Eligibility Check

Check all cars at once:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user_456",
    "message": "Which of my cars can enter Amsterdam city center?"
  }'
```

**Expected Response:**
```json
{
  "session_id": "user_456",
  "reply": "Out of your 4 vehicles, 2 are allowed...",
  "pending_question": false,
  "options": null,
  "state": null
}
```

### Example 3: Disambiguation Flow

When multiple zones match, the system asks for clarification:

**Step 1 - Initial query:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user_789",
    "message": "Can I drive in Amsterdam with my car?"
  }'
```

**Response (disambiguation needed):**
```json
{
  "session_id": "user_789",
  "reply": "Which zone are you asking about?",
  "pending_question": true,
  "options": [
    {
      "index": 0,
      "label": "Amsterdam City Center LEZ (LEZ)",
      "zone_id": "ams_lez_01"
    },
    {
      "index": 1,
      "label": "Amsterdam Logistics ZEZ (ZEZ)",
      "zone_id": "ams_zez_01"
    }
  ],
  "state": null
}
```

**Step 2 - Answer disambiguation:**
```bash
curl -X POST http://localhost:8000/chat/answer \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user_789",
    "selection_index": 0
  }'
```

**Final Response:**
```json
{
  "session_id": "user_789",
  "reply": "Your vehicle is allowed to enter Amsterdam City Center LEZ...",
  "pending_question": false,
  "options": null,
  "state": null
}
```

### Example 4: Policy-Only Query

Ask about zone rules without mentioning a car:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user_999",
    "message": "What are the pollution rules in Amsterdam city center?"
  }'
```

**Expected Response:**
```json
{
  "session_id": "user_999",
  "reply": "The Amsterdam City Center LEZ bans diesel passenger cars with Euro 4 or lower...",
  "pending_question": false,
  "options": null,
  "state": null
}
```

### Example 5: Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "agent-orchestrator"
}
```

## Mock Data

The PoC includes mock data for demonstration:

### Cars (all sessions share these):
- **AB-123-CD**: Diesel, Euro 4, M1 (passenger) - *Banned in most LEZs*
- **EF-456-GH**: Petrol, Euro 5, M1 - *Usually allowed*
- **IJ-789-KL**: Electric, M1 - *Always allowed*
- **MN-321-OP**: Diesel, Euro 6, N1 (commercial) - *Depends on zone*

### Zones:
- **Amsterdam City Center LEZ**: Bans diesel Euro 4 and below for M1
- **Amsterdam Logistics ZEZ**: Requires zero-emission (BEV) for N1
- **Rotterdam Environmental Zone**: Bans diesel Euro 3 and below

## Key Design Decisions

### 1. Deterministic Eligibility
The `decide_eligibility()` function in [app/rules.py](app/rules.py) uses pure Python logic. The LLM never makes the allow/deny decision.

### 2. LangGraph State Machine
The workflow in [app/graph.py](app/graph.py) uses conditional edges to route based on:
- Intent type (single_car / fleet / policy_only)
- Disambiguation needs (multiple matches)
- Missing data (car fields)

### 3. JSON Schema Validation
All LLM outputs are parsed into Pydantic models with automatic retry and repair on parse failure.

### 4. Model Selection
- **Default**: `gpt-4o-mini` for all calls
- **Fallback**: Same model for now (in production, upgrade to `gpt-4o` on failure)

### 5. Session State
In-memory dictionary stores conversation state. In production, use Redis or database.

## Extending the PoC

### Add Real Services
Replace mock functions in [app/tools.py](app/tools.py):
```python
def list_user_cars(session_id: str) -> list[Car]:
    # Call actual car registration API
    response = httpx.get(f"https://api.example.com/users/{session_id}/cars")
    return [Car(**c) for c in response.json()]
```

### Add More Rules
Extend [app/rules.py](app/rules.py) with additional policy logic:
- Time-based restrictions
- Emission zone tiers
- Vintage car exemptions
- Permit checking

### Add Authentication
Add API key or JWT authentication to FastAPI:
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/chat", dependencies=[Depends(security)])
async def chat(request: ChatRequest):
    ...
```

### Add Observability
Add structured logging and tracing:
```python
import structlog

logger = structlog.get_logger()
logger.info("decision_made", car_id=car.car_id, allowed=decision.allowed)
```

## Troubleshooting

### OpenAI API Errors
If you see authentication errors:
1. Verify `OPENAI_API_KEY` is set correctly
2. Check API key has sufficient quota
3. Ensure you're using a valid model name

### Import Errors
If you see module not found:
```bash
# Make sure you're in the project root and venv is activated
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### LangGraph State Issues
If state isn't persisting across turns:
- Check that session_id is consistent across requests
- Verify session store is properly initialized
- For debugging, add `"state": result_state.model_dump()` to responses

## License

MIT License - This is a proof-of-concept for demonstration purposes.

## Contact

For questions or issues, please open an issue in the repository.
