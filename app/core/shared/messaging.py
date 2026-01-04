"""Agent messaging protocol for inter-agent communication."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Any, Optional


class AgentMessage(BaseModel):
    """
    Standard message format for communication between agents.
    
    This message protocol enables:
    - Request tracing across agent boundaries
    - Context sharing between agents
    - Stateless conversation management (client provides history)
    - Correlation of related operations
    
    Attributes:
        trace_id: Unique ID for each user request (for debugging/monitoring)
        correlation_id: Links related traces (e.g., batch operations)
        sender: Name of sending agent (e.g., "intent_agent")
        receiver: Name of target agent (e.g., "pollution_agent")
        payload: Request/response data (domain-specific)
        context: Shared context across agents (optional)
        conversation_history: Chat history from client (stateless design)
        timestamp: When message was created
    """
    
    trace_id: str = Field(..., description="Unique ID for this request")
    correlation_id: str = Field(..., description="Links related traces")
    sender: str = Field(..., description="Sending agent name")
    receiver: str = Field(..., description="Target agent name")
    payload: Dict[str, Any] = Field(..., description="Request/response data")
    context: Dict[str, Any] = Field(default_factory=dict, description="Shared context")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Chat history from client (stateless)"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def create_reply(
        self,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> 'AgentMessage':
        """
        Create a reply message (swaps sender/receiver).
        
        Args:
            payload: Response data
            context: Updated context (optional, defaults to current context)
            
        Returns:
            New AgentMessage with swapped sender/receiver
        """
        return AgentMessage(
            trace_id=self.trace_id,
            correlation_id=self.correlation_id,
            sender=self.receiver,  # Swap
            receiver=self.sender,  # Swap
            payload=payload,
            context=context or self.context,
            conversation_history=self.conversation_history,
            timestamp=datetime.now()
        )
