# Soccer-AI - CLAUDE.md

## Project Overview

Soccer-AI is a living knowledge base with AI-powered chat interface for soccer/football information.

**Architecture**: SQLite + FTS5 → FastAPI → Haiku API → React Frontend

## Quick Start

```bash
# Backend
cd backend
pip install fastapi uvicorn anthropic aiohttp
python main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Directory Structure

```
soccer-AI/
├── CLAUDE.md              # This file
├── WORK_TRACKER-soccer-ai.wt  # Work tracking
├── schema.sql             # Database schema
├── api_design.md          # API specification
├── backend/
│   ├── main.py            # FastAPI app
│   ├── database.py        # SQLite + FTS5 queries
│   ├── models.py          # Pydantic models
│   ├── rag.py             # RAG retrieval logic
│   ├── ai_response.py     # Haiku integration
│   ├── routers/           # API route handlers
│   └── soccer_ai.db       # SQLite database
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   └── services/      # API client
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── seed_data.py       # Initial data seeding
│   └── daily_update.py    # Automation script
└── data/
    └── sample_data.json   # Test data
```

## Key Files

### Backend

- **main.py**: FastAPI application with CORS, routes, startup
- **database.py**: SQLite connection, FTS5 queries, CRUD operations
- **rag.py**: Retrieval logic - parses query, searches FTS5, builds context
- **ai_response.py**: Haiku API calls, prompt templates, response formatting

### Frontend

- **App.tsx**: Main chat interface
- **components/ChatMessage.tsx**: Message bubbles
- **components/ChatInput.tsx**: Input with send button
- **hooks/useChat.ts**: Chat state management
- **services/api.ts**: API client functions

## Common Commands

```bash
# Initialize database
cd backend && python -c "import database; database.init_db()"

# Run backend (development)
cd backend && uvicorn main:app --reload --port 8000

# Run frontend (development)
cd frontend && npm run dev

# Seed sample data
cd scripts && python seed_data.py

# Run daily update manually
cd scripts && python daily_update.py
```

## API Endpoints

Primary endpoint:
```
POST /api/v1/chat
{"message": "How did Arsenal play yesterday?"}
```

See `api_design.md` for full specification.

## RAG Flow

1. User submits question via chat
2. `rag.py` extracts entities (teams, players, dates)
3. FTS5 queries find relevant database rows
4. Context built from matching data
5. Haiku API generates natural language response
6. Response returned to frontend

## Environment Variables

```bash
# backend/.env
ANTHROPIC_API_KEY=your-key-here
DATABASE_PATH=./soccer_ai.db
```

## Testing

```bash
# Test database queries
python -c "import database; print(database.search_players('Haaland'))"

# Test RAG retrieval
python -c "import rag; print(rag.retrieve_context('Arsenal injuries'))"

# Test API
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Who is the top scorer in Premier League?"}'
```

## Dependencies

### Backend (Python 3.12+)
- fastapi
- uvicorn
- anthropic
- aiohttp (for web scraping)
- python-dotenv

### Frontend (Node 18+)
- react
- typescript
- tailwindcss
- vite

## Cost Estimates

- Haiku API: ~$0.001 per query
- At 1000 queries/day: ~$1/day
- Daily updates: ~$0.10/day
- **Total**: ~$35/month at scale
