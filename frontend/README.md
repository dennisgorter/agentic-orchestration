# Frontend - Agent Orchestrator

React-based chat interface for the Agent Orchestrator POC.

## Features

- 💬 **Interactive Chat Interface**: Clean, modern chat UI
- 🎯 **Example Queries**: Pre-built example questions to guide users
- 🚗 **Available Cars Display**: Shows test cars with their eligibility status
- 🔍 **Trace ID Display**: Shows trace IDs for debugging
- ✨ **Smart Disambiguation**: Interactive buttons for disambiguation choices
- 📱 **Responsive Design**: Works on desktop and mobile

## What Can You Ask?

### Single Car Eligibility
- "Is my car AB-123-CD allowed to enter Amsterdam city center?"
- "Can I drive my electric car IJ-789-KL into Amsterdam city center?"
- "Is EF-456-GH allowed in Rotterdam?"

### Fleet Queries
- "Which of my cars can enter Amsterdam city center?"
- "Can any of my cars access the Amsterdam logistics zone?"

### Policy Information
- "What are the pollution rules in Amsterdam?"
- "What are the pollution rules in Rotterdam?"
- "Tell me about the Amsterdam LEZ zone"

## Available Test Cars

- **AB-123-CD** - Diesel Euro 4 (❌ Banned in Amsterdam LEZ)
- **EF-456-GH** - Diesel Euro 5 (✅ Allowed in Amsterdam LEZ)
- **IJ-789-KL** - Electric (✅ Allowed everywhere)
- **MN-321-OP** - Petrol Euro 6 (✅ Allowed in Amsterdam LEZ)

## Setup

### Prerequisites

- Node.js 18+ and npm
- Backend API running on port 8000

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The frontend will be available at: http://localhost:3000

The Vite proxy will forward `/api/*` requests to `http://localhost:8000`.

### Build for Production

```bash
npm run build
```

The build output will be in the `dist/` folder.

### Preview Production Build

```bash
npm run preview
```

## Architecture

```
frontend/
├── index.html          # HTML entry point
├── package.json        # Dependencies
├── vite.config.js      # Vite configuration with proxy
└── src/
    ├── main.jsx        # React entry point
    ├── App.jsx         # Main chat component
    ├── App.css         # Styling
    └── index.css       # Global styles
```

## API Integration

The frontend communicates with the backend via:

- `POST /api/chat` - Send user message
- `POST /api/chat/answer` - Send disambiguation selection

All requests include a session ID and trace IDs are displayed in the UI.

## Features Demonstrated

### 1. Welcome Screen
Shows available cars and example queries when chat is empty.

### 2. Message Flow
- User messages appear on the right (purple gradient)
- Assistant responses on the left (white)
- Timestamps for all messages
- Trace IDs for debugging

### 3. Disambiguation Handling
When the agent needs clarification:
- Options appear as clickable buttons
- User selects an option
- Flow continues automatically

### 4. Loading States
- Animated dots while waiting for response
- Disabled input during processing

### 5. Error Handling
- Clear error messages
- Red styling for errors
- Error details displayed

## Customization

### Change Colors

Edit the gradients in `App.css` and `index.css`:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Add More Examples

Edit the `EXAMPLE_QUERIES` array in `App.jsx`:

```javascript
const EXAMPLE_QUERIES = [
  {
    category: "Your Category",
    queries: ["Your example question"]
  }
];
```

### Change API URL

Edit `vite.config.js` to point to a different backend:

```javascript
proxy: {
  '/api': {
    target: 'http://your-backend:8000',
    // ...
  }
}
```

## Tips for Users

1. **Start with examples** - Click any example query to begin
2. **Check available cars** - Only use the listed test cars
3. **Follow disambiguation** - When asked to choose, click an option
4. **View trace IDs** - Use them to debug issues with backend team
5. **Session persistence** - Your conversation is tracked by session ID

## Troubleshooting

### Backend Connection Issues

If you see connection errors:

1. Ensure backend is running: `http://localhost:8000/health`
2. Check CORS is enabled in backend
3. Verify proxy configuration in `vite.config.js`

### Port Already in Use

If port 3000 is busy:

```bash
# Edit vite.config.js and change the port
server: {
  port: 3001,  // Change to any available port
  // ...
}
```

### Build Errors

Clear node_modules and reinstall:

```bash
rm -rf node_modules package-lock.json
npm install
```

## Production Deployment

### Option 1: Static Hosting

Build and deploy the `dist/` folder to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

Update API URL in production to point to your deployed backend.

### Option 2: Docker

Create a Dockerfile:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
RUN npm install -g serve
CMD ["serve", "-s", "dist", "-l", "3000"]
```

Build and run:

```bash
docker build -t orchestrator-frontend .
docker run -p 3000:3000 orchestrator-frontend
```

## License

POC - Internal Use Only
