# EchoLink API — Documentation & Testing Guide

## How to Start the Server

Navigate to the API directory and run:

```bash
cd /Users/shreyaroshan/Downloads/archive/echolink_api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**What each flag means:**
- `main:app` — load the FastAPI `app` object from `main.py`
- `--host 0.0.0.0` — accept connections from any network interface (not just localhost)
- `--port 8000` — listen on port 8000
- `--reload` — automatically restart the server whenever you save a `.py` file (dev mode only)

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [...]
INFO:     Application startup complete.
```

---

## How We Verified the API Was Running

### Step 1 — Health Check via `curl`

```bash
curl -s http://localhost:8000/ | python3 -m json.tool
```

`curl -s` sends a silent HTTP GET request.  
`python3 -m json.tool` pretty-prints the JSON response.

**Response we got:**
```json
{
    "status": "ok",
    "service": "EchoLink API",
    "version": "1.0.0",
    "rule_count": 127246
}
```
This confirmed the server was up AND the database was connected (it queried the `rules` table and returned the count).

---

### Step 2 — Recommend Endpoint

```bash
curl -s "http://localhost:8000/recommend?track=Daft%20Punk%20-%20Get%20Lucky&limit=5"
```

> `%20` is the URL-encoded space character. Spaces in query parameters must be encoded.

**Response confirmed:**
- Track was found in the `tracks` table
- 5 recommendations returned (all Random Access Memories album tracks)
- All quality metrics (jaccard, confidence, lift, pair_count) populated correctly

---

### Step 3 — Search Endpoint

```bash
curl -s "http://localhost:8000/search?q=coldplay&limit=5"
```

**Response confirmed:**
- 5 Coldplay tracks returned, alphabetically ordered
- Only tracks that have at least one outgoing rule were returned (the `EXISTS` filter)

---

### Step 4 — Benchmark Endpoint

```bash
curl -s "http://localhost:8000/benchmark"
```

**Response confirmed:**
- Both rulesets (Apriori + FP-Growth) returned with computed quality stats
- Speedup factor of 15x correctly calculated

---

### Interactive Docs (Swagger UI)

FastAPI automatically generates an interactive API explorer.  
Open in your browser: **http://localhost:8000/docs**

You can test every endpoint visually — fill in parameters and click Execute.

---

## Architecture Overview

```
Client (Browser / curl)
        │
        ▼
  FastAPI (main.py)         ← routes, validation, response shaping
        │
        ▼
  database.py               ← connection pool, helper functions
        │
        ▼
  PostgreSQL (echolink DB)
    ├── tracks    (46,151 rows)
    ├── rulesets  (2 rows)
    └── rules     (127,246 rows)
```

**Connection pool** (`psycopg2.ThreadedConnectionPool`):  
Keeps 2–10 persistent connections open. Each API request borrows one, uses it, and returns it — much faster than opening a new connection per request.

---

## Endpoint Reference

---

### `GET /`
**Purpose:** Health check. Confirms the API server is running and the database is reachable.

**Parameters:** None

**Example:**
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "status": "ok",
  "service": "EchoLink API",
  "version": "1.0.0",
  "rule_count": 127246
}
```

**What it does internally:**
Runs `SELECT COUNT(*) FROM rules` to verify the DB connection is alive and returns the total rule count as a quick sanity check.

---

### `GET /search`
**Purpose:** Autocomplete search — find tracks by artist or track name. Used by the UI's search bar.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `q` | string | ✅ Yes | — | Search query (min 1 character) |
| `limit` | int | No | 10 | Max results to return (1–50) |

**Example:**
```bash
curl "http://localhost:8000/search?q=radiohead&limit=3"
```

**Response:**
```json
{
  "query": "radiohead",
  "count": 3,
  "results": [
    { "item": "Radiohead - Creep", "artistname": "Radiohead", "trackname": "Creep" },
    { "item": "Radiohead - Fake Plastic Trees", "artistname": "Radiohead", "trackname": "Fake Plastic Trees" },
    { "item": "Radiohead - Karma Police", "artistname": "Radiohead", "trackname": "Karma Police" }
  ]
}
```

**How it works:**
- Searches `artistname`, `trackname`, and the combined `item` column using `LIKE %query%`
- **Only returns tracks that have at least one association rule** (the `EXISTS` subquery). This ensures the search only shows tracks the recommendation engine can actually handle — no dead ends.
- Ordering: exact matches first → starts-with matches → contains matches → alphabetical

---

### `GET /recommend`
**Purpose:** Core recommendation engine. Given a track name, returns the top N associated songs ranked by a chosen metric.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `track` | string | ✅ Yes | — | Exact item name (e.g., `Daft Punk - Get Lucky`) |
| `limit` | int | No | 10 | Number of recommendations (1–50) |
| `ruleset_id` | int | No | 1 | Which mining run to use (1 = Apriori, 2 = FP-Growth) |
| `sort_by` | string | No | `jaccard` | Ranking metric: `jaccard`, `confidence`, `pair_count`, `lift` |

**Example:**
```bash
curl "http://localhost:8000/recommend?track=Coldplay%20-%20Yellow&limit=3&sort_by=pair_count"
```

**Response:**
```json
{
  "track": {
    "item": "Coldplay - Yellow",
    "artistname": "Coldplay",
    "trackname": "Yellow"
  },
  "ruleset": { "id": 1, "algorithm": "Apriori" },
  "sort_by": "pair_count",
  "count": 3,
  "recommendations": [
    {
      "track": "Coldplay - The Scientist",
      "artistname": "Coldplay",
      "trackname": "The Scientist",
      "confidence": 0.4424,
      "jaccard": 0.2726,
      "lift": 55.2,
      "pair_count": 380,
      "support": 0.002346
    }
  ]
}
```

**What each metric means:**

| Metric | Meaning | Good for |
|---|---|---|
| `jaccard` | % of playlists with **either** song that have **both** | Most balanced — default |
| `confidence` | % of Song A's playlists that also have Song B | Directional strength |
| `pair_count` | Raw number of playlists containing both songs | Raw popularity of the pair |
| `lift` | How much more likely the pair is vs. random chance | Statistical significance |
| `support` | % of all playlists containing both songs | Global reach |

**Error cases:**
- `404` if the track name doesn't exist in the `tracks` table
- `404` if the `ruleset_id` doesn't exist
- `400` if `sort_by` is not one of the valid options
- Returns `count: 0` with a helpful message if the track exists but has no rules in the chosen ruleset

---

### `GET /rulesets`
**Purpose:** Returns metadata about all association rule mining runs — which algorithm was used, what thresholds were applied, how many rules were generated, and how long it took.

**Parameters:** None

**Example:**
```bash
curl http://localhost:8000/rulesets
```

**Response:**
```json
{
  "rulesets": [
    {
      "id": 1,
      "algorithm": "Apriori",
      "min_support": 20,
      "min_pair_count": 50,
      "min_confidence": 0.1,
      "min_jaccard": 0.01,
      "runtime_seconds": 95.8,
      "rule_count": 126945,
      "run_date": "2026-07-07T...",
      "notes": "v3 — Fixed popularity bias..."
    },
    {
      "id": 2,
      "algorithm": "FP-Growth",
      "min_support": 809,
      "min_pair_count": 0,
      "min_confidence": 0.5,
      "min_jaccard": 0.05,
      "runtime_seconds": 6.4,
      "rule_count": 301,
      "run_date": "2026-07-07T...",
      "notes": "mlxtend implementation..."
    }
  ]
}
```

**Why this matters:**  
Every rule in the `rules` table has a `ruleset_id` foreign key pointing to this table. This means you can compare recommendations from different algorithms or threshold configurations side-by-side without reprocessing the data.

---

### `GET /rulesets/{ruleset_id}`
**Purpose:** Single ruleset detail with a preview of its top 5 rules by Jaccard.

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ruleset_id` | int (path) | ✅ Yes | ID of the ruleset |

