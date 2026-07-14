import pytest
from unittest.mock import patch, MagicMock

# Import the FastAPI endpoints to test, making sure import resolves
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import main

# ══════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════

@patch("main.db.query_one")
def test_health_check_unit(mock_query_one, client):
    """Test health check endpoint with mocked database count."""
    mock_query_one.return_value = {"rule_count": 127246}
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "EchoLink API"
    assert data["rule_count"] == 127246
    mock_query_one.assert_called_once_with("SELECT COUNT(*) AS rule_count FROM rules;")


# ══════════════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════════════

@patch("main.db.query")
@patch("main.db.query_one")
def test_stats_unit(mock_query_one, mock_query, client):
    """Test stats endpoint returns correct keys and structure."""
    mock_query_one.side_effect = [
        {"n": 46151},  # tracks count
        {"n": 127246}  # rules count
    ]
    mock_query.side_effect = [
        [{"track": "Consequent 1", "artistname": "Artist 1", "trackname": "Track 1", "times_recommended": 5}], # top_recommended
        [{"track": "Antecedent 1", "artistname": "Artist 2", "trackname": "Track 2", "outgoing_rules": 10}], # top_connected
        [{"id": 1, "algorithm": "Apriori", "rule_count": 126945, "notes": "notes"}] # rulesets
    ]

    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tracks"] == 46151
    assert data["total_rules"] == 127246
    assert len(data["top_recommended"]) == 1
    assert len(data["top_connected"]) == 1
    assert len(data["rulesets"]) == 1


# ══════════════════════════════════════════════════════════════════════
# SEARCH
# ══════════════════════════════════════════════════════════════════════

