"""
Soccer-AI Database Module
SQLite + FTS5 for knowledge base and RAG retrieval
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime, date

# Database path
DB_PATH = Path(__file__).parent / "soccer_ai.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return dicts instead of tuples
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database with schema."""
    with get_connection() as conn:
        with open(SCHEMA_PATH, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
    print(f"Database initialized at {DB_PATH}")


def dict_from_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert sqlite3.Row to dict."""
    return dict(row) if row else None


# ============================================
# TEAM OPERATIONS
# ============================================

def get_teams(limit: int = 20, offset: int = 0, league: Optional[str] = None) -> List[Dict]:
    """Get list of teams with optional filtering."""
    with get_connection() as conn:
        query = "SELECT * FROM teams"
        params = []

        if league:
            query += " WHERE league = ?"
            params.append(league)

        query += " ORDER BY name LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        return [dict_from_row(row) for row in cursor.fetchall()]


def get_team(team_id: int) -> Optional[Dict]:
    """Get single team by ID."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
        return dict_from_row(cursor.fetchone())


def get_team_by_name(name: str) -> Optional[Dict]:
    """Get team by name (case-insensitive)."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM teams WHERE LOWER(name) = LOWER(?) OR LOWER(short_name) = LOWER(?)",
            (name, name)
        )
        return dict_from_row(cursor.fetchone())


# ============================================
# PLAYER OPERATIONS
# ============================================

def get_players(
    limit: int = 20,
    offset: int = 0,
    team_id: Optional[int] = None,
    position: Optional[str] = None
) -> List[Dict]:
    """Get list of players with optional filtering."""
    with get_connection() as conn:
        query = "SELECT p.*, t.name as team_name FROM players p LEFT JOIN teams t ON p.team_id = t.id"
        conditions = []
        params = []

        if team_id:
            conditions.append("p.team_id = ?")
            params.append(team_id)
        if position:
            conditions.append("p.position = ?")
            params.append(position)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY p.name LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        return [dict_from_row(row) for row in cursor.fetchall()]


def get_player(player_id: int) -> Optional[Dict]:
    """Get single player by ID with team info."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT p.*, t.name as team_name, t.league
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.id
            WHERE p.id = ?
        """, (player_id,))
        return dict_from_row(cursor.fetchone())


def get_player_stats(player_id: int, season: Optional[str] = None) -> Dict:
    """Get player statistics summary."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                COUNT(*) as games,
                SUM(goals) as total_goals,
                SUM(assists) as total_assists,
                AVG(rating) as avg_rating,
                SUM(minutes_played) as total_minutes,
                SUM(yellow_cards) as yellow_cards,
                SUM(red_cards) as red_cards
            FROM player_stats
            WHERE player_id = ?
        """, (player_id,))
        return dict_from_row(cursor.fetchone())


# ============================================
# GAME OPERATIONS
# ============================================

def get_games(
    limit: int = 20,
    offset: int = 0,
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict]:
    """Get list of games with optional filtering."""
    with get_connection() as conn:
        query = """
            SELECT g.*,
                   ht.name as home_team_name, ht.short_name as home_team_short,
                   at.name as away_team_name, at.short_name as away_team_short
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
        """
        conditions = []
        params = []

        if team_id:
            conditions.append("(g.home_team_id = ? OR g.away_team_id = ?)")
            params.extend([team_id, team_id])
        if status:
            conditions.append("g.status = ?")
            params.append(status)
        if date_from:
            conditions.append("g.date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("g.date <= ?")
            params.append(date_to)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY g.date DESC, g.time DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        return [dict_from_row(row) for row in cursor.fetchall()]


def get_game(game_id: int) -> Optional[Dict]:
    """Get single game with full details."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT g.*,
                   ht.name as home_team_name, ht.short_name as home_team_short,
                   at.name as away_team_name, at.short_name as away_team_short
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            WHERE g.id = ?
        """, (game_id,))
        game = dict_from_row(cursor.fetchone())

        if game:
            # Get events
            events_cursor = conn.execute("""
                SELECT ge.*, p.name as player_name
                FROM game_events ge
                LEFT JOIN players p ON ge.player_id = p.id
                WHERE ge.game_id = ?
                ORDER BY ge.minute
            """, (game_id,))
            game['events'] = [dict_from_row(row) for row in events_cursor.fetchall()]

        return game


def get_recent_games(team_id: int, limit: int = 5) -> List[Dict]:
    """Get team's recent finished games."""
    return get_games(limit=limit, team_id=team_id, status='finished')


def get_upcoming_games(team_id: int, limit: int = 5) -> List[Dict]:
    """Get team's upcoming scheduled games."""
    today = date.today().isoformat()
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT g.*,
                   ht.name as home_team_name,
                   at.name as away_team_name
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            WHERE (g.home_team_id = ? OR g.away_team_id = ?)
              AND g.date >= ?
              AND g.status = 'scheduled'
            ORDER BY g.date ASC
            LIMIT ?
        """, (team_id, team_id, today, limit))
        return [dict_from_row(row) for row in cursor.fetchall()]


# ============================================
# INJURY OPERATIONS
# ============================================

def get_injuries(
    team_id: Optional[int] = None,
    status: str = 'active',
    limit: int = 50
) -> List[Dict]:
    """Get injuries with optional filtering."""
    with get_connection() as conn:
        query = """
            SELECT i.*, p.name as player_name, t.name as team_name
            FROM injuries i
            JOIN players p ON i.player_id = p.id
            LEFT JOIN teams t ON p.team_id = t.id
            WHERE i.status = ?
        """
        params = [status]

        if team_id:
            query += " AND p.team_id = ?"
            params.append(team_id)

        query += " ORDER BY i.occurred_date DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        return [dict_from_row(row) for row in cursor.fetchall()]


# ============================================
# TRANSFER OPERATIONS
# ============================================

def get_transfers(
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Dict]:
    """Get transfers with optional filtering."""
    with get_connection() as conn:
        query = """
            SELECT tr.*,
                   p.name as player_name,
                   ft.name as from_team_name,
                   tt.name as to_team_name
            FROM transfers tr
            JOIN players p ON tr.player_id = p.id
            LEFT JOIN teams ft ON tr.from_team_id = ft.id
            LEFT JOIN teams tt ON tr.to_team_id = tt.id
        """
        conditions = []
        params = []

        if team_id:
            conditions.append("(tr.from_team_id = ? OR tr.to_team_id = ?)")
            params.extend([team_id, team_id])
        if status:
            conditions.append("tr.status = ?")
            params.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY tr.announced_date DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        return [dict_from_row(row) for row in cursor.fetchall()]


# ============================================
# STANDINGS OPERATIONS
# ============================================

def get_standings(league: str, season: str = "2024-25") -> List[Dict]:
    """Get league standings."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT s.*, t.name as team_name, t.short_name
            FROM standings s
            JOIN teams t ON s.team_id = t.id
            WHERE s.league = ? AND s.season = ?
            ORDER BY s.position ASC
        """, (league, season))
        return [dict_from_row(row) for row in cursor.fetchall()]


# ============================================
# FTS5 SEARCH (RAG RETRIEVAL)
# ============================================

def escape_fts_query(query: str) -> str:
    """
    Escape special characters and reserved words for FTS5 queries.

    FTS5 has reserved boolean operators (OR, AND, NOT) that cause syntax errors
    if they appear in user queries. We wrap each token in double quotes to treat
    them as literals.

    Bug fix: Insight #927 - FTS5 reserved word collision
    Bug fix: Insight #929 - Null bytes and control character sanitization
    """
    # First: Remove null bytes and control characters (security)
    escaped = ''.join(c for c in query if ord(c) >= 32 or c in '\t\n\r')

    # Second: Remove HTML-like tags (XSS prevention)
    import re
    escaped = re.sub(r'<[^>]*>', ' ', escaped)

    # Third: Remove FTS5 special characters
    special_chars = ['?', '*', '"', "'", '(', ')', '[', ']', '{', '}', ':', '^', '-', '!', '&', '|', '<', '>']
    for char in special_chars:
        escaped = escaped.replace(char, ' ')

    # Clean up multiple spaces and get tokens
    tokens = escaped.split()

    if not tokens:
        return ""

    # FTS5 reserved words that cause syntax errors
    reserved_words = {'OR', 'AND', 'NOT', 'NEAR'}

    # Wrap each token in double quotes to treat as literal
    # This prevents OR/AND/NOT from being interpreted as boolean operators
    quoted_tokens = []
    for token in tokens:
        token = token.strip()
        if token:
            # Always quote to be safe - handles reserved words and special cases
            quoted_tokens.append(f'"{token}"')

    # Join with spaces (FTS5 implicit AND)
    return ' '.join(quoted_tokens)


def search_players(query: str, limit: int = 10) -> List[Dict]:
    """Full-text search on players."""
    escaped_query = escape_fts_query(query)
    if not escaped_query:
        return []
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT p.*, t.name as team_name
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.id
            WHERE p.id IN (
                SELECT rowid FROM players_fts WHERE players_fts MATCH ?
            )
            LIMIT ?
        """, (escaped_query, limit))
        return [dict_from_row(row) for row in cursor.fetchall()]


