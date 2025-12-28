# Soccer-AI - CLAUDE.md

## ⚠️ CRITICAL: Read This First

**Soccer-AI has TWO frontend directories. Only ONE should be used:**

| Directory | What It Is | Status |
|-----------|------------|--------|
| `frontend/` | React + Vite + TypeScript | ✅ PRIMARY - Build this |
| `flask-frontend/` | Simple Flask static server | ⚠️ TESTING ONLY - Ignore |

**The backend is FastAPI** (`backend/main.py`), NOT Flask. The `flask-frontend/` is just a lightweight testing tool that proxies to FastAPI.

---

## Project Vision

Soccer-AI is an **emotionally intelligent football companion** - not a stats bot.

**Core Philosophy** (from ARIEL_FULL_STORY.md):
> "What if the AI wasn't neutral? What if it was a fan?"

The AI should:
- FEEL the weight of rivalries
- Know you don't casually mention "that Agüero goal" to a Man United supporter
- Understand pre-match hope vs post-loss grief
- Use UK English: "match" not "game", "nil" not "zero", "pitch" not "field"

**Identity**: "Fan at heart. Analyst in nature."

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                           │
│  React Frontend (frontend/)  ←── Build this on PC           │
│  • Chat with club personas                                  │
│  • Games/fixtures display                                   │
│  • Standings with form indicators                           │
│  • Predictor integration                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (port 8000)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER                              │
│  FastAPI Backend (backend/main.py)                          │
│  • 25+ endpoints                                            │
│  • CORS configured                                          │
│  • Security/rate limiting                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ INTELLIGENCE    │ │ KNOWLEDGE GRAPH │ │ PREDICTOR       │
│ ai_response.py  │ │ database.py     │ │ backend/        │
│ rag.py          │ │ kg_nodes/edges  │ │ predictor/      │
│ Fan Personas    │ │ 41 nodes        │ │ Power Ratings   │
│ Haiku API       │ │ 37 edges        │ │ Draw Detection  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Directory Structure (Current)

```
soccer-AI/
├── CLAUDE.md                    # THIS FILE - Project instructions
├── README.md                    # Quick start guide
├── schema.sql                   # Database schema (14KB)
├── api_design.md                # API specification
│
├── backend/                     # ✅ FastAPI Backend (COMPLETE)
│   ├── main.py                  # FastAPI app (54KB, 25+ endpoints)
│   ├── database.py              # SQLite + FTS5 + KG (65KB)
│   ├── rag.py                   # Hybrid RAG (34KB)
│   ├── ai_response.py           # Haiku + personas (25KB)
│   ├── models.py                # Pydantic models
│   ├── security_session.py      # Session-based security
│   ├── soccer_ai.db             # Main database (335KB)
│   ├── soccer_ai_kg.db          # Knowledge graph (303KB)
│   ├── predictor/               # ⭐ NEW: Match prediction
│   │   ├── team_ratings.py      # ELO-style power ratings
│   │   ├── draw_detector.py     # Third Knowledge patterns
│   │   ├── backtest_ratings.py  # Validation framework
│   │   └── tune_draw_threshold.py
│   ├── kg/                      # Knowledge graph data
│   ├── routers/                 # API route handlers
│   ├── tests/                   # Test suite
│   └── test_*.py                # Individual test files
│
├── frontend/                    # ✅ React Frontend (BUILD THIS)
│   ├── src/                     # React source code
│   │   ├── App.tsx              # Main app
│   │   ├── components/          # UI components
│   │   ├── hooks/               # Custom React hooks
│   │   └── services/            # API client
│   ├── dist/                    # Built output
│   ├── package.json             # Dependencies
│   └── vite.config.ts           # Vite config
│
├── flask-frontend/              # ⚠️ IGNORE - Testing only
│   └── (Simple Flask server for quick tests)
│
├── docs/                        # Documentation
│   ├── ARIEL_FULL_STORY.md      # The vision document
│   ├── SOCCER_AI_SYSTEM_ATLAS.md # Architecture diagrams
│   └── *.ctx                    # Context files
│
├── scripts/                     # Utility scripts
│   ├── seed_data.py             # Database seeding
│   └── fetch_espn.py            # ESPN data fetch
│
└── data/                        # Data files
    └── espn_*.json              # ESPN API responses
```

