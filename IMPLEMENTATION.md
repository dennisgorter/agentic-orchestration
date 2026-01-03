# Agent Orchestrator - Implementation Summary

## ✅ Completed Implementation

This document provides a technical summary of the completed Agent Orchestrator service.

---

## 📁 Project Structure

```
agentic-orchestrator/
├── app/
│   ├── __init__.py           # Package marker
│   ├── main.py              # FastAPI endpoints (/chat, /chat/answer, /health)
│   ├── models.py            # Pydantic schemas (Car, Zone, Policy, Decision, etc.)
│   ├── graph.py             # LangGraph workflow with nodes and routing
│   ├── llm.py               # OpenAI client with retry/repair logic
│   ├── rules.py             # Deterministic eligibility decision engine
│   ├── tools.py             # Mock services (cars, policies, zone resolution)
│   └── state.py             # In-memory session state management
│
├── tests/
│   ├── __init__.py
│   └── test_graph.py        # Unit tests with mocked LLM calls
│
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── .gitignore              # Git ignore rules
├── README.md               # User documentation
├── start.sh                # Quick start script
├── test_api.sh             # API testing script with curl examples
└── workflow_diagram.py     # ASCII workflow visualization
```

---

## 🎯 Key Features Implemented

### 1. Multi-Intent Support
- ✅ **Single Car Query**: "Is my car AB-123-CD allowed in Amsterdam?"
- ✅ **Fleet Query**: "Which of my cars can enter Amsterdam?"
- ✅ **Policy-Only Query**: "What are the pollution rules in Amsterdam?"

### 2. Smart Disambiguation
- ✅ Multiple zones match → Ask user to select
- ✅ Multiple cars match → Ask user to select
- ✅ No car specified for single_car intent → Ask user to select
- ✅ Natural question phrasing via LLM

### 3. Deterministic Decision Logic
- ✅ Rule-based eligibility checking (NO LLM in decision)
- ✅ Example rule 1: Diesel Euro 4 banned in Amsterdam LEZ (M1 vehicles)
- ✅ Example rule 2: N1 vehicles must be BEV in Amsterdam ZEZ
- ✅ Missing field detection (fuel_type, euro_class, vehicle_category)
- ✅ Returns allowed="unknown" when data insufficient

### 4. LLM Integration (OpenAI)
- ✅ Intent + slot extraction from user message
- ✅ Disambiguation question generation
- ✅ Final explanation generation (grounded in facts)
- ✅ JSON schema validation with Pydantic
- ✅ Automatic retry on parse failure
- ✅ Repair step: strip markdown, re-prompt model
- ✅ Fallback model on continued failure
- ✅ Uses gpt-4o-mini as default model

### 5. LangGraph Orchestration
- ✅ State machine with conditional routing
- ✅ Nodes: extract_intent → resolve_zone → resolve_car → fetch_policy → decide → explain
- ✅ Conditional edges based on:
  - Intent type
  - Disambiguation needs
  - Missing data
- ✅ Early termination on disambiguation (pending_question)
- ✅ Resume workflow after user answers

### 6. Mock Services
- ✅ 4 sample cars (diesel euro4, petrol euro5, electric, diesel euro6 N1)
- ✅ 3 zones (Amsterdam LEZ, Amsterdam ZEZ, Rotterdam LEZ)
- ✅ Zone policies with rules and exemptions
- ✅ Easy to replace with real API calls

### 7. API Design
- ✅ POST /chat - Main entry point
- ✅ POST /chat/answer - Handle disambiguation responses
- ✅ GET /health - Health check
- ✅ Consistent response schema (reply, pending_question, options)
- ✅ Session state persistence across conversation
- ✅ CORS enabled
- ✅ Auto-generated OpenAPI docs

### 8. Testing
- ✅ Unit tests for all workflow nodes
- ✅ Mocked LLM calls (no API key needed for tests)
- ✅ Test cases:
  - Intent extraction (single, fleet, policy)
  - Zone resolution (single, multiple, none)
  - Car resolution (single, multiple, not found)
  - Policy fetch
  - Decision making (allowed, banned, unknown)
  - Missing fields handling
  - Fleet eligibility
- ✅ Run with: `pytest tests/ -v`

---

## 🏗️ Architecture Highlights

### Deterministic Control Flow
```
LangGraph orchestrates the workflow.
LLM never decides routing or eligibility.
Business logic is pure Python functions.
```

