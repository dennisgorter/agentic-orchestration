"""FastAPI application with versioned endpoints (v1 and v2).

Version 2.0.0 - Two-agent architecture
- V1 endpoints: Backward compatible (direct to pollution agent)
- V2 endpoints: New multi-agent router (via intent agent)
"""

import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.api.models import (
    ChatRequestV1,
    ChatRequestV2,
    ChatResponse,
    HealthResponse
)
from app.core.agents.intent.agent import IntentAgent
from app.core.agents.pollution.agent import PollutionAgent
from app.core.shared.messaging import AgentMessage
from app.infrastructure.logging_config import setup_logging, set_trace_id, get_trace_id, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize agents
pollution_agent = PollutionAgent()
intent_agent = IntentAgent()
intent_agent.register_agent(pollution_agent)

logger.info("Agent system initialized:")
logger.info(f"  - {pollution_agent.name}: Domain expert for pollution zones")
logger.info(f"  - {intent_agent.name}: Router with {len(intent_agent.agents)} registered agents")

# Create FastAPI app
app = FastAPI(
    title="Agent Orchestrator",
    description="Car pollution zone eligibility service - Multi-agent architecture",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    """Add trace_id to all requests for traceability."""
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)
    
    logger.info(f"[{trace_id}] Incoming: {request.method} {request.url.path}")
    
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    
    logger.info(f"[{trace_id}] Completed: {response.status_code}")
    
    return response


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns service status, version, and registered agents.
    """
    logger.debug("Health check requested")
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        agents=intent_agent.list_agents()
    )


@app.post("/v1/chat", response_model=ChatResponse, tags=["v1"])
async def chat_v1(request: ChatRequestV1):
    """
    V1 Chat endpoint (backward compatible).
    
    Routes directly to pollution agent without intent classification.
    This maintains compatibility with existing clients.
    
    Features:
    - Direct routing to pollution agent
    - Stateless (client provides conversation history)
    - No session management
    
    Args:
        request: ChatRequestV1 with message and optional conversation history
        
    Returns:
        ChatResponse with reply, trace_id, and correlation_id
    """
    trace_id = get_trace_id() or str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    
    logger.info(f"[{trace_id}] V1 Chat: {request.message[:80]}...")
    
    try:
        # Create message for pollution agent (bypass intent router)
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
        
        # Route directly to pollution agent
        response = await pollution_agent.handle(message)
        
        logger.info(f"[{trace_id}] V1 Response generated")
        
        return ChatResponse(
            reply=response.payload["answer"],
            trace_id=trace_id,
            correlation_id=correlation_id
        )
        
    except Exception as e:
        logger.error(f"[{trace_id}] V1 Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.post("/v2/chat", response_model=ChatResponse, tags=["v2"])
async def chat_v2(request: ChatRequestV2):
    """
    V2 Chat endpoint (new multi-agent router).
    
    Uses intent agent for routing, enabling multi-domain expansion.
    Currently routes to pollution agent, but prepared for additional domains.
    
    Features:
    - Intent classification and routing
    - Multi-domain ready
    - Stateless (client provides conversation history)
    - Agent registry system
    
    Args:
        request: ChatRequestV2 with message and optional conversation history
        
    Returns:
        ChatResponse with reply, trace_id, and correlation_id
    """
    trace_id = get_trace_id() or str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    
    logger.info(f"[{trace_id}] V2 Chat: {request.message[:80]}...")
    
    try:
        # Route via intent agent (multi-domain ready)
        answer = await intent_agent.route(
            request_payload={
                "message": request.message,
                "conversation_history": request.conversation_history or []
            },
            trace_id=trace_id,
            correlation_id=correlation_id
        )
        
        logger.info(f"[{trace_id}] V2 Response generated")
        
        return ChatResponse(
            reply=answer,
            trace_id=trace_id,
            correlation_id=correlation_id
        )
        
    except Exception as e:
        logger.error(f"[{trace_id}] V2 Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


# For backward compatibility during transition
@app.post("/chat", response_model=ChatResponse, tags=["Legacy"])
async def chat_legacy(request: ChatRequestV1):
    """
    Legacy chat endpoint (redirects to V1).
    
    Maintained for backward compatibility during migration.
    Will be deprecated in future releases.
    
    **Deprecated**: Use /v1/chat or /v2/chat instead.
    """
    logger.warning("Legacy /chat endpoint used - recommend migrating to /v1/chat or /v2/chat")
    return await chat_v1(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