def search_teams(query: str, limit: int = 10) -> List[Dict]:
    """Full-text search on teams."""
    escaped_query = escape_fts_query(query)
    if not escaped_query:
        return []
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM teams
            WHERE id IN (
                SELECT rowid FROM teams_fts WHERE teams_fts MATCH ?
            )
            LIMIT ?
        """, (escaped_query, limit))
        return [dict_from_row(row) for row in cursor.fetchall()]


def search_news(query: str, limit: int = 10) -> List[Dict]:
    """Full-text search on news articles."""
    escaped_query = escape_fts_query(query)
    if not escaped_query:
        return []
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM news
            WHERE id IN (
                SELECT rowid FROM news_fts WHERE news_fts MATCH ?
            )
            ORDER BY published_at DESC
            LIMIT ?
        """, (escaped_query, limit))
        return [dict_from_row(row) for row in cursor.fetchall()]


def search_all(query: str, limit: int = 5) -> Dict[str, List[Dict]]:
    """Search across all FTS tables."""
    return {
        "players": search_players(query, limit),
        "teams": search_teams(query, limit),
        "news": search_news(query, limit)
    }


# ============================================
# WRITE OPERATIONS (For data updates)
# ============================================

def insert_team(team_data: Dict) -> int:
    """Insert a new team."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO teams (name, short_name, league, country, stadium, founded, logo_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            team_data['name'],
            team_data.get('short_name'),
            team_data['league'],
            team_data['country'],
            team_data.get('stadium'),
            team_data.get('founded'),
            team_data.get('logo_url')
        ))
        conn.commit()
        return cursor.lastrowid


def insert_player(player_data: Dict) -> int:
    """Insert a new player."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO players (name, team_id, position, nationality, birth_date, jersey_number)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            player_data['name'],
            player_data.get('team_id'),
            player_data.get('position'),
            player_data.get('nationality'),
            player_data.get('birth_date'),
            player_data.get('jersey_number')
        ))
        conn.commit()
        return cursor.lastrowid


