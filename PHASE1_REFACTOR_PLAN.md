# Phase 1 Refactor: Two-Agent Architecture

**Date:** January 4, 2026  
**Goal:** Prepare system for multi-domain expansion while keeping current functionality  
**Effort:** 1-2 weeks  
**Risk:** Low (minimal code changes)

---

## Executive Summary

Refactor current monolithic agent into **two-agent architecture**:
1. **Intent Agent** - Router/orchestrator (ready for future domains)
2. **Pollution Agent** - Domain expert (current functionality)

**Key Decisions:**
- ✅ Stateless service (React client manages conversation state)
- ✅ API versioning (/v1/chat backward compatible, /v2/chat new router)
- ✅ Agent messaging with trace_id + correlation_id
- ✅ Folder structure for multi-domain readiness

---

## Current vs. Target Architecture

### Current (Monolithic)
```
FastAPI /chat → Pollution Zone Agent (LangGraph) → Response
                  ↓
            Intent extraction + tools + rules + explain
```

### Target (Two-Agent, Multi-Domain Ready)
```
FastAPI /v2/chat → Intent Agent (Router) → Pollution Agent → Response
                         ↓                        ↓
                   Classify intent          LangGraph workflow
                   Create AgentMessage      (current logic)
                   Route to domain
```

---

## Implementation Steps

### Step 1: Folder Structure (1 hour)

```bash
# Create new structure
mkdir -p app/api/v1 app/api/middleware
mkdir -p app/core/agents/intent app/core/agents/pollution
mkdir -p app/core/shared
mkdir -p tests/unit tests/integration

# Move existing files
mv app/graph.py app/core/agents/pollution/graph.py
mv app/tools.py app/core/agents/pollution/tools.py
mv app/rules.py app/core/agents/pollution/rules.py
mv app/models.py app/core/shared/models.py
mv app/llm.py app/core/shared/llm.py
```

**Result:**
```
app/
├── api/
│   ├── __init__.py
│   ├── main.py                   # NEW: FastAPI with /v1 and /v2
│   ├── v1/
│   │   └── chat.py               # Backward compatible endpoint
│   └── middleware/
│       ├── tracing.py            # trace_id + correlation_id
│       └── error_handling.py
│
├── core/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py               # NEW: BaseAgent interface
│   │   ├── intent/
│   │   │   ├── __init__.py
│   │   │   └── agent.py          # NEW: IntentAgent (router)
│   │   └── pollution/
│   │       ├── __init__.py
│   │       ├── agent.py          # NEW: PollutionAgent wrapper
│   │       ├── graph.py          # MOVED from app/graph.py
│   │       ├── tools.py          # MOVED from app/tools.py
│   │       └── rules.py          # MOVED from app/rules.py
│   └── shared/
│       ├── __init__.py
│       ├── messaging.py          # NEW: AgentMessage
│       ├── llm.py                # MOVED from app/llm.py
│       └── models.py             # MOVED from app/models.py
│
├── infrastructure/
│   ├── __init__.py
│   ├── logging_config.py         # EXISTING
│   └── trace_store.py            # EXISTING
│
└── tests/
    ├── unit/
    │   ├── test_intent_agent.py
    │   └── test_pollution_agent.py
    └── integration/
        └── test_agent_communication.py
```

### Step 2: Create Base Classes (2 hours)

**File:** `app/core/agents/base.py`
```python
from abc import ABC, abstractmethod
from typing import Optional

class BaseAgent(ABC):
    """Base class for all domain agents."""
    
    name: str  # e.g., "pollution_agent"
    
    @abstractmethod
    async def handle(self, message: 'AgentMessage') -> 'AgentMessage':
        """Handle an agent message and return response."""
        pass
```

**File:** `app/core/shared/messaging.py`
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class AgentMessage(BaseModel):
    """Message passed between agents."""
    trace_id: str              # Unique per user request
    correlation_id: str        # Links related traces (batch operations)
    sender: str                # "intent_agent", "pollution_agent"
    receiver: str              # Target agent name
    payload: dict              # Request data
    context: dict = {}         # Shared context across agents
    conversation_history: List[dict] = []  # From client (stateless)
    timestamp: datetime
    
    class Config:
        arbitrary_types_allowed = True
