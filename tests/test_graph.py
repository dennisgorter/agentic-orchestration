"""Tests for the LangGraph workflow (with mocked LLM)."""
import pytest
from unittest.mock import Mock, patch
from datetime import date

from app.models import AgentState, IntentRequest, Car, ZoneCandidate, Decision
from app.graph import (
    extract_intent_node,
    resolve_zone_node,
    resolve_car_node,
    fetch_policy_node,
    decide_node,
    explain_node
)


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    with patch('app.graph.get_llm_client') as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_state():
    """Create a sample agent state."""
    return AgentState(
        session_id="test_session",
        message="Is my car AB-123-CD allowed in Amsterdam city center?"
    )


def test_extract_intent_single_car(mock_llm_client, sample_state):
    """Test intent extraction for single car query."""
    # Mock LLM response
    mock_llm_client.call_extract_intent_slots.return_value = IntentRequest(
        intent="single_car",
        car_identifier="AB-123-CD",
        city="Amsterdam",
        zone_phrase="city center"
    )
    
    result = extract_intent_node(sample_state)
    
    assert result.intent == "single_car"
    assert result.car_identifier == "AB-123-CD"
    assert result.city == "Amsterdam"
    assert result.zone_phrase == "city center"


def test_extract_intent_fleet(mock_llm_client):
    """Test intent extraction for fleet query."""
    state = AgentState(
        session_id="test",
        message="Which of my cars can enter Amsterdam?"
    )
    
    mock_llm_client.call_extract_intent_slots.return_value = IntentRequest(
        intent="fleet",
        car_identifier=None,
        city="Amsterdam",
        zone_phrase=None
    )
    
    result = extract_intent_node(state)
    
    assert result.intent == "fleet"
    assert result.car_identifier is None
    assert result.city == "Amsterdam"


def test_resolve_zone_single_match():
    """Test zone resolution with single match."""
    state = AgentState(
        session_id="test",
        message="test",
        city="Rotterdam",
        zone_phrase=None
    )
    
    result = resolve_zone_node(state)
    
    # Rotterdam has only 1 zone in mock data
    assert result.selected_zone is not None
    assert result.selected_zone.city == "Rotterdam"
    assert result.next_step == "fetch_policy"
    assert not result.pending_question


def test_resolve_zone_multiple_matches(mock_llm_client):
    """Test zone resolution with multiple matches (disambiguation)."""
    state = AgentState(
        session_id="test",
        message="test",
        city="Amsterdam",
        zone_phrase="city center"
    )
    
    mock_llm_client.call_make_disambiguation_question.return_value = \
        "Which zone are you asking about?"
    
    result = resolve_zone_node(state)
    
    # Amsterdam has multiple zones
    assert len(result.zone_candidates) > 1
    assert result.pending_question
    assert result.pending_type == "zone"
    assert len(result.disambiguation_options) > 0
    assert result.next_step == "end"


def test_resolve_zone_no_city():
    """Test zone resolution without city."""
    state = AgentState(
        session_id="test",
        message="test",
        city=None
    )
    
    result = resolve_zone_node(state)
    
    assert "city" in result.reply.lower()
    assert result.next_step == "end"


def test_resolve_car_single_match():
    """Test car resolution with single identifier match."""
    state = AgentState(
        session_id="test",
        message="test",
        intent="single_car",
        car_identifier="AB-123-CD"
    )
    
    result = resolve_car_node(state)
    
    assert result.selected_car is not None
    assert result.selected_car.plate == "AB-123-CD"
    assert result.next_step == "fetch_policy"


def test_resolve_car_fleet():
    """Test car resolution for fleet query."""
    state = AgentState(
        session_id="test",
        message="test",
        intent="fleet"
    )
    
    result = resolve_car_node(state)
    
    assert len(result.cars) > 0
    assert result.next_step == "fetch_policy"


def test_fetch_policy():
    """Test policy fetching."""
    state = AgentState(
        session_id="test",
        message="test",
        selected_zone=ZoneCandidate(
            city="Amsterdam",
            zone_id="ams_lez_01",
            zone_name="Amsterdam City Center LEZ",
            zone_type="LEZ"
        )
    )
    
    result = fetch_policy_node(state)
    
    assert result.policy is not None
    assert result.policy.zone_id == "ams_lez_01"
    assert result.next_step == "decide"


def test_decide_single_car_allowed():
    """Test decision for single car (allowed)."""
    from app.tools import get_policy
    
    # Electric car should be allowed
    state = AgentState(
        session_id="test",
        message="test",
        intent="single_car",
        selected_car=Car(
            car_id="car_003",
            plate="IJ-789-KL",
            fuel_type="electric",
            euro_class=None,
            first_reg_date=date(2021, 1, 10),
            vehicle_category="M1"
        ),
        policy=get_policy("ams_lez_01")
    )
    
    result = decide_node(state)
    
    assert result.decision is not None
    assert result.decision.allowed == "true"
    assert result.next_step == "explain"


def test_decide_single_car_banned():
    """Test decision for single car (banned)."""
    from app.tools import get_policy
    
    # Diesel euro4 should be banned in Amsterdam LEZ
    state = AgentState(
        session_id="test",
        message="test",
        intent="single_car",
        selected_car=Car(
            car_id="car_001",
            plate="AB-123-CD",
            fuel_type="diesel",
            euro_class="euro4",
            first_reg_date=date(2010, 3, 15),
            vehicle_category="M1"
        ),
        policy=get_policy("ams_lez_01")
    )
    
    result = decide_node(state)
    
    assert result.decision is not None
    assert result.decision.allowed == "false"
    assert result.next_step == "explain"


def test_decide_fleet():
    """Test decision for fleet."""
    from app.tools import list_user_cars, get_policy
    
    state = AgentState(
        session_id="test",
        message="test",
        intent="fleet",
        cars=list_user_cars("test"),
        policy=get_policy("ams_lez_01")
    )
    
    result = decide_node(state)
    
    assert len(result.fleet_decisions) > 0
    assert result.next_step == "explain"
    
    # Check that we have different outcomes
    allowed = [fd for fd in result.fleet_decisions if fd.decision.allowed == "true"]
    banned = [fd for fd in result.fleet_decisions if fd.decision.allowed == "false"]
    
    assert len(allowed) > 0  # Electric and euro5/6 should be allowed
    assert len(banned) > 0   # Euro4 diesel should be banned


def test_explain_node(mock_llm_client):
    """Test explanation generation."""
    state = AgentState(
        session_id="test",
        message="test",
        intent="single_car",
        decision=Decision(
            allowed="true",
            reason_code="MEETS_REQUIREMENTS",
            factors=["Vehicle meets requirements"],
            missing_fields=[],
            next_actions=[]
        )
    )
    
    mock_llm_client.call_explain.return_value = "Your vehicle is allowed to enter the zone."
    
    result = explain_node(state)
    
    assert result.reply != ""
    assert result.next_step == "end"
    mock_llm_client.call_explain.assert_called_once()


def test_missing_fields_decision():
    """Test decision with missing vehicle fields."""
    from app.tools import get_policy
    
    # Car without euro class
    state = AgentState(
        session_id="test",
        message="test",
        intent="single_car",
        selected_car=Car(
            car_id="incomplete",
            plate="XX-000-XX",
            fuel_type="diesel",
            euro_class=None,  # Missing!
            vehicle_category="M1"
        ),
        policy=get_policy("ams_lez_01")
    )
    
    result = decide_node(state)
    
    assert result.decision is not None
    assert result.decision.allowed == "unknown"
    assert "euro_class" in result.decision.missing_fields
    assert len(result.decision.next_actions) > 0
