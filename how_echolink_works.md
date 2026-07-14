# How EchoLink Works
*Plain English — no jargon*

---

## The Core Idea

EchoLink does not use machine learning, user history, or audio analysis.

It does one thing: **it learns which songs people put in the same playlist.**

If thousands of people independently decided to put "Get Lucky" and "Lose Yourself to Dance" in the same playlist, that's a signal. It means those songs belong together. EchoLink mines that signal from 161,000 real Spotify playlists and turns it into a recommendation engine.

---

## Step 1 — The Raw Data

We started with a dataset of **12.9 million rows**. Each row is one song in one playlist:

```
user_id      | playlist_name  | artist_name  | track_name
-------------|----------------|--------------|-------------------
user_abc123  | Chill Vibes    | Daft Punk    | Get Lucky
user_abc123  | Chill Vibes    | Coldplay     | Yellow
user_abc123  | Chill Vibes    | Radiohead    | Creep
user_xyz789  | Gym Hits       | Eminem       | Lose Yourself
...
```

After cleaning, we had:
- **161,953 unique playlists** (called "baskets")
- **46,151 unique songs**

---

## Step 2 — Turning Playlists into Baskets

Each playlist becomes a **set of songs** — order doesn't matter, duplicates removed:

```
Playlist "Chill Vibes" → { Daft Punk - Get Lucky, Coldplay - Yellow, Radiohead - Creep }
Playlist "Gym Hits"    → { Eminem - Lose Yourself, AC/DC - Thunderstruck }
```

This is the input format for both algorithms. We call each playlist a "basket" because the idea comes from market basket analysis — the same technique used to discover that beer and nappies are frequently bought together.

---

## Step 3A — Apriori (our main algorithm)

Apriori finds which **pairs of songs appear together** across many playlists.

### How it runs:

**Pass 1:** Count how often each individual song appears.
Keep only songs that appear in at least **20 playlists** (filtering out extreme rarities).
→ Result: 46,151 frequent songs

**Pass 2:** For every pair of those frequent songs, count how many playlists contain both.
→ This produces millions of pair counts like:
```
(Get Lucky, Lose Yourself to Dance) → appeared together in 617 playlists
(Get Lucky, Instant Crush)          → appeared together in 552 playlists
(Get Lucky, Yellow)                 → appeared together in 38 playlists
```

**Filter:** Only keep pairs that co-occur in at least **50 playlists**.
This is the main quality gate — it ensures there's real, repeated evidence of association.

**Generate rules:** For every qualifying pair, create two directed rules:
```
Get Lucky → Lose Yourself to Dance   (confidence: 0.48, because 617/1273 playlists)
Lose Yourself to Dance → Get Lucky   (confidence: 0.69, because 617/900 playlists)
```

The confidence values differ because one song is more common than the other.

**Score each rule** with 4 metrics:
- **Support** — what fraction of ALL 161K playlists have both songs? (0.00381 = 0.38%)
- **Confidence** — of playlists with Song A, how many % also have Song B? (0.48 = 48%)
- **Lift** — how much more than random chance? (78x more likely than if placement were random)
- **Jaccard** — of playlists with EITHER song, how many % have BOTH? (0.37 = 37%)