```

### Step 3: Create Pollution Agent Wrapper (1 hour)

**File:** `app/core/agents/pollution/agent.py`
```python
from core.agents.base import BaseAgent
from core.shared.messaging import AgentMessage
from .graph import get_graph  # Existing LangGraph
from datetime import datetime

class PollutionAgent(BaseAgent):
    """Domain expert for pollution zone eligibility."""
    
    name = "pollution_agent"
    
    def __init__(self, cache=None):
        self.graph = get_graph()  # Existing LangGraph workflow
        self.cache = cache  # Optional: for future policy caching
    
    async def handle(self, message: AgentMessage) -> AgentMessage:
        """Process pollution zone query using existing LangGraph."""
        
        # Extract from message
        query = message.payload["message"]
        conversation_history = message.conversation_history
        
        # Use existing LangGraph workflow (NO CHANGES to graph logic)
        result = await self.graph.ainvoke({
            "message": query,
            "conversation_history": conversation_history,
            "trace_id": message.trace_id
        })
        
        # Return response message
        return AgentMessage(
            trace_id=message.trace_id,
            correlation_id=message.correlation_id,
            sender=self.name,
            receiver=message.sender,
            payload={"answer": result["reply"]},
            context=message.context,
            conversation_history=conversation_history,
            timestamp=datetime.now()
        )
```

**File:** `app/core/agents/pollution/__init__.py`
```python
from .agent import PollutionAgent

__all__ = ['PollutionAgent']
```

### Step 4: Create Intent Agent (Router) (2 hours)

**File:** `app/core/agents/intent/agent.py`
```python
from core.agents.base import BaseAgent
from core.shared.messaging import AgentMessage
from datetime import datetime
from typing import Dict

class IntentAgent(BaseAgent):
    """Routes requests to domain agents based on intent."""
    
    name = "intent_agent"
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent):
        """Register a domain agent."""
        self.agents[agent.name] = agent
        print(f"Registered agent: {agent.name}")
    
    async def route(
        self, 
        request_payload: dict, 
        trace_id: str, 
        correlation_id: str
    ) -> str:
        """Route request to appropriate domain agent."""
        
        # 1. Classify intent (simple for now: only 1 domain)
        intent = self._classify_intent(request_payload["message"])
        
        # 2. Create agent message
        message = AgentMessage(
            trace_id=trace_id,
            correlation_id=correlation_id,
            sender=self.name,
            receiver=intent,
            payload=request_payload,
            conversation_history=request_payload.get("conversation_history", []),
            context={},
            timestamp=datetime.now()
        )
        
        # 3. Route to agent (synchronous call)
        agent = self.agents.get(intent)
        if not agent:
            return f"Sorry, I don't know how to help with that yet."
        
        response = await agent.handle(message)
        return response.payload["answer"]
    
    def _classify_intent(self, message: str) -> str:
        """Classify intent. Simple for now - single domain."""
        # For single domain, always return pollution_agent
        # TODO: When 3+ domains added, use LLM for classification:
        #   - "Which domain: pollution_check, parking_info, complaint?"
        #   - Parse LLM response
        #   - Return agent name
        return "pollution_agent"
```

### Step 5: Update API with Versioning (3 hours)

**File:** `app/api/models.py`
```python
from pydantic import BaseModel
from typing import Optional, List, Dict

class ChatRequestV1(BaseModel):
    """V1 API request (backward compatible)."""
    message: str
    conversation_history: Optional[List[Dict]] = None

class ChatRequestV2(BaseModel):
    """V2 API request (new router)."""
    message: str
    conversation_history: Optional[List[Dict]] = None
    # Future: domain_hint, user_id, etc.

class ChatResponse(BaseModel):
    """API response."""
    reply: str
    trace_id: str
    correlation_id: str
    # Future: suggested_actions, sources, etc.