### LLM Usage Pattern
```python
# 1. Extract structured data
intent = llm.call_extract_intent_slots(user_message)

# 2. Generate natural questions
question = llm.call_make_disambiguation_question("car", options)

# 3. Explain decisions
reply = llm.call_explain(decision, car, policy, zone)
```

### State Machine Pattern
```
Each node returns updated AgentState.
Conditional edges route based on state fields.
Pending questions pause workflow until user answers.
```

### Error Handling
- JSON parse failures → Automatic repair + retry
- Missing city → User-friendly error message
- Zone not found → Clear error response
- Car not found → Prompt for valid identifier
- Missing vehicle data → Return unknown + list missing fields

---

## 📊 Mock Data Summary

### Cars
| Plate | Fuel | Euro | Category | Expected Result in Amsterdam LEZ |
|-------|------|------|----------|----------------------------------|
| AB-123-CD | Diesel | Euro 4 | M1 | ❌ BANNED |
| EF-456-GH | Petrol | Euro 5 | M1 | ✅ ALLOWED |
| IJ-789-KL | Electric | N/A | M1 | ✅ ALLOWED |
| MN-321-OP | Diesel | Euro 6 | N1 | ✅ ALLOWED (LEZ), ❌ BANNED (ZEZ) |

### Zones
| Zone | City | Type | Key Rules |
|------|------|------|-----------|
| Amsterdam City Center LEZ | Amsterdam | LEZ | Ban diesel Euro 4 and below (M1) |
| Amsterdam Logistics ZEZ | Amsterdam | ZEZ | Ban non-BEV (N1 commercial) |
| Rotterdam Environmental Zone | Rotterdam | LEZ | Ban diesel Euro 3 and below |

---

## 🚀 Quick Start Commands

```bash
# 1. Setup
cd /Users/dennisgorter/Projects/agentic-orchestrator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
export OPENAI_API_KEY="sk-..."

# 3. Run
uvicorn app.main:app --reload
# OR use convenience script:
./start.sh

# 4. Test
pytest tests/ -v
# OR test API endpoints:
./test_api.sh

# 5. View workflow
python workflow_diagram.py
```

---

## 📝 Example API Interactions

### Single Car Check (Banned)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user1",
    "message": "Is my car AB-123-CD allowed in Amsterdam city center?"
  }'

# Response: "Your vehicle AB-123-CD (diesel, euro4) is not allowed..."
```

### Fleet Check
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user2",
    "message": "Which of my cars can enter Amsterdam city center?"
  }'

# Response: Lists allowed/banned cars with reasons
```

### Disambiguation Flow
```bash
# Step 1: Ambiguous query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user3",
    "message": "Can I drive in Amsterdam?"
  }'

# Response: pending_question=true, options=[...]

# Step 2: User selects option 0
curl -X POST http://localhost:8000/chat/answer \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user3",
    "selection_index": 0
  }'

# Response: Final eligibility result
```

---

## 🔧 Extension Points

### 1. Replace Mock Services
In [app/tools.py](app/tools.py), replace stub functions with real API calls:
```python
import httpx

def list_user_cars(session_id: str) -> list[Car]:
    response = httpx.get(f"https://api.example.com/cars?user={session_id}")
    return [Car(**c) for c in response.json()]
```

### 2. Add More Rules
In [app/rules.py](app/rules.py), extend `decide_eligibility()`:
```python
# Add time-based restrictions
if policy.time_restricted:
    current_hour = datetime.now().hour
    if 7 <= current_hour <= 9:  # Rush hour
        # Apply stricter rules
```

### 3. Add Authentication
In [app/main.py](app/main.py):
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/chat", dependencies=[Depends(security)])
async def chat(request: ChatRequest, token: HTTPAuthorizationCredentials = Depends(security)):
    # Validate token
```

### 4. Add Persistent Storage
Replace [app/state.py](app/state.py) with Redis:
```python
import redis

class RedisSessionStore:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379)
    
    def get(self, session_id: str) -> Optional[AgentState]:
        data = self.redis.get(f"session:{session_id}")
        if data:
            return AgentState.model_validate_json(data)
```

### 5. Add Observability
```python
import structlog

logger = structlog.get_logger()

def decide_node(state: AgentState):
    logger.info("decision_started", car=state.selected_car.plate)
    decision = decide_eligibility(...)
    logger.info("decision_made", allowed=decision.allowed, reason=decision.reason_code)