def insert_game(game_data: Dict) -> int:
    """Insert a new game."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO games (date, time, home_team_id, away_team_id, home_score, away_score,
                              status, competition, matchday, venue, attendance, referee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_data['date'],
            game_data.get('time'),
            game_data['home_team_id'],
            game_data['away_team_id'],
            game_data.get('home_score'),
            game_data.get('away_score'),
            game_data.get('status', 'scheduled'),
            game_data.get('competition'),
            game_data.get('matchday'),
            game_data.get('venue'),
            game_data.get('attendance'),
            game_data.get('referee')
        ))
        conn.commit()
        return cursor.lastrowid


def insert_news(news_data: Dict) -> int:
    """Insert a news article."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO news (title, content, summary, source, source_url, published_at,
                             category, related_team_ids, related_player_ids)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            news_data['title'],
            news_data.get('content'),
            news_data.get('summary'),
            news_data.get('source'),
            news_data.get('source_url'),
            news_data.get('published_at'),
            news_data.get('category'),
            json.dumps(news_data.get('related_team_ids', [])),
            json.dumps(news_data.get('related_player_ids', []))
        ))
        conn.commit()
        return cursor.lastrowid


# ============================================
# LEGENDS & CLUB PERSONALITY
# ============================================

def get_legends(team_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
    """Get club legends with optional team filtering."""
    with get_connection() as conn:
        if team_id:
            cursor = conn.execute("""
                SELECT l.*, t.name as team_name
                FROM club_legends l
                LEFT JOIN teams t ON l.team_id = t.id
                WHERE l.team_id = ?
                ORDER BY l.name
                LIMIT ?
            """, (team_id, limit))
        else:
            cursor = conn.execute("""
                SELECT l.*, t.name as team_name
                FROM club_legends l
                LEFT JOIN teams t ON l.team_id = t.id
                ORDER BY t.name, l.name
                LIMIT ?
            """, (limit,))
        return [dict_from_row(row) for row in cursor.fetchall()]


def get_legend(legend_id: int) -> Optional[Dict]:
    """Get single legend by ID."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT l.*, t.name as team_name
            FROM club_legends l
            LEFT JOIN teams t ON l.team_id = t.id
            WHERE l.id = ?
        """, (legend_id,))
        return dict_from_row(cursor.fetchone())


def get_legend_by_name(name: str) -> Optional[Dict]:
    """Get legend by name (partial match)."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT l.*, t.name as team_name
            FROM club_legends l
            LEFT JOIN teams t ON l.team_id = t.id
            WHERE LOWER(l.name) LIKE LOWER(?)
        """, (f"%{name}%",))
        return dict_from_row(cursor.fetchone())


def get_club_identity(team_id: int) -> Optional[Dict]:
    """Get club identity/personality."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT ci.*, t.name as team_name
            FROM club_identity ci
            LEFT JOIN teams t ON ci.team_id = t.id
            WHERE ci.team_id = ?
        """, (team_id,))
        row = cursor.fetchone()
        if row:
            result = dict_from_row(row)
            # Parse JSON fields
            for field in ['core_values', 'vocabulary', 'forbidden_topics', 'rival_teams']:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except:
                        pass
            return result
        return None


