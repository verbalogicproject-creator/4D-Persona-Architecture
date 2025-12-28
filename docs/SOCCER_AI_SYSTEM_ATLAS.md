# Soccer-AI System Atlas

## Architecture Overview

```mermaid
graph TB
    subgraph "CLIENT LAYER"
        UI[React Frontend]
        API_CLIENT[API Client]
    end

    subgraph "API LAYER"
        FASTAPI[FastAPI Server]
        ROUTERS[Route Handlers]
        MIDDLEWARE[Security Middleware]
    end

    subgraph "INTELLIGENCE LAYER"
        RAG[Hybrid RAG Engine]
        AI_RESP[AI Response Generator]
        PERSONA[Fan Persona System]
    end

    subgraph "KNOWLEDGE GRAPH LAYER"
        KG_NODES[(kg_nodes)]
        KG_EDGES[(kg_edges)]
        TRAVERSAL[Graph Traversal]
        CONTEXT[Entity Context]
    end

    subgraph "DATA LAYER"
        FTS5[FTS5 Search]
        TEAMS[(teams)]
        LEGENDS[(club_legends)]
        MOMENTS[(club_moments)]
        MOOD[(club_mood)]
        RIVALRIES[(club_rivalries)]
    end

    subgraph "EXTERNAL"
        HAIKU[Claude Haiku API]
        ESPN[ESPN Data Feed]
    end

    UI --> API_CLIENT
    API_CLIENT --> FASTAPI
    FASTAPI --> ROUTERS
    ROUTERS --> MIDDLEWARE
    MIDDLEWARE --> RAG

    RAG --> FTS5
    RAG --> TRAVERSAL
    TRAVERSAL --> KG_NODES
    TRAVERSAL --> KG_EDGES
    CONTEXT --> MOOD

    RAG --> AI_RESP
    AI_RESP --> PERSONA
    AI_RESP --> HAIKU

    KG_NODES -.-> TEAMS
    KG_NODES -.-> LEGENDS
    KG_NODES -.-> MOMENTS
    KG_EDGES -.-> RIVALRIES
```

## Data Flow: Query to Response

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant SEC as Security
    participant RAG as Hybrid RAG
    participant KG as Knowledge Graph
    participant FTS as FTS5 Search
    participant AI as Haiku API

    U->>API: POST /api/v1/chat
    API->>SEC: detect_injection(query)

    alt Injection Detected
        SEC-->>U: snap_back_response
    else Clean Query
        SEC->>RAG: retrieve_hybrid(query)

        par Parallel Retrieval
            RAG->>FTS: search_all(query)
            RAG->>KG: extract_kg_entities(query)
            KG->>KG: traverse_kg(nodes)
            KG->>KG: get_entity_context()
        end

        RAG->>RAG: fuse_contexts(fts, kg, mood)
        RAG->>AI: generate_response_kg_rag()
        AI-->>U: relationship-aware response
    end
```

## Knowledge Graph Schema

```mermaid
erDiagram
    KG_NODES {
        int node_id PK
        string node_type
        int entity_id FK
        string name
        json properties
    }

    KG_EDGES {
        int edge_id PK
        int source_id FK
        int target_id FK
        string relationship
        float weight
        json properties
    }

    TEAMS {
        int id PK
        string name
        string league
    }

    CLUB_LEGENDS {
        int id PK
        int team_id FK
        string name
        string era
    }

    CLUB_MOMENTS {
        int id PK
        int team_id FK
        string title
        string emotion
    }

    CLUB_RIVALRIES {
        int id PK
        int team_id FK
        int rival_team_id FK
        int intensity
    }

    CLUB_MOOD {
        int id PK
        int team_id FK
        string current_mood
        float mood_intensity
    }

    KG_NODES ||--o{ KG_EDGES : "source_id"
    KG_NODES ||--o{ KG_EDGES : "target_id"
    KG_NODES }o--|| TEAMS : "entity_id (team)"
    KG_NODES }o--|| CLUB_LEGENDS : "entity_id (legend)"
    KG_NODES }o--|| CLUB_MOMENTS : "entity_id (moment)"
```

## Graph Relationship Types

```mermaid
graph LR
    subgraph "Node Types"
        TEAM((Team))
        LEGEND((Legend))
        MOMENT((Moment))
    end

    subgraph "Relationships"
        LEGEND -->|legendary_at| TEAM
        MOMENT -->|occurred_at| TEAM
        MOMENT -->|against| TEAM
        TEAM -->|rival_of| TEAM
    end

    style TEAM fill:#e74c3c
    style LEGEND fill:#f39c12
    style MOMENT fill:#3498db
