#!/bin/bash

echo "🚀 Starting Frontend Server"
echo "============================"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running on port 8000"
else
    echo "⚠️  Warning: Backend doesn't appear to be running on port 8000"
    echo "   Please start the backend first: ./start.sh"
    echo ""
fi

echo ""
echo "🌐 Starting frontend on http://localhost:3000"
echo "   Press Ctrl+C to stop"
echo ""

npm run dev
