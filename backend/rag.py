"""
Soccer-AI RAG Module
Retrieval Augmented Generation - extracts relevant context from database
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import database


# ============================================
# ENTITY EXTRACTION
# ============================================

# Common team name variations
TEAM_ALIASES = {
    "man utd": "Manchester United",
    "man united": "Manchester United",
    "united": "Manchester United",
    "man city": "Manchester City",
    "city": "Manchester City",
    "liverpool": "Liverpool",
    "arsenal": "Arsenal",
    "gunners": "Arsenal",
    "chelsea": "Chelsea",
    "blues": "Chelsea",
    "spurs": "Tottenham",
    "tottenham": "Tottenham",
    "barca": "Barcelona",
    "barcelona": "Barcelona",
    "real": "Real Madrid",
    "real madrid": "Real Madrid",
    "bayern": "Bayern Munich",
    "psg": "Paris Saint-Germain",
}

# Time expressions
TIME_PATTERNS = {
    "yesterday": -1,
    "today": 0,
    "tomorrow": 1,
    "last week": -7,
    "this week": 0,
    "last game": -1,  # Contextual
    "recent": -7,
    "latest": -3,
}


def deduplicate_sources(sources: List[Dict]) -> List[Dict]:
    """
    Remove duplicate sources from the list.
    Uses (type, id) as unique key. For sources without ID, uses (type, name/rival) or just (type, None).
    Bug fix: Insight #930 - Duplicate sources in hybrid RAG
    """
    seen = set()
    unique = []

    for source in sources:
        source_type = source.get("type", "unknown")
        source_id = source.get("id")
        source_name = source.get("name", "")
        source_rival = source.get("rival", "")

        if source_id is not None:
            # Use type + id as key
            key = (source_type, "id", source_id)
        elif source_name:
            # Use type + name as key (for named entities like legends)
            key = (source_type, "name", source_name)
        elif source_rival:
            # Use type + rival as key (for rivalries)
            key = (source_type, "rival", source_rival)
        else:
            # For sources with no identifying info, dedupe by type only (keep first)
            key = (source_type, "none", None)

        if key not in seen:
            seen.add(key)
            unique.append(source)

    return unique


def extract_entities(query: str) -> Dict[str, Any]:
    """
    Extract entities from natural language query.
    Returns dict with: teams, players, dates, intent
    """
    query_lower = query.lower()
    entities = {
        "teams": [],
        "players": [],
        "dates": [],
        "intent": detect_intent(query_lower),
        "raw_query": query
    }

    # Extract team mentions
    for alias, full_name in TEAM_ALIASES.items():
        if alias in query_lower:
            entities["teams"].append(full_name)

    # Extract time references
    for pattern, days_delta in TIME_PATTERNS.items():
        if pattern in query_lower:
            target_date = datetime.now() + timedelta(days=days_delta)
            entities["dates"].append(target_date.strftime("%Y-%m-%d"))

    # If no specific date, check for date patterns (e.g., "December 18")
    date_match = re.search(r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(\d{4}))?', query)
    if date_match:
        try:
            month_str = date_match.group(1)
            day = int(date_match.group(2))
            year = int(date_match.group(3)) if date_match.group(3) else datetime.now().year
            month = datetime.strptime(month_str, "%B").month
            entities["dates"].append(f"{year}-{month:02d}-{day:02d}")
        except ValueError:
            pass

    # Try to find player names via FTS search
    # Extract potential player names (capitalized words not matching teams)
    words = query.split()
    potential_names = []
    for i, word in enumerate(words):
        if word[0].isupper() and word.lower() not in TEAM_ALIASES:
            # Could be a player name - try to combine with next word
            if i + 1 < len(words) and words[i + 1][0].isupper():
                potential_names.append(f"{word} {words[i + 1]}")
            else:
                potential_names.append(word)

    # Verify player names against database
    for name in potential_names:
        players = database.search_players(name, limit=1)
        if players:
            entities["players"].append(players[0])

    return entities


def detect_intent(query: str) -> str:
    """
    Detect the intent of the query.
    Returns: score, injury, transfer, fixture, standing, player_info, team_info, general
    """
    query = query.lower()

    # Score/result queries
    if any(word in query for word in ["score", "result", "won", "lost", "draw", "played", "beat"]):
        return "score"

    # Injury queries
    if any(word in query for word in ["injury", "injured", "hurt", "fitness", "sidelined", "out"]):
        return "injury"

    # Transfer queries
    if any(word in query for word in ["transfer", "sign", "buy", "sell", "loan", "rumor", "deal"]):
        return "transfer"

    # Fixture/schedule queries
    if any(word in query for word in ["next game", "fixture", "when", "schedule", "playing next"]):
        return "fixture"

    # Standing/table queries
    if any(word in query for word in ["standing", "table", "position", "rank", "points"]):
        return "standing"

    # Stats queries
    if any(word in query for word in ["stats", "goals", "assists", "top scorer", "most", "average"]):
        return "stats"

    # Player info
    if any(word in query for word in ["who is", "tell me about", "player"]):
        return "player_info"

    # Team info
    if any(word in query for word in ["team", "squad", "roster", "club"]):
        return "team_info"

    return "general"


# ============================================
# CONTEXT RETRIEVAL
# ============================================

def retrieve_context(query: str) -> Tuple[str, List[Dict]]:
    """
    Main RAG function. Retrieves relevant context for the query.
    Returns: (formatted_context, source_references)
    """
    entities = extract_entities(query)
    intent = entities["intent"]
    context_parts = []
    sources = []

    # Route to appropriate retrieval based on intent
    if intent == "score":
        ctx, src = retrieve_score_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "injury":
        ctx, src = retrieve_injury_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "transfer":
        ctx, src = retrieve_transfer_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "fixture":
        ctx, src = retrieve_fixture_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "standing":
        ctx, src = retrieve_standing_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "stats":
        ctx, src = retrieve_stats_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "player_info":
        ctx, src = retrieve_player_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "team_info":
        ctx, src = retrieve_team_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    else:
        # General query - search everything
        ctx, src = retrieve_general_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    # Also search news for additional context
    news_ctx, news_src = retrieve_news_context(entities)
    if news_ctx:
        context_parts.append(news_ctx)
        sources.extend(news_src)

    return "\n\n".join(filter(None, context_parts)), sources


def retrieve_score_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve game score/result context."""
    context_lines = []
    sources = []

    for team_name in entities.get("teams", []):
        team = database.get_team_by_name(team_name)
        if not team:
            continue

        # Get recent games
        if entities.get("dates"):
            # Specific date
            games = database.get_games(
                team_id=team["id"],
                date_from=entities["dates"][0],
                date_to=entities["dates"][0],
                limit=5
            )
        else:
            # Recent games
            games = database.get_recent_games(team["id"], limit=3)

        for game in games:
            home = game["home_team_name"]
            away = game["away_team_name"]
            score = f"{game.get('home_score', '?')}-{game.get('away_score', '?')}"
            date = game["date"]
            status = game["status"]

            if status == "finished":
                context_lines.append(
                    f"Game on {date}: {home} {score} {away} at {game.get('venue', 'unknown venue')}"
                )
            else:
                context_lines.append(
                    f"Upcoming game on {date}: {home} vs {away} ({status})"
                )

            sources.append({"type": "game", "id": game["id"]})

            # Get events if available
            if game.get("events"):
                for event in game["events"]:
                    if event["event_type"] == "goal":
                        context_lines.append(
                            f"  - Goal: {event['player_name']} ({event['minute']}')"
                        )

    return "\n".join(context_lines), sources


