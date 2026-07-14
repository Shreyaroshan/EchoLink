"""
EchoLink — Phase 1C + 1D + 1E: Item ID, Min-Support Filter & Final Save
========================================================================
What this script does:
  1C. Creates composite item ID (artistname + trackname)
  1D. Applies min-support filter — drops tracks appearing in < 25 baskets
  1E. Saves the final mine-ready dataset as 'spotify_clean.csv'

Input:  spotify_1a_clean.csv   (output from Phase 1A)
Output: spotify_clean.csv      (final dataset for Apriori / FP-Growth)

MIN_SUPPORT = 25
  → Only keep tracks that appear in at least 25 unique playlists
  → Keeps niche/indie tracks while removing true one-hit wonders
"""

import pandas as pd
import time

# ── CONFIG ────────────────────────────────────────────────────────────
MIN_SUPPORT = 25   # ← change this to experiment with different thresholds

start = time.time()

# ── STEP 1C: LOAD + CREATE ITEM ID ───────────────────────────────────
print("⏳ Step 1C: Loading Phase 1A output and creating item IDs...")
print(f"   Reading: spotify_1a_clean.csv")

df = pd.read_csv(
    'spotify_1a_clean.csv',
    dtype={
        'artistname':   'category',
        'playlistname': 'category',
    }
)

print(f"✅ Loaded: {len(df):,} rows  ({time.time()-start:.1f}s elapsed)")
print(f"   Unique baskets:  {df['basket_id'].nunique():,}")
print(f"   Unique tracks (before filter): {df['trackname'].nunique():,}")
print()

import re

def normalize_track(name: str) -> str:
    """
    Strip common variant suffixes from track names so that
    'Get Lucky', 'Get Lucky (Radio Edit)', 'Get Lucky - Remastered'
    all map to the same canonical item string.

    Strips (in order):
      - Parenthesised suffixes: (Radio Edit), (Remastered), (feat. X),
        (ft. X), (Live), (Acoustic), (Instrumental), (Version), (Single),
        (Extended), (Original Mix), (Club Mix), (Album Version), (Bonus Track)
      - Dash-separated suffixes after a space-dash-space:
        ' - Radio Edit', ' - Remastered', ' - Live', etc.
    Preserves the core title capitalisation.
    """
    if not isinstance(name, str):
        return name

    # Remove parenthesised suffixes
    name = re.sub(
        r'\s*\('
        r'(?:'
        r'[Rr]adio\s*[Ee]dit|[Rr]emaster(?:ed)?(?:\s+\d{4})?|'
        r'[Ff](?:ea)?t\.?\s+[^)]+|[Ll]ive(?:\s+[^)]*)?|'
        r'[Aa]coustic(?:\s+[^)]*)?|[Ii]nstrumental|'
        r'[Ee]xtended(?:\s+[Mm]ix)?|[Oo]riginal\s+[Mm]ix|'
        r'[Cc]lub\s+[Mm]ix|[Aa]lbum\s+[Vv]ersion|'
        r'[Ss]ingle\s+[Vv]ersion|[Bb]onus\s+[Tt]rack|'
        r'\d{4}\s+[Rr]emaster|\d{4}\s+[Dd]igital\s+[Rr]emaster|'
        r'[Rr]emission|[Rr]emix|[Dd]eluxe|[Ee]dition|[Vv]ersion'
        r')'
        r'[^)]*\)',
        '',
        name
    )

    # Remove dash-separated suffixes (e.g. ' - Radio Edit', ' - Live', ' - Remastered')
    name = re.sub(
        r'\s+-\s+(?:'
        r'[Rr]adio\s*[Ee]dit|[Rr]emaster(?:ed)?(?:\s+\d{4})?|'
        r'[Ll]ive(?:\s+.+)?|[Aa]coustic(?:\s+.+)?|'
        r'[Ff](?:ea)?t\.?\s+\S+.*|[Rr]emix|[Vv]ersion|'
        r'\d{4}\s+[Rr]emaster|\d{4}\s+[Dd]igital\s+[Rr]emaster'
        r')$',
        '',
        name
    )

    return name.strip()

