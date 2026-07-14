# EchoLink — Full Project Documentation
*Simple language guide to everything built so far*

---

## What Is EchoLink?

EchoLink is a **music recommendation system** built on a concept called **association rule mining**.

Instead of using machine learning or user profiles, it learns from **161,000 real Spotify playlists** — specifically, which songs people tend to put in the same playlist. If Song A and Song B appear together in hundreds of playlists, EchoLink knows they "go together," and will recommend Song B when someone searches for Song A.

Think of it like this: if you go to a supermarket and observe millions of shopping baskets, you'll notice that chips and salsa are almost always bought together. That's association mining. We're doing the same thing, but with songs and playlists.

---

## Project Architecture (Big Picture)

```
Raw CSV Data (3.3M rows)
       ↓ Phase 1: Clean & Prepare
Baskets (161K playlists as item sets)
       ↓ Phase 2B: Apriori
Association Rules (126K song pairs with strength metrics)
       ↓ Phase 2C: FP-Growth (comparison/benchmark)
Benchmark results (FP-Growth vs Apriori speed comparison)
       ↓ Phase 3: Database
PostgreSQL (tracks, rulesets, rules tables)
       ↓ Phase 4: Backend API
FastAPI server (REST endpoints for recommendations)
       ↓ Phase 5 (next): Frontend
Web App (search bar, results, benchmark dashboard)
```

---

## Phase 1 — Data Preprocessing

**Script:** `phase_1a_clean.py`, `phase_1cde_clean.py`  
**Input:** Raw Spotify playlist CSV  
**Output:** `spotify_clean.csv`, `item_lookup.csv`

### What the raw data looked like

The raw dataset had **3.3 million rows**, each representing one song in one playlist. A single playlist might have 30 rows (one per song). Each row had:
- `user_id` — who created the playlist (hashed, anonymous)
- `playlistname` — what the user named the playlist
- `artistname` — artist of the track
- `trackname` — name of the track

### What we needed to change

**Problem 1 — No unique playlist ID:**  
The raw data doesn't have a playlist ID column. We needed to identify each unique playlist so we could treat it as one "basket."

**Solution:** We created a `basket_id` by combining `user_id + playlistname`:
```
"abc123||Chill Vibes"   ← user abc123's playlist named Chill Vibes
"xyz789||Gym Hits"      ← user xyz789's playlist named Gym Hits
```
This way, even if two different users both have a playlist called "Chill Vibes," they're treated as separate baskets.

**Problem 2 — No single item identifier:**  
We needed one column to uniquely identify a song. Artist name alone isn't unique (multiple songs by same artist). Track name alone isn't unique (same song name by different artists).

**Solution:** We created an `item` column = `"Artist - Track"`:
```
"Daft Punk - Get Lucky"
"Coldplay - Yellow"
```

**Problem 3 — Duplicates:**  
Some playlists had the same song listed twice. We removed duplicates within each basket — a song is either in a playlist or it isn't.

### Output files

**`spotify_clean.csv`** — cleaned version with columns: `basket_id`, `item`, `artistname`, `trackname`

**`item_lookup.csv`** — unique list of all 46,151 distinct tracks with their artist and track name separated. Used by the UI to display human-readable names.

---

## Phase 2B — Apriori Algorithm (Custom Implementation)

**Script:** `phase_2b_apriori.py`  
**Input:** `spotify_clean.csv`  
**Output:** `apriori_rules.csv`

### What is Apriori?

Apriori is a classic data mining algorithm that finds **pairs of items that frequently appear together**.

It works in steps:
1. Count how many times each individual item appears *(which songs appear in 20+ playlists?)*
2. For each pair of frequent items, count how many times they appear **in the same basket**
3. For pairs that co-occur enough times, calculate quality metrics
4. Output rules: *"If playlist has Song A → it likely also has Song B"*

### The Basket Concept

We converted our data into **baskets** — each basket is one playlist as a set of songs:

```
basket_id: "userA||Chill Vibes"
items: {Daft Punk - Get Lucky, Coldplay - Yellow, Radiohead - Creep}

basket_id: "userB||Gym Hits"
items: {Eminem - Lose Yourself, AC/DC - Thunderstruck}
```

