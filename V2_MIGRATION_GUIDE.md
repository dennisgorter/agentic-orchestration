# Version 2.0.0 Migration Guide

## What's New in v2.0.0

### 🎯 Two-Agent Architecture
- **Intent Agent**: Routes requests to appropriate domain agents
- **Pollution Agent**: Wraps existing LangGraph workflow (domain expert)
- **Multi-domain ready**: Add new domains by registering agents

### 📡 API Versioning
- **`/v1/chat`**: Backward compatible endpoint (direct to pollution agent)
- **`/v2/chat`**: New multi-agent router (via intent agent)
- **`/chat`**: Legacy endpoint (deprecated, redirects to v1)

### 🔄 Stateless Design
- Client manages conversation history (no server-side sessions)
- Perfect horizontal scaling
- No Redis or session storage needed

### 🏗️ New Folder Structure
```
app/
├── api/                  # HTTP layer
│   ├── main.py          # FastAPI with v1/v2 endpoints
│   └── models.py        # Request/response schemas
├── core/
│   ├── agents/          # Domain agents
│   │   ├── base.py      # BaseAgent interface
│   │   ├── intent/      # Intent routing agent
│   │   └── pollution/   # Pollution domain agent
│   └── shared/          # Shared utilities
│       ├── messaging.py # AgentMessage protocol
│       ├── models.py    # Pydantic models
│       └── llm.py       # OpenAI client
└── infrastructure/      # Logging, tracing
```

---

## Quick Start

### Start v2 API
```bash
export OPENAI_API_KEY="your-key"
./start_v2.sh
```

The API will run on http://localhost:8001

### Test v2 Endpoint
```bash
curl -X POST http://localhost:8001/v2/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Is my car AB-123-CD allowed in Amsterdam?",
    "conversation_history": []
  }'
```

### Health Check
```bash
curl http://localhost:8001/health
# Returns: {"status":"healthy","version":"2.0.0","agents":["pollution_agent"]}
```

---

## API Changes

### V1 Endpoint (Backward Compatible)
```bash
POST /v1/chat
{
  "message": "Is my car allowed?",
  "conversation_history": [...]  # optional
}
```

**Response:**
```json
{
  "reply": "Yes, your diesel Euro 6 car AB-123-CD is allowed...",
  "trace_id": "abc-123",
  "correlation_id": "xyz-789"
}
```

### V2 Endpoint (New Router)
```bash
POST /v2/chat
{
  "message": "Is my car allowed?",
  "conversation_history": [...]  # optional
}
```

**Response:** Same format as v1

**Key Difference:**
- V1: Routes directly to pollution agent
- V2: Uses intent agent for routing (multi-domain ready)

---

## Migration Steps

### Option 1: Keep Using V1 (No Changes Required)
Your existing code continues to work with `/v1/chat`. No migration needed.

### Option 2: Migrate to V2 (Recommended)
1. Update your API endpoint from `/chat` or `/v1/chat` to `/v2/chat`
2. No other changes required (request/response format identical)

### Option 3: Gradual Migration (Canary Deployment)
```javascript
const API_VERSION = Math.random() < 0.1 ? "v2" : "v1";  // 10% on v2
const response = await fetch(`/${API_VERSION}/chat`, {...});
```

---

## For Developers

### Adding a New Domain Agent

**Step 1: Create Agent Class**
```python
# app/core/agents/parking/agent.py
from app.core.agents.base import BaseAgent
from app.core.shared.messaging import AgentMessage

class ParkingAgent(BaseAgent):
    name = "parking_agent"
    
    async def handle(self, message: AgentMessage) -> AgentMessage:
        # Your domain logic here
        answer = process_parking_query(message.payload["message"])
        return message.create_reply(payload={"answer": answer})
```

**Step 2: Register Agent**
```python
# app/api/main.py
from app.core.agents.parking.agent import ParkingAgent

parking_agent = ParkingAgent()
intent_agent.register_agent(parking_agent)
```

**Step 3: Update Intent Classification**
```python
# app/core/agents/intent/agent.py
def _classify_intent(self, message: str) -> str:
    if "park" in message.lower():
        return "parking_agent"
    # ... existing logic
```

That's it! Your new domain is live.

---

## Testing

### Run Unit Tests
```bash
pytest tests/unit/ -v
```

**Expected Output:**
```
tests/unit/test_intent_agent.py::test_agent_registration PASSED
tests/unit/test_intent_agent.py::test_routing PASSED
tests/unit/test_pollution_agent.py::test_handle PASSED
...
12 passed in 0.5s
```

### Test API Manually
```bash
# Health check
curl http://localhost:8001/health | jq

# V2 chat
curl -X POST http://localhost:8001/v2/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' | jq

# V1 chat (backward compatible)
curl -X POST http://localhost:8001/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' | jq
```

---

## Architecture Comparison

### V1 (Single Agent)
```
Client → FastAPI → Pollution Agent (LangGraph) → Response
```

### V2 (Multi-Agent)
```
Client → FastAPI → Intent Agent → Pollution Agent → Response
                       ↓
                   (routes by intent)
```

---

## Performance Impact

- **Latency**: +5-10ms for intent routing (negligible)
- **Throughput**: No change (stateless design)
- **Scalability**: Improved (no session storage)
- **Memory**: Reduced (no session state)

---

## FAQ

**Q: Do I need to migrate immediately?**  
A: No. V1 endpoints remain fully supported. Migrate when convenient.

**Q: What breaks if I use v2?**  
A: Nothing. Request/response format is identical.

**Q: Why two agents if only one domain?**  
A: Prepares for multi-domain expansion. Minimal overhead now, easy to extend later.

**Q: What happened to session management?**  
A: Removed. Client manages conversation history (like ChatGPT). This enables perfect horizontal scaling.

**Q: Can I run v1 and v2 simultaneously?**  
A: Yes! Both endpoints work on the same server.

**Q: How do I debug issues?**  
A: Check `trace_id` in response. Look for matching log entries.

---

## Troubleshooting

### Issue: "Agent not found"
**Cause:** Agent not registered with IntentAgent  
**Fix:** Check `app/api/main.py` for `intent_agent.register_agent()` call

### Issue: "OPENAI_API_KEY must be set"
**Cause:** Environment variable not set  
**Fix:** `export OPENAI_API_KEY="your-key"` before starting server

### Issue: "Session ID required"
**Cause:** Old code calling new agent directly  
**Fix:** Use API endpoints, not direct agent calls

---

## Rollback Plan

If issues arise:

### Immediate Rollback (Frontend)
```javascript
const API_VERSION = "v1";  // Switch back to v1
```

### Full Rollback (Server)
```bash
git checkout v1.0.0
./start.sh  # Original single-agent version
```

---

## Next Steps

1. ✅ **v2.0.0 Deployed** - Two-agent architecture
2. 🔄 **Frontend Migration** - Update to use v2 endpoints
3. 📊 **Performance Monitoring** - Compare v1 vs v2 metrics
4. 🚀 **Multi-Domain Expansion** - Add parking, complaints, etc.

---

## Support

- **Documentation**: [PHASE1_REFACTOR_PLAN.md](PHASE1_REFACTOR_PLAN.md)
- **Architecture**: [ARCHITECTURE_ASSESSMENT.md](ARCHITECTURE_ASSESSMENT.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Issues**: GitHub Issues

**Version:** 2.0.0  
**Date:** January 4, 2026  
**Status:** Production Ready
