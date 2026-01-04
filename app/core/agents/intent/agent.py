"""Intent routing agent for multi-domain orchestration.

This agent acts as the entry point for all user requests and:
- Classifies user intent to determine domain
- Routes requests to appropriate domain agents
- Maintains agent registry
- Handles responses from domain agents

Future: When 3+ domains added, will use LLM for intent classification.
Current: Single domain (pollution) - simple routing.
"""

from app.core.agents.base import BaseAgent
from app.core.shared.messaging import AgentMessage
from datetime import datetime
from typing import Dict, Optional
import uuid


class IntentAgent(BaseAgent):
    """
    Router agent that classifies intents and delegates to domain agents.
    
    Architecture:
    - Acts as orchestrator/coordinator
    - Maintains registry of domain agents
    - Routes based on intent classification
    - Handles agent responses
    
    Evolution:
    - Phase 1: Single domain (pollution) - simple routing
    - Phase 2: 2-3 domains - keyword-based routing
    - Phase 3: 3+ domains - LLM-based intent classification
    """
    
    name = "intent_agent"
    
    def __init__(self):
        """Initialize intent agent with empty registry."""
        self.agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register a domain agent for routing.
        
        Args:
            agent: Domain agent instance (must have unique name)
            
        Raises:
            ValueError: If agent name already registered
        """
        if agent.name in self.agents:
            raise ValueError(f"Agent '{agent.name}' already registered")
        
        self.agents[agent.name] = agent
        print(f"[IntentAgent] Registered: {agent.name}")
    
    def unregister_agent(self, agent_name: str) -> None:
        """
        Unregister a domain agent.
        
        Args:
            agent_name: Name of agent to remove
        """
        if agent_name in self.agents:
            del self.agents[agent_name]
            print(f"[IntentAgent] Unregistered: {agent_name}")
    
    def list_agents(self) -> list[str]:
        """Return list of registered agent names."""
        return list(self.agents.keys())
    
    async def route(
        self,
        request_payload: dict,
        trace_id: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Route request to appropriate domain agent.
        
        High-level workflow:
        1. Classify intent (determine domain)
        2. Create AgentMessage
        3. Route to target agent
        4. Return response
        
        Args:
            request_payload: Request data including:
                - message: User query
                - conversation_history: Previous messages (optional)
            trace_id: Unique ID for tracing
            correlation_id: Optional correlation ID (defaults to trace_id)
            
        Returns:
            Response string from domain agent
            
        Raises:
            ValueError: If no agent can handle the request
        """
        
        # Default correlation_id to trace_id if not provided
        if correlation_id is None:
            correlation_id = trace_id
        
        # 1. Classify intent
        intent = self._classify_intent(request_payload.get("message", ""))
        
        # 2. Get target agent
        agent = self.agents.get(intent)
        if not agent:
            available = ", ".join(self.agents.keys()) if self.agents else "none"
            return (
                f"Sorry, I don't know how to help with that yet. "
                f"I can help with: {available}"
            )
        
        # 3. Create agent message
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
        
        # 4. Route to agent
        print(f"[{trace_id}] IntentAgent routing to: {intent}")
        response = await agent.handle(message)
        
        # 5. Return answer
        return response.payload.get("answer", "No response from agent.")
    
    async def handle(self, message: AgentMessage) -> AgentMessage:
        """
        Handle incoming message (alternate interface for agent-to-agent calls).
        
        Args:
            message: Incoming agent message
            
        Returns:
            AgentMessage with routing result
        """
        answer = await self.route(
            request_payload=message.payload,
            trace_id=message.trace_id,
            correlation_id=message.correlation_id
        )
        
        return message.create_reply(
            payload={"answer": answer}
        )
    
    def _classify_intent(self, message: str) -> str:
        """
        Classify user intent to determine target domain.
        
        Phase 1 (Current): Single domain - always return pollution_agent
        Phase 2 (2-3 domains): Keyword-based classification
        Phase 3 (3+ domains): LLM-based classification
        
        Args:
            message: User query
            
        Returns:
            Agent name to route to (e.g., "pollution_agent")
            
        Example future implementation for 3+ domains:
            ```python
            prompt = f'''Classify this request into one domain:
            
            Request: {message}
            
            Domains:
            - pollution_check: Car eligibility for pollution zones
            - parking_info: Parking rules and availability
            - complaint: File complaints or violations
            
            Return only the domain name.'''
            
            response = await llm_call(prompt)
            return response.strip() + "_agent"
            ```
        """
        
        # Phase 1: Single domain - simple routing
        # Always route to pollution agent (only domain we have)
        return "pollution_agent"
        
        # TODO: When adding 2nd/3rd domain, implement keyword-based routing:
        # message_lower = message.lower()
        # if any(word in message_lower for word in ["park", "parking", "spot"]):
        #     return "parking_agent"
        # elif any(word in message_lower for word in ["complain", "report", "violation"]):
        #     return "complaint_agent"
        # else:
        #     return "pollution_agent"  # default
    
    def __repr__(self) -> str:
        agent_count = len(self.agents)
        return f"<IntentAgent(agents={agent_count})>"
