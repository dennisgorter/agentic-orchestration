"""FastAPI application for Agent Orchestrator service."""
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.models import ChatRequest, ChatAnswerRequest, ChatResponse, AgentState
from app.state import get_session_store
from app.graph import get_graph
from app.logging_config import setup_logging, set_trace_id, get_trace_id, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Agent Orchestrator",
    description="Car pollution zone eligibility service",
    version="1.0.0"
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
    
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    
    logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}")
    
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "healthy", "service": "agent-orchestrator"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint. Process user message and return response.
    
    May return a disambiguation question if multiple cars/zones match.
    """
    trace_id = get_trace_id()
    logger.info(f"Chat request - session: {request.session_id}, message: {request.message[:50]}...")
    
    session_store = get_session_store()
    graph = get_graph()
    
    # Get or create session state
    state = session_store.create_or_get(request.session_id, request.message)
    state.trace_id = trace_id or ""
    
    logger.info(f"[{request.session_id}] BEFORE GRAPH - car_identifier: {state.car_identifier}, "
               f"selected_car: {state.selected_car.plate if state.selected_car else None}")
    
    # Convert to dict for LangGraph
    state_dict = state.model_dump()
    
    try:
        logger.info(f"Starting graph execution - session: {request.session_id}")
        # Run graph
        result = graph.invoke(state_dict)
        
        # Convert back to AgentState
        result_state = AgentState(**result)
        
        logger.info(f"[{request.session_id}] AFTER GRAPH - car_identifier: {result_state.car_identifier}, "
                   f"selected_car: {result_state.selected_car.plate if result_state.selected_car else None}")
        
        # Update session store
        session_store.set(request.session_id, result_state)
        
        logger.info(f"Graph completed - session: {request.session_id}, pending_question: {result_state.pending_question}")
        
        # Build response
        response = ChatResponse(
            session_id=request.session_id,
            reply=result_state.reply,
            pending_question=result_state.pending_question,
            options=result_state.disambiguation_options if result_state.pending_question else None,
            state=None,  # Optionally include for debugging: result_state.model_dump()
            trace_id=trace_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request - session: {request.session_id}, error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.post("/chat/answer", response_model=ChatResponse)
async def chat_answer(request: ChatAnswerRequest):
    """
    Handle user's answer to a disambiguation question.
    
    User selects from previously presented options.
    """
    trace_id = get_trace_id()
    logger.info(f"Disambiguation answer - session: {request.session_id}, selection: {request.selection_index}")
    
    session_store = get_session_store()
    graph = get_graph()
    
    # Get existing session
    state = session_store.get(request.session_id)
    
    if not state:
        logger.warning(f"Session not found: {request.session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    logger.info(f"[{request.session_id}] DISAMBIGUATION ANSWER - car_identifier: {state.car_identifier}, "
               f"selected_car: {state.selected_car.plate if state.selected_car else None}")
    
    if not state.pending_question:
        logger.warning(f"No pending question for session: {request.session_id}")
        raise HTTPException(status_code=400, detail="No pending question for this session")
    
    # Validate selection
    if request.selection_index < 0 or request.selection_index >= len(state.disambiguation_options):
        logger.warning(f"Invalid selection index: {request.selection_index} for session: {request.session_id}")
        raise HTTPException(status_code=400, detail="Invalid selection index")
    
    # Apply selection
    selected_option = state.disambiguation_options[request.selection_index]
    logger.info(f"Selected option: {selected_option.get('label')} for session: {request.session_id}")
    
    if state.pending_type == "car":
        # Find and set selected car
        matching_cars = [c for c in state.cars if c.car_id == selected_option.get("car_id")]
        if matching_cars:
            state.selected_car = matching_cars[0]
        else:
            raise HTTPException(status_code=500, detail="Selected car not found in state")
    elif state.pending_type == "zone":
        # Find and set selected zone
        matching_zones = [z for z in state.zone_candidates if z.zone_id == selected_option.get("zone_id")]
        if matching_zones:
            state.selected_zone = matching_zones[0]
        else:
            raise HTTPException(status_code=500, detail="Selected zone not found in state")
    
    # Clear pending state
    # Determine next step based on what was disambiguated (before clearing pending_type)
    disambiguated_type = state.pending_type
    
    # Clear pending state
    state.pending_question = False
    state.pending_type = None
    state.disambiguation_options = []
    
    # Set next step based on what was just disambiguated
    if disambiguated_type == "car":
        # After car disambiguation, we need to resolve zone
        state.next_step = "resolve_zone"
    elif disambiguated_type == "zone":
        # After zone disambiguation, fetch policy
        state.next_step = "fetch_policy"
    else:
        # Fallback
        if state.selected_zone and not state.policy:
            state.next_step = "fetch_policy"
        elif state.selected_car and not state.selected_zone:
            state.next_step = "resolve_zone"
        else:
            state.next_step = "decide"
    
    # Convert to dict for LangGraph
    state_dict = state.model_dump()
    
    try:
        # Continue from the appropriate node
        # We need to manually invoke the next steps since we're resuming mid-flow
        logger.info(f"Continuing from: {state.next_step} for session: {request.session_id}")
        
        if state.next_step == "resolve_zone":
            from app.graph import resolve_zone_node, fetch_policy_node, decide_node, explain_node
            
            state_result = resolve_zone_node(AgentState(**state_dict))
            state_dict = state_result.model_dump()
            
            # If zone disambiguation is needed, stop here
            if state_result.pending_question:
                logger.info(f"Additional disambiguation needed for session: {request.session_id}")
                session_store.set(request.session_id, state_result)
                return ChatResponse(
                    session_id=request.session_id,
                    reply=state_result.reply,
                    pending_question=state_result.pending_question,
                    options=state_result.disambiguation_options,
                    state=None,
                    trace_id=trace_id
                )
            
            # Continue to fetch_policy
            if state_result.next_step == "fetch_policy":
                state_result = fetch_policy_node(AgentState(**state_dict))
                state_dict = state_result.model_dump()
            
            if state_result.next_step == "decide":
                state_result = decide_node(AgentState(**state_dict))
                state_dict = state_result.model_dump()
            
            if state_result.next_step == "explain":
                state_result = explain_node(AgentState(**state_dict))
                state_dict = state_result.model_dump()
            
            result_state = state_result
        elif state.next_step == "fetch_policy":
            from app.graph import fetch_policy_node, decide_node, explain_node
            
            state_result = fetch_policy_node(AgentState(**state_dict))
            state_dict = state_result.model_dump()
            
            if state_result.next_step == "decide":
                state_result = decide_node(AgentState(**state_dict))
                state_dict = state_result.model_dump()
            
            if state_result.next_step == "explain":
                state_result = explain_node(AgentState(**state_dict))
                state_dict = state_result.model_dump()
            
            result_state = state_result
        elif state.next_step == "decide":
            from app.graph import decide_node, explain_node
            
            state_result = decide_node(AgentState(**state_dict))
            state_dict = state_result.model_dump()
            
            if state_result.next_step == "explain":
                state_result = explain_node(AgentState(**state_dict))
                state_dict = state_result.model_dump()
            
            result_state = state_result
        else:
            result_state = AgentState(**state_dict)
        
        # Update session store
        session_store.set(request.session_id, result_state)
        
        logger.info(f"Disambiguation resolved - session: {request.session_id}, final reply length: {len(result_state.reply)}")
        
        # Build response
        response = ChatResponse(
            session_id=request.session_id,
            reply=result_state.reply,
            pending_question=result_state.pending_question,
            options=result_state.disambiguation_options if result_state.pending_question else None,
            state=None,
            trace_id=trace_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing disambiguation answer - session: {request.session_id}, error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing answer: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