Pairs are only counted **within the same basket** — never across baskets. This is crucial — it means the co-occurrence naturally captures playlist context.

### The 4 Quality Metrics

For every pair of songs (A, B), we calculate:

**1. Support**
> "What fraction of ALL playlists contain both songs?"

```
support = pair_count / total_baskets
```
A support of 0.003 means the pair appears in 0.3% of all playlists (about 480 out of 161,953).

**2. Confidence**
> "Of all playlists containing Song A, what % also contain Song B?"

```
confidence = pair_count / count_A
```
Confidence of 0.48 means: if a playlist has "Get Lucky," there's a 48% chance it also has "Lose Yourself to Dance."

**3. Lift**
> "How much more likely is this pair vs. pure random chance?"

```
lift = confidence / (count_B / total_baskets)
```
Lift > 1 means the pair appears more than random. Higher = stronger association.

*⚠️ Problem with Lift:* Rare songs get astronomically high lift values (1000+) just because they're rare — not because the association is meaningful. Lift alone is misleading for this dataset.

**4. Jaccard Similarity**
> "Of all playlists containing EITHER song, what % contain BOTH?"

```
jaccard = pair_count / (count_A + count_B - pair_count)
```
Jaccard ranges from 0 to 1. It's not fooled by rarity. A Jaccard of 0.38 means 38% of playlists that have either song have both — that's a genuinely strong relationship.

*We use Jaccard as the primary ranking metric* because it's balanced and unaffected by how popular or obscure a song is.

---

### The Popularity Bias Problem (and How We Fixed It)

**Version 1 (broken):** We initially used `MIN_CONFIDENCE = 0.5` as the filter.

This accidentally excluded **all popular tracks** like "Daft Punk - Get Lucky."

**Why?** "Get Lucky" appears in 1,273 playlists — summer playlists, pop playlists, party playlists, gym playlists, road trip playlists, etc. Because it's so popular and diverse, no single song appears alongside it in more than 50% of those playlists. So confidence never reaches 0.5, even when the actual co-occurrence count is 617 times!

**Niche tracks don't have this problem.** The Lord of the Rings soundtrack (Howard Shore) appears in 26 playlists — all of which are dedicated LOTR soundtrack playlists. Every single one has all the same tracks. So confidence = 1.0 (100%). Niche tracks always travel together.

```
Result: Our old rule set had ZERO rules for "Daft Punk - Get Lucky"
        but 21 rules for "Howard Shore - Éowyn's Dream" ❌
```

**Version 2 (fixed):** We switched to an **absolute pair count** as the main filter:

```python
MIN_PAIR_COUNT = 50   # must appear together in at least 50 playlists
MIN_CONF       = 0.1  # loose 10% confidence (just a weak directional signal)
MIN_JACCARD    = 0.01 # very loose, used for ranking only
```

Now "Get Lucky" + "Lose Yourself to Dance" (which co-occur in 617 playlists) easily passes the 50-basket threshold. The result:

```
"Daft Punk - Get Lucky" now has 41 rules:
  → Give Life Back to Music   pair_count: 538
  → Lose Yourself to Dance    pair_count: 617
  → Instant Crush             pair_count: 552
  → Doin' it Right            pair_count: 537
  ... (all Random Access Memories album tracks)
```

### Final Output

**`apriori_rules.csv`** — 126,945 rows, sorted by Jaccard descending.

Each row is one directional rule:
```
antecedent, consequent, support, confidence, lift, jaccard, pair_count, count_a, count_b
"Daft Punk - Get Lucky", "Daft Punk - Lose Yourself to Dance", 0.00381, 0.4847, 78.18, 0.3717, 617, 1273, 900
```

Note: rules are **directional** — `A → B` and `B → A` are stored as separate rows because their confidence values differ. (If Get Lucky has 1273 appearances and Lose Yourself has 900, then `Get Lucky → Lose Yourself` has conf 617/1273=0.48, but `Lose Yourself → Get Lucky` has conf 617/900=0.69.)

---

## Phase 2C — FP-Growth Benchmark