def retrieve_injury_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve injury context."""
    context_lines = []
    sources = []

    # Get injuries for mentioned teams
    for team_name in entities.get("teams", []):
        team = database.get_team_by_name(team_name)
        if team:
            injuries = database.get_injuries(team_id=team["id"], status="active")
            if injuries:
                context_lines.append(f"Current injuries for {team_name}:")
                for injury in injuries:
                    context_lines.append(
                        f"  - {injury['player_name']}: {injury['injury_type']} "
                        f"({injury['severity']}), expected return: {injury.get('expected_return', 'unknown')}"
                    )
                    sources.append({"type": "injury", "id": injury["id"]})

    # Get injuries for mentioned players
    for player in entities.get("players", []):
        injuries = database.get_injuries(status="active")
        player_injuries = [i for i in injuries if i["player_id"] == player["id"]]
        for injury in player_injuries:
            context_lines.append(
                f"{player['name']} injury: {injury['injury_type']} ({injury['severity']})"
            )
            sources.append({"type": "injury", "id": injury["id"]})

    # If no specific team/player, get all active injuries
    if not context_lines:
        injuries = database.get_injuries(status="active", limit=10)
        context_lines.append("Current active injuries:")
        for injury in injuries:
            context_lines.append(
                f"  - {injury['player_name']} ({injury['team_name']}): {injury['injury_type']}"
            )
            sources.append({"type": "injury", "id": injury["id"]})

    return "\n".join(context_lines), sources


def retrieve_transfer_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve transfer context."""
    context_lines = []
    sources = []

    for team_name in entities.get("teams", []):
        team = database.get_team_by_name(team_name)
        if team:
            transfers = database.get_transfers(team_id=team["id"], limit=10)
            if transfers:
                context_lines.append(f"Recent transfers involving {team_name}:")
                for transfer in transfers:
                    direction = "to" if transfer["to_team_id"] == team["id"] else "from"
                    other_team = transfer["from_team_name"] if direction == "to" else transfer["to_team_name"]
                    fee = f"€{transfer['fee_eur']:,}" if transfer.get("fee_eur") else "undisclosed"
                    context_lines.append(
                        f"  - {transfer['player_name']}: {direction} {other_team} ({transfer['transfer_type']}, {fee})"
                    )
                    sources.append({"type": "transfer", "id": transfer["id"]})

    # Check for transfer rumors
    rumors = database.get_transfers(status="rumor", limit=5)
    if rumors:
        context_lines.append("\nRecent transfer rumors:")
        for rumor in rumors:
            context_lines.append(
                f"  - {rumor['player_name']}: {rumor['from_team_name']} → {rumor['to_team_name']} (rumored)"
            )
            sources.append({"type": "transfer", "id": rumor["id"]})

    return "\n".join(context_lines), sources


