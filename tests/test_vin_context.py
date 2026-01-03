#!/usr/bin/env python3
"""
Test script to verify VIN/car context is preserved across conversation turns.
This reproduces the issue where asking "And for Rotterdam?" loses the car context.
"""
import os
import sys

# Ensure OPENAI_API_KEY is set
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set")
    sys.exit(1)

from app.state import get_session_store
from app.graph import get_graph
from app.models import AgentState

def test_vin_preservation():
    """Test that car/VIN is preserved across turns when asking about different zones."""
    
    print("\n" + "="*80)
    print("TEST: VIN Context Preservation Across Turns")
    print("="*80)
    
    session_id = "test_vin_context_001"
    session_store = get_session_store()
    graph = get_graph()
    
    # First message: Ask about specific car in Amsterdam
    print("\n[Turn 1] User: 'Is EF-456-GH allowed in Amsterdam LEZ?'")
    print("-" * 80)
    
    state1 = session_store.create_or_get(session_id, "Is EF-456-GH allowed in Amsterdam LEZ?")
    result1 = graph.invoke(state1.model_dump())
    result_state1 = AgentState(**result1)
    session_store.set(session_id, result_state1)
    
    print(f"Reply: {result_state1.reply[:100]}...")
    print(f"Car Identifier: {result_state1.car_identifier}")
    print(f"Selected Car: {result_state1.selected_car.plate if result_state1.selected_car else None}")
    print(f"City: {result_state1.city}")
    
    # Store the expected values
    expected_car_identifier = result_state1.car_identifier
    expected_selected_car = result_state1.selected_car
    
    # Second message: Ask about Rotterdam without mentioning car
    print("\n[Turn 2] User: 'And for Rotterdam?'")
    print("-" * 80)
    
    state2 = session_store.create_or_get(session_id, "And for Rotterdam?")
    print(f"After create_or_get - Car Identifier: {state2.car_identifier}")
    print(f"After create_or_get - Selected Car: {state2.selected_car.plate if state2.selected_car else None}")
    
    result2 = graph.invoke(state2.model_dump())
    result_state2 = AgentState(**result2)
    session_store.set(session_id, result_state2)
    
    print(f"Reply: {result_state2.reply[:100]}...")
    print(f"Car Identifier: {result_state2.car_identifier}")
    print(f"Selected Car: {result_state2.selected_car.plate if result_state2.selected_car else None}")
    print(f"City: {result_state2.city}")
    
    # Verify car context is preserved
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    
    success = True
    
    if result_state2.car_identifier == expected_car_identifier:
        print(f"✅ car_identifier preserved: {result_state2.car_identifier}")
    else:
        print(f"❌ car_identifier LOST!")
        print(f"   Expected: {expected_car_identifier}")
        print(f"   Got: {result_state2.car_identifier}")
        success = False
    
    if result_state2.selected_car and expected_selected_car and result_state2.selected_car.plate == expected_selected_car.plate:
        print(f"✅ selected_car preserved: {result_state2.selected_car.plate}")
    else:
        print(f"❌ selected_car LOST!")
        print(f"   Expected: {expected_selected_car.plate if expected_selected_car else None}")
        print(f"   Got: {result_state2.selected_car.plate if result_state2.selected_car else None}")
        success = False
    
    if result_state2.city == "Rotterdam":
        print(f"✅ New city recognized: {result_state2.city}")
    else:
        print(f"❌ City not updated correctly: {result_state2.city}")
        success = False
    
    print("\n" + "="*80)
    if success:
        print("🎉 TEST PASSED: Car context preserved across turns!")
    else:
        print("💥 TEST FAILED: Car context was lost!")
    print("="*80 + "\n")
    
    return success


if __name__ == "__main__":
    try:
        success = test_vin_preservation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