**Script:** `phase_2c_fpgrowth.py`  
**Input:** `spotify_clean.csv`  
**Output:** `fpgrowth_rules.csv`, benchmark timing data

### What is FP-Growth?

FP-Growth is a smarter alternative to Apriori. Instead of counting every pair explicitly, it builds a compressed data structure called an **FP-Tree** (Frequent Pattern Tree) and mines rules from that.

**Analogy:** Apriori is like reading every book in a library one by one to find common themes. FP-Growth first builds an index of the library and then mines from the index — much faster.

### Why We Ran It

We ran FP-Growth purely as a **benchmark** — to compare its speed and output against our custom Apriori.

### The Memory Problem

FP-Growth (via the `mlxtend` Python library) requires converting the data into a **dense matrix** — a grid where every row is a playlist and every column is a song. With 161,953 playlists and 46,151 songs, this grid would have **7.4 BILLION cells**. That would crash any normal computer.

**Solution:** We raised the minimum support threshold to 809 (the top 118 most popular songs only). This made the matrix small enough to fit in RAM.

This is a real-world trade-off: FP-Growth is faster *at the mining step*, but needs preprocessing to reduce the item space for sparse datasets like this.

### Results

| Metric | Apriori (custom) | FP-Growth (mlxtend) |
|---|---|---|
| Min support | 20 baskets | 809 baskets |
| Items in scope | 46,151 | 118 |
| Rules generated | 126,945 | 301 |
| Runtime | 95.8s | 6.4s |
| Speedup | 1x | **~15x faster** |

**Key finding:** FP-Growth's core algorithm is ~15x faster, but it required a 40x higher support threshold. This means Apriori gives us far broader coverage (46K items vs 118 items), while FP-Growth is faster but limited to only the most popular tracks.

Both rulesets are stored in the database for comparison in the benchmark dashboard.

---

## Phase 3 — Database Setup

**Script:** `phase_3a_database.py`  
**Database:** PostgreSQL 17 (running via pgAdmin)

### Why a Database?

The `apriori_rules.csv` file has 126,945 rows. When the web app frontend asks "what songs go with Song A?", we can't load the whole CSV file on every request — that would be slow and wasteful. Instead, we load the data once into PostgreSQL, create indexes, and then every query runs in milliseconds.

### Schema Design

We use 3 tables:

---

**Table 1: `tracks`**  
Stores every unique song.

```
item        TEXT (Primary Key)   "Daft Punk - Get Lucky"
artistname  TEXT                 "Daft Punk"
trackname   TEXT                 "Get Lucky"
```

`item` is the unique identifier used everywhere. The separate `artistname` and `trackname` columns let the frontend display them separately (e.g., bold the track name, show artist in lighter text).

**Rows:** 46,151

---

**Table 2: `rulesets`**  
Stores metadata about each mining run.

```
id               INT  (Primary Key, auto-increment)
algorithm        TEXT  "Apriori" or "FP-Growth"
run_date         TIMESTAMP
min_support      INT   20 (individual song threshold)
min_pair_count   INT   50 (pair co-occurrence threshold)
min_confidence   FLOAT 0.1
min_jaccard      FLOAT 0.01
runtime_seconds  FLOAT 95.8
rule_count       INT   126945
notes            TEXT  "v3 — Fixed popularity bias..."
```

This table enables the benchmark dashboard to compare algorithms. Every rule knows which mining run produced it via the `ruleset_id` foreign key.

**Rows:** 2 (one Apriori, one FP-Growth)

---

**Table 3: `rules`**  
Stores every association rule.

```
id          INT   (Primary Key, auto-increment)
ruleset_id  INT   → references rulesets(id)
antecedent  TEXT  "Daft Punk - Get Lucky"
consequent  TEXT  "Daft Punk - Lose Yourself to Dance"
support     FLOAT 0.00381
confidence  FLOAT 0.4847
lift        FLOAT 78.18
jaccard     FLOAT 0.3717
pair_count  INT   617
count_a     INT   1273
count_b     INT   900
```

**Rows:** 127,246 (126,945 Apriori + 301 FP-Growth)

