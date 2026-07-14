import pytest

# Import main to test integration
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database as db

# Check if DB is accessible and populated
try:
    res = db.query_one("SELECT COUNT(*) AS n FROM tracks;")
    if not res or res["n"] == 0:
        pytest.skip("Database is empty. Skipping integration tests.", allow_module_level=True)
except Exception as e:
    pytest.skip(f"Database not available ({e}). Skipping integration tests.", allow_module_level=True)


# ══════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION TEST
# ══════════════════════════════════════════════════════════════════════

def test_db_connection():
    """Verify that we can establish a connection to the PostgreSQL database."""
    conn = db.get_pool().getconn()
    try:
        assert conn is not None
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        res = cur.fetchone()[0]
        assert res == 1
    finally:
        db.get_pool().putconn(conn)


# ══════════════════════════════════════════════════════════════════════
# HEALTH CHECK INTEGRATION TEST
# ══════════════════════════════════════════════════════════════════════

def test_health_check_integration(client):
    """Test health check directly interacts with the database and returns total rule count."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["rule_count"] > 100000  # Database should have ~127k+ rules loaded


# ══════════════════════════════════════════════════════════════════════
# STATS INTEGRATION TEST
# ══════════════════════════════════════════════════════════════════════

def test_stats_integration(client):
    """Test stats returns valid tables and populated top tracks from DB."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tracks"] > 40000
    assert data["total_rules"] > 100000
    assert len(data["rulesets"]) >= 2
    assert len(data["top_recommended"]) == 10
    assert len(data["top_connected"]) == 10


# ══════════════════════════════════════════════════════════════════════
# SEARCH INTEGRATION TEST
# ══════════════════════════════════════════════════════════════════════

def test_search_integration(client):
    """Test search retrieves real items (such as Coldplay or Daft Punk) from live DB."""
    # Search for "Coldplay" under Apriori (ruleset 1)
    response = client.get("/search?q=coldplay&ruleset_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    # Every item returned should contain "coldplay" in the artist name or item string
    assert any("coldplay" in track["artistname"].lower() for track in data["results"])


# ══════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS INTEGRATION TEST
# ══════════════════════════════════════════════════════════════════════

def test_recommend_integration(client):
    """Test recommendation engine query, sorting, and same-artist filtering on live DB."""
    track_name = "Coldplay - Yellow"
    
    # 1. Test standard recommendations (excluding same artist, Jaccard descending)
    response = client.get(f"/recommend?track={track_name}&ruleset_id=1&sort_by=jaccard&exclude_same_artist=true&limit=10")
    assert response.status_code == 200
    data = response.json()
    
    assert data["track"]["item"] == track_name
    recs = data["recommendations"]
    assert len(recs) > 0
    
    # Check same-artist filter worked
    assert not any(r["artistname"] == "Coldplay" for r in recs)
    
    # Check Jaccard sorting is sorted DESC
    jaccards = [r["jaccard"] for r in recs]
    assert jaccards == sorted(jaccards, reverse=True)

    # 2. Test standard recommendations including same artist
    response_include = client.get(f"/recommend?track={track_name}&ruleset_id=1&sort_by=jaccard&exclude_same_artist=false&limit=10")
    assert response_include.status_code == 200
    data_include = response_include.json()
    recs_include = data_include["recommendations"]
    
    # Coldplay tracks co-occurring should now be included
    assert any(r["artistname"] == "Coldplay" for r in recs_include)


# ══════════════════════════════════════════════════════════════════════
# BENCHMARK INTEGRATION TEST
# ══════════════════════════════════════════════════════════════════════

def test_benchmark_integration(client):
    """Test benchmark endpoint computes stats across the real rulesets in the DB."""
    response = client.get("/benchmark")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["benchmark"]) >= 2
    assert data["summary"]["fastest_algorithm"] == "FP-Growth"
    assert data["summary"]["most_rules"] == "Apriori"
    assert data["summary"]["speedup_factor"] is not None
    assert data["summary"]["speedup_factor"] > 1.0
