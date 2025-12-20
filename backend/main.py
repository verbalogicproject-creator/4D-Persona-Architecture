"""
Soccer-AI FastAPI Application
Main entry point for the backend API
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import database
import rag
import ai_response
from models import (
    ChatRequest, ChatResponse, ChatSource,
    ApiResponse, PaginatedMeta, SearchResults, DbStats,
    TeamBase, TeamDetail, PlayerBase, PlayerDetail, PlayerStats,
    GameBase, GameDetail, InjuryBase, TransferBase, StandingEntry,
    NewsArticle, ErrorResponse, ErrorDetail
)

# ============================================
# APP INITIALIZATION
# ============================================

app = FastAPI(
    title="Soccer-AI",
    description="Living knowledge base with AI-powered chat for soccer information",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation storage (use Redis in production)
conversations = {}


# ============================================
# STARTUP/SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    if not Path(database.DB_PATH).exists():
        database.init_db()
    # Initialize analytics table (CP6)
    database.init_analytics()
    print(f"Soccer-AI started. Database: {database.DB_PATH}")


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ============================================
# CHAT ENDPOINT (Primary Interface)
# ============================================

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint. User asks natural language question, gets AI response.
    Uses KG-RAG hybrid retrieval and logs analytics.
    """
    import time
    start_time = time.time()

    try:
        # Get or create conversation
        conv_id = request.conversation_id or str(uuid.uuid4())
        history = conversations.get(conv_id, [])

        # Check for injection attempt first
        is_injection, pattern = ai_response.detect_injection(request.message)

        if is_injection:
            # Log injection attempt
            database.log_query(
                query=request.message,
                was_injection_attempt=True,
                response_time_ms=int((time.time() - start_time) * 1000)
            )
            # Return snap-back response
            snap_back = ai_response.get_snap_back_response("default")
            return ChatResponse(
                response=snap_back,
                conversation_id=conv_id,
                sources=[],
                confidence=0.0
            )

        # KG-RAG hybrid retrieval (upgraded from basic RAG)
        context, sources, metadata = rag.retrieve_hybrid(request.message)

        # Generate AI response (KG-aware)
        result = ai_response.generate_response(
            query=request.message,
            context=context,
            sources=sources,
            conversation_history=history
        )

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Log query analytics (CP6)
        try:
            # Extract first club from entities if available
            club_detected = None
            entities = metadata.get('entities', {})
            teams = entities.get('teams', [])
            if teams:
                club_detected = teams[0]

            database.log_query(
                query=request.message,
                kg_intent=metadata.get('kg_intent'),
                club_detected=club_detected,
                kg_nodes_used=entities.get('kg_nodes', 0) if isinstance(entities.get('kg_nodes'), int) else len(entities.get('kg_nodes', [])),
                source_count=len(sources),
                confidence=result.get('confidence'),
                response_time_ms=response_time_ms,
                was_injection_attempt=False
            )
        except Exception:
            pass  # Don't fail on analytics errors

        # Update conversation history
        history.append({"role": "user", "content": request.message})
        history.append({"role": "assistant", "content": result["response"]})
        conversations[conv_id] = history[-10:]  # Keep last 10 messages

        # Format sources
        formatted_sources = [
            ChatSource(type=s["type"], id=s.get("id"))
            for s in sources
        ]

        return ChatResponse(
            response=result["response"],
            conversation_id=conv_id,
            sources=formatted_sources,
            confidence=result.get("confidence", 0.5),
            usage=result.get("usage")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TEAMS ENDPOINTS
# ============================================

@app.get("/api/v1/teams")
async def list_teams(
    league: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List teams with optional filtering."""
    teams = database.get_teams(limit=limit, offset=offset, league=league)
    return ApiResponse(
        data=teams,
        meta={"limit": limit, "offset": offset, "timestamp": datetime.utcnow().isoformat()}
    )


@app.get("/api/v1/teams/{team_id}")
async def get_team(team_id: int):
    """Get team by ID."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return ApiResponse(data=team)


@app.get("/api/v1/teams/{team_id}/squad")
async def get_team_squad(team_id: int):
    """Get team's player squad."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    players = database.get_players(team_id=team_id, limit=50)
    return ApiResponse(data={"team": team, "players": players})


@app.get("/api/v1/teams/{team_id}/fixtures")
async def get_team_fixtures(team_id: int, limit: int = 5):
    """Get team's upcoming fixtures."""
    fixtures = database.get_upcoming_games(team_id, limit=limit)
    return ApiResponse(data=fixtures)


@app.get("/api/v1/teams/{team_id}/results")
async def get_team_results(team_id: int, limit: int = 5):
    """Get team's recent results."""
    results = database.get_recent_games(team_id, limit=limit)
    return ApiResponse(data=results)


# ============================================
# PLAYERS ENDPOINTS
# ============================================

@app.get("/api/v1/players")
async def list_players(
    team_id: Optional[int] = None,
    position: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List players with optional filtering."""
    players = database.get_players(
        limit=limit, offset=offset,
        team_id=team_id, position=position
    )
    return ApiResponse(
        data=players,
        meta={"limit": limit, "offset": offset, "timestamp": datetime.utcnow().isoformat()}
    )


@app.get("/api/v1/players/{player_id}")
async def get_player(player_id: int):
    """Get player by ID."""
    player = database.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return ApiResponse(data=player)


@app.get("/api/v1/players/{player_id}/stats")
async def get_player_stats(player_id: int, season: Optional[str] = None):
    """Get player statistics."""
    player = database.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    stats = database.get_player_stats(player_id, season)
    return ApiResponse(data={"player": player, "stats": stats})


@app.get("/api/v1/players/search")
async def search_players(q: str, limit: int = 10):
    """Search players by name."""
    players = database.search_players(q, limit=limit)
    return ApiResponse(data=players)


# ============================================
# GAMES ENDPOINTS
# ============================================

@app.get("/api/v1/games")
async def list_games(
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List games with optional filtering."""
    games = database.get_games(
        limit=limit, offset=offset,
        team_id=team_id, status=status,
        date_from=date_from, date_to=date_to
    )
    return ApiResponse(
        data=games,
        meta={"limit": limit, "offset": offset, "timestamp": datetime.utcnow().isoformat()}
    )


@app.get("/api/v1/games/{game_id}")
async def get_game(game_id: int):
    """Get game by ID with events."""
    game = database.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return ApiResponse(data=game)


@app.get("/api/v1/games/live")
async def get_live_games():
    """Get currently live games."""
    games = database.get_games(status="live", limit=20)
    return ApiResponse(data=games)


@app.get("/api/v1/games/today")
async def get_today_games():
    """Get today's games."""
    today = datetime.now().strftime("%Y-%m-%d")
    games = database.get_games(date_from=today, date_to=today, limit=50)
    return ApiResponse(data=games)


@app.get("/api/v1/games/upcoming")
async def get_upcoming_games(limit: int = 20):
    """Get upcoming games."""
    games = database.get_games(status="scheduled", limit=limit)
    return ApiResponse(data=games)


# ============================================
# INJURIES ENDPOINTS
# ============================================

@app.get("/api/v1/injuries")
async def list_injuries(
    team_id: Optional[int] = None,
    status: str = "active",
    limit: int = 50
):
    """List injuries with optional filtering."""
    injuries = database.get_injuries(team_id=team_id, status=status, limit=limit)
    return ApiResponse(data=injuries)


@app.get("/api/v1/injuries/active")
async def get_active_injuries(limit: int = 50):
    """Get all active injuries."""
    injuries = database.get_injuries(status="active", limit=limit)
    return ApiResponse(data=injuries)


@app.get("/api/v1/injuries/team/{team_id}")
async def get_team_injuries(team_id: int):
    """Get injuries for a specific team."""
    injuries = database.get_injuries(team_id=team_id, status="active")
    return ApiResponse(data=injuries)


# ============================================
# TRANSFERS ENDPOINTS
# ============================================

@app.get("/api/v1/transfers")
async def list_transfers(
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """List transfers with optional filtering."""
    transfers = database.get_transfers(team_id=team_id, status=status, limit=limit)
    return ApiResponse(data=transfers)


@app.get("/api/v1/transfers/recent")
async def get_recent_transfers(limit: int = 20):
    """Get recent completed transfers."""
    transfers = database.get_transfers(status="completed", limit=limit)
    return ApiResponse(data=transfers)


@app.get("/api/v1/transfers/rumors")
async def get_transfer_rumors(limit: int = 20):
    """Get transfer rumors."""
    transfers = database.get_transfers(status="rumor", limit=limit)
    return ApiResponse(data=transfers)


@app.get("/api/v1/transfers/team/{team_id}")
async def get_team_transfers(team_id: int):
    """Get transfers for a specific team."""
    transfers = database.get_transfers(team_id=team_id, limit=50)
    return ApiResponse(data=transfers)


# ============================================
# STANDINGS ENDPOINTS
# ============================================

@app.get("/api/v1/standings/{league}")
async def get_standings(league: str, season: str = "2024-25"):
    """Get league standings."""
    standings = database.get_standings(league, season)
    return ApiResponse(data=standings)


# ============================================
# LEGENDS ENDPOINTS
# ============================================

@app.get("/api/v1/legends")
async def list_legends(
    team_id: Optional[int] = None,
    limit: int = Query(default=50, ge=1, le=100)
):
    """List club legends with optional team filtering."""
    legends = database.get_legends(team_id=team_id, limit=limit)
    return ApiResponse(data=legends)


@app.get("/api/v1/legends/{legend_id}")
async def get_legend(legend_id: int):
    """Get legend by ID."""
    legend = database.get_legend(legend_id)
    if not legend:
        raise HTTPException(status_code=404, detail="Legend not found")
    return ApiResponse(data=legend)


@app.get("/api/v1/legends/search/{query}")
async def search_legends(query: str, limit: int = 10):
    """Search legends by name."""
    legends = database.search_legends(query, limit=limit)
    return ApiResponse(data=legends)


@app.get("/api/v1/teams/{team_id}/legends")
async def get_team_legends(team_id: int):
    """Get all legends for a team."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    legends = database.get_legends(team_id=team_id)
    return ApiResponse(data={"team": team, "legends": legends})


# ============================================
# CLUB PERSONALITY ENDPOINTS
# ============================================

@app.get("/api/v1/teams/{team_id}/identity")
async def get_team_identity(team_id: int):
    """Get club identity/personality."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    identity = database.get_club_identity(team_id)
    return ApiResponse(data={"team": team, "identity": identity})


@app.get("/api/v1/teams/{team_id}/moments")
async def get_team_moments(team_id: int, limit: int = 20):
    """Get iconic moments for a club."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    moments = database.get_club_moments(team_id, limit=limit)
    return ApiResponse(data={"team": team, "moments": moments})


@app.get("/api/v1/teams/{team_id}/rivalries")
async def get_team_rivalries(team_id: int):
    """Get rivalries for a club."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    rivalries = database.get_club_rivalries(team_id)
    return ApiResponse(data={"team": team, "rivalries": rivalries})


@app.get("/api/v1/teams/{team_id}/mood")
async def get_team_mood(team_id: int):
    """Get current mood for a club."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    mood = database.get_club_mood(team_id)
    return ApiResponse(data={"team": team, "mood": mood})


@app.get("/api/v1/teams/{team_id}/personality")
async def get_team_full_personality(team_id: int):
    """Get complete club personality (identity + mood + rivalries + moments)."""
    team = database.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return ApiResponse(data={
        "team": team,
        "identity": database.get_club_identity(team_id),
        "mood": database.get_club_mood(team_id),
        "rivalries": database.get_club_rivalries(team_id),
        "moments": database.get_club_moments(team_id, limit=5),
        "legends": database.get_legends(team_id=team_id, limit=5)
    })


# ============================================
# SEARCH ENDPOINT
# ============================================

@app.get("/api/v1/search")
async def search(
    q: str,
    type: str = "all",
    limit: int = 10
):
    """Unified search across all entities."""
    if type == "all":
        results = database.search_all(q, limit=limit)
    elif type == "players":
        results = {"players": database.search_players(q, limit=limit)}
    elif type == "teams":
        results = {"teams": database.search_teams(q, limit=limit)}
    elif type == "news":
        results = {"news": database.search_news(q, limit=limit)}
    else:
        results = database.search_all(q, limit=limit)

    total = sum(len(v) for v in results.values())

    return ApiResponse(
        data=SearchResults(query=q, results=results, total=total)
    )


# ============================================
# ADMIN ENDPOINTS
# ============================================

@app.get("/api/v1/admin/stats")
async def get_db_stats():
    """Get database statistics."""
    stats = database.get_db_stats()
    return ApiResponse(data=stats)


# ============================================
# ANALYTICS ENDPOINTS (CP6)
# ============================================

@app.get("/api/v1/analytics")
async def get_analytics(days: int = Query(default=7, ge=1, le=30)):
    """Get query analytics summary."""
    try:
        summary = database.get_analytics_summary(days=days)
        return ApiResponse(data=summary)
    except Exception as e:
        # Table might not exist yet
        return ApiResponse(data={
            "error": "Analytics not initialized",
            "message": str(e)
        })


@app.get("/api/v1/analytics/recent")
async def get_recent_analytics(limit: int = Query(default=20, ge=1, le=100)):
    """Get recent queries for debugging."""
    try:
        queries = database.get_recent_queries(limit=limit)
        return ApiResponse(data=queries)
    except Exception:
        return ApiResponse(data=[])


@app.get("/api/v1/analytics/hot")
async def get_hot_analytics(
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get most common query patterns."""
    try:
        hot = database.get_hot_queries(days=days, limit=limit)
        return ApiResponse(data=hot)
    except Exception:
        return ApiResponse(data=[])


# ============================================
# KNOWLEDGE GRAPH VISUALIZATION (CP7)
# ============================================

# Static file route for KG viewer
STATIC_DIR = Path(__file__).parent / "static"

@app.get("/kg-viewer")
async def kg_viewer():
    """Serve the Knowledge Graph visualization page."""
    viewer_path = STATIC_DIR / "kg_viewer.html"
    if viewer_path.exists():
        return FileResponse(viewer_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="KG Viewer not found")


@app.get("/api/v1/graph")
async def get_full_graph():
    """
    Get full Knowledge Graph in vis.js format.

    Returns nodes, edges, and stats for visualization.
    """
    try:
        graph = database.export_kg_to_vis_json()
        return ApiResponse(data=graph)
    except Exception as e:
        return ApiResponse(
            success=False,
            error={"code": "KG_EXPORT_ERROR", "message": str(e)}
        )


@app.get("/api/v1/graph/subgraph/{node_id}")
async def get_subgraph(
    node_id: str,
    depth: int = Query(default=1, ge=0, le=3)
):
    """
    Get subgraph centered on a specific node.

    Useful for focused visualizations.
    - depth=0: Just the center node
    - depth=1: Center + immediate connections
    - depth=2: Two hops out
    - depth=3: Three hops (max)
    """
    try:
        # Handle both integer and string node IDs
        try:
            node_id_int = int(node_id)
            node_id_actual = str(node_id_int)
        except ValueError:
            node_id_actual = node_id

        subgraph = database.export_kg_subgraph(node_id_actual, depth=depth)
        return ApiResponse(data=subgraph)
    except Exception as e:
        return ApiResponse(
            success=False,
            error={"code": "SUBGRAPH_ERROR", "message": str(e)}
        )


@app.get("/api/v1/graph/team/{team_id}")
async def get_team_graph(
    team_id: int,
    depth: int = Query(default=1, ge=0, le=3)
):
    """
    Get subgraph for a team by team ID.

    Convenience endpoint that looks up team's KG node.
    """
    try:
        # Get team name
        team = database.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Find KG node
        node = database.find_kg_node_by_name(team["name"])
        if not node:
            return ApiResponse(data={
                "nodes": [],
                "edges": [],
                "message": f"Team {team['name']} not in Knowledge Graph"
            })

        subgraph = database.export_kg_subgraph(node["node_id"], depth=depth)
        subgraph["team"] = team
        return ApiResponse(data=subgraph)
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            error={"code": "TEAM_GRAPH_ERROR", "message": str(e)}
        )


# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "meta": None,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "meta": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc)
            }
        }
    )


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
