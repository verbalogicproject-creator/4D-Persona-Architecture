# Soccer-AI API Contracts

**Generated**: 2025-12-21
**Backend**: FastAPI (port 8000)
**Total Endpoints**: 50+

---

## Response Wrapper (All Endpoints)

```typescript
interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  meta?: {
    limit?: number;
    offset?: number;
    timestamp?: string;
    [key: string]: any;
  };
  error?: {
    code: string;
    message: string;
  };
}
```

---

## 1. CHAT (Primary Interface) ⭐

### POST /api/v1/chat

**Request:**
```typescript
interface ChatRequest {
  message: string;           // 1-1000 chars
  conversation_id?: string;  // Optional, creates new if omitted
  club?: string;             // Fan persona: "arsenal", "chelsea", etc.
}
```

**Response:**
```typescript
interface ChatResponse {
  response: string;
  conversation_id: string;
  sources: Array<{
    type: string;
    id?: number;
  }>;
  confidence: number;        // 0-1
  usage?: {
    input_tokens: number;
    output_tokens: number;
  };
}
```

**Valid Clubs:**
```
arsenal, chelsea, manchester_united, liverpool, manchester_city,
tottenham, newcastle, west_ham, everton, brighton, aston_villa,
wolves, crystal_palace, fulham, nottingham_forest, brentford,
bournemouth, leicester, analyst (neutral)
```

---

## 2. CLUBS & PERSONAS ⭐

### GET /api/v1/clubs

**Response:**
```typescript
interface Club {
  id: string;      // "arsenal"
  name: string;    // "Arsenal"
}
// Returns: ApiResponse<Club[]>
```

### GET /api/v1/personas

**Response:**
```typescript
interface Persona {
  club_key: string;
  team_id: number;
  display_name: string;
  identity: {
    nickname?: string;
    founded?: number;
    stadium?: string;
    colors?: string;
    philosophy?: string;
  };
  mood: {
    current_mood: string;      // "optimistic", "anxious", etc.
    intensity: number;         // 0-1
    last_updated: string;
  };
}
// Returns: ApiResponse<{ personas: Persona[], total: number }>
```

---

## 3. TEAMS

### GET /api/v1/teams

**Query Params:** `league?`, `limit?` (1-100), `offset?`

**Response:**
```typescript
interface Team {
  id: number;
  name: string;
  short_name?: string;
  league: string;
  country: string;
  stadium?: string;
  founded?: number;
  logo_url?: string;
}
// Returns: ApiResponse<Team[]>
```

### GET /api/v1/teams/{team_id}

Returns single `Team` with same shape.

### GET /api/v1/teams/{team_id}/personality

**Response (Full Club Context):**
```typescript
{
  team: Team;
  identity: {
    nickname?: string;
    founded?: number;
    stadium?: string;
    manager?: string;
    philosophy?: string;
  };
  mood: {
    current_mood: string;
    intensity: number;
  };
  rivalries: Array<{
    rival_team_id: number;
    rival_name: string;
    rivalry_name: string;
    intensity: number;        // 1-10
  }>;
  moments: Array<{
    id: number;
    title: string;
    date: string;
    emotion: string;
    description: string;
  }>;
  legends: Array<{
    id: number;
    name: string;
    position: string;
    years_active: string;
  }>;
}
```

---

## 4. FIXTURES & GAMES ⭐

### GET /api/v1/games/today

**Response:**
```typescript
interface Game {
  id: number;
  date: string;              // "YYYY-MM-DD"
  time?: string;             // "HH:MM"
  status: string;            // "scheduled", "live", "finished"
  home_team_id: number;
  home_team_name: string;
  home_team_short?: string;
  away_team_id: number;
  away_team_name: string;
  away_team_short?: string;
  home_score?: number;
  away_score?: number;
  competition?: string;
  venue?: string;
}
// Returns: ApiResponse<Game[]>
```

### GET /api/v1/games/upcoming

Same response shape as above.

### GET /api/v1/games/live

Same response shape (filtered to live matches).

---

## 5. STANDINGS ⭐

### GET /api/v1/standings/{league}

**Query Params:** `season?` (default: "2024-25")

**Response:**
```typescript
interface StandingEntry {
  position: number;
  team_id: number;
  team_name: string;
  short_name?: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  form?: string;             // "WWDLW" - last 5 results
}
// Returns: ApiResponse<StandingEntry[]>
```

---

## 6. PREDICTIONS ⭐

### POST /api/v1/predict

**Query Params:**
- `home_team` (string)
- `away_team` (string)
- `favorite` (string)
- `underdog` (string)
- `match_date?` (string)

**Response:**
```typescript
interface Prediction {
  home_team: string;
  away_team: string;
  favorite: string;
  underdog: string;
  side_a_score: number;      // Favorite weakness (0-100)
  side_b_score: number;      // Underdog strength (0-100)
  base_upset_prob: number;   // 0-1
  pattern_multiplier: number;
  final_upset_prob: number;  // 0-1
  patterns_triggered: Array<{
    name: string;
    multiplier: number;
    confidence: number;
  }>;
  confidence_level: string;  // "low", "medium", "high"
  key_insight: string;
}
```

