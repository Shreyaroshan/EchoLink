"""
EchoLink — Phase 2B: Apriori From Scratch (v3 — fixed popularity bias)
=======================================================================
Problem fixed:
  v2 used ratio-based filters (MIN_CONF=0.5, MIN_JACCARD=0.05) which
  completely excluded popular tracks like "Daft Punk - Get Lucky" because
  popular songs spread across many diverse playlist types, so no single
  co-song consistently reaches 50% — even when they co-occur 300+ times.

Fix:
  Replace pure ratio filters with an ABSOLUTE co-occurrence count.
  MIN_PAIR_COUNT = 50 → a pair must appear together in 50+ baskets.
  This captures popular tracks (real signal) while filtering noise.

Config:
  MIN_SUPPORT    = 20   → individual track in at least 20 baskets
  MIN_CONF       = 0.1  → loose ratio (some directional signal)
  MIN_PAIR_COUNT = 50   → absolute co-occurrence count (main quality gate)
  MIN_JACCARD    = 0.01 → very loose, used for ranking only

Input:   spotify_clean.csv
Output:  apriori_rules.csv
"""

import pandas as pd
from itertools import combinations
from collections import Counter
import time

# ── CONFIG ────────────────────────────────────────────────────────────
MIN_SUPPORT    = 20    # individual track must appear in at least this many baskets
MIN_CONF       = 0.1   # loose confidence (10%) — ratio-based directional signal
MIN_PAIR_COUNT = 50    # MAIN GATE: pair must co-occur in at least 50 baskets
MIN_JACCARD    = 0.01  # very loose — used for ranking, not strict filtering

start = time.time()
print("=" * 60)
print("EchoLink — Phase 2B: Apriori From Scratch (v3)")
print("=" * 60)
print(f"  Min Support (individual): {MIN_SUPPORT} baskets")
print(f"  Min Confidence:           {MIN_CONF}  (10%)")
print(f"  Min Pair Count:           {MIN_PAIR_COUNT} baskets  ← main quality gate")
print(f"  Min Jaccard:              {MIN_JACCARD} (1% overlap, for ranking)")
print(f"  Note: Captures popular tracks AND niche tracks")
print()


# ── STEP 1: LOAD DATA & BUILD BASKETS ─────────────────────────────────
print("⏳ Step 1: Loading data and building baskets...")

df = pd.read_csv('spotify_clean.csv')

baskets = (
    df.groupby('basket_id')['item']
    .apply(frozenset)
    .to_dict()
)