def get_club_moments(team_id: int, limit: int = 20) -> List[Dict]:
    """Get iconic moments for a club."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT cm.*, t.name as team_name
            FROM club_moments cm
            LEFT JOIN teams t ON cm.team_id = t.id
            WHERE cm.team_id = ?
            ORDER BY cm.date DESC
            LIMIT ?
        """, (team_id, limit))
        results = []
        for row in cursor.fetchall():
            result = dict_from_row(row)
            if result.get('keywords'):
                try:
                    result['keywords'] = json.loads(result['keywords'])
                except:
                    pass
            results.append(result)
        return results


def get_club_rivalries(team_id: int) -> List[Dict]:
    """Get rivalries for a club."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT cr.*, t.name as team_name, rt.name as rival_name
            FROM club_rivalries cr
            LEFT JOIN teams t ON cr.team_id = t.id
            LEFT JOIN teams rt ON cr.rival_team_id = rt.id
            WHERE cr.team_id = ?
            ORDER BY cr.intensity DESC
        """, (team_id,))
        results = []
        for row in cursor.fetchall():
            result = dict_from_row(row)
            for field in ['key_moments', 'banter_phrases']:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except:
                        pass
            results.append(result)
        return results


def get_club_mood(team_id: int) -> Optional[Dict]:
    """Get current mood for a club."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT cm.*, t.name as team_name
            FROM club_mood cm
            LEFT JOIN teams t ON cm.team_id = t.id
            WHERE cm.team_id = ?
        """, (team_id,))
        return dict_from_row(cursor.fetchone())


def search_legends(query: str, limit: int = 10) -> List[Dict]:
    """Search legends by name or story content."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT l.*, t.name as team_name
            FROM club_legends l
            LEFT JOIN teams t ON l.team_id = t.id
            WHERE LOWER(l.name) LIKE LOWER(?)
               OR LOWER(l.story) LIKE LOWER(?)
               OR LOWER(l.fan_nickname) LIKE LOWER(?)
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        return [dict_from_row(row) for row in cursor.fetchall()]


# ============================================
# KNOWLEDGE GRAPH (KG-RAG)
# ============================================

def init_knowledge_graph():
    """Initialize KG tables."""
    with get_connection() as conn:
        # Node table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kg_nodes (
                node_id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT NOT NULL,
                entity_id INTEGER,
                name TEXT NOT NULL,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON kg_nodes(node_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_name ON kg_nodes(name COLLATE NOCASE)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_entity ON kg_nodes(node_type, entity_id)")

        # Edge table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kg_edges (
                edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                relationship TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                properties TEXT,
                FOREIGN KEY (source_id) REFERENCES kg_nodes(node_id),
                FOREIGN KEY (target_id) REFERENCES kg_nodes(node_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON kg_edges(source_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON kg_edges(target_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_rel ON kg_edges(relationship)")
        conn.commit()
    print("Knowledge Graph tables initialized")


def create_kg_node(node_type: str, entity_id: int, name: str,
                   properties: Dict = None) -> int:
    """Create a node in the knowledge graph."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO kg_nodes (node_type, entity_id, name, properties)
            VALUES (?, ?, ?, ?)
        """, (node_type, entity_id, name, json.dumps(properties) if properties else None))
        conn.commit()
        return cursor.lastrowid


def create_kg_edge(source_id: int, target_id: int, relationship: str,
                   weight: float = 1.0, properties: Dict = None) -> int:
    """Create an edge in the knowledge graph."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO kg_edges (source_id, target_id, relationship, weight, properties)
            VALUES (?, ?, ?, ?, ?)
        """, (source_id, target_id, relationship, weight,
              json.dumps(properties) if properties else None))
        conn.commit()
        return cursor.lastrowid


def get_kg_node(node_id: int) -> Optional[Dict]:
    """Get a node by ID."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM kg_nodes WHERE node_id = ?", (node_id,))
        row = cursor.fetchone()
        if row:
            result = dict_from_row(row)
            if result.get('properties'):
                try:
                    result['properties'] = json.loads(result['properties'])
                except:
                    pass
            return result
        return None


def get_kg_node_by_entity(node_type: str, entity_id: int) -> Optional[Dict]:
    """Get a node by entity type and ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM kg_nodes WHERE node_type = ? AND entity_id = ?",
            (node_type, entity_id)
        )
        row = cursor.fetchone()
        if row:
            result = dict_from_row(row)
            if result.get('properties'):
                try:
                    result['properties'] = json.loads(result['properties'])
                except:
                    pass
            return result
        return None


def find_kg_node_by_name(name: str) -> Optional[Dict]:
    """Find node by name (case-insensitive partial match)."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM kg_nodes WHERE LOWER(name) LIKE LOWER(?)",
            (f"%{name}%",)
        )
        row = cursor.fetchone()
        if row:
            result = dict_from_row(row)
            if result.get('properties'):
                try:
                    result['properties'] = json.loads(result['properties'])
                except:
                    pass
            return result
        return None


