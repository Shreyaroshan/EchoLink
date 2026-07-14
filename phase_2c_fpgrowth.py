"""
EchoLink — Phase 2C: FP-Growth via mlxtend
===========================================
What this script does:
  1. Loads spotify_clean.csv and builds transaction list
  2. Encodes transactions into one-hot format (mlxtend requirement)
  3. Runs FP-Growth to find frequent itemsets
  4. Generates association rules with support, confidence, lift, Jaccard
  5. Compares results and runtime against Phase 2B (Apriori)

⚠️  Memory note:
  mlxtend requires a dense one-hot boolean matrix (baskets × items).
  Full dataset (161K × 46K) = ~7.5 GB — too large for 16 GB RAM.
  Solution: Use min_support = 0.005 (810+ baskets) to reduce item space.
  This is a real benchmark finding — documented in the comparison output.

Config:
  FP_MIN_SUPPORT = 0.005   → item must appear in 0.5% of baskets (~810)
  MIN_CONF       = 0.5     → same as Apriori
  MIN_JACCARD    = 0.05    → same as Apriori

Input:   spotify_clean.csv
Output:  fpgrowth_rules.csv
"""

import pandas as pd
import numpy as np
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules
from collections import Counter
import time

# ── CONFIG ────────────────────────────────────────────────────────────
FP_MIN_SUPPORT = 0.005   # fraction of baskets (0.5% = ~810 baskets)
MIN_CONF       = 0.5
MIN_JACCARD    = 0.05

start = time.time()
print("=" * 58)
print("EchoLink — Phase 2C: FP-Growth via mlxtend")
print("=" * 58)
print(f"  FP Min Support:  {FP_MIN_SUPPORT} ({FP_MIN_SUPPORT*100:.1f}% of baskets)")
print(f"  Min Confidence:  {MIN_CONF}")
print(f"  Min Jaccard:     {MIN_JACCARD}")
print()
print("  ⚠️  Note: Higher min_support used vs Apriori due to")
print("     mlxtend's dense matrix memory requirements.")
print()


# ── STEP 1: LOAD & BUILD TRANSACTION LIST ─────────────────────────────
print("⏳ Step 1: Loading data and building transaction list...")

df = pd.read_csv('spotify_clean.csv')

# Group into list of lists (mlxtend format)
transactions = (
    df.groupby('basket_id')['item']
    .apply(list)
    .tolist()
)

total_baskets = len(transactions)
min_count = int(FP_MIN_SUPPORT * total_baskets)