---

### Why the Ruleset FK Design?

Without `ruleset_id`:
- You'd need two separate tables (apriori_rules, fpgrowth_rules)
- Adding a third algorithm means a third table
- Comparing algorithms requires joins across tables

With `ruleset_id`:
- One `rules` table holds everything
- Filter by algorithm: `WHERE ruleset_id = 1` for Apriori, `= 2` for FP-Growth
- Adding a third algorithm = just insert a new ruleset row and add its rules with the new ID

---

### Indexes (What They Do and Why They Matter)

An index is like a book's index — instead of reading every page to find a word, you jump directly to the right page.

```sql
CREATE INDEX idx_rules_antecedent ON rules(antecedent);
```

Without this index: "give me all rules where antecedent = 'Daft Punk - Get Lucky'" requires scanning all 127,246 rows one by one.

With this index: PostgreSQL jumps directly to the matching rows. For 127K rows, this goes from ~50ms to ~1ms.

**The 4 indexes we created:**

| Index | Column | Purpose |
|---|---|---|
| `idx_rules_antecedent` | `antecedent` | Fast rule lookup (main query pattern) |
| `idx_rules_consequent` | `consequent` | Reverse lookup ("what leads to this song?") |
| `idx_rules_ruleset` | `ruleset_id` | Fast filtering by algorithm |
| `idx_rules_jaccard` | `jaccard DESC` | Fast sorting by quality score |

---

### Loading Process