def retrieve_fixture_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve upcoming fixture context."""
    context_lines = []
    sources = []

    for team_name in entities.get("teams", []):
        team = database.get_team_by_name(team_name)
        if team:
            fixtures = database.get_upcoming_games(team["id"], limit=5)
            if fixtures:
                context_lines.append(f"Upcoming games for {team_name}:")
                for game in fixtures:
                    opponent = game["away_team_name"] if game["home_team_id"] == team["id"] else game["home_team_name"]
                    venue = "home" if game["home_team_id"] == team["id"] else "away"
                    context_lines.append(
                        f"  - {game['date']}: vs {opponent} ({venue})"
                    )
                    sources.append({"type": "game", "id": game["id"]})

    return "\n".join(context_lines), sources


def retrieve_standing_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve league standings context."""
    context_lines = []
    sources = []

    leagues = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]

    for team_name in entities.get("teams", []):
        team = database.get_team_by_name(team_name)
        if team:
            standings = database.get_standings(team["league"])
            team_standing = next((s for s in standings if s["team_id"] == team["id"]), None)
            if team_standing:
                context_lines.append(
                    f"{team_name} in {team['league']}: "
                    f"Position {team_standing['position']}, "
                    f"{team_standing['points']} points, "
                    f"Form: {team_standing.get('form', 'N/A')}"
                )
                sources.append({"type": "standing", "team_id": team["id"]})

                # Show nearby teams
                pos = team_standing["position"]
                nearby = [s for s in standings if abs(s["position"] - pos) <= 2]
                context_lines.append("Nearby teams:")
                for s in nearby:
                    context_lines.append(
                        f"  {s['position']}. {s['team_name']} - {s['points']} pts"
                    )

    return "\n".join(context_lines), sources


def retrieve_stats_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve player/team statistics context."""
    context_lines = []
    sources = []

    for player in entities.get("players", []):
        stats = database.get_player_stats(player["id"])
        if stats:
            context_lines.append(
                f"{player['name']} season stats: "
                f"{stats.get('total_goals', 0)} goals, "
                f"{stats.get('total_assists', 0)} assists in "
                f"{stats.get('games', 0)} games"
            )
            sources.append({"type": "player_stats", "player_id": player["id"]})

    return "\n".join(context_lines), sources


def retrieve_player_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve player information context."""
    context_lines = []
    sources = []

    for player in entities.get("players", []):
        context_lines.append(
            f"{player['name']}: {player.get('position', 'Unknown')} for {player.get('team_name', 'Unknown')}, "
            f"Nationality: {player.get('nationality', 'Unknown')}"
        )
        sources.append({"type": "player", "id": player["id"]})

        # Add stats
        stats = database.get_player_stats(player["id"])
        if stats and stats.get("games", 0) > 0:
            context_lines.append(
                f"  Season: {stats.get('total_goals', 0)} goals, {stats.get('total_assists', 0)} assists"
            )

    return "\n".join(context_lines), sources