def get_kg_edges_from(node_id: int, relationship: str = None) -> List[Dict]:
    """Get all edges from a node, optionally filtered by relationship."""
    with get_connection() as conn:
        if relationship:
            cursor = conn.execute("""
                SELECT e.*, n.name as target_name, n.node_type as target_type
                FROM kg_edges e
                JOIN kg_nodes n ON e.target_id = n.node_id
                WHERE e.source_id = ? AND e.relationship = ?
                ORDER BY e.weight DESC
            """, (node_id, relationship))
        else:
            cursor = conn.execute("""
                SELECT e.*, n.name as target_name, n.node_type as target_type
                FROM kg_edges e
                JOIN kg_nodes n ON e.target_id = n.node_id
                WHERE e.source_id = ?
                ORDER BY e.weight DESC
            """, (node_id,))
        return [dict_from_row(row) for row in cursor.fetchall()]


def get_kg_edges_to(node_id: int, relationship: str = None) -> List[Dict]:
    """Get all edges pointing TO a node (reverse traversal)."""
    with get_connection() as conn:
        if relationship:
            cursor = conn.execute("""
                SELECT e.*, n.name as source_name, n.node_type as source_type
                FROM kg_edges e
                JOIN kg_nodes n ON e.source_id = n.node_id
                WHERE e.target_id = ? AND e.relationship = ?
                ORDER BY e.weight DESC
            """, (node_id, relationship))
        else:
            cursor = conn.execute("""
                SELECT e.*, n.name as source_name, n.node_type as source_type
                FROM kg_edges e
                JOIN kg_nodes n ON e.source_id = n.node_id
                WHERE e.target_id = ?
                ORDER BY e.weight DESC
            """, (node_id,))
        return [dict_from_row(row) for row in cursor.fetchall()]


def traverse_kg(node_id: int, depth: int = 1, relationship: str = None) -> List[Dict]:
    """BFS traversal from node up to specified depth."""
    visited = {node_id}
    current_level = [node_id]
    results = []

    for d in range(depth):
        next_level = []
        for nid in current_level:
            edges = get_kg_edges_from(nid, relationship)
            for edge in edges:
                target_id = edge['target_id']
                if target_id not in visited:
                    visited.add(target_id)
                    next_level.append(target_id)
                    target_node = get_kg_node(target_id)
                    results.append({
                        'node': target_node,
                        'edge': edge,
                        'depth': d + 1
                    })
        current_level = next_level
        if not current_level:
            break

    return results


def get_entity_context(entity_type: str, entity_id: int) -> Dict:
    """Get full context for an entity via graph traversal."""
    node = get_kg_node_by_entity(entity_type, entity_id)
    if not node:
        return {}

    context = {'entity': node}
    node_id = node['node_id']

    if entity_type == 'team':
        # Get legends (edges TO this team)
        context['legends'] = get_kg_edges_to(node_id, 'legendary_at')
        # Get rivalries
        context['rivalries'] = get_kg_edges_from(node_id, 'rival_of')
        # Get moments (edges TO this team)
        context['moments'] = get_kg_edges_to(node_id, 'occurred_at')
        # Get mood from regular table
        context['mood'] = get_club_mood(entity_id)

    elif entity_type == 'legend':
        # Get team
        team_edges = get_kg_edges_from(node_id, 'legendary_at')
        if team_edges:
            context['team'] = get_kg_node(team_edges[0]['target_id'])

    elif entity_type == 'moment':
        # Get team
        team_edges = get_kg_edges_from(node_id, 'occurred_at')
        if team_edges:
            context['team'] = get_kg_node(team_edges[0]['target_id'])
        # Get opponent
        opponent_edges = get_kg_edges_from(node_id, 'against')
        if opponent_edges:
            context['opponent'] = get_kg_node(opponent_edges[0]['target_id'])

    return context