# Create item = "Artist - NormalisedTrack"
df['item'] = (
    df['artistname'].astype(str).str.strip()
    + ' - '
    + df['trackname'].astype(str).str.strip().apply(normalize_track)
)

# Also store the raw display names for the lookup (UI shows them)
df['trackname_display'] = df['trackname'].astype(str).str.strip()
df['trackname'] = df['trackname'].astype(str).str.strip().apply(normalize_track)

print(f"   Sample items after normalization:")
for item in df['item'].head(5).values:
    print(f"     → {item}")
print()


# ── STEP 1D: MIN-SUPPORT FILTER ───────────────────────────────────────
print(f"⏳ Step 1D: Applying min-support filter (threshold = {MIN_SUPPORT} baskets)...")

# For each item, count how many UNIQUE baskets it appears in
item_basket_counts = df.groupby('item')['basket_id'].nunique()

total_items_before = item_basket_counts.shape[0]
popular_items = item_basket_counts[item_basket_counts >= MIN_SUPPORT].index
total_items_after = len(popular_items)
items_dropped = total_items_before - total_items_after

print(f"   Items before filter: {total_items_before:,}")
print(f"   Items after  filter: {total_items_after:,}")
print(f"   Items dropped:       {items_dropped:,}  ({100*items_dropped/total_items_before:.1f}% removed)")
print()

# Show distribution — how many items at each threshold level
print("   Frequency breakdown:")
print(f"     In 1–10 baskets:    {(item_basket_counts.between(1,10)).sum():,} items  (dropped)")
print(f"     In 11–24 baskets:   {(item_basket_counts.between(11,24)).sum():,} items  (dropped)")
print(f"     In 25–50 baskets:   {(item_basket_counts.between(25,50)).sum():,} items  (kept ✅)")
print(f"     In 51–100 baskets:  {(item_basket_counts.between(51,100)).sum():,} items  (kept ✅)")
print(f"     In 100+ baskets:    {(item_basket_counts > 100).sum():,} items  (kept ✅)")
print()

rows_before = len(df)
df = df[df['item'].isin(popular_items)]
rows_removed = rows_before - len(df)

print(f"✅ Filtered dataset:")
print(f"   Rows:    {len(df):,}  (removed {rows_removed:,} rows)")
print(f"   Baskets: {df['basket_id'].nunique():,}")
print(f"   Items:   {df['item'].nunique():,}")
print(f"   ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 1E: SAVE FINAL CLEAN DATASET ────────────────────────────────
print("⏳ Step 1E: Saving final clean dataset...")

# Only basket_id and item — all Apriori/FP-Growth needs
output = df[['basket_id', 'item']]
output.to_csv('spotify_clean.csv', index=False)

print(f"✅ Saved: spotify_clean.csv")
print()

# Also save a lookup table: item → artist, trackname (useful for the UI later)
print("⏳ Saving item lookup table (for UI display later)...")
lookup = (
    df[['item', 'artistname', 'trackname']]
    .drop_duplicates(subset='item')
    .sort_values('item')
)
lookup.to_csv('item_lookup.csv', index=False)
print(f"✅ Saved: item_lookup.csv  ({len(lookup):,} unique tracks)")
print()


# ── FINAL SUMMARY ─────────────────────────────────────────────────────
total_time = time.time() - start
print("=" * 55)
print("🎉 PHASE 1C + 1D + 1E COMPLETE")
print("=" * 55)
print(f"  Min-support threshold:   {MIN_SUPPORT} baskets")
print(f"  Final rows:              {len(df):,}")
print(f"  Final unique baskets:    {df['basket_id'].nunique():,}")
print(f"  Final unique items:      {df['item'].nunique():,}")
print(f"  Total time:              {total_time:.1f} seconds")
print()
print("📁 Output files:")
print("  → spotify_clean.csv    (basket_id + item — for mining)")
print("  → item_lookup.csv      (item → artist + track — for UI)")
print()
print("➡️  Phase 1 complete! Next: Phase 2 — Association Rule Mining")