The script:
1. Drops existing tables (so it's safe to re-run)
2. Creates tables fresh with the updated schema
3. Bulk-loads `item_lookup.csv` → `tracks` table (46K rows, <1s)
4. Inserts Apriori ruleset metadata → `rulesets` table
5. Bulk-loads `apriori_rules.csv` → `rules` table in chunks of 10,000 rows (~3s)
6. Inserts FP-Growth ruleset metadata and its rules
7. Creates all 4 indexes
8. Runs a verification query ("top 5 rules for Daft Punk - Get Lucky")

Total time: **~3 seconds** to load 127K rules into a production-ready database.

---

## Phase 4 — FastAPI Backend API

**Script:** `echolink_api/main.py`, `echolink_api/database.py`  
**Running at:** `http://localhost:8000`

### What is an API?

An API (Application Programming Interface) is the middleman between the frontend (what the user sees in the browser) and the database. The frontend never talks to the database directly — it sends a request to the API, the API queries the database, and returns the result as JSON.

```
Browser → "GET /recommend?track=Daft Punk - Get Lucky" → FastAPI → PostgreSQL
Browser ← { recommendations: [...] }                  ← FastAPI ← DB result
```

### Why FastAPI?

FastAPI is a modern Python web framework. It was chosen because:
- **Fast to write** — very clean, readable code
- **Auto-validation** — automatically checks that parameters are the right type
- **Auto-docs** — generates an interactive Swagger UI at `/docs` for free
- **Fast to run** — uses `uvicorn` (async server), handles many requests simultaneously

### The Connection Pool

Instead of opening and closing a database connection for every request (slow), we open 2–10 connections at startup and reuse them:

```
Request 1 → borrows connection → runs query → returns connection
Request 2 → borrows connection → runs query → returns connection
(connections stay open and ready)
```

This is handled by `psycopg2.ThreadedConnectionPool` in `database.py`.

### CORS — Why It's Enabled

CORS (Cross-Origin Resource Sharing) is a browser security rule. If the frontend runs on `http://localhost:3000` and tries to call the API on `http://localhost:8000`, the browser blocks it by default (different ports = different "origin").

We added `CORSMiddleware` with `allow_origins=["*"]` to allow any origin during development. In production, you'd restrict this to just your frontend domain.

---

### All API Endpoints

---

**`GET /`** — Health Check

*What it does:* Checks that the server is running AND the database is connected. Returns total rule count.

*When to use:* To verify the server started correctly.

```bash
curl http://localhost:8000/
# → {"status": "ok", "rule_count": 127246}
```

---

**`GET /search?q=daft&limit=10`** — Track Search / Autocomplete

*What it does:* Searches for tracks by artist or song name. Only returns tracks that have at least one recommendation available.

*When to use:* Powers the search bar in the UI. As the user types, the frontend calls this endpoint to show matching tracks.

*Important detail:* The `EXISTS` filter ensures results are only tracks the system can actually recommend for. If a track has no rules (edge case), it won't appear in search results — avoiding dead ends.

```bash
curl "http://localhost:8000/search?q=radiohead&limit=5"
```

---

**`GET /recommend?track=...&limit=10&ruleset_id=1&sort_by=jaccard`** — Get Recommendations

*What it does:* The core endpoint. Takes a track name and returns the top N most associated songs from the database.

*Parameters:*
- `track` — exact song name (required)
- `limit` — how many to return (default 10, max 50)
- `ruleset_id` — 1 for Apriori, 2 for FP-Growth (default 1)
- `sort_by` — `jaccard` (default), `confidence`, `pair_count`, or `lift`

*When to use:* Called when the user clicks on a track in the search results to get its recommendations.

```bash
curl "http://localhost:8000/recommend?track=Coldplay%20-%20Yellow&limit=5"
```

---

**`GET /rulesets`** — All Mining Run Metadata

*What it does:* Returns a list of all algorithm runs stored in the database — their parameters, runtime, and rule counts.

*When to use:* Populates the benchmark dashboard's "runs" section.

```bash
curl http://localhost:8000/rulesets
```

---

**`GET /rulesets/{id}`** — Single Ruleset Details

*What it does:* Returns detailed info for one specific ruleset, including its top 5 rules by Jaccard (a preview).

```bash
curl http://localhost:8000/rulesets/1
```

---

**`GET /benchmark`** — Algorithm Comparison

*What it does:* Returns a side-by-side comparison of all algorithms including computed quality stats (average Jaccard, average confidence, max pair count) calculated live from the rules table.

Also returns a `summary` object with:
- Which algorithm was fastest
- Which algorithm produced the most rules
- The speedup factor (how many times faster)

```bash
curl http://localhost:8000/benchmark
# → Apriori: 95.8s, 126,945 rules | FP-Growth: 6.4s, 301 rules | Speedup: 15x
```

---

**`GET /stats`** — Database Overview

*What it does:* Full summary for the dashboard's overview cards:
- Total track count
- Total rule count
- Top 10 most recommended songs (appear most as consequents)
- Top 10 most connected songs (have the most outgoing rules — best to search for)

```bash
curl http://localhost:8000/stats
```

---

## Current Status

| Phase | Status | Output |
|---|---|---|
| 1 — Preprocessing | ✅ Complete | `spotify_clean.csv`, `item_lookup.csv` |
| 2B — Apriori | ✅ Complete (v3, bias fixed) | `apriori_rules.csv` (126,945 rules) |
| 2C — FP-Growth Benchmark | ✅ Complete | `fpgrowth_rules.csv` (301 rules) |
| 3 — Database | ✅ Complete | PostgreSQL `echolink` DB (3 tables, 4 indexes) |
| 4 — Backend API | ✅ Complete | FastAPI running at `localhost:8000` |
| 5 — Frontend | 🔜 Next | Web app (search + recommendations + benchmark dashboard) |

---

## Key Design Decisions & Why

| Decision | Why |
|---|---|
| `basket_id = user_id + playlistname` | No native playlist ID in dataset; this uniquely identifies each playlist |
| `item = "Artist - Track"` | Unique identifier that works even when artist or track names overlap |
| Jaccard over Lift for filtering | Lift is mathematically misleading for rare items; Jaccard is always 0–1 |
| `MIN_PAIR_COUNT = 50` (absolute) | Ratio-based confidence excluded popular tracks; absolute count is fair across all popularity levels |
| `tracks` table separate from `rules` | Normalisation — display names stored once, not repeated in every rule row |
| `rulesets` table | Lets you compare multiple algorithm runs without duplicating or restructuring the rules table |
| 4 indexes on rules | Without indexes, every recommendation query would scan all 127K rows |
| Connection pool in API | Avoids reconnecting to DB on every request — essential for performance under concurrent load |
