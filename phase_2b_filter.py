"""
EchoLink — Phase 2B (Filter): Apply Stricter Thresholds to Apriori Rules
=========================================================================
Re-filters the already-computed apriori_rules.csv with tighter thresholds.
No need to re-run the expensive pair counting step.

New thresholds:
  MIN_CONF = 0.2  (was 0.1)  → at least 20% co-occurrence rate
  MIN_LIFT = 2.5  (was 1.5)  → at least 2.5x better than random

Input:   apriori_rules.csv       (canonical output from Phase 2B — used by the DB)
Output:  apriori_rules_clean.csv (exploration artifact — NOT loaded into the database;
                                  the DB uses apriori_rules.csv directly)
"""

import pandas as pd

# ── CONFIG ────────────────────────────────────────────────────────────
MIN_CONF = 0.2
MIN_LIFT = 2.5

# ── LOAD ──────────────────────────────────────────────────────────────
print("⏳ Loading apriori_rules.csv...")
rules = pd.read_csv('apriori_rules.csv')
print(f"✅ Loaded: {len(rules):,} rules")
print()

# ── FILTER ────────────────────────────────────────────────────────────
print(f"⏳ Applying filters: MIN_CONF={MIN_CONF}, MIN_LIFT={MIN_LIFT}...")

filtered = rules[
    (rules['confidence'] >= MIN_CONF) &
    (rules['lift']       >= MIN_LIFT)
]

removed = len(rules) - len(filtered)
print(f"✅ Rules after filter: {len(filtered):,}")
print(f"   Removed:            {removed:,}  ({100*removed/len(rules):.1f}% of original)")
print()

# ── BREAKDOWN ─────────────────────────────────────────────────────────
print("📊 Quality breakdown of filtered rules:")
print(f"   Lift  2.5–5.0:  {len(filtered[(filtered['lift'] >= 2.5) & (filtered['lift'] < 5)]):,} rules")
print(f"   Lift  5.0–10:   {len(filtered[(filtered['lift'] >= 5)   & (filtered['lift'] < 10)]):,} rules")
print(f"   Lift  10–50:    {len(filtered[(filtered['lift'] >= 10)  & (filtered['lift'] < 50)]):,} rules")
print(f"   Lift  50+:      {len(filtered[filtered['lift'] >= 50]):,} rules  ← very strong")
print()
print(f"   Conf 0.20–0.40: {len(filtered[(filtered['confidence'] >= 0.2) & (filtered['confidence'] < 0.4)]):,} rules")
print(f"   Conf 0.40–0.60: {len(filtered[(filtered['confidence'] >= 0.4) & (filtered['confidence'] < 0.6)]):,} rules")
print(f"   Conf 0.60–0.80: {len(filtered[(filtered['confidence'] >= 0.6) & (filtered['confidence'] < 0.8)]):,} rules")
print(f"   Conf 0.80–1.00: {len(filtered[filtered['confidence'] >= 0.8]):,} rules  ← very reliable")
print()

# ── TOP 20 ────────────────────────────────────────────────────────────
# Fix 4b: Heading corrected — sort is Jaccard (the project-wide primary metric).
# Lift is used only as a filter gate above (MIN_LIFT = 2.5), not for ranking.
print("🏆 Top 20 rules by Jaccard:")
print("-" * 95)
print(f"{'Antecedent':<40} {'Consequent':<35} {'Lift':>8}  {'Conf':>6}  {'Count':>6}")
print("-" * 95)
for _, row in filtered.head(20).iterrows():
    a = str(row['antecedent'])[:39]
    b = str(row['consequent'])[:34]
    print(f"{a:<40} {b:<35} {row['lift']:>8.2f}  {row['confidence']:>6.2f}  {int(row['pair_count']):>6,}")
print()

# ── SAVE ──────────────────────────────────────────────────────────────
filtered.to_csv('apriori_rules_clean.csv', index=False)
print(f"✅ Saved: apriori_rules_clean.csv  ({len(filtered):,} rules)")
print()
print("=" * 50)
print("✅ Filtering complete. Ready for Phase 2C — FP-Growth")
print("=" * 50)