def populate_knowledge_graph():
    """Populate KG from existing data tables."""
    init_knowledge_graph()

    with get_connection() as conn:
        # Clear existing KG data
        conn.execute("DELETE FROM kg_edges")
        conn.execute("DELETE FROM kg_nodes")
        conn.commit()

    node_map = {}  # (type, entity_id) -> node_id

    # 1. Create team nodes
    teams = get_teams(limit=100)
    for team in teams:
        node_id = create_kg_node('team', team['id'], team['name'], {
            'league': team.get('league'),
            'stadium': team.get('stadium')
        })
        node_map[('team', team['id'])] = node_id

    # 2. Create legend nodes + edges
    legends = get_legends(limit=100)
    for legend in legends:
        node_id = create_kg_node('legend', legend['id'], legend['name'], {
            'era': legend.get('era'),
            'position': legend.get('position'),
            'achievements': legend.get('achievements')
        })
        node_map[('legend', legend['id'])] = node_id
        # Edge: legend -> team
        team_node_id = node_map.get(('team', legend['team_id']))
        if team_node_id:
            create_kg_edge(node_id, team_node_id, 'legendary_at')

    # 3. Create moment nodes + edges
    # All Top 6: City(1), Liverpool(2), Arsenal(3), Chelsea(4), ManU(5), Spurs(6)
    for team_id in [1, 2, 3, 4, 5, 6]:
        moments = get_club_moments(team_id, limit=50)
        for moment in moments:
            node_id = create_kg_node('moment', moment['id'], moment['title'], {
                'emotion': moment.get('emotion'),
                'significance': moment.get('significance'),
                'date': moment.get('date'),
                'opponent': moment.get('opponent')
            })
            node_map[('moment', moment['id'])] = node_id
            # Edge: moment -> team
            team_node_id = node_map.get(('team', team_id))
            if team_node_id:
                create_kg_edge(node_id, team_node_id, 'occurred_at')
            # Edge: moment -> opponent (if opponent is tracked)
            if moment.get('opponent'):
                opponent_team = get_team_by_name(moment['opponent'])
                if opponent_team:
                    opponent_node_id = node_map.get(('team', opponent_team['id']))
                    if opponent_node_id:
                        create_kg_edge(node_id, opponent_node_id, 'against')

    # 4. Create rivalry edges
    # All Top 6: City(1), Liverpool(2), Arsenal(3), Chelsea(4), ManU(5), Spurs(6)
    for team_id in [1, 2, 3, 4, 5, 6]:
        rivalries = get_club_rivalries(team_id)
        for rivalry in rivalries:
            team_node_id = node_map.get(('team', team_id))
            rival_node_id = node_map.get(('team', rivalry['rival_team_id']))
            if team_node_id and rival_node_id:
                create_kg_edge(team_node_id, rival_node_id, 'rival_of',
                              weight=rivalry['intensity'] / 10.0,
                              properties={'type': rivalry.get('rivalry_type')})

    # Count results
    with get_connection() as conn:
        nodes = conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        edges = conn.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]

    print(f"Knowledge Graph populated: {nodes} nodes, {edges} edges")
    return {'nodes': nodes, 'edges': edges}


def get_kg_stats() -> Dict:
    """Get KG statistics."""
    with get_connection() as conn:
        nodes = conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        edges = conn.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]

        # By type
        type_counts = {}
        cursor = conn.execute(
            "SELECT node_type, COUNT(*) as count FROM kg_nodes GROUP BY node_type"
        )
        for row in cursor.fetchall():
            type_counts[row['node_type']] = row['count']

        return {
            'total_nodes': nodes,
            'total_edges': edges,
            'by_type': type_counts
        }


# ============================================
# QUERY ANALYTICS (CP6)
# ============================================

def init_analytics():
    """Initialize analytics table."""
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS query_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                intent TEXT,
                kg_intent TEXT,
                club_detected TEXT,
                kg_nodes_used INTEGER DEFAULT 0,
                kg_edges_traversed INTEGER DEFAULT 0,
                response_time_ms INTEGER,
                source_count INTEGER DEFAULT 0,
                confidence REAL,
                was_injection_attempt INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_analytics_created
            ON query_analytics(created_at)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_analytics_intent
            ON query_analytics(intent)
        ''')
        conn.commit()
    print("Analytics table initialized")


def log_query(
    query: str,
    intent: str = None,
    kg_intent: str = None,
    club_detected: str = None,
    kg_nodes_used: int = 0,
    kg_edges_traversed: int = 0,
    response_time_ms: int = None,
    source_count: int = 0,
    confidence: float = None,
    was_injection_attempt: bool = False
) -> int:
    """Log a query for analytics."""
    with get_connection() as conn:
        cursor = conn.execute('''
            INSERT INTO query_analytics
            (query, intent, kg_intent, club_detected, kg_nodes_used,
             kg_edges_traversed, response_time_ms, source_count,
             confidence, was_injection_attempt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            query[:500],  # Truncate long queries
            intent,
            kg_intent,
            club_detected,
            kg_nodes_used,
            kg_edges_traversed,
            response_time_ms,
            source_count,
            confidence,
            1 if was_injection_attempt else 0
        ))
        conn.commit()
        return cursor.lastrowid


