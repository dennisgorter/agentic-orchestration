"""Unit tests for PollutionAgent wrapper."""

import pytest
from datetime import datetime
from app.core.agents.pollution.agent import PollutionAgent
from app.core.shared.messaging import AgentMessage


@pytest.mark.asyncio
async def test_pollution_agent_initialization():
    """Test that pollution agent initializes correctly."""
    agent = PollutionAgent()
    
    assert agent.name == "pollution_agent"
    assert agent.graph is not None
    assert isinstance(agent.cache, dict)


@pytest.mark.asyncio
async def test_pollution_agent_with_cache():
    """Test pollution agent initialization with custom cache."""
    custom_cache = {"test": "data"}
    agent = PollutionAgent(cache=custom_cache)
    
    assert agent.cache == custom_cache


@pytest.mark.asyncio 
async def test_handle_creates_proper_reply():
    """Test that handle method creates proper reply structure."""
    agent = PollutionAgent()
    
    message = AgentMessage(
        trace_id="test-123",
        correlation_id="corr-123",
        sender="intent_agent",
        receiver="pollution_agent",
        payload={"message": "test query"},
        conversation_history=[],
        context={},
        timestamp=datetime.now()
    )
    
    response = await agent.handle(message)
    
    # Verify response structure
    assert response.trace_id == "test-123"
    assert response.correlation_id == "corr-123"
    assert response.sender == "pollution_agent"
    assert response.receiver == "intent_agent"
    assert "answer" in response.payload
    assert isinstance(response.payload["answer"], str)


@pytest.mark.asyncio
async def test_handle_preserves_trace_id():
    """Test that trace_id is preserved through message handling."""
    agent = PollutionAgent()
    
    trace_id = "unique-trace-456"
    message = AgentMessage(
        trace_id=trace_id,
        correlation_id="corr-456",
        sender="test",
        receiver="pollution_agent",
        payload={"message": "Is my car allowed?"},
        conversation_history=[],
        context={},
        timestamp=datetime.now()
    )
    
    response = await agent.handle(message)
    
    assert response.trace_id == trace_id


@pytest.mark.asyncio
async def test_repr():
    """Test string representation."""
    agent = PollutionAgent()
    
    repr_str = repr(agent)
    assert "PollutionAgent" in repr_str
    assert "pollution_agent" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
