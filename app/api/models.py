"""API request/response models for versioned endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class ChatRequestV1(BaseModel):
    """
    V1 API request (backward compatible with existing implementation).
    
    Used by /v1/chat endpoint which routes directly to pollution agent
    without intent classification.
    """
    
    message: str = Field(..., description="User query")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Previous chat messages for context"
    )


class ChatRequestV2(BaseModel):
    """
    V2 API request (new multi-agent router).
    
    Used by /v2/chat endpoint which uses intent agent for routing.
    Prepares for multi-domain expansion.
    """
    
    message: str = Field(..., description="User query")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Previous chat messages for context"
    )
    # Future fields for multi-domain:
    # domain_hint: Optional[str] = Field(None, description="Suggest domain")
    # user_id: Optional[str] = Field(None, description="User identifier")
    # session_metadata: Optional[Dict] = Field(None, description="Extra context")


class ChatResponse(BaseModel):
    """
    Unified response for both V1 and V2 endpoints.
    
    Contains the assistant's response plus tracing information.
    """
    
    reply: str = Field(..., description="Assistant response")
    trace_id: str = Field(..., description="Unique request ID for debugging")
    correlation_id: str = Field(..., description="Links related requests")
    pending_question: Optional[bool] = Field(None, description="Whether disambiguation is needed")
    options: Optional[List[Dict]] = Field(None, description="Disambiguation options")
    
    # Future fields:
    # suggested_actions: Optional[List[str]] = Field(None, description="Follow-up actions")
    # sources: Optional[List[Dict]] = Field(None, description="Reference data")
    # confidence: Optional[float] = Field(None, description="Response confidence")


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    agents: List[str] = Field(..., description="Registered agents")