def retrieve_team_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve team information context."""
    context_lines = []
    sources = []

    for team_name in entities.get("teams", []):
        team = database.get_team_by_name(team_name)
        if team:
            context_lines.append(
                f"{team['name']}: {team['league']} ({team['country']}), "
                f"Stadium: {team.get('stadium', 'Unknown')}"
            )
            sources.append({"type": "team", "id": team["id"]})

            # Get standing
            standings = database.get_standings(team["league"])
            team_standing = next((s for s in standings if s["team_id"] == team["id"]), None)
            if team_standing:
                context_lines.append(
                    f"  Current position: {team_standing['position']} with {team_standing['points']} points"
                )

    return "\n".join(context_lines), sources


def retrieve_news_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve relevant news context."""
    context_lines = []
    sources = []

    # Build search query from entities
    search_terms = []
    search_terms.extend(entities.get("teams", []))
    search_terms.extend([p["name"] for p in entities.get("players", [])])

    if search_terms:
        search_query = " OR ".join(search_terms)
        news = database.search_news(search_query, limit=3)
        if news:
            context_lines.append("Related news:")
            for article in news:
                context_lines.append(f"  - {article['title']} ({article.get('source', 'Unknown')})")
                if article.get("summary"):
                    context_lines.append(f"    {article['summary']}")
                sources.append({"type": "news", "id": article["id"]})

    return "\n".join(context_lines), sources


