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

## Security Flow

```mermaid
stateDiagram-v2
    [*] --> CLEAN: User Query
    CLEAN --> INJECTION_CHECK: Process

    INJECTION_CHECK --> BLOCKED: Pattern Match
    INJECTION_CHECK --> ALLOWED: No Pattern

    BLOCKED --> SNAP_BACK: Log Attempt
    SNAP_BACK --> [*]: Return In-Character Response

    ALLOWED --> KG_RAG: Continue
    KG_RAG --> RESPONSE: Generate
    RESPONSE --> [*]: Return AI Response
```

## Current Stats

| Metric | Value |
|--------|-------|
| KG Nodes | 41 |
| KG Edges | 37 |
| Clubs (Deep) | 3 (Arsenal, Chelsea, ManU) |
| Clubs (Basic) | 20 |
| Legends | 9 |
| Moments | 12 |
| Rivalries | 9 edges |
| API Cost/Query | ~$0.002 |

## File Structure

```
soccer-AI/
├── CLAUDE.md                    # Project instructions
├── schema.sql                   # Database schema
├── api_design.md               # API specification
├── docs/
│   ├── SOCCER_AI_SYSTEM_ATLAS.md        # This file
│   ├── UNIFIED_IMPLEMENTATION_PLAN.ctx  # Production plan
│   ├── KG_RAG_IMPLEMENTATION_PLAN.ctx   # KG-RAG details
│   ├── FOOTBALL_AI_EXPANSION_ROADMAP.ctx
│   └── REMAINING_PHASES_PRESERVED.ctx
├── backend/
│   ├── main.py                 # FastAPI entry
│   ├── database.py             # DB + KG layer
│   ├── rag.py                  # Hybrid RAG
│   ├── ai_response.py          # AI generation
│   ├── models.py               # Pydantic models
│   ├── soccer_ai.db            # SQLite database
│   ├── test_kg.py              # KG tests
│   ├── test_hybrid_rag.py      # Hybrid tests
│   └── test_kg_rag_demo.py     # Full demo
└── frontend/                   # (Separate Plan)
    └── [React App]
```
