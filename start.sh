#!/bin/bash

# Quick start script for Agent Orchestrator

echo "🚀 Agent Orchestrator - Quick Start"
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚡ IMPORTANT: Edit .env and add your OpenAI API key!"
    echo "   OPENAI_API_KEY=sk-..."
    echo ""
    read -p "Press Enter after you've added your API key..."
fi

# Load environment variables from .env
if [ -f ".env" ]; then
    echo "🔑 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Start the server
echo ""
echo "🌐 Starting FastAPI server (v2.0.0 - Multi-Agent Architecture)..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   V1 (backward compatible): http://localhost:8000/v1/chat"
echo "   V2 (multi-agent router): http://localhost:8000/v2/chat"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.api.main:app --reload > backend.log 2>&1
