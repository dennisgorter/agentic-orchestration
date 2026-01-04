"""Unit tests for IntentAgent routing logic."""

import pytest
from datetime import datetime
from app.core.agents.intent.agent import IntentAgent
from app.core.agents.pollution.agent import PollutionAgent
from app.core.shared.messaging import AgentMessage


@pytest.mark.asyncio
async def test_intent_agent_initialization():
    """Test that intent agent initializes with empty registry."""
    agent = IntentAgent()
    
    assert agent.name == "intent_agent"
    assert len(agent.agents) == 0
    assert agent.list_agents() == []


@pytest.mark.asyncio
async def test_agent_registration():
    """Test registering a domain agent."""
    intent_agent = IntentAgent()
    pollution_agent = PollutionAgent()
    
    intent_agent.register_agent(pollution_agent)
    
    assert len(intent_agent.agents) == 1
    assert "pollution_agent" in intent_agent.agents
    assert intent_agent.list_agents() == ["pollution_agent"]


@pytest.mark.asyncio
async def test_duplicate_registration_raises_error():
    """Test that registering the same agent twice raises ValueError."""
    intent_agent = IntentAgent()
    pollution_agent = PollutionAgent()
    
    intent_agent.register_agent(pollution_agent)
    
    with pytest.raises(ValueError, match="already registered"):
        intent_agent.register_agent(pollution_agent)


@pytest.mark.asyncio
async def test_agent_unregistration():
    """Test unregistering a domain agent."""
    intent_agent = IntentAgent()
    pollution_agent = PollutionAgent()
    
    intent_agent.register_agent(pollution_agent)
    assert len(intent_agent.agents) == 1
    
    intent_agent.unregister_agent("pollution_agent")
    assert len(intent_agent.agents) == 0


@pytest.mark.asyncio
async def test_classify_intent_returns_pollution():
    """Test that intent classification returns pollution_agent for all queries."""
    intent_agent = IntentAgent()
    
    # Test various queries all route to pollution_agent
    assert intent_agent._classify_intent("Is my car allowed?") == "pollution_agent"
    assert intent_agent._classify_intent("Amsterdam pollution rules") == "pollution_agent"
    assert intent_agent._classify_intent("diesel ban") == "pollution_agent"


@pytest.mark.asyncio
async def test_route_with_no_agents():
    """Test routing when no agents are registered."""
    intent_agent = IntentAgent()
    
    result = await intent_agent.route(
        request_payload={"message": "test"},
        trace_id="test-123"
    )
    
    assert "don't know how to help" in result.lower()
    assert "none" in result.lower()


@pytest.mark.asyncio
async def test_handle_creates_proper_reply():
    """Test that handle method creates proper reply message."""
    intent_agent = IntentAgent()
    pollution_agent = PollutionAgent()
    intent_agent.register_agent(pollution_agent)
    
    # Create incoming message
    message = AgentMessage(
        trace_id="test-123",
        correlation_id="corr-123",
        sender="test",
        receiver="intent_agent",
        payload={"message": "test query"},
        conversation_history=[],
        context={},
        timestamp=datetime.now()
    )
    
    response = await intent_agent.handle(message)
    
    assert response.trace_id == "test-123"
    assert response.correlation_id == "corr-123"
    assert response.sender == "intent_agent"
    assert response.receiver == "test"
    assert "answer" in response.payload


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
