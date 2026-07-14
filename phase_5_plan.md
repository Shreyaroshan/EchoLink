# EchoLink — Phase 5: React Frontend Plan
*What we're building, why, and how*

---

## Tech Stack

| Tool | Why |
|---|---|
| **Vite + React + TypeScript** | Fast dev server, modern React, type safety |
| **Vanilla CSS** | Full design control, no framework overhead |
| **D3.js** (network graph only) | Purpose-built for force-directed network visualizations |

D3 is the only external library beyond React — everything else (bar charts, stat cards, tables) is built in plain CSS.

---

## 4 Views / Tabs

### 1. 🔍 Discover
The main recommendation screen.

**What the user does:**
- Types a song or artist name into the search bar
- A dropdown appears with matching tracks (autocomplete)
- Clicking a track shows its top recommendations
- Clicking any recommendation searches for *that* song (chain browsing)

**Controls the user has:**
- Toggle between **Apriori** and **FP-Growth** ruleset
- Sort results by: **Jaccard** (default) / **Confidence** / **Pair Count** / **Lift**
- How many results to show (10 / 25 / 50)

**What each recommendation card shows:**
- Artist + track name
- Jaccard score as a filled bar (primary metric)
- Confidence, Lift, Pair Count as secondary stats

---

### 2. 📊 Benchmark Dashboard
Side-by-side comparison of the two algorithms.

**Top stat cards:**
- Total tracks in database (46,151)
- Total rules stored (127,246)
- Speedup factor (15×)

**Comparison table:** Runtime, Rule count, Avg Jaccard, Avg Confidence, Max pair count — one row per algorithm.

**CSS bar charts (no library needed):**
- Runtime: Apriori 95.8s vs FP-Growth 6.4s
- Rule count: 126,945 vs 301

**Bottom tables:**
- Top 10 most *connected* songs (songs with the most outgoing rules — best to search for)
- Top 10 most *recommended* songs (songs that appear most as a recommendation result)

---

### 3. 🕸️ Rule Explorer + Co-occurrence Network
*New addition.* Two things in one view:

#### Rule Explorer (table/list)
Browse all rules directly — not just for one song.
- Search by antecedent or consequent name
- Filter by metric threshold (e.g. only show rules where Jaccard > 0.3)
- Sort by any metric column
- Shows: Antecedent → Consequent, Jaccard, Confidence, Lift, Pair Count

#### Co-occurrence Network (D3 force graph)
A visual graph where:
- **Nodes** = songs
- **Edges** = association rules between them
- **Edge thickness** = Jaccard score (thicker = stronger association)
- **Node size** = number of connections (more rules = bigger node)

**How it works:**
- User searches for a seed song in the network
- The graph renders that song + its top N neighbours
- Clicking any neighbour node expands it, showing *its* connections
- Hovering an edge shows the Jaccard, Confidence, and Pair Count for that rule

This gives an intuitive visual sense of how songs cluster — album tracks cluster tightly, genre-spanning tracks have many looser connections.

---

### 4. ℹ️ About / How It Works
Plain-language explanation for anyone reading the project.

- What association rule mining is (with the supermarket analogy)
- The 4 metrics explained simply (Support, Confidence, Lift, Jaccard)
- Why Jaccard is the primary metric (lift is misleading for rare items)
- The popularity bias problem and how we fixed it
- Architecture pipeline: CSV → Apriori → DB → API → Frontend (CSS diagram)
- Link to the Swagger API docs at `localhost:8000/docs`

---

## File Structure

```
echolink_frontend/
├── index.html
├── vite.config.ts
├── package.json
├── src/
│   ├── main.tsx
│   ├── App.tsx              ← tab router + nav bar
│   ├── api.ts               ← all fetch calls to localhost:8000
│   ├── index.css            ← design tokens, global styles
│   ├── components/
│   │   ├── SearchBar.tsx         ← debounced input + autocomplete dropdown
│   │   ├── TrackCard.tsx         ← selected track hero card
│   │   ├── RecommendCard.tsx     ← single recommendation card
│   │   ├── SortControls.tsx      ← metric sort pill buttons
│   │   ├── RulesetToggle.tsx     ← Apriori ↔ FP-Growth toggle
│   │   ├── StatCard.tsx          ← number stat card
│   │   ├── BarChart.tsx          ← CSS-only bar chart
│   │   ├── NetworkGraph.tsx      ← D3 force-directed co-occurrence graph
│   │   ├── RuleTable.tsx         ← filterable/sortable rules table
│   │   └── Skeleton.tsx          ← shimmer loading placeholder
│   └── views/
│       ├── Discover.tsx
│       ├── Benchmark.tsx
│       ├── Explorer.tsx          ← Rule explorer + network graph
│       └── About.tsx
```

---

## Design System

| Property | Value |
|---|---|
| Font | Inter (Google Fonts) |
| Background | `#09090f` (near-black) |
| Surface | `#13131c` / `#1c1c2a` |
| Accent | `#7c3aed` (violet) → `#06b6d4` (cyan) gradient |
| Text primary | `#f1f5f9` |
| Text muted | `#64748b` |
| Border | `rgba(255,255,255,0.07)` |
| Card style | Glassmorphism — `backdrop-filter: blur(12px)` |
| Transitions | `200ms ease` on all interactive elements |
| Hover | Cards lift with `translateY(-2px)` + glow shadow |

---

## API Calls Used

| View | Endpoint | Purpose |
|---|---|---|
| Discover | `GET /search?q=` | Autocomplete |
| Discover | `GET /recommend?track=` | Get recommendations |
| Benchmark | `GET /benchmark` | Algorithm comparison data |
| Benchmark | `GET /stats` | Stat cards + top tracks tables |
| Explorer | `GET /recommend?track=&limit=50` | Load neighbour rules for graph |
| Explorer | `GET /search?q=` | Search seed node |
| All | `GET /` | Health check on load |

---

## Implementation Order

1. Scaffold Vite + React app
2. Build `api.ts` (all fetch functions)
3. Build `index.css` (full design system)
4. Build shared components (SearchBar, StatCard, Skeleton, etc.)
5. Build **Discover** view (core flow)
6. Build **Benchmark** view
7. Build **Explorer** view — Rule table first, then network graph
8. Build **About** view
9. Wire up App.tsx routing + nav bar
10. Polish: loading states, error states, empty states, animations

---

## Notes

- API base URL is a single constant in `api.ts` — easy to change for deployment
- Network graph: loads top 20 rules for the seed node only (keeps graph readable)
  - Expanding a node loads its top 10 neighbours on click
  - Max 80 nodes rendered at once (older nodes fade out on expansion)
- No backend changes needed — all 7 existing endpoints are sufficient
