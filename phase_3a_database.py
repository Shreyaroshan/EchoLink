"""
EchoLink — Phase 3A: Database Schema + Data Load (v2)
=====================================================
Schema (updated based on project design):
  tracks    → unique tracks/items (artist + trackname)
  rulesets  → metadata for each mining run (algorithm, params, runtime)
  rules     → association rules with ruleset_id FK

This allows:
  - Comparing multiple algorithm runs in the benchmark dashboard
  - Tracking exactly which parameters produced which rules
  - Filtering UI by ruleset (Apriori vs FP-Growth, different thresholds)

Connection: localhost:5432, database=echolink
"""

import psycopg2
import psycopg2.extras
import pandas as pd
import time
import os
from datetime import datetime

# ── CONNECTION CONFIG ─────────────────────────────────────────────────
# Reads from environment variables; falls back to localhost defaults.
# To override: export DB_PASSWORD=yourpassword (no code change needed)
DB_CONFIG = {
    'host':     os.getenv('DB_HOST',     'localhost'),
    'port':     int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME',     'echolink'),
    'user':     os.getenv('DB_USER',     'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgresql'),
}

# ── APRIORI RUN METADATA (from Phase 2B) ─────────────────────────────
APRIORI_META = {
    'algorithm':       'Apriori',
    'min_support':     20,
    'min_pair_count':  50,
    'min_confidence':  0.1,
    'min_jaccard':     0.01,
    'runtime_seconds': 95.8,
    'notes':           'v3 — Fixed popularity bias. MIN_PAIR_COUNT=50 (absolute) is the main quality gate. Full item coverage (46K items). 126,945 rules.'
}

# ── FP-GROWTH RUN METADATA (from Phase 2C) ───────────────────────────
FPGROWTH_META = {
    'algorithm':       'FP-Growth',
    'min_support':     809,
    'min_pair_count':  0,
    'min_confidence':  0.5,
    'min_jaccard':     0.05,
    'runtime_seconds': 6.4,
    'notes':           'mlxtend implementation. Higher support threshold due to dense matrix memory constraint. 118 items in scope. No absolute pair count filter used.'
}

start = time.time()
print("=" * 58)
print("EchoLink — Phase 3A: Database Setup (v2)")
print("=" * 58)
print()

# ── CONNECT ───────────────────────────────────────────────────────────
try:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0].split(',')[0]
    print(f"✅ Connected: {version}")
    print()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    raise


# ══════════════════════════════════════════════════════════════════════
# CREATE TABLES
# ══════════════════════════════════════════════════════════════════════

print("⏳ Creating tables...")

# Drop in reverse dependency order
cur.execute("DROP TABLE IF EXISTS rules    CASCADE;")
cur.execute("DROP TABLE IF EXISTS rulesets CASCADE;")
cur.execute("DROP TABLE IF EXISTS tracks   CASCADE;")


# ── TABLE: tracks ─────────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE tracks (
        item        TEXT PRIMARY KEY,        -- "Artist - Track" combined key
        artistname  TEXT NOT NULL,
        trackname   TEXT NOT NULL
    );
""")
print("  ✅ tracks")


# ── TABLE: rulesets ───────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE rulesets (
        id               SERIAL PRIMARY KEY,
        algorithm        TEXT      NOT NULL,    -- 'Apriori' | 'FP-Growth'
        run_date         TIMESTAMP NOT NULL DEFAULT NOW(),
        min_support      INT       NOT NULL,    -- individual track basket count threshold
        min_pair_count   INT       NOT NULL DEFAULT 0,  -- absolute pair co-occurrence threshold
        min_confidence   FLOAT     NOT NULL,
        min_jaccard      FLOAT     NOT NULL,
        runtime_seconds  FLOAT,                 -- total script runtime
        rule_count       INT,                   -- populated after rules load
        notes            TEXT                   -- free text for context
    );
""")
print("  ✅ rulesets")


# ── TABLE: rules ──────────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE rules (
        id          SERIAL  PRIMARY KEY,
        ruleset_id  INT     NOT NULL REFERENCES rulesets(id) ON DELETE CASCADE,
        antecedent  TEXT    NOT NULL,
        consequent  TEXT    NOT NULL,
        support     FLOAT   NOT NULL,
        confidence  FLOAT   NOT NULL,
        lift        FLOAT   NOT NULL,
        jaccard     FLOAT   NOT NULL,
        pair_count  INT     NOT NULL,
        count_a     INT     NOT NULL,
        count_b     INT     NOT NULL
    );