print(f"✅ Loaded: {len(df):,} rows → {total_baskets:,} baskets")
print(f"   Min support count: {min_count:,} baskets")
print(f"   ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 2: PRE-FILTER ITEMS (memory optimization) ────────────────────
print("⏳ Step 2: Pre-filtering items to those meeting min support...")

# Count individual item frequencies (across ALL baskets)
item_counts_all = Counter(item for txn in transactions for item in txn)

# Only keep items meeting FP_MIN_SUPPORT
frequent_item_set = {item for item, count in item_counts_all.items()
                     if count >= min_count}

# Filter each transaction to only frequent items
transactions_filtered = [
    [item for item in txn if item in frequent_item_set]
    for txn in transactions
]

# Remove empty baskets
transactions_filtered = [t for t in transactions_filtered if len(t) > 1]

# Recount item frequencies within filtered baskets only
# ⚠️  This is what mlxtend uses — must be consistent!
filtered_item_counts = Counter(item for txn in transactions_filtered for item in txn)
n_filtered = len(transactions_filtered)   # baskets mlxtend sees

print(f"✅ Items meeting threshold: {len(frequent_item_set):,} (from {len(item_counts_all):,})")
print(f"   Baskets after filtering: {n_filtered:,}")
print(f"   Estimated matrix size:   {n_filtered * len(frequent_item_set) / 1e9:.2f} GB")
print(f"   ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 3: ONE-HOT ENCODE ────────────────────────────────────────────
print("⏳ Step 3: One-hot encoding transactions (mlxtend format)...")

te = TransactionEncoder()
te_array = te.fit(transactions_filtered).transform(transactions_filtered)
df_encoded = pd.DataFrame(te_array, columns=te.columns_)

print(f"✅ Encoded matrix shape: {df_encoded.shape[0]:,} × {df_encoded.shape[1]:,}")
print(f"   Memory usage: {df_encoded.memory_usage(deep=True).sum() / 1e9:.2f} GB")
print(f"   ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 4: RUN FP-GROWTH ─────────────────────────────────────────────
print("⏳ Step 4: Running FP-Growth algorithm...")
t_fpgrowth_start = time.time()

frequent_itemsets = fpgrowth(
    df_encoded,
    min_support=FP_MIN_SUPPORT,
    use_colnames=True
)

t_fpgrowth_end = time.time()
fpgrowth_time = t_fpgrowth_end - t_fpgrowth_start

# Only keep pairs (2-itemsets) for fair comparison with Apriori
pairs = frequent_itemsets[frequent_itemsets['itemsets'].apply(len) == 2]

print(f"✅ Frequent itemsets found: {len(frequent_itemsets):,}")
print(f"   Of which pairs (2-items): {len(pairs):,}")
print(f"   FP-Growth core runtime:   {fpgrowth_time:.1f}s")
print(f"   ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 5: GENERATE RULES ────────────────────────────────────────────
print("⏳ Step 5: Generating association rules...")

raw_rules = association_rules(
    frequent_itemsets,
    metric='confidence',
    min_threshold=MIN_CONF,
    num_itemsets=len(frequent_itemsets)
)

# Flatten antecedent/consequent from frozensets to strings
raw_rules['antecedent'] = raw_rules['antecedents'].apply(lambda x: list(x)[0])
raw_rules['consequent'] = raw_rules['consequents'].apply(lambda x: list(x)[0])

# ✅ FIX: Use n_filtered (mlxtend's reference) for pair_count
#         and filtered_item_counts (same reference) for count_a/count_b
raw_rules['pair_count'] = (raw_rules['support'] * n_filtered).round().astype(int)
raw_rules['count_a'] = raw_rules['antecedent'].map(filtered_item_counts)
raw_rules['count_b'] = raw_rules['consequent'].map(filtered_item_counts)
raw_rules['jaccard'] = raw_rules['pair_count'] / (
    raw_rules['count_a'] + raw_rules['count_b'] - raw_rules['pair_count']
)

# Apply Jaccard filter
rules_df = raw_rules[raw_rules['jaccard'] >= MIN_JACCARD].copy()
rules_df = rules_df[[
    'antecedent', 'consequent', 'support', 'confidence', 'lift',
    'jaccard', 'pair_count', 'count_a', 'count_b'
]].sort_values('jaccard', ascending=False)

# Fix 1: Guard against duplicate directed pairs (safety net)
before = len(rules_df)
rules_df = rules_df.drop_duplicates(['antecedent', 'consequent'])
duplicates_dropped = before - len(rules_df)
if duplicates_dropped > 0:
    print(f"  ⚠️  WARNING: dropped {duplicates_dropped} duplicate directed pairs!")
else:
    print(f"  ✅ No duplicate directed pairs found ({before} rules clean)")

print(f"✅ Rules after filters: {len(rules_df):,}")
print(f"   ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 6: SAVE ──────────────────────────────────────────────────────
rules_df.to_csv('fpgrowth_rules.csv', index=False)
print(f"✅ Saved: fpgrowth_rules.csv  ({len(rules_df):,} rules)")
print()


# ── TOP 20 ────────────────────────────────────────────────────────────
print("🏆 Top 20 FP-Growth rules by Jaccard:")
print("-" * 100)
print(f"{'Antecedent':<38} {'Consequent':<33} {'Jacc':>6}  {'Conf':>6}  {'Count':>6}")
print("-" * 100)
for _, row in rules_df.head(20).iterrows():
    a = str(row['antecedent'])[:37]
    b = str(row['consequent'])[:32]
    print(f"{a:<38} {b:<33} {row['jaccard']:>6.3f}  {row['confidence']:>6.2f}  {int(row['pair_count']):>6,}")
print()


# ── BENCHMARK COMPARISON ──────────────────────────────────────────────
apriori_time = 95.8   # recorded from Phase 2B v3 run (see EchoLink_Project_Docs.md)
total_time = time.time() - start

print("=" * 58)
print("📊 BENCHMARK: Apriori vs FP-Growth")
print("=" * 58)
print(f"{'Metric':<30} {'Apriori':>12} {'FP-Growth':>12}")
print("-" * 56)
print(f"{'Min support threshold':<30} {'20 baskets':>12} {f'{min_count} baskets':>12}")
print(f"{'Items in scope':<30} {'46,151':>12} {len(frequent_item_set):>12,}")
print(f"{'Rules generated':<30} {'126,945':>12} {len(rules_df):>12,}")
print(f"{'Total runtime (s)':<30} {apriori_time:>12.1f} {total_time:>12.1f}")
print(f"{'FP-Growth core only (s)':<30} {'N/A':>12} {fpgrowth_time:>12.1f}")
print()
print("  ⚠️  Note: Different min_support thresholds used.")
print("     Apriori (custom): min 20 baskets  — full item coverage")
print("     FP-Growth (mlxtend): min 810 baskets — memory constrained")
print("     This is a real-world limitation worth showing in the dashboard.")
print()
print("=" * 58)
print("🎉 PHASE 2C COMPLETE — FP-Growth Done")
print("=" * 58)
print("➡️  Next: Phase 2D — Merge & finalize rules for database")