**Primary ranking metric: Jaccard.** Lift is mathematically misleading for rare songs (a song that appears in only 5 playlists but always with the same partner gets lift of 1000+, which isn't genuinely useful). Jaccard is always between 0 and 1, and treats popular and niche songs fairly.

**Final output:** `apriori_rules.csv` — **126,945 directional rules**, sorted by Jaccard.

### The popularity bias fix:

Early versions used `MIN_CONFIDENCE = 0.5` as the filter. This silently killed all popular songs.

Why? "Get Lucky" is in 1,273 playlists — summer playlists, party playlists, gym playlists, road trip playlists. No single co-song consistently reaches 50% because the playlists are too diverse. So popular songs had **zero rules** generated for them.

Meanwhile a Lord of the Rings soundtrack track in 26 playlists (all dedicated LOTR playlists) had confidence of 1.0 — it always travels with the same tracks. So it had 21 rules.

Fix: switch from ratio-based to **absolute co-occurrence count**. `MIN_PAIR_COUNT = 50` means: if two songs appear together in 50+ playlists, that's enough evidence regardless of how popular they are.

---

## Step 3B — FP-Growth (benchmark comparison)

FP-Growth is a smarter, faster version of the same idea. Instead of comparing every pair of songs directly, it builds a compressed tree structure (called an FP-Tree) that summarizes the entire dataset, then mines rules from the tree.

**Why it's faster:** Apriori has to scan all 161K playlists once per pair candidate. FP-Growth scans the data twice total, builds the tree, then mines from memory.

**Why we can't use it as the main algorithm for this dataset:**

FP-Growth (via the `mlxtend` library) requires converting playlists into a dense matrix:

```
161,953 playlists × 46,151 songs = 7.4 billion cells
```

That's ~7.5 GB of RAM just to represent the data — more than a typical machine has free. To make it work, we had to raise the threshold to songs that appear in 809+ playlists. That shrinks the scope to only the **118 most popular songs** (instead of 46,151).

**Result:**

| | Apriori (custom) | FP-Growth (mlxtend) |
|---|---|---|
| Songs in scope | 46,151 | 118 |
| Rules generated | 126,945 | 301 |
| Runtime | 95.8s | 6.4s |
| Speedup | 1× | 15× faster |

FP-Growth is 15× faster at the core mining step, but it can only work with the top 0.25% of songs due to the memory constraint. For a real recommendation system covering the full catalogue, Apriori gives far better coverage.

Both rulesets are stored in the database. The frontend lets you toggle between them to see the difference.

---

## Step 4 — The Database

All 126,945 Apriori rules + 301 FP-Growth rules are loaded into **PostgreSQL** once.

Schema:
- **tracks** table — 46,151 songs with artist and track name
- **rulesets** table — metadata for each mining run (algorithm, parameters, runtime)
- **rules** table — 127,246 rules with all 4 quality metrics + a link to which ruleset produced them

4 indexes are created on the rules table so that every query runs in milliseconds instead of seconds.

---

## Step 5 — The API

A **FastAPI** server sits between the database and the frontend. It exposes clean REST endpoints:

```
GET /search?q=daft          → autocomplete: returns matching tracks
GET /recommend?track=...    → core: returns top N rules for a song
GET /benchmark              → comparison stats for both algorithms
GET /stats                  → top connected tracks, overview numbers
```

When you search for "Daft Punk - Get Lucky" and ask for recommendations:
1. API queries the database for all rules where `antecedent = 'Daft Punk - Get Lucky'`
2. Sorts by Jaccard (or whichever metric you chose)
3. Joins with the tracks table to get clean artist/track names
4. Returns the top 10 as JSON

The whole query takes ~1ms because of the index on `antecedent`.

---

## Step 6 — The Frontend

A **React + Vite** web app with 4 views:

**Discover** — type any song, get recommendations. Toggle between Apriori and FP-Growth. Sort by Jaccard, Confidence, Pair Count, or Lift. Click any result to chain-browse to its own recommendations.

**Benchmark** — side-by-side visual comparison of both algorithms. Runtime bar charts, rule count charts, quality metric comparison table, and top-connected-song leaderboards.

**Rule Explorer** — two views in one:
- *Network graph* (D3.js force-directed): songs as nodes, associations as edges. Edge thickness = Jaccard strength. Click a node to expand its connections.
- *Table view*: all 50 rules for the seed song, filterable by track name and minimum Jaccard threshold.

**About** — plain-language explanation of how it all works (you're reading the standalone version of that content right now).

---

## How a Recommendation Actually Happens

User types "Coldplay - Yellow" and hits enter.

```
Browser → GET /recommend?track=Coldplay - Yellow&limit=10&ruleset_id=1&sort_by=jaccard
                                    ↓
API queries PostgreSQL:
  SELECT consequent, jaccard, confidence, lift, pair_count
  FROM rules
  WHERE antecedent = 'Coldplay - Yellow'
  AND ruleset_id = 1
  ORDER BY jaccard DESC
  LIMIT 10;
                                    ↓
Database uses idx_rules_antecedent index → result in ~1ms
                                    ↓
API joins with tracks table → returns artist + track names
                                    ↓
Browser renders 10 recommendation cards sorted by Jaccard
```

The result isn't "songs similar to Yellow." It's "songs that people who added Yellow to their playlists also tended to add." The distinction matters — it's behavioral association, not audio similarity.

---

## Why Different Sort Metrics Give Different Results

This is the most common point of confusion when using the app.

Each metric captures a different dimension of "association":

| Metric | What it measures | Who it favours |
|---|---|---|
| **Jaccard** | Share of playlists with either song that have both | Genuinely associated pairs, balanced across popularity |
| **Confidence** | % of Song A's playlists that also have Song B | Niche songs that always travel together |
| **Pair Count** | Raw number of playlists with both songs | The most popular songs overall (popular = high counts) |
| **Lift** | How much more likely than pure random chance | Rare, tightly-coupled niche pairs (can be extremely high for rare songs) |

Example for "Get Lucky":
- **Jaccard top result** → *Lose Yourself to Dance* — genuinely the strongest balanced association
- **Confidence top result** → a deep Random Access Memories cut — appears in nearly every Get Lucky playlist
- **Pair Count top result** → whatever massive Daft Punk hit has the biggest raw overlap
- **Lift top result** → possibly an obscure B-side — rare, so the lift denominator is tiny

This divergence is intentional. Jaccard is the default because it's the most honest and balanced signal.