""")
print("  ✅ rules  (with ruleset_id FK → rulesets)")
print()
conn.commit()


# ══════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════

# ── LOAD: tracks ──────────────────────────────────────────────────────
print("⏳ Loading tracks from item_lookup.csv...")

items_df = pd.read_csv('item_lookup.csv').dropna().drop_duplicates(subset='item')
records  = list(items_df[['item', 'artistname', 'trackname']].itertuples(index=False, name=None))

psycopg2.extras.execute_values(
    cur,
    "INSERT INTO tracks (item, artistname, trackname) VALUES %s ON CONFLICT DO NOTHING",
    records, page_size=1000
)
conn.commit()

cur.execute("SELECT COUNT(*) FROM tracks;")
print(f"✅ Loaded {cur.fetchone()[0]:,} tracks  ({time.time()-start:.1f}s elapsed)")
print()


# ── INSERT: Apriori ruleset record ────────────────────────────────────
print("⏳ Inserting Apriori ruleset metadata...")

cur.execute("""
    INSERT INTO rulesets (algorithm, run_date, min_support, min_pair_count, min_confidence, min_jaccard, runtime_seconds, notes)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id;
""", (
    APRIORI_META['algorithm'],
    datetime.now(),
    APRIORI_META['min_support'],
    APRIORI_META['min_pair_count'],
    APRIORI_META['min_confidence'],
    APRIORI_META['min_jaccard'],
    APRIORI_META['runtime_seconds'],
    APRIORI_META['notes']
))
apriori_ruleset_id = cur.fetchone()[0]
conn.commit()
print(f"✅ Apriori ruleset ID: {apriori_ruleset_id}")
print()


# ── LOAD: Apriori rules ───────────────────────────────────────────────
# apriori_rules.csv is the canonical rules file produced by phase_2b_apriori.py.
# apriori_rules_clean.csv is an exploration artifact (stricter filters) — NOT loaded here.
print("⏳ Loading Apriori rules from apriori_rules.csv...")
print("   Loading ~127K rows in chunks of 10,000  (filtered by MIN_PAIR_COUNT=50 in Phase 2B)...")

rules_df   = pd.read_csv('apriori_rules.csv').dropna()
CHUNK_SIZE = 10_000
total      = len(rules_df)
loaded     = 0

for i in range(0, total, CHUNK_SIZE):
    chunk   = rules_df.iloc[i:i+CHUNK_SIZE]
    records = [
        (apriori_ruleset_id,
         row.antecedent, row.consequent,
         row.support, row.confidence, row.lift,
         row.jaccard, int(row.pair_count),
         int(row.count_a), int(row.count_b))
        for row in chunk.itertuples()
    ]
    psycopg2.extras.execute_values(
        cur,
        """INSERT INTO rules
           (ruleset_id, antecedent, consequent, support, confidence,
            lift, jaccard, pair_count, count_a, count_b)
           VALUES %s""",
        records, page_size=1000
    )
    conn.commit()
    loaded += len(chunk)
    pct = 100 * loaded / total
    print(f"   [{pct:5.1f}%] {loaded:,}/{total:,} rules  |  {time.time()-start:.1f}s elapsed")

# Update rule_count on ruleset
cur.execute("UPDATE rulesets SET rule_count = %s WHERE id = %s;", (loaded, apriori_ruleset_id))
conn.commit()
print(f"✅ Loaded {loaded:,} Apriori rules")
print()


# ── INSERT: FP-Growth ruleset record ──────────────────────────────────
print("⏳ Inserting FP-Growth ruleset metadata...")

cur.execute("""
    INSERT INTO rulesets (algorithm, run_date, min_support, min_pair_count, min_confidence, min_jaccard, runtime_seconds, notes)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id;