```

---

## 🧪 Testing Strategy

### Unit Tests (tests/test_graph.py)
- All workflow nodes tested independently
- LLM calls mocked (no API usage)
- Test cases cover:
  - Happy paths (allowed, banned, unknown)
  - Edge cases (missing data, not found)
  - Disambiguation flows
  - Fleet processing

### Integration Testing (manual)
- Use `test_api.sh` for end-to-end API testing
- Verify OpenAI integration works
- Test conversation continuity across turns

### Load Testing (future)
```bash
# Example with Apache Bench
ab -n 1000 -c 10 -p payload.json -T application/json \
  http://localhost:8000/chat
```

---

## 📐 Design Decisions Rationale

### Why LangGraph?
- Explicit state management (vs. implicit in chains)
- Visual workflow representation
- Conditional routing without complex if/else
- Easy to debug and extend

### Why Separate Decision from LLM?
- Deterministic = testable, auditable, explainable
- Legal/compliance requirements for allow/deny
- Consistent outcomes (no hallucination risk)
- LLM for UX (understanding, phrasing), not logic

### Why In-Memory State for PoC?
- Simplest for demonstration
- No infrastructure dependencies
- Easy to replace (see Redis example above)

### Why Mock Services?
- Self-contained demo (no external APIs needed)
- Faster development and testing
- Clear API contract defined
- Easy to swap with real services

---

## 🎓 Code Organization Principles

1. **Separation of Concerns**
   - Models: Pure data structures (models.py)
   - Business Logic: Rules without side effects (rules.py)
   - I/O: LLM calls, service calls (llm.py, tools.py)
   - Orchestration: Workflow graph (graph.py)
   - API: HTTP layer (main.py)

2. **Type Safety**
   - All models use Pydantic
   - Type hints throughout
   - Strict JSON validation

3. **Testability**
   - Pure functions where possible
   - Dependency injection (get_llm_client, get_session_store)
   - Mocking at module boundaries

4. **Error Handling**
   - LLM parse failures → Automatic repair
   - Missing data → Clear error messages
   - Invalid input → HTTP 400 with details
   - Internal errors → HTTP 500 with safe message

---

## ✅ Requirements Checklist

### Functional Requirements
- ✅ Single car eligibility queries
- ✅ Fleet eligibility queries
- ✅ Policy-only queries
- ✅ Multi-car disambiguation
- ✅ Multi-zone disambiguation
- ✅ Missing field handling
- ✅ Real OpenAI API integration
- ✅ Deterministic decision logic
- ✅ Mock car and policy services

### Technical Requirements
- ✅ Python with FastAPI
- ✅ LangGraph for orchestration
- ✅ Pydantic for schemas
- ✅ OpenAI Python SDK
- ✅ gpt-4o-mini as default model
- ✅ JSON schema validation
- ✅ Retry/repair on parse failure
- ✅ In-memory session state
- ✅ POST /chat endpoint
- ✅ POST /chat/answer endpoint
- ✅ GET /health endpoint

### Deliverables
- ✅ Complete source code
- ✅ requirements.txt
- ✅ README.md with setup instructions
- ✅ 3+ curl examples
- ✅ Unit tests
- ✅ Quick start script
- ✅ API test script
- ✅ Workflow documentation

---

## 📞 Support & Next Steps

### To Run the Service
```bash
./start.sh
```

### To Test the API
```bash
./test_api.sh
```

### To Run Tests
```bash
pytest tests/ -v
```

### To Visualize Workflow
```bash
python workflow_diagram.py
```

### To Deploy to Production
1. Replace mock services with real APIs
2. Add authentication (JWT/API keys)
3. Use Redis/PostgreSQL for session state
4. Add structured logging and monitoring
5. Configure reverse proxy (nginx)
6. Set up HTTPS with Let's Encrypt
7. Deploy with Docker/Kubernetes
8. Add rate limiting
9. Set up CI/CD pipeline

---

## 🎉 Summary

This is a **complete, production-ready PoC** that demonstrates:
- ✅ Sophisticated LLM orchestration with LangGraph
- ✅ Deterministic business logic (not LLM-based decisions)
- ✅ Robust error handling and retry logic
- ✅ Clean architecture with clear separation of concerns
- ✅ Comprehensive testing strategy
- ✅ Excellent developer experience (scripts, docs, examples)

The service is ready to run and can be extended to a production system by replacing mock services and adding infrastructure components.