def get_analytics_summary(days: int = 7) -> Dict:
    """Get analytics summary for the last N days."""
    with get_connection() as conn:
        # Total queries
        total = conn.execute('''
            SELECT COUNT(*) as count FROM query_analytics
            WHERE created_at >= datetime('now', ?)
        ''', (f'-{days} days',)).fetchone()['count']

        # Injection attempts
        injections = conn.execute('''
            SELECT COUNT(*) as count FROM query_analytics
            WHERE was_injection_attempt = 1
            AND created_at >= datetime('now', ?)
        ''', (f'-{days} days',)).fetchone()['count']

        # By intent
        intent_stats = {}
        cursor = conn.execute('''
            SELECT intent, COUNT(*) as count
            FROM query_analytics
            WHERE intent IS NOT NULL
            AND created_at >= datetime('now', ?)
            GROUP BY intent
            ORDER BY count DESC
        ''', (f'-{days} days',))
        for row in cursor.fetchall():
            intent_stats[row['intent']] = row['count']

        # By KG intent
        kg_intent_stats = {}
        cursor = conn.execute('''
            SELECT kg_intent, COUNT(*) as count
            FROM query_analytics
            WHERE kg_intent IS NOT NULL
            AND created_at >= datetime('now', ?)
            GROUP BY kg_intent
            ORDER BY count DESC
        ''', (f'-{days} days',))
        for row in cursor.fetchall():
            kg_intent_stats[row['kg_intent']] = row['count']

        # Most queried clubs
        club_stats = {}
        cursor = conn.execute('''
            SELECT club_detected, COUNT(*) as count
            FROM query_analytics
            WHERE club_detected IS NOT NULL
            AND created_at >= datetime('now', ?)
            GROUP BY club_detected
            ORDER BY count DESC
            LIMIT 10
        ''', (f'-{days} days',))
        for row in cursor.fetchall():
            club_stats[row['club_detected']] = row['count']

        # Average response time
        avg_time = conn.execute('''
            SELECT AVG(response_time_ms) as avg_ms
            FROM query_analytics
            WHERE response_time_ms IS NOT NULL
            AND created_at >= datetime('now', ?)
        ''', (f'-{days} days',)).fetchone()['avg_ms']

        # Average confidence
        avg_conf = conn.execute('''
            SELECT AVG(confidence) as avg_conf
            FROM query_analytics
            WHERE confidence IS NOT NULL
            AND created_at >= datetime('now', ?)
        ''', (f'-{days} days',)).fetchone()['avg_conf']

        # KG usage stats
        kg_usage = conn.execute('''
            SELECT
                AVG(kg_nodes_used) as avg_nodes,
                AVG(kg_edges_traversed) as avg_edges,
                SUM(CASE WHEN kg_nodes_used > 0 THEN 1 ELSE 0 END) as kg_queries
            FROM query_analytics
            WHERE created_at >= datetime('now', ?)
        ''', (f'-{days} days',)).fetchone()

        return {
            'period_days': days,
            'total_queries': total,
            'injection_attempts': injections,
            'injection_rate': injections / total if total > 0 else 0,
            'by_intent': intent_stats,
            'by_kg_intent': kg_intent_stats,
            'by_club': club_stats,
            'avg_response_time_ms': round(avg_time, 2) if avg_time else None,
            'avg_confidence': round(avg_conf, 3) if avg_conf else None,
            'kg_usage': {
                'queries_using_kg': kg_usage['kg_queries'] or 0,
                'avg_nodes_per_query': round(kg_usage['avg_nodes'], 2) if kg_usage['avg_nodes'] else 0,
                'avg_edges_per_query': round(kg_usage['avg_edges'], 2) if kg_usage['avg_edges'] else 0
            }
        }