""", (
    FPGROWTH_META['algorithm'],
    datetime.now(),
    FPGROWTH_META['min_support'],
    FPGROWTH_META['min_pair_count'],
    FPGROWTH_META['min_confidence'],
    FPGROWTH_META['min_jaccard'],
    FPGROWTH_META['runtime_seconds'],
    FPGROWTH_META['notes']
))
fpgrowth_ruleset_id = cur.fetchone()[0]
conn.commit()


# ── LOAD: FP-Growth rules ─────────────────────────────────────────────
fpgrowth_df = pd.read_csv('fpgrowth_rules.csv').dropna()
records = [
    (fpgrowth_ruleset_id,
     row.antecedent, row.consequent,
     row.support, row.confidence, row.lift,
     row.jaccard, int(row.pair_count),
     int(row.count_a), int(row.count_b))
    for row in fpgrowth_df.itertuples()
]
psycopg2.extras.execute_values(
    cur,
    """INSERT INTO rules
       (ruleset_id, antecedent, consequent, support, confidence,
        lift, jaccard, pair_count, count_a, count_b)
       VALUES %s""",
    records, page_size=1000
)
cur.execute("UPDATE rulesets SET rule_count = %s WHERE id = %s;", (len(fpgrowth_df), fpgrowth_ruleset_id))
conn.commit()
print(f"✅ FP-Growth ruleset ID: {fpgrowth_ruleset_id}  ({len(fpgrowth_df):,} rules)")
print()


# ══════════════════════════════════════════════════════════════════════
# CREATE INDEXES
# ══════════════════════════════════════════════════════════════════════

print("⏳ Creating indexes...")
cur.execute("CREATE INDEX idx_rules_antecedent  ON rules(antecedent);")
cur.execute("CREATE INDEX idx_rules_consequent  ON rules(consequent);")
cur.execute("CREATE INDEX idx_rules_ruleset     ON rules(ruleset_id);")
cur.execute("CREATE INDEX idx_rules_jaccard     ON rules(jaccard DESC);")
cur.execute("CREATE INDEX idx_rules_ant_ruleset ON rules(antecedent, ruleset_id, jaccard DESC);")
conn.commit()
print("  ✅ idx_rules_antecedent  — fast rule lookup by input song")
print("  ✅ idx_rules_consequent  — reverse lookups")
print("  ✅ idx_rules_ruleset     — filter by algorithm")
print("  ✅ idx_rules_jaccard     — sort by quality")
print("  ✅ idx_rules_ant_ruleset — composite: antecedent + ruleset_id + jaccard (Fix 6: covers /recommend query exactly)")
print()


# ══════════════════════════════════════════════════════════════════════
# VERIFY
# ══════════════════════════════════════════════════════════════════════

print("🔍 Verification:")
print()

# Table counts
cur.execute("SELECT COUNT(*) FROM tracks;")
print(f"   tracks:    {cur.fetchone()[0]:,} rows")
cur.execute("SELECT COUNT(*) FROM rules;")
print(f"   rules:     {cur.fetchone()[0]:,} rows")

# Ruleset summary
print()
print("   Rulesets:")
cur.execute("SELECT id, algorithm, min_support, min_pair_count, min_confidence, runtime_seconds, rule_count FROM rulesets ORDER BY id;")
for row in cur.fetchall():
    print(f"     ID:{row[0]}  {row[1]:<12}  support≥{row[2]}  pair_count≥{row[3]}  conf≥{row[4]}  runtime:{row[5]}s  rules:{row[6]:,}")

# Sample rules for "Daft Punk - Get Lucky" from Apriori
print()
print("   🎵 Top 5 rules for 'Daft Punk - Get Lucky' (Apriori, by Jaccard):")
cur.execute("""
    SELECT r.consequent, ROUND(r.jaccard::numeric, 3), ROUND(r.confidence::numeric, 2), r.pair_count
    FROM   rules r
    WHERE  r.antecedent  = 'Daft Punk - Get Lucky'
    AND    r.ruleset_id  = %s
    ORDER  BY r.jaccard DESC
    LIMIT  5;
""", (apriori_ruleset_id,))
rows = cur.fetchall()
for row in rows:
    print(f"     → {str(row[0])[:45]:<46} Jacc:{row[1]}  Conf:{row[2]}  Count:{row[3]}")
if not rows:
    print("     (no rules found)")

cur.close()
conn.close()

total_time = time.time() - start
print()
print("=" * 58)
print("🎉 PHASE 3A COMPLETE — Database Ready")
print("=" * 58)
print(f"  Tables:    tracks, rulesets, rules")
print(f"  Indexes:   4 indexes created")
print(f"  Runtime:   {total_time:.1f}s ({total_time/60:.1f} mins)")
print()
print("➡️  Next: Phase 4 — Backend API (FastAPI)")