### GET /api/v1/predict/patterns

**Response:**
```typescript
interface Pattern {
  name: string;
  description: string;
  factor_a: string;
  factor_b: string;
  interaction_type: string;
  multiplier: number;
  confidence: number;
}
// Returns: ApiResponse<{ patterns: Pattern[], total: number }>
```

### GET /api/v1/match/preview/{home_team_id}/{away_team_id}

**Response (Bridge Endpoint):**
```typescript
{
  match: {
    home_team: Team;
    away_team: Team;
    is_derby: boolean;
    derby_info?: object;
  };
  fan_context: {
    home: { identity: object; mood: object };
    away: { identity: object; mood: object };
  };
  predictor_context: {
    home_insights: object[];
    away_insights: object[];
    prediction: Prediction;
  };
  talking_points: string[];
}
```

---

## 7. LEGENDS

### GET /api/v1/legends

**Query Params:** `team_id?`, `limit?`

**Response:**
```typescript
interface Legend {
  id: number;
  name: string;
  team_id?: number;
  position?: string;
  years_active?: string;
  achievements?: string;
  defining_moment?: string;
  legacy_description?: string;
}
// Returns: ApiResponse<Legend[]>
```

### POST /api/v1/legends/{legend_id}/tell-story

**Query Params:** `angle` ("career" | "moment" | "legacy")

**Response:**
```typescript
{
  legend: Legend;
  story: string;             // AI-generated narrative
  angle: string;
  team: Team;
}
```

---

## 8. TRIVIA

### GET /api/v1/trivia

**Query Params:** `team_id?`, `category?`, `difficulty?`

**Response:**
```typescript
interface TriviaQuestion {
  id: number;
  question: string;
  options: string[];
  difficulty: string;        // "easy", "medium", "hard", "expert"
  category: string;
  team_id?: number;
  // Note: correct_answer is hidden
}
// Returns: ApiResponse<TriviaQuestion>
```

### POST /api/v1/trivia/check

**Query Params:** `question_id`, `answer`

**Response:**
```typescript
{
  correct: boolean;
  correct_answer: string;
  explanation?: string;
}
```

---

## 9. SEARCH

### GET /api/v1/search

**Query Params:** `q` (required), `type?` ("all"|"players"|"teams"|"news"), `limit?`

**Response:**
```typescript
{
  query: string;
  results: {
    players?: Player[];
    teams?: Team[];
    news?: NewsArticle[];
  };
  total: number;
}
```

---

## 10. BANTER & DERBIES

### GET /api/v1/banter/{team1}/{team2}

**Response:**
```typescript
{
  team1: string;
  team2: string;
  banter: {
    [team1]_says: string;
    [team2]_says: string;
    neutral: string;
  };
  is_historic_rivalry: boolean;
}
```

### GET /api/v1/derby/{city}

**Cities:** london, manchester, merseyside, tyne-wear

**Response:**
```typescript
{
  city: string;
  derby: {
    name: string;
    teams: string[];
    key_matches: Array<{
      name: string;
      teams: string[];
      intensity: number;
    }>;
    description: string;
  };
  teams: Array<{
    team: Team;
    mood: object;
  }>;
}
```

---

## 11. KNOWLEDGE GRAPH

### GET /api/v1/graph

**Response (vis.js format):**
```typescript
{
  nodes: Array<{
    id: string;
    label: string;
    type: string;            // "team", "legend", "moment"
    color: string;
  }>;
  edges: Array<{
    from: string;
    to: string;
    label: string;           // "legendary_at", "rival_of", etc.
  }>;
  stats: {
    node_count: number;
    edge_count: number;
  };
}
```

---

## 12. ANALYTICS & ADMIN

### GET /api/v1/admin/stats

**Response:**
```typescript
{
  teams: number;
  players: number;
  games: number;
  player_stats: number;
  injuries: number;
  transfers: number;
  standings: number;
  news: number;
  game_events: number;
}
```

### GET /api/v1/metrics

**Response:**
```typescript
{
  analytics: object;
  database: DbStats;
  security: object;
  timestamp: string;
}
```

---

## 13. HEALTH

### GET /health

**Response:**
```typescript
{
  status: "healthy";
  timestamp: string;
}
```

---

## Error Responses

All errors follow this format:
```typescript
{
  success: false;
  data: null;
  meta: null;
  error: {
    code: string;            // "HTTP_404", "INTERNAL_ERROR", etc.
    message: string;
  };
}
```

---

## Key Frontend Pages & Required Endpoints

| Page | Primary Endpoints |
|------|-------------------|
| **Chat** | POST /api/v1/chat, GET /api/v1/clubs |
| **Fixtures** | GET /api/v1/games/today, /upcoming |
| **Standings** | GET /api/v1/standings/premier-league |
| **Predictions** | GET /api/v1/match/preview/{h}/{a} |
| **Team Profile** | GET /api/v1/teams/{id}/personality |
| **Trivia** | GET /api/v1/trivia, POST /api/v1/trivia/check |
