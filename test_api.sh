#!/bin/bash

# Test script with example curl commands

BASE_URL="http://localhost:8000"

echo "🧪 Agent Orchestrator - API Test Examples"
echo "=========================================="
echo ""
echo "Make sure the server is running (./start.sh)"
echo ""

# Helper function to handle disambiguation automatically
handle_response() {
    local session_id=$1
    local response=$2
    local step_label=$3
    local user_message=$4
    
    # Extract trace_id from response
    local trace_id=$(echo "$response" | jq -r '.trace_id // "no-trace"')
    
    echo "📨 User Input: \"$user_message\""
    echo "🔍 Trace ID: $trace_id"
    echo ""
    echo "$response" | jq '.'
    echo ""
    
    # Check if disambiguation is needed (API returns pending_question)
    local needs_disambiguation=$(echo "$response" | jq -r '.pending_question // false')
    
    if [ "$needs_disambiguation" = "true" ]; then
        echo "⚠️  Disambiguation needed for $step_label"
        echo "   Automatically selecting first option..."
        echo ""
        
        # Send disambiguation response to /chat/answer endpoint
        DISAMBIGUATION_RESPONSE=$(curl -s -X POST $BASE_URL/chat/answer \
          -H "Content-Type: application/json" \
          -d "{
            \"session_id\": \"$session_id\",
            \"selection_index\": 0
          }")
        
        local disambiguation_trace_id=$(echo "$DISAMBIGUATION_RESPONSE" | jq -r '.trace_id // "no-trace"')
        
        echo "📨 User Selection: 0 (first option)"
        echo "🔍 Trace ID: $disambiguation_trace_id"
        echo ""
        echo "$DISAMBIGUATION_RESPONSE" | jq '.'
        echo ""
    fi
}

echo "1️⃣  Health Check"
echo "----------------"
curl -s $BASE_URL/health | jq '.'
echo ""
echo ""

# Example 1: Single car eligibility
echo "2️⃣  Example 1: Single Car Eligibility (Diesel Euro 4 - Should be BANNED)"
echo "-----------------------------------------------------------------------"
RESPONSE=$(curl -s -X POST $BASE_URL/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_user_1",
    "message": "Is my car AB-123-CD allowed to enter Amsterdam city center?"
  }')
handle_response "demo_user_1" "$RESPONSE" "Example 1" "Is my car AB-123-CD allowed to enter Amsterdam city center?"
echo ""

# Example 2: Electric car (should be allowed)
echo "3️⃣  Example 2: Electric Car Check (Should be ALLOWED)"
echo "----------------------------------------------------"
RESPONSE=$(curl -s -X POST $BASE_URL/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_user_2",
    "message": "Can I drive my electric car IJ-789-KL into Amsterdam city center?"
  }')
handle_response "demo_user_2" "$RESPONSE" "Example 2" "Can I drive my electric car IJ-789-KL into Amsterdam city center?"
echo ""

# Example 3: Fleet query
echo "4️⃣  Example 3: Fleet Eligibility Check"
echo "------------------------------------"
RESPONSE=$(curl -s -X POST $BASE_URL/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_user_3",
    "message": "Which of my cars can enter Amsterdam city center?"
  }')
handle_response "demo_user_3" "$RESPONSE" "Example 3" "Which of my cars can enter Amsterdam city center?"
echo ""

# Example 4: Policy-only query
echo "5️⃣  Example 4: Policy Information Only"
echo "------------------------------------"
RESPONSE=$(curl -s -X POST $BASE_URL/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_user_4",
    "message": "What are the pollution rules in Rotterdam?"
  }')
handle_response "demo_user_4" "$RESPONSE" "Example 4" "What are the pollution rules in Rotterdam?"
echo ""

# Example 5: Disambiguation flow (explicitly testing multi-step)
echo "6️⃣  Example 5: Disambiguation Flow (Intentionally Ambiguous)"
echo "----------------------------------------------------------"
RESPONSE=$(curl -s -X POST $BASE_URL/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_user_5",
    "message": "Can I drive my car into Amsterdam?"
  }')
handle_response "demo_user_5" "$RESPONSE" "Example 5" "Can I drive my car into Amsterdam?"

echo ""
echo "✅ All examples completed!"
echo ""
echo "💡 Tips:"
echo "   - Try different car plates: AB-123-CD, EF-456-GH, IJ-789-KL, MN-321-OP"
echo "   - Try different cities: Amsterdam, Rotterdam"
echo "   - Check /docs for interactive API documentation"