```

**File:** `app/api/main.py`
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.agents.intent.agent import IntentAgent
from core.agents.pollution.agent import PollutionAgent
from infrastructure.logging_config import setup_logging, get_logger
from .models import ChatRequestV1, ChatRequestV2, ChatResponse
import uuid
from datetime import datetime

# Setup
setup_logging()
logger = get_logger(__name__)
app = FastAPI(title="Agent Orchestrator", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
pollution_agent = PollutionAgent()
intent_agent = IntentAgent()
intent_agent.register_agent(pollution_agent)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "agents": list(intent_agent.agents.keys())
    }

@app.post("/v1/chat", response_model=ChatResponse, tags=["v1"])
async def chat_v1(request: ChatRequestV1):
    """
    V1 endpoint (backward compatible).
    Routes directly to pollution agent without intent classification.
    """
    trace_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    
    logger.info(f"[{trace_id}] V1 Chat request: {request.message[:50]}...")
    
    try:
        # Direct to pollution agent (bypass intent routing)
        message = AgentMessage(
            trace_id=trace_id,
            correlation_id=correlation_id,
            sender="api_v1",
            receiver="pollution_agent",
            payload={"message": request.message},
            conversation_history=request.conversation_history or [],
            context={},
            timestamp=datetime.now()
        )
        
        response = await pollution_agent.handle(message)
        
        return ChatResponse(
            reply=response.payload["answer"],
            trace_id=trace_id,
            correlation_id=correlation_id
        )
        
    except Exception as e:
        logger.error(f"[{trace_id}] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v2/chat", response_model=ChatResponse, tags=["v2"])
async def chat_v2(request: ChatRequestV2):
    """
    V2 endpoint (new multi-agent router).
    Uses intent agent for routing (future-ready for multiple domains).
    """
    trace_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    
    logger.info(f"[{trace_id}] V2 Chat request: {request.message[:50]}...")
    
    try:
        answer = await intent_agent.route(
            request_payload={
                "message": request.message,
                "conversation_history": request.conversation_history or []
            },
            trace_id=trace_id,
            correlation_id=correlation_id
        )
        
        return ChatResponse(
            reply=answer,
            trace_id=trace_id,
            correlation_id=correlation_id
        )
        
    except Exception as e:
        logger.error(f"[{trace_id}] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 6: Update Frontend for Stateless Design (2 hours)

**File:** `frontend/src/App.jsx` (key changes)
```javascript
const [messages, setMessages] = useState([]);
const [sessionId] = useState(() => uuidv4());  // Still generate for trace correlation

const API_VERSION = "v2";  // Switch between v1 and v2