@patch("main.db.query")
def test_search_unit(mock_query, client):
    """Test search autocomplete with mocks."""
    mock_query.return_value = [
        {"item": "Coldplay - Yellow", "artistname": "Coldplay", "trackname": "Yellow"}
    ]
    
    response = client.get("/search?q=yellow&limit=5&ruleset_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "yellow"
    assert data["ruleset_id"] == 1
    assert data["count"] == 1
    assert data["results"][0]["trackname"] == "Yellow"


# ══════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════

@patch("main.db.query")
@patch("main.db.query_one")
def test_recommend_unit_success(mock_query_one, mock_query, client):
    """Test recommendations when same-artist exclusion is active."""
    # Mocking track existence check
    mock_query_one.side_effect = [
        {"item": "Coldplay - Yellow", "artistname": "Coldplay", "trackname": "Yellow"}, # track_info
        {"id": 1, "algorithm": "Apriori"}, # ruleset existence check
        {"n": 3} # total rule count
    ]
    
    # Mocking returning rules list (some from Coldplay, some from other artists)
    mock_query.return_value = [
        {"track": "Coldplay - Clocks", "artistname": "Coldplay", "trackname": "Clocks", "confidence": 0.8, "jaccard": 0.4, "lift": 5.0, "pair_count": 100, "support": 0.005},
        {"track": "Keane - Somewhere Only We Know", "artistname": "Keane", "trackname": "Somewhere Only We Know", "confidence": 0.6, "jaccard": 0.35, "lift": 4.5, "pair_count": 80, "support": 0.004},
        {"track": "Snow Patrol - Chasing Cars", "artistname": "Snow Patrol", "trackname": "Chasing Cars", "confidence": 0.5, "jaccard": 0.3, "lift": 4.0, "pair_count": 60, "support": 0.003}
    ]
    
    # Requesting with exclude_same_artist=True (default)
    response = client.get("/recommend?track=Coldplay - Yellow&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["track"]["trackname"] == "Yellow"
    # Should exclude Coldplay - Clocks
    assert data["count"] == 2
    assert data["recommendations"][0]["artistname"] == "Keane"
    assert data["recommendations"][1]["artistname"] == "Snow Patrol"


@patch("main.db.query")
@patch("main.db.query_one")
def test_recommend_unit_include_same_artist(mock_query_one, mock_query, client):
    """Test recommendations when same-artist exclusion is disabled."""
    mock_query_one.side_effect = [
        {"item": "Coldplay - Yellow", "artistname": "Coldplay", "trackname": "Yellow"},
        {"id": 1, "algorithm": "Apriori"},
        {"n": 3}
    ]
    mock_query.return_value = [
        {"track": "Coldplay - Clocks", "artistname": "Coldplay", "trackname": "Clocks", "confidence": 0.8, "jaccard": 0.4, "lift": 5.0, "pair_count": 100, "support": 0.005},
        {"track": "Keane - Somewhere Only We Know", "artistname": "Keane", "trackname": "Somewhere Only We Know", "confidence": 0.6, "jaccard": 0.35, "lift": 4.5, "pair_count": 80, "support": 0.004}
    ]
    
    response = client.get("/recommend?track=Coldplay - Yellow&limit=10&exclude_same_artist=false")
    assert response.status_code == 200
    data = response.json()
    # Should include Coldplay - Clocks
    assert data["count"] == 2
    assert data["recommendations"][0]["artistname"] == "Coldplay"


@patch("main.db.query_one")
def test_recommend_unit_not_found(mock_query_one, client):
    """Test recommend endpoint returns 404 if seed track does not exist."""
    mock_query_one.return_value = None  # Track not found
    
    response = client.get("/recommend?track=Unknown - Unknown")
    assert response.status_code == 404
    assert "Track not found" in response.json()["detail"]


@patch("main.db.query_one")
def test_recommend_unit_invalid_sort(mock_query_one, client):
    """Test recommend endpoint returns 400 for invalid sort_by metric."""
    response = client.get("/recommend?track=Coldplay - Yellow&sort_by=invalid")
    assert response.status_code == 400
    assert "sort_by must be one of" in response.json()["detail"]


# ══════════════════════════════════════════════════════════════════════
# BENCHMARK
# ══════════════════════════════════════════════════════════════════════

@patch("main.db.query")
@patch("main.db.query_one")
def test_benchmark_unit(mock_query_one, mock_query, client):
    """Test benchmark endpoint computes speedup and quality stats correctly."""
    mock_query.return_value = [
        {"id": 1, "algorithm": "Apriori", "min_support": 20, "min_pair_count": 50, "min_confidence": 0.1, "runtime_seconds": 90.0, "rule_count": 100000},
        {"id": 2, "algorithm": "FP-Growth", "min_support": 800, "min_pair_count": 0, "min_confidence": 0.5, "runtime_seconds": 10.0, "rule_count": 500}
    ]
    # mock live DB stats computed for ruleset 1 and then ruleset 2
    mock_query_one.side_effect = [
        {"avg_jaccard": 0.05, "avg_confidence": 0.25, "avg_lift": 12.5, "max_jaccard": 0.6, "max_pair_count": 500}, # RS 1 stats
        {"avg_jaccard": 0.15, "avg_confidence": 0.75, "avg_lift": 85.0, "max_jaccard": 0.8, "max_pair_count": 1000} # RS 2 stats
    ]

    response = client.get("/benchmark")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["benchmark"]) == 2
    assert data["benchmark"][0]["avg_jaccard"] == 0.05
    assert data["benchmark"][1]["avg_jaccard"] == 0.15
    
    # Speedup = 90.0 / 10.0 = 9.0
    assert data["summary"]["speedup_factor"] == 9.0
    assert data["summary"]["fastest_algorithm"] == "FP-Growth"
    assert data["summary"]["most_rules"] == "Apriori"


@patch("main.db.query")
def test_benchmark_unit_empty_db(mock_query, client):
    """Test benchmark endpoint handles empty database (no rulesets) without crashing."""
    mock_query.return_value = [] # No rulesets
    
    response = client.get("/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert len(data["benchmark"]) == 0
    assert data["summary"]["fastest_algorithm"] is None
    assert data["summary"]["speedup_factor"] is None