```

## Module Responsibility Map

```mermaid
mindmap
  root((Soccer-AI))
    Backend
      database.py
        SQLite Connection
        FTS5 Search
        KG Schema
        KG Traversal
        CRUD Operations
      rag.py
        Entity Extraction
        Intent Detection
        FTS5 Retrieval
        KG Retrieval
        Context Fusion
      ai_response.py
        Security Layer
        Prompt Templates
        Haiku Integration
        KG-RAG Generation
        Cost Tracking
      main.py
        FastAPI App
        CORS Config
        Route Registration
    Data
      Teams & Players
      Games & Events
      Injuries & Transfers
      Club Personality
        Legends
        Moments
        Rivalries
        Mood
    Knowledge Graph
      41 Nodes
        20 Teams
        9 Legends
        12 Moments
      37 Edges
        legendary_at
        occurred_at
        against
        rival_of
```

## Security Flow (Session-Based Escalation)

```mermaid
stateDiagram-v2
    [*] --> NORMAL: New Session

    NORMAL --> WARNED: 1st Injection (0ms delay)
    WARNED --> CAUTIOUS: 2nd Injection (500ms delay)
    CAUTIOUS --> ESCALATED: 3rd Injection (1000ms delay)
    ESCALATED --> ESCALATED: More Injections (2000ms delay)

    ESCALATED --> PROBATION: Genuine Query
    PROBATION --> NORMAL: 5 Clean Queries
    PROBATION --> ESCALATED: Injection Attempt

    WARNED --> NORMAL: 5 Clean Queries
    CAUTIOUS --> NORMAL: 10 Clean Queries

    note right of NORMAL: snap_back response
    note right of ESCALATED: security_persona response
```

## Security Response Types

```mermaid
graph TD
    subgraph "Detection"
        QUERY[User Query] --> DETECT{Injection Pattern?}
    end

    subgraph "Session State"
        DETECT -->|Yes| STATE{Current State?}
        STATE -->|normal/warned/cautious| SNAP[Fan Snap-Back]
        STATE -->|escalated| SECURITY[Security Persona]
    end

    subgraph "Rate Limiting"
        SNAP --> DELAY1[+0-1000ms delay]
        SECURITY --> DELAY2[+2000ms delay]
    end

    subgraph "Logging"
        DELAY1 --> LOG[Log to security_log]
        DELAY2 --> LOG
        LOG --> RESPONSE[Return Response]
    end

    DETECT -->|No| CLEAN[Clean Query Processing]
    CLEAN --> RAG[Hybrid RAG]
    RAG --> RESPONSE

    style SECURITY fill:#e74c3c
    style SNAP fill:#f39c12
    style CLEAN fill:#27ae60
```

## Trivia System Flow

```mermaid
graph LR
    subgraph "Request"
        REQ[GET /trivia] --> PARAMS{team_id? difficulty?}
    end

    subgraph "Selection"
        PARAMS -->|Filter| QUERY[Query trivia_questions]
        QUERY --> RANDOM[Random Selection]
    end

    subgraph "Response"
        RANDOM --> FORMAT[Format Question]
        FORMAT --> HIDE[Hide correct_answer]
        HIDE --> CLIENT[Return to Client]
    end

    subgraph "Check"
        ANSWER[POST /trivia/check] --> VERIFY{Match?}
        VERIFY -->|Yes| CORRECT[✓ + Explanation]
        VERIFY -->|No| WRONG[✗ + Correct Answer]
    end

    style CORRECT fill:#27ae60
    style WRONG fill:#e74c3c
```

## Predictor Integration (IMPLEMENTED)

```mermaid
graph TB
    subgraph "Fan App (Soccer-AI)"
        FAN[Chat Interface]
        PERSONA[Fan Personas x18]
        TRIVIA[Trivia System]
        MOOD[(club_mood)]
    end

    subgraph "Predictor Module (backend/predictor/)"
        RATINGS[team_ratings.py]
        DRAWS[draw_detector.py]
        BACKTEST[backtest_ratings.py]
        TUNE[tune_draw_threshold.py]
    end

    subgraph "Third Knowledge Patterns"
        P1[close_matchup]
        P2[midtable_clash]
        P3[defensive_matchup]
        P4[parked_bus_risk]
        P5[derby_caution]
        P6[top_vs_top]
    end

    subgraph "Prediction Flow"
        RATINGS -->|power_diff| DRAWS
        P1 & P2 & P3 & P4 & P5 & P6 -->|patterns| DRAWS
        DRAWS -->|62.9% accuracy| FAN
    end

    subgraph "API Endpoints"
        API1[GET /predictions/match/home/away]
        API2[GET /predictions/weekend]
    end

    DRAWS --> API1
    DRAWS --> API2

    style RATINGS fill:#f39c12
    style DRAWS fill:#9b59b6
    style FAN fill:#3498db