def retrieve_general_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve context for general queries using FTS search."""
    context_lines = []
    sources = []

    # Use the raw query for FTS search
    query = entities.get("raw_query", "")
    if query:
        results = database.search_all(query, limit=3)

        if results["teams"]:
            context_lines.append("Teams found:")
            for team in results["teams"]:
                context_lines.append(f"  - {team['name']} ({team['league']})")
                sources.append({"type": "team", "id": team["id"]})

        if results["players"]:
            context_lines.append("Players found:")
            for player in results["players"]:
                context_lines.append(f"  - {player['name']} ({player.get('team_name', 'Unknown')})")
                sources.append({"type": "player", "id": player["id"]})

        if results["news"]:
            context_lines.append("Related news:")
            for article in results["news"]:
                context_lines.append(f"  - {article['title']}")
                sources.append({"type": "news", "id": article["id"]})

    return "\n".join(context_lines), sources


# ============================================
# KNOWLEDGE GRAPH ENHANCED RETRIEVAL (KG-RAG)
# Hybrid retrieval: FTS5 (β=0.60) + Graph (γ=0.40)
# ============================================

# Intent patterns that benefit from graph traversal
KG_INTENT_PATTERNS = {
    "multi_hop": ["best", "greatest", "iconic", "legendary", "famous", "memorable"],
    "relationship": ["compare", "vs", "versus", "rivalry", "between"],
    "discovery": ["connection", "related", "link", "any", "history with"],
    "emotional": ["feeling", "mood", "how are we", "atmosphere"],
}

# Legend and moment keywords for KG routing
LEGEND_KEYWORDS = ["legend", "legendary", "greatest", "icon", "hero", "hall of fame"]
MOMENT_KEYWORDS = ["moment", "memory", "derby", "classic", "famous", "iconic", "invincibles"]
RIVALRY_KEYWORDS = ["rival", "rivalry", "derby", "enemy", "hate", "spurs", "enemy"]


def detect_kg_intent(query: str) -> Optional[str]:
    """Detect if query would benefit from KG traversal."""
    query_lower = query.lower()

    # Priority order: specific intents first, then general

    # Check for rivalry-specific FIRST (most specific)
    if any(word in query_lower for word in RIVALRY_KEYWORDS):
        return "rivalry"

    # Check for moment-specific
    if any(word in query_lower for word in MOMENT_KEYWORDS):
        return "moment"

    # Check for legend-specific
    if any(word in query_lower for word in LEGEND_KEYWORDS):
        return "legend"

    # Check for emotional/mood queries
    if any(word in query_lower for word in KG_INTENT_PATTERNS["emotional"]):
        return "emotional"

    # Check for discovery queries
    if any(word in query_lower for word in KG_INTENT_PATTERNS["discovery"]):
        return "discovery"

    # Check for relationship queries
    if any(word in query_lower for word in KG_INTENT_PATTERNS["relationship"]):
        return "relationship"

    # Check for multi-hop queries (most general)
    if any(word in query_lower for word in KG_INTENT_PATTERNS["multi_hop"]):
        return "multi_hop"

    return None


def extract_kg_entities(query: str) -> Dict[str, Any]:
    """Extract entities and resolve them to KG nodes."""
    # Start with standard extraction
    entities = extract_entities(query)

    # Add KG-specific fields
    entities["kg_nodes"] = []
    entities["kg_intent"] = detect_kg_intent(query)

    # Resolve teams to KG nodes
    for team_name in entities.get("teams", []):
        node = database.find_kg_node_by_name(team_name)
        if node:
            entities["kg_nodes"].append(node)

    # Search for legends mentioned
    query_lower = query.lower()
    legends = database.get_legends(limit=100)
    for legend in legends:
        # Check if legend name is in query
        if legend["name"].lower() in query_lower:
            node = database.find_kg_node_by_name(legend["name"])
            if node:
                entities["kg_nodes"].append(node)

    return entities


def retrieve_kg_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve context from Knowledge Graph."""
    context_parts = []
    sources = []
    kg_intent = entities.get("kg_intent")

    for node in entities.get("kg_nodes", []):
        node_type = node["node_type"]
        entity_id = node["entity_id"]
        node_id = node["node_id"]

        # Get full entity context via graph traversal
        kg_ctx = database.get_entity_context(node_type, entity_id)

        if node_type == "team":
            # Team context
            context_parts.append(f"## {node['name']} Knowledge Graph")

            # Legends
            if kg_ctx.get("legends"):
                legend_names = [e["source_name"] for e in kg_ctx["legends"][:5]]
                context_parts.append(f"**Legends**: {', '.join(legend_names)}")
                sources.extend([{"type": "kg_legend", "name": n} for n in legend_names])

            # Rivalries
            if kg_ctx.get("rivalries"):
                for rival in kg_ctx["rivalries"]:
                    weight = rival.get("weight", 0)
                    intensity = "fierce" if weight >= 0.9 else "strong" if weight >= 0.7 else "notable"
                    context_parts.append(f"**Rivalry**: {intensity} with {rival['target_name']}")
                    sources.append({"type": "kg_rivalry", "rival": rival["target_name"]})

            # Iconic moments
            if kg_ctx.get("moments"):
                context_parts.append("**Iconic Moments**:")
                for moment in kg_ctx["moments"][:4]:
                    moment_node = database.get_kg_node(moment["source_id"])
                    if moment_node and moment_node.get("properties"):
                        props = moment_node["properties"]
                        emotion = props.get("emotion", "")
                        context_parts.append(f"  - {moment['source_name']} ({emotion})")
                        sources.append({"type": "kg_moment", "name": moment["source_name"]})

            # Current mood
            if kg_ctx.get("mood"):
                mood = kg_ctx["mood"]
                context_parts.append(f"**Current Mood**: {mood.get('current_mood', 'unknown')}")
                context_parts.append(f"  Reason: {mood.get('mood_reason', '')}")

        elif node_type == "legend":
            # Legend context
            context_parts.append(f"## Legend: {node['name']}")

            if node.get("properties"):
                props = node["properties"]
                if props.get("era"):
                    context_parts.append(f"**Era**: {props['era']}")
                if props.get("position"):
                    context_parts.append(f"**Position**: {props['position']}")

            # What team
            if kg_ctx.get("team"):
                team = kg_ctx["team"]
                context_parts.append(f"**Club**: {team['name']}")
                sources.append({"type": "kg_team", "name": team["name"]})

            # Multi-hop: get team's rivals (legend's rivalries by extension)
            if kg_intent == "relationship" or kg_intent == "rivalry":
                team_edges = database.get_kg_edges_from(node_id, "legendary_at")
                if team_edges:
                    team_node_id = team_edges[0]["target_id"]
                    rivals = database.get_kg_edges_from(team_node_id, "rival_of")
                    if rivals:
                        rival_names = [r["target_name"] for r in rivals]
                        context_parts.append(f"**Rivalries (via team)**: vs {', '.join(rival_names)}")

    # Special handling for rivalry queries
    if kg_intent == "rivalry" and len(entities.get("kg_nodes", [])) >= 1:
        team_node = next((n for n in entities["kg_nodes"] if n["node_type"] == "team"), None)
        if team_node:
            rivalries = database.get_club_rivalries(team_node["entity_id"])
            if rivalries:
                context_parts.append("\n## Rivalry Details")
                for rivalry in rivalries[:3]:
                    context_parts.append(f"**{rivalry['rival_name']}** ({rivalry['rivalry_type']})")
                    context_parts.append(f"  Intensity: {rivalry['intensity']}/10")
                    if rivalry.get("banter_phrases"):
                        phrases = rivalry["banter_phrases"][:2] if isinstance(rivalry["banter_phrases"], list) else []
                        if phrases:
                            context_parts.append(f"  Banter: {'; '.join(phrases)}")

    # Special handling for moment queries
    if kg_intent == "moment" and entities.get("kg_nodes"):
        team_node = next((n for n in entities["kg_nodes"] if n["node_type"] == "team"), None)
        if team_node:
            moments = database.get_club_moments(team_node["entity_id"], limit=5)
            if moments:
                context_parts.append("\n## Memorable Moments")
                for moment in moments:
                    context_parts.append(f"**{moment['title']}** ({moment.get('date', 'unknown')})")
                    if moment.get("description"):
                        context_parts.append(f"  {moment['description'][:200]}")
                    sources.append({"type": "kg_moment", "id": moment["id"]})

    return "\n".join(context_parts), sources


