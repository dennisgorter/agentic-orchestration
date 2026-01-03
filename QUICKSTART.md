# Quick Start Guide - Agent Orchestrator POC

This guide will help you get the Agent Orchestrator POC up and running in minutes.

## Prerequisites

- **Python 3.9+** (for backend)
- **Node.js 18+** (for frontend)
- **OpenAI API Key** (get one at https://platform.openai.com/)

## Step-by-Step Setup

### 1. Backend Setup (5 minutes)

```bash
# Navigate to project directory
cd agentic-orchestrator

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Start the backend server
./start.sh
```

✅ **Backend should now be running at:** http://localhost:8000

Verify it's working:
```bash
curl http://localhost:8000/health
```

### 2. Frontend Setup (3 minutes)

Open a **new terminal window**, then:

```bash
# Navigate to frontend directory
cd agentic-orchestrator/frontend

# Install Node.js dependencies
npm install

# Start the frontend server
npx vite
```

✅ **Frontend should now be running at:** http://localhost:3000

### 3. Start Chatting! 🎉

1. Open http://localhost:3000 in your browser
2. You'll see a welcome screen with:
   - Available test cars
   - Example queries you can try
3. Click any example query or type your own!

## What Can You Ask?

### Try These Examples

**Single Car Checks:**
- "Is my car AB-123-CD allowed to enter Amsterdam city center?"
- "Can I drive my electric car IJ-789-KL into Amsterdam city center?"

**Fleet Queries:**
- "Which of my cars can enter Amsterdam city center?"

**Policy Questions:**
- "What are the pollution rules in Amsterdam?"
- "What are the pollution rules in Rotterdam?"

**Multilingual Support** (7 languages supported):
- English: "Is my car allowed in Amsterdam?"
- Spanish: "¿Puedo conducir mi coche en Amsterdam?"
- French: "Puis-je conduire ma voiture à Amsterdam?"
- Dutch: "Kan ik met mijn auto in Amsterdam rijden?"
- German: "Darf ich mit meinem Auto in Amsterdam fahren?"
- Italian: "Posso guidare la mia auto ad Amsterdam?"
- Portuguese: "Posso dirigir meu carro em Amsterdã?"

The system automatically detects your language and responds accordingly!

### Available Test Cars

| Plate Number | Type | Status |
|--------------|------|--------|
| AB-123-CD | Diesel Euro 4 | ❌ Banned in Amsterdam LEZ |
| EF-456-GH | Diesel Euro 5 | ✅ Allowed in Amsterdam LEZ |
| IJ-789-KL | Electric | ✅ Allowed everywhere |
| MN-321-OP | Petrol Euro 6 | ✅ Allowed in Amsterdam LEZ |

### Available Cities

- **Amsterdam** (LEZ and ZEZ zones)
- **Rotterdam** (Environmental Zone)

## Understanding the Flow

### Normal Query Flow

1. You ask: "Is my car AB-123-CD allowed in Amsterdam?"
2. System extracts: car plate, city
3. System asks: "Which zone?" (if ambiguous)
4. You select: "Amsterdam City Center LEZ"
5. System provides: Eligibility result with explanation

### Disambiguation

When the system needs clarification, you'll see:
- A question from the assistant
- Clickable buttons with options
- Select an option to continue

## Features to Notice

1. **Trace IDs** - Each request has a unique ID (shown at bottom of messages)
2. **Session Tracking** - Your conversation is tracked by session ID
3. **Smart Disambiguation** - System asks clarifying questions when needed
4. **Clean UI** - Modern, responsive chat interface
5. **Car Context Preservation** - Ask follow-up questions without repeating the car plate
   - Example: "Is EF-456-GH allowed in Amsterdam?" → "And for Rotterdam?" (car preserved)
6. **Multilingual** - System detects your language and responds in the same language

## Troubleshooting

### Backend Won't Start

**Issue:** Port 8000 already in use
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
```

**Issue:** OpenAI API key not set
```bash
# Set it again in your terminal
export OPENAI_API_KEY="sk-your-key-here"
```

### Frontend Won't Start

**Issue:** Port 3000 already in use
```bash
# Kill the process
lsof -ti:3000 | xargs kill -9
```

**Issue:** Dependencies not installed
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Can't Connect to Backend

**Issue:** CORS errors in browser console

1. Check backend is running: http://localhost:8000/health
2. Check proxy configuration in `frontend/vite.config.js`
3. Restart both servers

### Wrong Responses

**Issue:** System doesn't understand queries

- Only use the **test cars** listed above (AB-123-CD, EF-456-GH, etc.)
- Only ask about **Amsterdam** or **Rotterdam**
- Follow the example query patterns

## Testing the API Directly

Want to test without the UI?

```bash
# Test with curl
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_user",
    "message": "Is my car AB-123-CD allowed in Amsterdam?"
  }'
```

Or use the test script:
```bash
./test_api.sh
```

## Architecture Overview

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │────────▶│   Frontend  │────────▶│   Backend   │
│             │         │   (React)   │         │  (FastAPI)  │
│   Port 3000 │◀────────│             │◀────────│  Port 8000  │
└─────────────┘         └─────────────┘         └─────────────┘
                              │                        │
                              │                        │
                              ▼                        ▼
                        User Interface          LangGraph Workflow
                        - Chat UI                - Intent extraction
                        - Examples               - Car resolution
                        - Disambiguation         - Zone resolution
                                                 - Policy fetch
                                                 - Decision making
                                                 - LLM explanation
```

## Next Steps

1. **Try all examples** - Click through the pre-built queries
2. **Test disambiguation** - Ask "Which of my cars can enter Amsterdam?"
3. **Check trace IDs** - Use them to debug requests
4. **View logs** - Check terminal for structured logs with trace IDs
5. **Read documentation**:
   - Main README.md
   - TRACEABILITY.md
   - frontend/README.md

## Production Notes

This is a **POC** (Proof of Concept) with:
- Mock data (cars and policies in memory)
- No database persistence
- Simple session management
- Test data only

For production, you would need:
- Real database for cars and policies
- User authentication
- Session persistence
- Error monitoring
- Load balancing
- API rate limiting

## Support

Issues or questions?
- Check the main README.md for detailed documentation
- Review TRACEABILITY.md for debugging with trace IDs
- Check frontend/README.md for UI-specific questions

## Quick Commands Reference

```bash
# Backend
./start.sh                  # Start backend server
./test_api.sh              # Test API endpoints
python validate.py         # Validate setup

# Frontend
cd frontend
npm install                # Install dependencies
npx vite                   # Start frontend server
npm run build              # Build for production

# Both
# Terminal 1: Backend
./start.sh

# Terminal 2: Frontend  
cd frontend && npx vite
```

---

**Enjoy exploring the Agent Orchestrator POC! 🚀**
