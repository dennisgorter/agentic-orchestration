#!/bin/bash
#V2 API Startup Script

set -e

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable not set"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start v2 API
echo "Starting Agent Orchestrator v2.0.0..."
echo "Multi-agent architecture: Intent Router + Pollution Expert"
echo ""

python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8001