---

## Quick Start (PC)

### 1. Start Backend

```bash
cd soccer-AI/backend

# Install dependencies
pip install fastapi uvicorn anthropic aiohttp python-dotenv httpx

# Set API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Run server
uvicorn main:app --reload --port 8000
```

Backend will be at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 2. Start Frontend

```bash
cd soccer-AI/frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend will be at: `http://localhost:5173`

---

## API Endpoints (Key)

### Chat
```
POST /api/v1/chat
{
  "message": "How did Arsenal play?",
  "club_id": "arsenal"  // Optional: activates fan persona
}
```

### Predictions (NEW)
```
GET /api/v1/predictions/match/{home_team}/{away_team}
GET /api/v1/predictions/weekend
```

### Data
```
GET /api/v1/teams
GET /api/v1/standings
GET /api/v1/fixtures
GET /api/v1/fixtures/today
```

See `api_design.md` for full specification.

---

## The Predictor Module

**Location**: `backend/predictor/`

**What It Does**:
- ELO-style power ratings for all 20 Premier League teams
- Third Knowledge draw detection (6 patterns)
- Achieves **62.9% accuracy** on Premier League predictions

**Key Files**:
| File | Purpose |
|------|---------|
| `team_ratings.py` | Power rating system (0-100 scale) |
| `draw_detector.py` | 6 Third Knowledge patterns for draws |
| `backtest_ratings.py` | Validation on 70 real matches |
| `tune_draw_threshold.py` | Threshold optimization |

**Third Knowledge Patterns**:
1. `close_matchup` - Power diff < 10
2. `midtable_clash` - Both teams positions 8-15
3. `defensive_matchup` - Both teams defensive style
4. `parked_bus_risk` - Big favorite vs defensive underdog
5. `derby_caution` - Rivalry matches
6. `top_vs_top` - Top 6 clashes

---

## Fan Personas (20 Clubs - One Per PL Team)

Each Premier League club has a unique persona with:
- **Emotional state**: Tracks current mood based on results
- **Legends**: Club icons to reference
- **Moments**: Defining matches in history
- **Rivalries**: Who they hate and why
- **Vocabulary**: Club-specific terms

Example persona activation:
```
POST /api/v1/chat
{
  "message": "What do you think of Spurs?",
  "club_id": "arsenal"
}

Response: "Ah, the lot from down the lane? *chuckles* Look, we've
got 13 league titles. They've got... what exactly? That one year
they put the pressure on? North London is RED, always has been."
```

---

## Knowledge Graph

**Stats**: 41 nodes, 37 edges

**Node Types**:
- Teams (20)
- Legends (9+)
- Moments (12+)

**Edge Types**:
- `legendary_at`: Legend → Team
- `occurred_at`: Moment → Team
- `against`: Moment → Rival Team
- `rival_of`: Team ↔ Team

---

## Testing

```bash
cd backend

# Run all tests
python run_all_tests.sh

# Individual tests
python test_api.py
python test_kg.py
python test_hybrid_rag.py

# Test predictor
cd predictor
python backtest_ratings.py
python tune_draw_threshold.py
```

---

## Environment Variables

```bash
# backend/.env
ANTHROPIC_API_KEY=your-key-here
DATABASE_PATH=./soccer_ai.db
KG_DATABASE_PATH=./soccer_ai_kg.db
```

---

## Cost Model

- Haiku API: ~$0.002 per query
- 1000 queries/day: ~$2/day
- Monthly at scale: ~$60

---

## What PC Claude Should Do

1. **DO NOT** touch `flask-frontend/` - it's for testing only
2. **DO** build out `frontend/` React app
3. **DO** connect to FastAPI backend on port 8000
4. **DO** implement chat interface with club persona selection
5. **DO** add predictor display (predictions for upcoming matches)
6. **DO** preserve the emotional/fan personality in all UI copy

---

## The Vision (Remember This)

From ARIEL_FULL_STORY.md:

> "That lad on the tip of his toes, split second before Beckham's freekick.
> That's the feeling. That's always the feeling."

This is NOT a stats bot. This is a fan companion that:
- Celebrates victories with you
- Mourns losses with you
- Knows your rivals and hates them too
- Speaks authentic football language

**Fan at heart. Analyst in nature.**
