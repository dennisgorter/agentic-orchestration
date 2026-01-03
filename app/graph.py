"""LangGraph workflow for agent orchestration."""
from typing import Literal
from langgraph.graph import StateGraph, END
from app.models import AgentState, FleetDecision
from app.llm import get_llm_client
from app.tools import list_user_cars, resolve_zone, get_policy, find_car_by_identifier
from app.rules import decide_eligibility
from app.logging_config import get_logger

logger = get_logger(__name__)


# ========== Graph Node Functions ==========

def extract_intent_node(state: AgentState) -> AgentState:
    """Extract intent and slots from user message using LLM."""
    logger.info(f"[{state.session_id}] extract_intent_node - message: {state.message[:50]}...")
    
    llm = get_llm_client()
    intent_data = llm.call_extract_intent_slots(state.message)
    
    state.intent = intent_data.intent
    state.car_identifier = intent_data.car_identifier
    state.city = intent_data.city
    state.zone_phrase = intent_data.zone_phrase
    
    logger.info(f"[{state.session_id}] Intent extracted: {state.intent}, city: {state.city}, car: {state.car_identifier}")
    
    return state


def resolve_zone_node(state: AgentState) -> AgentState:
    """Resolve city and zone phrase to specific zone(s)."""
    if not state.city:
        # No city specified - set error reply
        state.reply = "I need to know which city you're asking about. Could you specify the city?"
        state.pending_question = False
        state.next_step = "end"
        return state
    
    candidates = resolve_zone(state.city, state.zone_phrase)
    
    if not candidates:
        state.reply = f"I couldn't find any pollution zones in {state.city}. Please check the city name."
        state.pending_question = False
        state.next_step = "end"
        return state
    
    if len(candidates) == 1:
        # Single match - proceed
        state.selected_zone = candidates[0]
        state.zone_candidates = candidates
        state.next_step = "fetch_policy"
        logger.info(f"[{state.session_id}] Zone resolved: {candidates[0].zone_name}")
        return state
    
    # Multiple matches - ask for disambiguation
    logger.info(f"[{state.session_id}] Zone disambiguation needed - {len(candidates)} candidates")
    state.zone_candidates = candidates
    state.pending_question = True
    state.pending_type = "zone"
    
    options = [
        {
            "index": i,
            "label": f"{c.zone_name} ({c.zone_type})",
            "zone_id": c.zone_id
        }
        for i, c in enumerate(candidates)
    ]
    state.disambiguation_options = options
    
    llm = get_llm_client()
    state.reply = llm.call_make_disambiguation_question("zone", options)
    state.next_step = "end"
    
    return state


def resolve_car_node(state: AgentState) -> AgentState:
    """Resolve car(s) based on intent."""
    logger.info(f"[{state.session_id}] resolve_car_node - intent: {state.intent}, identifier: {state.car_identifier}")
    
    cars = list_user_cars(state.session_id)
    
    if state.intent == "fleet":
        # Return all cars for fleet query
        state.cars = cars
        state.next_step = "resolve_zone"
        return state
    
    # Single car intent
    if state.car_identifier:
        # Find specific car
        matches = find_car_by_identifier(cars, state.car_identifier)
        
        if not matches:
            state.reply = f"I couldn't find a car matching '{state.car_identifier}'. Please check the plate number."
            state.pending_question = False
            state.next_step = "end"
            return state
        
        if len(matches) == 1:
            state.selected_car = matches[0]
            state.next_step = "resolve_zone"
            return state
        
        # Multiple matches - ask for disambiguation
        logger.info(f"[{state.session_id}] Car disambiguation needed - {len(matches)} matches")
        state.cars = matches
        state.pending_question = True
        state.pending_type = "car"
        
        options = [
            {
                "index": i,
                "label": f"{c.plate} ({c.fuel_type or 'unknown fuel'}, {c.euro_class or 'unknown euro class'})",
                "car_id": c.car_id
            }
            for i, c in enumerate(matches)
        ]
        state.disambiguation_options = options
        
        llm = get_llm_client()
        state.reply = llm.call_make_disambiguation_question("car", options)
        state.next_step = "end"
        
        return state
    
    # No identifier - check if multiple cars
    if len(cars) > 1:
        # Ambiguous - ask which car
        state.cars = cars
        state.pending_question = True
        state.pending_type = "car"
        
        options = [
            {
                "index": i,
                "label": f"{c.plate} ({c.fuel_type or 'unknown fuel'}, {c.euro_class or 'unknown euro class'})",
                "car_id": c.car_id
            }
            for i, c in enumerate(cars)
        ]
        state.disambiguation_options = options
        
        llm = get_llm_client()
        state.reply = llm.call_make_disambiguation_question("car", options)
        state.next_step = "end"
        
        return state
    
    # Single car on file
    if cars:
        state.selected_car = cars[0]
        state.next_step = "resolve_zone"
    else:
        state.reply = "You don't have any cars registered. Please add a vehicle first."
        state.pending_question = False
        state.next_step = "end"
    
    return state


