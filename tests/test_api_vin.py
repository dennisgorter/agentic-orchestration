#!/usr/bin/env python3
"""
Test VIN context via direct API calls to reproduce the exact issue.
"""
import os
import sys
import requests
import json

if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not set")
    sys.exit(1)

API_URL = "http://localhost:8000"
SESSION_ID = f"debug_session_{os.getpid()}"

def test_via_api():
    print("="*80)
    print("Testing VIN Context Loss via API")
    print(f"Session ID: {SESSION_ID}")
    print("="*80)
    
    # Request 1
    print("\n[Request 1] Is EF-456-GH allowed in Amsterdam LEZ?")
    print("-"*80)
    
    response1 = requests.post(f"{API_URL}/chat", json={
        "session_id": SESSION_ID,
        "message": "Is EF-456-GH allowed in Amsterdam LEZ?"
    })
    
    data1 = response1.json()
    print(f"Trace ID: {data1.get('trace_id')}")
    print(f"Reply: {data1['reply'][:100]}...")
    
    # Request 2
    print("\n[Request 2] And for Rotterdam?")
    print("-"*80)
    
    response2 = requests.post(f"{API_URL}/chat", json={
        "session_id": SESSION_ID,
        "message": "And for Rotterdam?"
    })
    
    data2 = response2.json()
    print(f"Trace ID: {data2.get('trace_id')}")
    print(f"Reply: {data2['reply'][:100]}...")
    
    # Check if reply mentions EF-456-GH
    if "EF-456-GH" in data2['reply'] or "EF456GH" in data2['reply'].replace("-", "").replace(" ", ""):
        print("\n✅ SUCCESS: Car context preserved! Reply mentions EF-456-GH")
        return True
    else:
        print("\n❌ FAILURE: Car context lost! Reply does not mention EF-456-GH")
        print(f"\nFull reply: {data2['reply']}")
        return False

if __name__ == "__main__":
    try:
        success = test_via_api()
        print("\n" + "="*80)
        print("Check server logs for STATE RESTORE and STATE SAVE messages")
        print("="*80)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
