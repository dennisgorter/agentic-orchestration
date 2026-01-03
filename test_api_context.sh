#!/bin/bash
# Test script to reproduce VIN context loss issue via API

SESSION_ID="test_api_context_$(date +%s)"

echo "=========================================="
echo "Testing VIN Context via API"
echo "Session ID: $SESSION_ID"
echo "=========================================="

echo ""
echo "[Request 1] Is EF-456-GH allowed in Amsterdam LEZ?"
echo "--------------------------------------------------"
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Is EF-456-GH allowed in Amsterdam LEZ?\"}" \
  2>/dev/null | jq -r '.reply' | head -c 100
echo "..."

echo ""
echo ""
echo "[Request 2] And for Rotterdam?"
echo "--------------------------------------------------"
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"And for Rotterdam?\"}" \
  2>/dev/null | jq -r '.reply' | head -c 100
echo "..."

echo ""
echo ""
echo "=========================================="
echo "Check backend logs for:"
echo "  - BEFORE GRAPH"
echo "  - STATE RESTORE" 
echo "  - STATE SAVE"
echo "  - AFTER GRAPH"
echo "=========================================="
