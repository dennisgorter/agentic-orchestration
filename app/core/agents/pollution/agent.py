"""Pollution zone eligibility domain agent.

This agent wraps the existing LangGraph workflow for pollution zone
eligibility checks. It acts as a domain expert that:
- Processes pollution-related queries
- Uses LangGraph state machine for orchestration
- Maintains conversation context (from client)
- Returns eligibility decisions
"""

from app.core.agents.base import BaseAgent
from app.core.shared.messaging import AgentMessage
from .graph import get_graph
from datetime import datetime
from typing import Optional


class PollutionAgent(BaseAgent):
    """
    Domain expert for car pollution zone eligibility.
    
    This agent handles all pollution zone related queries including:
    - Single car eligibility checks ("Is my car allowed in Amsterdam?")
    - Fleet queries ("Which of my cars can enter Amsterdam?")
    - Policy information ("What are the pollution rules?")
    
    The agent uses the existing LangGraph workflow with 6 nodes:
    extract_intent → resolve_car → resolve_zone → fetch_policy → decide → explain
    """
    
    name = "pollution_agent"
    
    def __init__(self, cache: Optional[dict] = None):
        """
        Initialize pollution agent with optional cache.
        
        Args:
            cache: Optional cache for policies (future enhancement)
        """
        self.graph = get_graph()
        self.cache = cache or {}
    
    async def handle(self, message: AgentMessage) -> AgentMessage:
        """
        Process pollution zone query using existing LangGraph workflow.
        
        The workflow:
        1. Extract intent from user message
        2. Resolve car (if needed)
        3. Resolve zone (if needed)
        4. Fetch policy rules
        5. Make eligibility decision
        6. Generate explanation
        
        Args:
            message: AgentMessage containing:
                - payload["message"]: User query
                - conversation_history: Previous chat messages
                - trace_id: For debugging/monitoring
                
        Returns:
            AgentMessage with:
                - payload["answer"]: Response text
                - payload["decision"]: Eligibility decision (if applicable)
                - context: Updated context
        
        Raises:
            Exception: If LangGraph execution fails (includes trace_id)
        """
        
        # Extract from message
        query = message.payload.get("message", "")
        conversation_history = message.conversation_history
        
        # Use existing LangGraph workflow (NO CHANGES to graph logic)
        # The graph expects:
        # - message: User query
        # - conversation_history: List of previous messages
        # - trace_id: For logging
        # - session_id: Required by AgentState (use correlation_id)
        try:
            result = await self.graph.ainvoke({
                "message": query,
                "conversation_history": conversation_history,
                "trace_id": message.trace_id,
                "session_id": message.correlation_id  # Use correlation_id as session
            })
            
            # Extract answer from graph result
            answer = result.get("reply", "I couldn't process your request.")
            
            # Build response payload
            response_payload = {
                "answer": answer
            }
            
            # Include decision if available
            if "decision" in result:
                response_payload["decision"] = result["decision"]
            
            # Include disambiguation fields if available
            if "pending_question" in result:
                response_payload["pending_question"] = result["pending_question"]
            if "disambiguation_options" in result:
                response_payload["options"] = result["disambiguation_options"]
            
            # Return response message using helper
            return message.create_reply(
                payload=response_payload,
                context=message.context
            )
            
        except Exception as e:
            # Log error with trace_id for debugging
            error_msg = f"[{message.trace_id}] PollutionAgent error: {str(e)}"
            print(error_msg)  # Will be captured by logging system
            
            # Return error response
            return message.create_reply(
                payload={
                    "answer": "Sorry, I encountered an error processing your request. Please try again.",
                    "error": str(e)
                }
            )
    
    def __repr__(self) -> str:
        return f"<PollutionAgent(name='{self.name}')>"