```

### Predictor Accuracy Metrics

| Metric | Value |
|--------|-------|
| Overall Accuracy | **62.9%** |
| Base Power Ratings | 58.6% |
| Third Knowledge Boost | +4.3% |
| Draw Detection Recall | 36.4% |
| Draw Detection Precision | 47.1% |
| Optimal Threshold | 0.32 |

### Third Knowledge Pattern Details

| Pattern | Trigger Condition | Draw Boost |
|---------|-------------------|------------|
| `close_matchup` | Power diff < 10 | 1.3x - 1.8x |
| `midtable_clash` | Both teams positions 8-15 | 1.4x |
| `defensive_matchup` | Both teams defensive style | 1.35x |
| `parked_bus_risk` | Big favorite + defensive underdog | 1.25x |
| `derby_caution` | Rivalry match | 1.3x |
| `top_vs_top` | Both in top 6 | 1.25x |

## Gap Tracker Architecture

```mermaid
graph TD
    subgraph "Source Documents"
        DOCS[.md/.ctx files]
        SCHEMA[schema.sql]
        TESTS[test_*.py]
    end

    subgraph "Scanner"
        SCAN[scan_implementation_gaps.py]
        PARSE[Parse TODO/PENDING]
        COMPARE[Compare docs vs main.py]
    end

    subgraph "Database"
        GAPS[(implementation_gaps)]
    end

    subgraph "Admin API"
        GET[GET /admin/gaps]
        UPDATE[POST /admin/gaps/{id}/status]
    end

    DOCS --> SCAN
    SCHEMA --> SCAN
    TESTS --> SCAN
    SCAN --> PARSE
    PARSE --> COMPARE
    COMPARE --> GAPS

    GAPS --> GET
    UPDATE --> GAPS

    style GAPS fill:#e67e22
```

## Current Stats (Updated Dec 21, 2025)

| Metric | Value |
|--------|-------|
| KG Nodes | 41 |
| KG Edges | 37 |
| Fan Personas | **20** (one per Premier League club) |
| Clubs (Complete) | 20 (All Premier League) |
| Legends | 9+ |
| Moments | 12+ |
| Rivalries | 9 edges |
| Trivia Questions | 47 |
| Security States | 5 (normal→escalated) |
| Test Cases | 76+ |
| API Endpoints | 25+ |
| API Cost/Query | ~$0.002 |
| **Predictor Accuracy** | **62.9%** |
| Third Knowledge Patterns | 6 |

## File Structure

```
soccer-AI/
├── CLAUDE.md                    # Project instructions
├── README.md                    # Quick start guide
├── PC_HANDOFF_INSTRUCTIONS.ctx  # PC Claude briefing
├── schema.sql                   # Database schema
├── api_design.md               # API specification
├── docs/
│   ├── ARIEL_FULL_STORY.md              # Original vision document
│   ├── SOCCER_AI_SYSTEM_ATLAS.md        # This file
│   ├── UNIFIED_IMPLEMENTATION_PLAN.ctx  # Production plan
│   ├── KG_RAG_IMPLEMENTATION_PLAN.ctx   # KG-RAG details
│   └── FOOTBALL_AI_EXPANSION_ROADMAP.ctx
├── backend/
│   ├── main.py                 # FastAPI entry (54KB, 25+ endpoints)
│   ├── database.py             # DB + KG layer (65KB)
│   ├── rag.py                  # Hybrid RAG (34KB)
│   ├── ai_response.py          # AI generation + 20 personas (25KB)
│   ├── models.py               # Pydantic models
│   ├── security_session.py     # Injection protection
│   ├── soccer_ai.db            # SQLite database (335KB)
│   ├── soccer_ai_kg.db         # Knowledge graph (303KB)
│   ├── predictor/              # ⭐ Match prediction module
│   │   ├── team_ratings.py     # ELO-style power ratings
│   │   ├── draw_detector.py    # Third Knowledge patterns
│   │   ├── backtest_ratings.py # Validation (70 matches)
│   │   └── tune_draw_threshold.py # Threshold optimization
│   ├── kg/                     # Knowledge graph data
│   ├── routers/                # API route handlers
│   └── test_*.py               # Test files (10+)
├── frontend/                   # ✅ React app (build on PC)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── hooks/
│   │   └── services/
│   ├── dist/                   # Built output
│   └── package.json
└── flask-frontend/             # ⚠️ Testing only - ignore
    └── app.py
```