const handleSend = async (userMessage) => {
  // Add user message to UI
  const newMessages = [...messages, { role: "user", content: userMessage }];
  setMessages(newMessages);
  
  try {
    const response = await fetch(`/${API_VERSION}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userMessage,
        conversation_history: newMessages.slice(-5)  // Last 5 for context
      })
    });
    
    const data = await response.json();
    
    // Add assistant response
    setMessages([...newMessages, {
      role: "assistant",
      content: data.reply,
      trace_id: data.trace_id,
      correlation_id: data.correlation_id
    }]);
    
  } catch (error) {
    console.error("Chat error:", error);
    // Handle error
  }
};
```

### Step 7: Update Tests (2 hours)

**File:** `tests/unit/test_intent_agent.py`
```python
import pytest
from app.core.agents.intent.agent import IntentAgent
from app.core.agents.pollution.agent import PollutionAgent
from app.core.shared.messaging import AgentMessage
from datetime import datetime

@pytest.mark.asyncio
async def test_intent_agent_routes_to_pollution():
    """Test that intent agent routes pollution queries correctly."""
    
    # Setup
    pollution_agent = PollutionAgent()
    intent_agent = IntentAgent()
    intent_agent.register_agent(pollution_agent)
    
    # Act
    result = await intent_agent.route(
        request_payload={"message": "Is my car allowed in Amsterdam?"},
        trace_id="test-trace-123",
        correlation_id="test-corr-123"
    )
    
    # Assert
    assert isinstance(result, str)
    assert len(result) > 0
```

**File:** `tests/integration/test_agent_communication.py`
```python
import pytest
from app.core.agents.intent.agent import IntentAgent
from app.core.agents.pollution.agent import PollutionAgent
from app.core.shared.messaging import AgentMessage
from datetime import datetime

@pytest.mark.asyncio
async def test_full_agent_message_flow():
    """Test full message flow from intent agent to pollution agent."""
    
    # Setup
    pollution_agent = PollutionAgent()
    intent_agent = IntentAgent()
    intent_agent.register_agent(pollution_agent)
    
    # Create message
    message = AgentMessage(
        trace_id="test-123",
        correlation_id="corr-123",
        sender="test",
        receiver="intent_agent",
        payload={"message": "Is diesel allowed in Rotterdam?"},
        conversation_history=[],
        context={},
        timestamp=datetime.now()
    )
    
    # Act
    result = await intent_agent.route(
        request_payload=message.payload,
        trace_id=message.trace_id,
        correlation_id=message.correlation_id
    )
    
    # Assert
    assert "rotterdam" in result.lower() or "diesel" in result.lower()
```

---

## Testing Checklist

### Unit Tests
- [ ] `test_intent_agent.py` - Intent classification
- [ ] `test_intent_agent.py` - Agent registration
- [ ] `test_pollution_agent.py` - Message handling
- [ ] `test_pollution_agent.py` - LangGraph integration

### Integration Tests
- [ ] `test_agent_communication.py` - Full message flow
- [ ] `test_api_v1.py` - V1 endpoint (backward compatibility)
- [ ] `test_api_v2.py` - V2 endpoint (intent routing)

### Manual Tests
- [ ] V1 endpoint works with existing frontend
- [ ] V2 endpoint works with updated frontend
- [ ] Conversation history flows correctly
- [ ] Trace IDs appear in logs
- [ ] Correlation IDs link related requests

---

## Deployment Strategy

### Phase 1a: Deploy V1 (Backward Compatible)
1. Deploy new code with /v1/chat endpoint
2. Frontend continues using V1
3. Verify no regression
4. Monitor for 1 week

### Phase 1b: Enable V2 (Canary)
1. Add feature flag in frontend: `USE_V2_API=false`
2. Enable for 10% of users
3. Compare metrics (latency, errors, user satisfaction)
4. Gradually increase to 100%

### Phase 1c: Deprecate V1 (Optional)
1. Announce V1 deprecation (3 months notice)
2. Monitor V1 usage
3. When usage < 1%, remove V1 endpoint

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Zero Regression** | 0 broken tests | Run full test suite |
| **Performance** | <5% latency increase | Compare v1 vs v2 response times |
| **Code Coverage** | >80% | pytest --cov |
| **Agent Communication** | 100% success rate | Integration tests pass |
| **API Versioning** | Both endpoints work | Manual testing |

---

## Rollback Plan

If issues arise:

1. **Immediate**: Switch frontend back to V1
   ```javascript
   const API_VERSION = "v1";  // Rollback
   ```

2. **If V1 broken**: Revert entire deployment
   ```bash
   git revert HEAD
   ```

3. **Data loss**: None (stateless design)

---

## Future Enhancements (Post-Phase 1)

### When adding 3rd domain:
```python
# app/core/agents/parking/agent.py
class ParkingAgent(BaseAgent):
    name = "parking_agent"
    # ... domain-specific logic

# Register in main.py
parking_agent = ParkingAgent()
intent_agent.register_agent(parking_agent)

# Update intent classification
def _classify_intent(self, message: str) -> str:
    # Now use LLM for multi-domain routing
    prompt = f"""Classify: {message}
    Domains: pollution_check, parking_info, complaint
    Return: agent_name"""
    # ... LLM call
```

---

## Questions & Answers

**Q: Why refactor now if only 1 domain?**  
A: Minimal effort now vs. major refactor later. Sets pattern for future domains.

**Q: Why two agents instead of keeping monolith?**  
A: Intent agent becomes smarter as domains added. Pollution agent stays focused.

**Q: What if V2 is slower?**  
A: Extra routing hop adds ~10ms (negligible). Trade-off for clean architecture.

**Q: Can we skip V1 and only do V2?**  
A: Yes, but API versioning is best practice for production services.

**Q: Why stateless design?**  
A: Perfect horizontal scaling, simpler infrastructure, zero session complexity.

---

## Contact & Support

**Questions:** Consult with development team  
**Status Updates:** Daily standups during refactor  
**Blockers:** Escalate immediately  

**Document Version:** 1.0  
**Last Updated:** January 4, 2026
