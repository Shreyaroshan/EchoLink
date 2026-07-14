"""
EchoLink API — FastAPI Backend
==============================
Endpoints:
  GET /                         → Health check
  GET /stats                    → Database overview
  GET /search?q=&limit=         → Track autocomplete
  GET /recommend?track=&limit=&ruleset_id=&sort_by=
                                → Recommendations for a track
  GET /rulesets                 → All mining run metadata
  GET /benchmark                → Algorithm comparison data
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import database as db

# ── Fix 1: Safe column map — column names come from THIS dict, never from raw user input.
# The f-string below uses sort_col (our value), not sort_by (user input).
# The whitelist validation above is still the primary guard; this map is the structural fix.
SORT_COLUMN_MAP: dict[str, str] = {
    "jaccard":    "r.jaccard",
    "confidence": "r.confidence",
    "pair_count": "r.pair_count",
    "lift":       "r.lift",
}

# ── APP SETUP ─────────────────────────────────────────────────────────
app = FastAPI(
    title="EchoLink API",
    description="Music recommendation engine powered by association rule mining",
    version="1.0.0",
)

# CORS — allow the frontend (any origin in dev) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
def root():
    """Health check — confirms API and DB are up."""
    result = db.query_one("SELECT COUNT(*) AS rule_count FROM rules;")
    return {
        "status": "ok",
        "service": "EchoLink API",
        "version": "1.0.0",
        "rule_count": result["rule_count"] if result else 0,
    }


# ══════════════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════════════

@app.get("/stats", tags=["Stats"])
def get_stats():
    """Database overview — rule counts, top tracks, rulesets."""

    total_tracks = db.query_one("SELECT COUNT(*) AS n FROM tracks;")["n"]
    total_rules  = db.query_one("SELECT COUNT(*) AS n FROM rules;")["n"]

    # Top 10 most-recommended tracks (appear most as consequent)
    top_recommended = db.query("""
        SELECT r.consequent AS track,
               t.artistname,
               t.trackname,
               COUNT(*) AS times_recommended
        FROM   rules r
        LEFT JOIN tracks t ON t.item = r.consequent
        WHERE  r.ruleset_id = 1
        GROUP  BY r.consequent, t.artistname, t.trackname
        ORDER  BY times_recommended DESC
        LIMIT  10;
    """)

    # Top 10 tracks with most antecedent rules (most connected)
    top_connected = db.query("""
        SELECT r.antecedent AS track,
               t.artistname,
               t.trackname,
               COUNT(*) AS outgoing_rules
        FROM   rules r
        LEFT JOIN tracks t ON t.item = r.antecedent
        WHERE  r.ruleset_id = 1
        GROUP  BY r.antecedent, t.artistname, t.trackname
        ORDER  BY outgoing_rules DESC
        LIMIT  10;
    """)

    rulesets = db.query("""
        SELECT id, algorithm, min_support, min_pair_count,
               min_confidence, min_jaccard, runtime_seconds,
               rule_count, run_date::text, notes
        FROM   rulesets ORDER BY id;
    """)

    return {
        "total_tracks":    total_tracks,
        "total_rules":     total_rules,
        "rulesets":        rulesets,
        "top_recommended": top_recommended,
        "top_connected":   top_connected,
    }


# ══════════════════════════════════════════════════════════════════════
# SEARCH (autocomplete)
# ══════════════════════════════════════════════════════════════════════

@app.get("/search", tags=["Search"])
def search_tracks(
    q:          str = Query(..., min_length=1, description="Search query"),
    limit:      int = Query(10, ge=1, le=50,   description="Max results"),
    ruleset_id: int = Query(1,  ge=1,           description="Only return tracks that have rules in this ruleset"),
):
    """
    Autocomplete search for tracks.
    Searches both artistname and trackname.
    Fix 2: respects ruleset_id — only returns tracks with rules in the requested ruleset.
    This means switching to FP-Growth in the frontend filters autocomplete to the 118 FP-Growth songs.
    """
    results = db.query("""
        SELECT item, artistname, trackname FROM (
            SELECT DISTINCT t.item, t.artistname, t.trackname,
                   CASE WHEN LOWER(t.item) = LOWER(%s) THEN 0
                        WHEN LOWER(t.item) LIKE LOWER(%s) THEN 1
                        ELSE 2
                   END AS sort_key
            FROM   tracks t
            WHERE  (LOWER(t.artistname) LIKE LOWER(%s)
                 OR LOWER(t.trackname)  LIKE LOWER(%s)
                 OR LOWER(t.item)       LIKE LOWER(%s))
            AND EXISTS (
                SELECT 1 FROM rules r WHERE r.antecedent = t.item AND r.ruleset_id = %s
            )
        ) sub
        ORDER BY sort_key, artistname, trackname
        LIMIT %s;
    """, (q, f"{q}%", f"%{q}%", f"%{q}%", f"%{q}%", ruleset_id, limit))

    return {
        "query":      q,
        "ruleset_id": ruleset_id,
        "count":      len(results),
        "results":    results,
    }


# ══════════════════════════════════════════════════════════════════════
# RECOMMEND
# ══════════════════════════════════════════════════════════════════════

@app.get("/recommend", tags=["Recommend"])
def get_recommendations(
    track:               str  = Query(..., description="Exact track name (item identifier)"),
    limit:               int  = Query(10, ge=1, le=50, description="Number of recommendations"),
    ruleset_id:          int  = Query(1,  ge=1,        description="Ruleset to use (1=Apriori, 2=FP-Growth)"),
    sort_by:             str  = Query("jaccard",       description="Sort metric: jaccard | confidence | pair_count | lift"),
    exclude_same_artist: bool = Query(True,            description="Exclude recommendations from the same artist as the seed track"),
):
    """
    Get song recommendations for a given track.
    Returns top N rules where antecedent = track, sorted by chosen metric.

    By default, same-artist recommendations are excluded because within-artist
    co-occurrence dominates Jaccard scores (people put many songs from the same
    artist in one playlist), burying cross-artist discovery signals.
    Set exclude_same_artist=false to see the raw ranked list.
    """
    # Validate sort_by
    valid_sorts = {"jaccard", "confidence", "pair_count", "lift"}
    if sort_by not in valid_sorts:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of: {valid_sorts}")

    # Check track exists
    track_info = db.query_one(
        "SELECT item, artistname, trackname FROM tracks WHERE item = %s;",
        (track,)
    )
    if not track_info:
        raise HTTPException(status_code=404, detail=f"Track not found: '{track}'")

    # Check ruleset exists
    ruleset = db.query_one("SELECT id, algorithm FROM rulesets WHERE id = %s;", (ruleset_id,))
    if not ruleset:
        raise HTTPException(status_code=404, detail=f"Ruleset {ruleset_id} not found")

    seed_artist = track_info["artistname"]

    # Fix 7: Get total rule count for this track+ruleset before paging
    total_count_row = db.query_one(
        "SELECT COUNT(*) AS n FROM rules WHERE antecedent = %s AND ruleset_id = %s;",
        (track, ruleset_id)
    )
    total_count = total_count_row["n"] if total_count_row else 0

    # Fix 1: Use SORT_COLUMN_MAP so the SQL column comes from our code, not user input
    sort_col = SORT_COLUMN_MAP[sort_by]

    # When filtering same-artist results, fetch ALL rules for this track so we don't
    # exhaust the pool before finding enough cross-artist results.
    # Example: Coldplay - Yellow has 59 rules, top 25 are all Coldplay → limit*5 misses everything.
    fetch_limit = total_count if exclude_same_artist else limit
    if fetch_limit == 0:
        fetch_limit = limit

    # Get recommendations (fetch extra pool when filtering same-artist)
    all_recs = db.query(f"""
        SELECT r.consequent  AS track,
               t.artistname,
               t.trackname,
               r.confidence,
               r.jaccard,
               r.lift,
               r.pair_count,
               r.support
        FROM   rules r
        LEFT JOIN tracks t ON t.item = r.consequent
        WHERE  r.antecedent  = %s
        AND    r.ruleset_id  = %s
        ORDER  BY {sort_col} DESC
        LIMIT  %s;
    """, (track, ruleset_id, fetch_limit))

    # Count same-artist results in the full pool
    same_artist_count = sum(
        1 for r in all_recs if r.get("artistname") == seed_artist
    )

    # Apply same-artist filter if requested, then trim to requested limit
    if exclude_same_artist:
        recommendations = [
            r for r in all_recs if r.get("artistname") != seed_artist
        ][:limit]
    else:
        recommendations = all_recs[:limit]

    if not recommendations:
        msg = (
            f"No cross-artist rules found for this track in ruleset {ruleset_id}. "
            f"Found {same_artist_count} same-artist rules (toggle 'Exclude same artist' off to see them). "
            f"Total rules in DB: {total_count}"
            if exclude_same_artist and same_artist_count > 0
            else f"No rules found for this track in ruleset {ruleset_id}."
        )
        return {
            "track":               track_info,
            "ruleset":             ruleset,
            "sort_by":             sort_by,
            "exclude_same_artist": exclude_same_artist,
            "same_artist_count":   same_artist_count,
            "total_count":         total_count,   # Fix 7: total in DB, not just this page
            "count":               0,
            "recommendations":     [],
            "message":             msg,
        }

    return {
        "track":               track_info,
        "ruleset":             ruleset,
        "sort_by":             sort_by,
        "exclude_same_artist": exclude_same_artist,
        "same_artist_count":   same_artist_count,
        "total_count":         total_count,   # Fix 7: total rules in DB for this track+ruleset
        "count":               len(recommendations),
        "recommendations":     recommendations,
    }


# ══════════════════════════════════════════════════════════════════════
# RULESETS
# ══════════════════════════════════════════════════════════════════════

@app.get("/rulesets", tags=["Rulesets"])
def get_rulesets():
    """All mining run metadata."""
    rulesets = db.query("""
        SELECT id, algorithm, min_support, min_pair_count,
               min_confidence, min_jaccard, runtime_seconds,
               rule_count, run_date::text, notes
        FROM   rulesets
        ORDER  BY id;
    """)
    return {"rulesets": rulesets}


@app.get("/rulesets/{ruleset_id}", tags=["Rulesets"])
def get_ruleset(ruleset_id: int):
    """Single ruleset details with sample top rules."""
    ruleset = db.query_one(
        "SELECT * FROM rulesets WHERE id = %s;", (ruleset_id,)
    )
    if not ruleset:
        raise HTTPException(status_code=404, detail=f"Ruleset {ruleset_id} not found")

    # Top 5 rules by Jaccard for this ruleset
    top_rules = db.query("""
        SELECT antecedent, consequent, jaccard, confidence, pair_count
        FROM   rules
        WHERE  ruleset_id = %s
        ORDER  BY jaccard DESC
        LIMIT  5;
    """, (ruleset_id,))

    return {**ruleset, "top_rules": top_rules}


# ══════════════════════════════════════════════════════════════════════
# BENCHMARK
# ══════════════════════════════════════════════════════════════════════

@app.get("/benchmark", tags=["Benchmark"])
def get_benchmark():
    """
    Side-by-side algorithm comparison for the benchmark dashboard.
    Returns runtime, rule counts, and quality metrics per ruleset.
    """
    rulesets = db.query("""
        SELECT id, algorithm, min_support, min_pair_count,
               min_confidence, min_jaccard, runtime_seconds, rule_count
        FROM   rulesets ORDER BY id;
    """)

    comparison = []
    for rs in rulesets:
        # Quality stats for this ruleset
        stats = db.query_one("""
            SELECT AVG(jaccard)    AS avg_jaccard,
                   AVG(confidence) AS avg_confidence,
                   AVG(lift)       AS avg_lift,
                   MAX(jaccard)    AS max_jaccard,
                   MAX(pair_count) AS max_pair_count
            FROM   rules
            WHERE  ruleset_id = %s;
        """, (rs["id"],))

        comparison.append({
            "id":               rs["id"],
            "algorithm":        rs["algorithm"],
            "min_support":      rs["min_support"],
            "min_pair_count":   rs["min_pair_count"],
            "min_confidence":   rs["min_confidence"],
            "runtime_seconds":  rs["runtime_seconds"],
            "rule_count":       rs["rule_count"],
            "avg_jaccard":      round(stats["avg_jaccard"] or 0, 4),
            "avg_confidence":   round(stats["avg_confidence"] or 0, 4),
            "avg_lift":         round(stats["avg_lift"] or 0, 2),
            "max_jaccard":      round(stats["max_jaccard"] or 0, 4),
            "max_pair_count":   stats["max_pair_count"] or 0,
        })

    # Fix 5: Guard against empty rulesets (e.g. DB wiped before reload).
    # Return null for unpopulated summary fields instead of crashing.
    return {
        "benchmark": comparison,
        "summary": {
            "fastest_algorithm": min(rulesets, key=lambda r: r["runtime_seconds"])["algorithm"]
                                 if rulesets else None,
            "most_rules":        max(rulesets, key=lambda r: r["rule_count"])["algorithm"]
                                 if rulesets else None,
            "speedup_factor":    round(
                max(r["runtime_seconds"] for r in rulesets) /
                min(r["runtime_seconds"] for r in rulesets), 1
            ) if len(rulesets) >= 2 else None,
        }
    }