**Example:**
```bash
curl http://localhost:8000/rulesets/1
```

**Response:** Same as a single ruleset object, plus:
```json
{
  "top_rules": [
    {
      "antecedent": "Lecrae - Timepiece",
      "consequent": "Lecrae - Wish",
      "jaccard": 1.0,
      "confidence": 1.0,
      "pair_count": 27
    }
  ]
}
```

---

### `GET /benchmark`
**Purpose:** Side-by-side algorithm comparison for the benchmark dashboard. Returns runtime, rule counts, and average quality metrics for each ruleset.

**Parameters:** None

**Example:**
```bash
curl http://localhost:8000/benchmark
```

**Response:**
```json
{
  "benchmark": [
    {
      "id": 1,
      "algorithm": "Apriori",
      "min_support": 20,
      "min_pair_count": 50,
      "min_confidence": 0.1,
      "runtime_seconds": 95.8,
      "rule_count": 126945,
      "avg_jaccard": 0.3078,
      "avg_confidence": 0.4797,
      "avg_lift": 593.2,
      "max_jaccard": 1.0,
      "max_pair_count": 617
    },
    {
      "id": 2,
      "algorithm": "FP-Growth",
      "min_support": 809,
      "min_pair_count": 0,
      "min_confidence": 0.5,
      "runtime_seconds": 6.4,
      "rule_count": 301,
      "avg_jaccard": 0.096,
      "avg_confidence": 0.6062,
      "avg_lift": 13.42,
      "max_jaccard": 0.467,
      "max_pair_count": 617
    }
  ],
  "summary": {
    "fastest_algorithm": "FP-Growth",
    "most_rules": "Apriori",
    "speedup_factor": 15.0
  }
}
```

**What the summary fields mean:**
- `fastest_algorithm` — which algorithm had the lowest `runtime_seconds`
- `most_rules` — which algorithm produced the most rules
- `speedup_factor` — how many times faster the fastest was vs. the slowest (15x here)

> **Note:** The comparison is intentionally unequal — Apriori used `min_support=20` covering 46K items, while FP-Growth required `min_support=809` due to memory constraints. This real-world finding is documented in the benchmark.

---

### `GET /stats`
**Purpose:** Full database overview. Used by the dashboard's summary cards.

**Parameters:** None

**Response includes:**
- `total_tracks` — number of unique songs in the database
- `total_rules` — total rules across all rulesets
- `rulesets` — full list of all mining runs
- `top_recommended` — top 10 songs appearing most often as a **consequent** (most recommended)
- `top_connected` — top 10 songs with the most **antecedent** rules (most connected — these return the most recommendations when searched)

---

## Error Handling

All endpoints return standard HTTP status codes:

| Code | Meaning | Example |
|---|---|---|
| `200` | Success | Normal response |
| `400` | Bad request | Invalid `sort_by` value |
| `404` | Not found | Track doesn't exist, invalid ruleset ID |
| `422` | Validation error | Missing required parameter, wrong type |
| `500` | Server error | Database connection failed |

Error responses follow FastAPI's standard format:
```json
{
  "detail": "Track not found: 'Unknown Artist - Unknown Song'"
}
```