def retrieve_hybrid(query: str) -> Tuple[str, List[Dict], Dict]:
    """
    Hybrid retrieval combining FTS5 + Knowledge Graph.
    Formula: β=0.60 (FTS5) + γ=0.40 (Graph)
    """
    # Extract entities with KG resolution
    entities = extract_kg_entities(query)

    # Get FTS5 context (standard RAG)
    fts_context, fts_sources = retrieve_context(query)

    # Get KG context
    kg_context, kg_sources = retrieve_kg_context(entities)

    # Get mood for emotional calibration
    team_mood = None
    if entities.get("kg_nodes"):
        team_node = next((n for n in entities["kg_nodes"] if n["node_type"] == "team"), None)
        if team_node:
            team_mood = database.get_club_mood(team_node["entity_id"])

    # Fuse contexts
    fused_context = fuse_contexts(fts_context, kg_context, team_mood)

    # Combine and deduplicate sources
    all_sources = deduplicate_sources(fts_sources + kg_sources)

    # Metadata
    metadata = {
        "entities": {
            "teams": entities.get("teams", []),
            "players": [p.get("name") for p in entities.get("players", [])],
            "kg_nodes": len(entities.get("kg_nodes", [])),
        },
        "kg_intent": entities.get("kg_intent"),
        "mood": team_mood.get("current_mood") if team_mood else None,
        "retrieval_type": "hybrid_kg_rag"
    }

    return fused_context, all_sources, metadata


def fuse_contexts(fts_context: str, kg_context: str, mood: Dict = None) -> str:
    """
    Merge FTS5 + Graph + Mood into rich context.
    Prioritizes graph context for relationship-aware responses.
    """
    parts = []

    # Graph context first (relationship awareness)
    if kg_context:
        parts.append(kg_context)

    # FTS5 results
    if fts_context:
        parts.append("\n## Retrieved Information")
        parts.append(fts_context)

    # Mood calibration
    if mood:
        parts.append(f"\n## Emotional Context")
        parts.append(f"Current mood: {mood.get('current_mood', 'neutral')}")
        parts.append(f"Intensity: {mood.get('mood_intensity', 5)}/10")
        if mood.get("mood_reason"):
            parts.append(f"Reason: {mood['mood_reason']}")

    return "\n".join(parts)


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    # Test entity extraction
    test_queries = [
        "How did Manchester United play yesterday?",
        "Is Haaland injured?",
        "What's the score of the Arsenal game?",
        "Show me Liverpool's upcoming fixtures",
        "Premier League standings",
        "Transfer news for Chelsea",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        entities = extract_entities(query)
        print(f"Entities: {entities}")
        print(f"Intent: {entities['intent']}")
