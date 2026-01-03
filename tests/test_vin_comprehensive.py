#!/usr/bin/env python3
"""
Comprehensive test for VIN preservation with detailed logging analysis.
Tests multiple scenarios to ensure car context is never lost.
"""
import os
import sys

if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set")
    sys.exit(1)

from app.state import get_session_store
from app.graph import get_graph
from app.models import AgentState

def run_conversation_test(test_name, messages, session_id):
    """Run a conversation test with multiple messages."""
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)
    
    session_store = get_session_store()
    graph = get_graph()
    
    results = []
    
    for i, message in enumerate(messages, 1):
        print(f"\n[Turn {i}] User: '{message}'")
        print("-" * 80)
        
        state = session_store.create_or_get(session_id, message)
        print(f"  Before graph - car_identifier: {state.car_identifier}, "
              f"selected_car: {state.selected_car.plate if state.selected_car else None}")
        
        result = graph.invoke(state.model_dump())
        result_state = AgentState(**result)
        session_store.set(session_id, result_state)
        
        print(f"  After graph - car_identifier: {result_state.car_identifier}, "
              f"selected_car: {result_state.selected_car.plate if result_state.selected_car else None}, "
              f"city: {result_state.city}")
        print(f"  Reply: {result_state.reply[:80]}...")
        
        results.append({
            'message': message,
            'car_identifier': result_state.car_identifier,
            'selected_car': result_state.selected_car,
            'city': result_state.city,
            'intent': result_state.intent
        })
    
    return results

def verify_results(results, expectations):
    """Verify test results match expectations."""
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    
    all_passed = True
    
    for i, (result, expected) in enumerate(zip(results, expectations), 1):
        print(f"\nTurn {i}:")
        for key, expected_value in expected.items():
            actual_value = result.get(key)
            if key == 'selected_car':
                actual_value = actual_value.plate if actual_value else None
            
            if actual_value == expected_value:
                print(f"  ✅ {key}: {actual_value}")
            else:
                print(f"  ❌ {key}: Expected '{expected_value}', Got '{actual_value}'")
                all_passed = False
    
    return all_passed

def main():
    all_tests_passed = True
    
    # Test 1: Basic VIN preservation across city change
    test1_results = run_conversation_test(
        "Basic VIN Preservation",
        [
            "Is EF-456-GH allowed in Amsterdam LEZ?",
            "And for Rotterdam?"
        ],
        "test_basic_001"
    )
    
    test1_passed = verify_results(test1_results, [
        {'car_identifier': 'EF-456-GH', 'selected_car': 'EF-456-GH', 'city': 'Amsterdam'},
        {'car_identifier': 'EF-456-GH', 'selected_car': 'EF-456-GH', 'city': 'Rotterdam'}
    ])
    
    if test1_passed:
        print("\n✅ Test 1 PASSED")
    else:
        print("\n❌ Test 1 FAILED")
        all_tests_passed = False
    
    # Test 2: Multiple zone changes with same car
    test2_results = run_conversation_test(
        "Multiple Zone Changes",
        [
            "Can my car AB-123-CD enter Amsterdam?",
            "What about Rotterdam?"
        ],
        "test_multi_002"
    )
    
    test2_passed = verify_results(test2_results, [
        {'car_identifier': 'AB-123-CD', 'selected_car': 'AB-123-CD', 'city': 'Amsterdam'},
        {'car_identifier': 'AB-123-CD', 'selected_car': 'AB-123-CD', 'city': 'Rotterdam'}
    ])
    
    if test2_passed:
        print("\n✅ Test 2 PASSED")
    else:
        print("\n❌ Test 2 FAILED")
        all_tests_passed = False
    
    # Test 3: Short follow-up (just city name)
    test3_results = run_conversation_test(
        "Very Short Follow-up",
        [
            "Is EF-456-GH allowed in Amsterdam?",
            "Rotterdam?"
        ],
        "test_short_003"
    )
    
    test3_passed = verify_results(test3_results, [
        {'car_identifier': 'EF-456-GH', 'selected_car': 'EF-456-GH', 'city': 'Amsterdam'},
        {'car_identifier': 'EF-456-GH', 'selected_car': 'EF-456-GH', 'city': 'Rotterdam'}
    ])
    
    if test3_passed:
        print("\n✅ Test 3 PASSED")
    else:
        print("\n❌ Test 3 FAILED")
        all_tests_passed = False
    
    # Test 4: Explicit car change should override
    test4_results = run_conversation_test(
        "Explicit Car Change",
        [
            "Is EF-456-GH allowed in Amsterdam?",
            "What about AB-123-CD in Rotterdam?"
        ],
        "test_change_004"
    )
    
    test4_passed = verify_results(test4_results, [
        {'car_identifier': 'EF-456-GH', 'selected_car': 'EF-456-GH', 'city': 'Amsterdam'},
        {'car_identifier': 'AB-123-CD', 'selected_car': 'AB-123-CD', 'city': 'Rotterdam'}
    ])
    
    if test4_passed:
        print("\n✅ Test 4 PASSED")
    else:
        print("\n❌ Test 4 FAILED")
        all_tests_passed = False
    
    # Final summary
    print("\n" + "="*80)
    print("OVERALL TEST RESULTS")
    print("="*80)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("💥 SOME TESTS FAILED!")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
