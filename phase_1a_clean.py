"""
EchoLink — Phase 1A: Remove Auto-Generated Playlists
=====================================================
What this script does:
  1. Loads the raw Spotify dataset
  2. Removes known auto-generated playlists (Starred, Liked from Radio, etc.)
  3. Creates a composite basket_id (user_id + playlistname)
  4. Removes any basket with more than 500 tracks (safety net)
  5. Saves the cleaned output as 'spotify_1a_clean.csv'
"""

import pandas as pd
import time

start = time.time()

# ── STEP 1: LOAD ──────────────────────────────────────────────────────
print("⏳ Step 1: Loading dataset... (this takes ~60–90 seconds)")

df = pd.read_csv(
    'spotify_dataset.csv',
    names=['user_id', 'artistname', 'trackname', 'playlistname'],
    skiprows=1,           # skip the header row
    on_bad_lines='skip',  # skip the ~1,205 malformed rows
    dtype={
        'artistname':   'category',   # store repeated strings efficiently
        'playlistname': 'category',   # store repeated strings efficiently
    }
)

print(f"✅ Loaded: {len(df):,} rows  ({time.time()-start:.1f}s elapsed)")
print(f"   Columns: {list(df.columns)}")
print()


# ── STEP 2: BLOCKLIST — Remove known auto-generated playlists ─────────
print("⏳ Step 2: Removing auto-generated playlists from blocklist...")

BLOCKLIST = [
    'Starred',                  # Spotify's old star/like button — 1.3M tracks
    'Liked from Radio',         # Auto-saved from radio thumbs-up
    'Favoritas de la radio',    # Spanish version of Liked from Radio
]

rows_before = len(df)
df = df[~df['playlistname'].isin(BLOCKLIST)]
rows_removed = rows_before - len(df)

print(f"✅ Removed: {rows_removed:,} rows from blocklist")
print(f"   Remaining: {len(df):,} rows  ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 3: COMPOSITE BASKET ID ───────────────────────────────────────
print("⏳ Step 3: Creating composite basket_id (user + playlist)...")

df['basket_id'] = (
    df['user_id'].str.strip()
    + '||'
    + df['playlistname'].astype(str).str.strip()
)

print(f"✅ Unique baskets created: {df['basket_id'].nunique():,}")
print(f"   ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 4: SIZE CAP — Remove baskets with > 500 tracks ───────────────
print("⏳ Step 4: Applying size cap (removing baskets > 500 tracks)...")

basket_sizes = df.groupby('basket_id')['trackname'].count()
valid_baskets = basket_sizes[basket_sizes <= 500].index
oversized = (basket_sizes > 500).sum()

rows_before = len(df)
df = df[df['basket_id'].isin(valid_baskets)]
rows_removed = rows_before - len(df)

print(f"✅ Removed: {oversized:,} oversized baskets ({rows_removed:,} rows)")
print(f"   Remaining: {len(df):,} rows  ({time.time()-start:.1f}s elapsed)")
print()


# ── STEP 5: VERIFY ────────────────────────────────────────────────────
print("🔍 Verifying results...")

# No blocklist playlists should remain
blocklist_remaining = df['playlistname'].isin(BLOCKLIST).sum()
assert blocklist_remaining == 0, f"ERROR: {blocklist_remaining} blocklist rows still present!"

# No basket should exceed 500 tracks
max_basket = df.groupby('basket_id')['trackname'].count().max()
assert max_basket <= 500, f"ERROR: Basket too large — {max_basket} tracks"

print(f"✅ No blocklist playlists remaining")
print(f"✅ Max basket size: {max_basket} tracks (≤ 500)")
print()


# ── STEP 6: SAVE ──────────────────────────────────────────────────────
print("⏳ Saving cleaned dataset to 'spotify_1a_clean.csv'...")

df[['user_id', 'artistname', 'trackname', 'playlistname', 'basket_id']].to_csv(
    'spotify_1a_clean.csv',
    index=False
)

print(f"✅ Saved: spotify_1a_clean.csv")
print()


# ── SUMMARY ───────────────────────────────────────────────────────────
total_time = time.time() - start
print("=" * 50)
print("🎉 PHASE 1A COMPLETE")
print("=" * 50)
print(f"  Total rows:          {len(df):,}")
print(f"  Unique baskets:      {df['basket_id'].nunique():,}")
print(f"  Unique artists:      {df['artistname'].nunique():,}")
print(f"  Unique playlists:    {df['playlistname'].nunique():,}")
print(f"  Total time:          {total_time:.1f} seconds")
print()
print("➡️  Next step: Run phase_1b_items.py (Phase 1B & 1C)")
