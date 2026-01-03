"""Pydantic models for the Agent Orchestrator service."""
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ========== Car Domain ==========

class Car(BaseModel):
    """Represents a vehicle."""
    car_id: str
    plate: str
    fuel_type: Optional[str] = None  # e.g., "diesel", "petrol", "electric", "hybrid"
    euro_class: Optional[str] = None  # e.g., "euro4", "euro5", "euro6"
    first_reg_date: Optional[date] = None
    vehicle_category: Optional[str] = None  # e.g., "M1" (passenger), "N1" (light commercial)


# ========== Zone Domain ==========

class ZoneCandidate(BaseModel):
    """A potential pollution zone match."""
    city: str
    zone_id: str
    zone_name: str
    zone_type: str  # e.g., "LEZ" (Low Emission Zone), "ZEZ" (Zero Emission Zone)


class ZonePolicyRule(BaseModel):
    """A single rule within a zone policy."""
    condition: str  # human-readable condition
    verdict: Literal["banned", "allowed"]
    applies_to: list[str]  # e.g., ["diesel", "euro4"]


class ZonePolicy(BaseModel):
    """Pollution policy for a specific zone."""
    city: str
    zone_id: str
    zone_name: str
    effective_from: date
    rules: list[ZonePolicyRule]
    exemptions: list[str] = Field(default_factory=list)  # e.g., ["vintage_cars", "disabled_permit"]


# ========== Decision Domain ==========

class Decision(BaseModel):
    """Eligibility decision for a car in a zone."""
    allowed: Literal["true", "false", "unknown"]
    reason_code: str
    factors: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class FleetDecision(BaseModel):
    """Decision for multiple cars."""
    car_id: str
    plate: str
    decision: Decision


# ========== Intent / LLM Output ==========

class IntentRequest(BaseModel):
    """Extracted intent and slots from user message."""
    intent: Literal["single_car", "fleet", "policy_only"]
    car_identifier: Optional[str] = None  # plate number or partial match
    city: Optional[str] = None
    zone_phrase: Optional[str] = None  # e.g., "city center", "downtown"


# ========== Agent State ==========

class AgentState(BaseModel):
    """State persisted across conversation turns."""
    session_id: str
    message: str = ""
    trace_id: str = ""  # For request tracing
    language: str = "en"  # Detected language code (e.g., "en", "es", "fr", "nl", "de")
    
    # Extracted slots
    intent: Optional[str] = None
    car_identifier: Optional[str] = None
    city: Optional[str] = None
    zone_phrase: Optional[str] = None
    
    # Resolved entities
    cars: list[Car] = Field(default_factory=list)
    selected_car: Optional[Car] = None
    zone_candidates: list[ZoneCandidate] = Field(default_factory=list)
    selected_zone: Optional[ZoneCandidate] = None
    policy: Optional[ZonePolicy] = None
    
    # Decisions
    decision: Optional[Decision] = None
    fleet_decisions: list[FleetDecision] = Field(default_factory=list)
    
    # Disambiguation state
    pending_question: bool = False
    pending_type: Optional[Literal["car", "zone"]] = None
    disambiguation_options: list[dict] = Field(default_factory=list)
    
    # Final output
    reply: str = ""
    
    # Control flow
    next_step: str = "extract_intent"


# ========== API Models ==========

class ChatRequest(BaseModel):
    """Request to /chat endpoint."""
    session_id: str
    message: str


class ChatAnswerRequest(BaseModel):
    """Request to /chat/answer endpoint."""
    session_id: str
    selection_index: int


class ChatResponse(BaseModel):
    """Response from chat endpoints."""
    session_id: str
    reply: str
    pending_question: bool = False
    options: Optional[list[dict]] = None
    state: Optional[dict] = None  # Debugging/optional
    trace_id: Optional[str] = None  # For request tracing