def fetch_policy_node(state: AgentState) -> AgentState:
    """Fetch policy for selected zone."""
    logger.info(f"[{state.session_id}] fetch_policy_node - zone: {state.selected_zone.zone_id if state.selected_zone else 'None'}")
    
    if not state.selected_zone:
        state.reply = "Error: No zone selected for policy fetch."
        state.next_step = "end"
        return state
    
    policy = get_policy(state.selected_zone.zone_id)
    
    if not policy:
        state.reply = f"I couldn't find policy information for {state.selected_zone.zone_name}."
        state.next_step = "end"
        return state
    
    state.policy = policy
    state.next_step = "decide"
    
    return state


def decide_node(state: AgentState) -> AgentState:
    """Make eligibility decision(s)."""
    logger.info(f"[{state.session_id}] decide_node - intent: {state.intent}")
    
    if not state.policy:
        state.reply = "Error: No policy available for decision."
        state.next_step = "end"
        return state
    
    if state.intent == "policy_only":
        # No decision needed, just explain policy
        state.next_step = "explain"
        return state
    
    if state.intent == "fleet":
        # Decide for all cars
        fleet_decisions = []
        for car in state.cars:
            decision = decide_eligibility(car, state.policy)
            fleet_decisions.append(FleetDecision(
                car_id=car.car_id,
                plate=car.plate,
                decision=decision
            ))
        state.fleet_decisions = fleet_decisions
    else:
        # Single car decision
        if not state.selected_car:
            state.reply = "Error: No car selected for decision."
            state.next_step = "end"
            return state
        
        decision = decide_eligibility(state.selected_car, state.policy)
        state.decision = decision
    
    state.next_step = "explain"
    return state


def explain_node(state: AgentState) -> AgentState:
    """Generate final explanation using LLM."""
    logger.info(f"[{state.session_id}] explain_node - generating final response")
    
    llm = get_llm_client()
    
    explanation = llm.call_explain(
        intent=state.intent,
        decision=state.decision,
        fleet_decisions=state.fleet_decisions,
        car=state.selected_car,
        cars=state.cars,
        policy=state.policy,
        zone=state.selected_zone
    )
    
    state.reply = explanation
    state.next_step = "end"
    
    return state


# ========== Routing Functions ==========

def route_after_intent(state: AgentState) -> str:
    """Route based on extracted intent."""
    if state.intent == "policy_only":
        return "resolve_zone"
    else:
        return "resolve_car"  # Resolve car first for car-related queries


def route_after_zone(state: AgentState) -> str:
    """Route after zone resolution."""
    if state.pending_question:
        return "end"
    
    # Respect explicit next_step from node
    if state.next_step == "fetch_policy":
        return "fetch_policy"
    
    if state.intent == "policy_only":
        return "fetch_policy"
    else:
        return "resolve_car"


def route_after_car(state: AgentState) -> str:
    """Route after car resolution."""
    if state.pending_question or state.next_step == "end":
        return "end"
    return "resolve_zone"  # Go to zone resolution next


def route_next_step(state: AgentState) -> str:
    """Generic router based on next_step field."""
    return state.next_step


# ========== Graph Construction ==========

def build_graph() -> StateGraph:
    """Build and compile the LangGraph workflow."""
    
    # Create graph
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("extract_intent", extract_intent_node)
    graph.add_node("resolve_zone", resolve_zone_node)
    graph.add_node("resolve_car", resolve_car_node)
    graph.add_node("fetch_policy", fetch_policy_node)
    graph.add_node("decide", decide_node)
    graph.add_node("explain", explain_node)
    
    # Set entry point
    graph.set_entry_point("extract_intent")
    
    # Add edges
    graph.add_conditional_edges(
        "extract_intent",
        route_after_intent,
        {
            "resolve_zone": "resolve_zone",
            "resolve_car": "resolve_car",
        }
    )
    
    graph.add_conditional_edges(
        "resolve_zone",
        route_after_zone,
        {
            "end": END,
            "fetch_policy": "fetch_policy",
            "resolve_car": "resolve_car",
        }
    )
    
    graph.add_conditional_edges(
        "resolve_car",
        route_after_car,
        {
            "end": END,
            "resolve_zone": "resolve_zone",
        }
    )
    
    graph.add_conditional_edges(
        "fetch_policy",
        route_next_step,
        {
            "decide": "decide",
            "end": END,
        }
    )
    
    graph.add_conditional_edges(
        "decide",
        route_next_step,
        {
            "explain": "explain",
            "end": END,
        }
    )
    
    graph.add_conditional_edges(
        "explain",
        route_next_step,
        {
            "end": END,
        }
    )
    
    return graph.compile()


# Global compiled graph
_compiled_graph = None


def get_graph():
    """Get or create compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph.with_config({"recursion_limit": 50})