def get_recent_queries(limit: int = 20) -> List[Dict]:
    """Get most recent queries for debugging."""
    with get_connection() as conn:
        cursor = conn.execute('''
            SELECT * FROM query_analytics
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        return [dict_from_row(row) for row in cursor.fetchall()]


def get_hot_queries(days: int = 7, limit: int = 10) -> List[Dict]:
    """Get most common query patterns."""
    with get_connection() as conn:
        cursor = conn.execute('''
            SELECT
                query,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence,
                AVG(response_time_ms) as avg_time_ms
            FROM query_analytics
            WHERE created_at >= datetime('now', ?)
            GROUP BY query
            ORDER BY count DESC
            LIMIT ?
        ''', (f'-{days} days', limit))
        return [dict_from_row(row) for row in cursor.fetchall()]


# ============================================
# KG VISUALIZATION EXPORT
# ============================================

def export_kg_to_vis_json() -> Dict:
    """
    Export Knowledge Graph in vis.js compatible format.

    Returns:
        {
            "nodes": [{"id": "team_3", "label": "Arsenal", "group": "team", ...}, ...],
            "edges": [{"from": "legend_1", "to": "team_3", "label": "legendary_at", ...}, ...],
            "stats": {"total_nodes": 62, "total_edges": 68, ...}
        }
    """
    # Color scheme for node types
    colors = {
        "team": "#e74c3c",      # Red - clubs are central
        "legend": "#f39c12",    # Orange - legends shine
        "moment": "#3498db",    # Blue - moments in time
        "default": "#95a5a6"    # Gray - fallback
    }

    # Shape scheme for node types
    shapes = {
        "team": "box",          # Box for clubs
        "legend": "star",       # Star for legends
        "moment": "diamond",    # Diamond for moments
        "default": "dot"
    }

    nodes = []
    edges = []

    with get_connection() as conn:
        # Get all nodes
        cursor = conn.execute('''
            SELECT node_id, name, node_type, properties
            FROM kg_nodes
        ''')

        for row in cursor.fetchall():
            node = dict_from_row(row)
            props = json.loads(node.get('properties', '{}') or '{}')

            vis_node = {
                "id": node["node_id"],
                "label": node["name"],
                "group": node["node_type"],
                "color": colors.get(node["node_type"], colors["default"]),
                "shape": shapes.get(node["node_type"], shapes["default"]),
                "title": f"{node['node_type'].title()}: {node['name']}"  # Tooltip
            }

            # Add extra info to tooltip
            if props:
                details = []
                if props.get("era"):
                    details.append(f"Era: {props['era']}")
                if props.get("position"):
                    details.append(f"Position: {props['position']}")
                if props.get("year"):
                    details.append(f"Year: {props['year']}")
                if props.get("emotion"):
                    details.append(f"Emotion: {props['emotion']}")
                if details:
                    vis_node["title"] += "\n" + "\n".join(details)

            # Size based on type
            if node["node_type"] == "team":
                vis_node["size"] = 30
            elif node["node_type"] == "legend":
                vis_node["size"] = 20
            else:
                vis_node["size"] = 15

            nodes.append(vis_node)

        # Get all edges
        cursor = conn.execute('''
            SELECT source_id, target_id, relationship, weight
            FROM kg_edges
        ''')

        edge_colors = {
            "legendary_at": "#f39c12",    # Orange
            "occurred_at": "#3498db",     # Blue
            "against": "#e74c3c",         # Red
            "rival_of": "#c0392b",        # Dark red
            "default": "#bdc3c7"          # Light gray
        }

        for row in cursor.fetchall():
            edge = dict_from_row(row)

            vis_edge = {
                "from": edge["source_id"],
                "to": edge["target_id"],
                "label": edge["relationship"].replace("_", " "),
                "value": edge["weight"],
                "color": edge_colors.get(edge["relationship"], edge_colors["default"]),
                "arrows": "to",
                "title": f"{edge['relationship']} (weight: {edge['weight']:.2f})"
            }

            # Style based on relationship
            if edge["relationship"] == "rival_of":
                vis_edge["dashes"] = True
                vis_edge["width"] = max(1, int(edge["weight"] * 3))

            edges.append(vis_edge)

    # Get stats
    stats = get_kg_stats()

    # Count edges by relationship type
    by_relationship = {}
    for edge in edges:
        rel = edge["label"]
        by_relationship[rel] = by_relationship.get(rel, 0) + 1

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": stats["total_nodes"],
            "total_edges": stats["total_edges"],
            "by_type": stats["by_type"],
            "by_relationship": by_relationship
        }
    }


def export_kg_subgraph(center_node_id, depth: int = 2) -> Dict:
    """
    Export a subgraph centered on a specific node.
    Useful for focused visualizations.

    Args:
        center_node_id: Can be int or str - will be normalized
        depth: How many hops out to include
    """
    # Normalize node_id to int for comparison
    try:
        center_id = int(center_node_id)
    except (ValueError, TypeError):
        center_id = center_node_id

    # Get the full graph
    full_graph = export_kg_to_vis_json()

    if depth == 0:
        # Just the center node
        center_nodes = [n for n in full_graph["nodes"] if n["id"] == center_id]
        return {"nodes": center_nodes, "edges": [], "stats": {"total_nodes": len(center_nodes)}}

    # Find connected nodes
    connected_ids = {center_id}
    current_layer = {center_id}

    for _ in range(depth):
        next_layer = set()
        for edge in full_graph["edges"]:
            if edge["from"] in current_layer:
                next_layer.add(edge["to"])
            if edge["to"] in current_layer:
                next_layer.add(edge["from"])
        connected_ids.update(next_layer)
        current_layer = next_layer

    # Filter nodes and edges
    subgraph_nodes = [n for n in full_graph["nodes"] if n["id"] in connected_ids]
    subgraph_edges = [e for e in full_graph["edges"]
                      if e["from"] in connected_ids and e["to"] in connected_ids]

    return {
        "nodes": subgraph_nodes,
        "edges": subgraph_edges,
        "center": center_node_id,
        "depth": depth,
        "stats": {
            "total_nodes": len(subgraph_nodes),
            "total_edges": len(subgraph_edges)
        }
    }


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_db_stats() -> Dict:
    """Get database statistics."""
    with get_connection() as conn:
        stats = {}
        tables = ['teams', 'players', 'games', 'player_stats', 'injuries',
                  'transfers', 'standings', 'news', 'game_events']

        for table in tables:
            cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = cursor.fetchone()['count']

        return stats


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
    print("Database stats:", get_db_stats())