total_baskets = len(baskets)
print(f"✅ Loaded: {len(df):,} rows → {total_baskets:,} baskets")
print(f"   ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 2: COUNT FREQUENT 1-ITEMSETS ─────────────────────────────────
print("⏳ Step 2: Counting individual item frequencies (1-itemsets)...")

item_counts = Counter()
for items in baskets.values():
    for item in items:
        item_counts[item] += 1

frequent_items = {item: count for item, count in item_counts.items()
                  if count >= MIN_SUPPORT}

print(f"✅ Total unique items:    {len(item_counts):,}")
print(f"   Frequent items (≥{MIN_SUPPORT}): {len(frequent_items):,}")
print(f"   ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 3: COUNT FREQUENT 2-ITEMSETS (PAIRS) ─────────────────────────
print("⏳ Step 3: Counting frequent pairs (2-itemsets)...")
print("   Progress shown every 50,000 baskets\n")

pair_counts = Counter()
frequent_item_set = set(frequent_items.keys())

for i, (basket_id, items) in enumerate(baskets.items()):

    if i > 0 and i % 50_000 == 0:
        elapsed = time.time() - start
        pct = 100 * i / total_baskets
        print(f"   [{pct:5.1f}%] {i:,}/{total_baskets:,} baskets  |  "
              f"{len(pair_counts):,} pairs found  |  {elapsed:.1f}s elapsed")

    frequent_in_basket = items & frequent_item_set
    for pair in combinations(sorted(frequent_in_basket), 2):
        pair_counts[pair] += 1

frequent_pairs = {pair: count for pair, count in pair_counts.items()
                  if count >= MIN_SUPPORT}

print()
print(f"✅ Total pairs found:         {len(pair_counts):,}")
print(f"   Frequent pairs (≥{MIN_SUPPORT}):   {len(frequent_pairs):,}")
print(f"   ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 4: GENERATE RULES WITH JACCARD ───────────────────────────────
print("⏳ Step 4: Generating association rules (with Jaccard)...")

rules = []

for (item_a, item_b), pair_count in frequent_pairs.items():

    count_a = item_counts[item_a]
    count_b = item_counts[item_b]

    support = pair_count / total_baskets

    # Jaccard — symmetric, unaffected by item rarity
    jaccard = pair_count / (count_a + count_b - pair_count)

    # Rule 1: A → B
    conf_ab = pair_count / count_a
    lift_ab = conf_ab / (count_b / total_baskets)  # stored for display only

    # FILTER: must pass confidence AND absolute pair count AND jaccard
    if conf_ab >= MIN_CONF and pair_count >= MIN_PAIR_COUNT and jaccard >= MIN_JACCARD:
        rules.append({
            'antecedent':  item_a,
            'consequent':  item_b,
            'support':     round(support, 6),
            'confidence':  round(conf_ab, 4),
            'lift':        round(lift_ab, 2),
            'jaccard':     round(jaccard, 4),
            'pair_count':  pair_count,
            'count_a':     count_a,
            'count_b':     count_b,
        })

    # Rule 2: B → A
    conf_ba = pair_count / count_b
    lift_ba = conf_ba / (count_a / total_baskets)

    if conf_ba >= MIN_CONF and pair_count >= MIN_PAIR_COUNT and jaccard >= MIN_JACCARD:
        rules.append({
            'antecedent':  item_b,
            'consequent':  item_a,
            'support':     round(support, 6),
            'confidence':  round(conf_ba, 4),
            'lift':        round(lift_ba, 2),
            'jaccard':     round(jaccard, 4),
            'pair_count':  pair_count,
            'count_a':     count_b,
            'count_b':     count_a,
        })

print(f"✅ Rules generated: {len(rules):,}")
print(f"   ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 5: SAVE ──────────────────────────────────────────────────────
print("⏳ Step 5: Saving rules...")

rules_df = pd.DataFrame(rules)
rules_df = rules_df.sort_values('jaccard', ascending=False)
rules_df.to_csv('apriori_rules.csv', index=False)

print(f"✅ Saved: apriori_rules.csv  ({len(rules_df):,} rules)")
print()


# ── BREAKDOWN ─────────────────────────────────────────────────────────
print("📊 Pair count distribution of rules:")
print(f"   50–100:     {len(rules_df[(rules_df['pair_count'] >= 50)  & (rules_df['pair_count'] < 100)]):,} rules  ← popular tracks")
print(f"   100–500:    {len(rules_df[(rules_df['pair_count'] >= 100) & (rules_df['pair_count'] < 500)]):,} rules")
print(f"   500–1000:   {len(rules_df[(rules_df['pair_count'] >= 500) & (rules_df['pair_count'] < 1000)]):,} rules")
print(f"   1000+:      {len(rules_df[rules_df['pair_count'] >= 1000]):,} rules  ← very strong co-occurrences")
print()
print("📊 Jaccard distribution (for ranking):")
print(f"   0.01–0.05:  {len(rules_df[(rules_df['jaccard'] >= 0.01) & (rules_df['jaccard'] < 0.05)]):,} rules  ← popular tracks (low Jacc expected)")
print(f"   0.05–0.20:  {len(rules_df[(rules_df['jaccard'] >= 0.05) & (rules_df['jaccard'] < 0.20)]):,} rules")
print(f"   0.20–0.50:  {len(rules_df[(rules_df['jaccard'] >= 0.20) & (rules_df['jaccard'] < 0.50)]):,} rules")
print(f"   0.50+:      {len(rules_df[rules_df['jaccard'] >= 0.50]):,} rules  ← near-inseparable niche pairs")
print()


# ── TOP 20 BY JACCARD ──────────────────────────────────────────────────
print("🏆 Top 20 rules by Jaccard:")
print("-" * 100)
print(f"{'Antecedent':<38} {'Consequent':<33} {'Jacc':>6}  {'Conf':>6}  {'Count':>6}")
print("-" * 100)
for _, row in rules_df.head(20).iterrows():
    a = str(row['antecedent'])[:37]
    b = str(row['consequent'])[:32]
    print(f"{a:<38} {b:<33} {row['jaccard']:>6.3f}  {row['confidence']:>6.2f}  {int(row['pair_count']):>6,}")
print()


# ── SUMMARY ───────────────────────────────────────────────────────────
total_time = time.time() - start
print("=" * 60)
print("🎉 PHASE 2B COMPLETE — Apriori v3 Done (popularity bias fixed)")
print("=" * 60)
print(f"  Total baskets:   {total_baskets:,}")
print(f"  Frequent items:  {len(frequent_items):,}")
print(f"  Frequent pairs:  {len(frequent_pairs):,}")
print(f"  Rules kept:      {len(rules_df):,}")
print(f"  Total runtime:   {total_time:.1f}s ({total_time/60:.1f} mins)")
print()
print("📁 Output: apriori_rules.csv  (sorted by Jaccard)")
print("➡️  Next: Phase 2C — FP-Growth via mlxtend")
