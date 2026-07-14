# 🎵 Spotify Playlist Dataset — EDA Report

> **Analyst's note:** This report walks through every important aspect of the Spotify playlist dataset in plain, simple language. Think of it as a guided tour of the data — what's in it, what it looks like, what's interesting, and what to watch out for.

---

## 📁 1. About the Dataset

| Property | Details |
|---|---|
| **File** | `spotify_dataset.csv` |
| **File Size** | ~1.1 GB |
| **Source** | #nowplaying tweets by Spotify users (academic research dataset) |
| **Research Paper** | Pichl et al., *"Towards a Context-Aware Music Recommendation Approach"*, ICDM 2015 |

**In plain English:** This dataset was built by looking at Twitter posts where people tweeted "#nowplaying" while using Spotify. Each row tells us: *which user* added *which song* by *which artist* to *which playlist*. It's essentially a massive snapshot of real Spotify listening habits captured through social media.

---

## 🧱 2. Structure of the Dataset

The dataset has **4 columns** and no extra metadata:

| Column | What It Means | Example |
|---|---|---|
| `user_id` | A scrambled (hashed) version of the Spotify username — you can't tell who the person is, just that rows with the same ID belong to the same person | `9cc0cfd4d7d7885102480dd99e7a90d6` |
| `artistname` | The name of the music artist | `Daft Punk` |
| `trackname` | The name of the song | `Get Lucky` |
| `playlistname` | The name of the playlist this song belongs to | `Starred` |

**One row = one track inside one playlist for one user.** If a song appears in 3 different playlists for the same user, it shows up 3 times.

---

## 📊 3. How Big Is the Dataset?

| Metric | Number |
|---|---|
| **Total rows (track entries)** | 12,900,774 (~12.9 million) |
| **Unique users** | 15,918 |
| **Unique artists** | 289,753 |
| **Unique tracks (songs)** | 2,035,902 (~2 million) |
| **Unique playlist names** | 160,138 |

**Plain English:**
- Nearly **13 million** individual track records — this is a very large dataset.
- Only **~16,000 users** generated all of this. That's a lot of music per person!
- Over **2 million unique songs** from nearly **290,000 unique artists** — it covers an enormous range of music.
- There are **160,000+ unique playlist names**, showing how creatively diverse people are when naming their playlists.

---

## 🧹 4. Data Quality — Missing Values & Errors

| Column | Missing / Empty Values | % of Total |
|---|---|---|
| `user_id` | 0 | 0% ✅ |
| `artistname` | 33,767 | 0.26% ⚠️ |
| `trackname` | 82 | ~0% ✅ |
| `playlistname` | 85 | ~0% ✅ |
| **Parse errors** (malformed rows) | 1,205 | ~0% |

**Plain English:**
- The data is **very clean overall** — almost no missing values.
- The only real issue is about **33,767 rows where the artist name is blank** (~0.26%). These are likely songs with unknown or missing attribution in Spotify's metadata.
- There are a tiny number of **malformed rows** (1,205 out of 12.9 million) — less than 0.01%. These are likely rows with special characters or encoding issues and are safe to drop.
- **Action:** Before modeling, filter out rows with empty `artistname`, and drop the 1,205 parse errors.

---

## 🏆 5. Most Popular Artists

These are the artists whose songs appear most frequently across all playlists:

| Rank | Artist | Total Track Appearances |
|---|---|---|
| 1 | **Daft Punk** | 36,086 |
| 2 | **Coldplay** | 35,485 |
| 3 | *(blank — missing artist)* | 33,767 |
| 4 | **Radiohead** | 31,429 |
| 5 | **The Rolling Stones** | 30,814 |
| 6 | **Kanye West** | 29,111 |
| 7 | **JAY Z** | 28,928 |
| 8 | **Eminem** | 28,896 |
| 9 | **Queen** | 28,079 |
| 10 | **David Bowie** | 27,791 |

**Plain English:**
- The dataset skews toward **classic rock, pop, hip-hop, and electronic music** — genres with broad, loyal fanbases.
- Daft Punk topping the list makes sense given the dataset is from Twitter-era Spotify users (~2015), when Daft Punk's "Random Access Memories" (2013) was hugely popular.
- The blank entry at #3 represents the 33,767 rows with missing artist names — these should be cleaned up before analysis.

---

## 🎵 6. Most Popular Tracks

These are the song *names* (not unique songs — just names) that appear most across all playlists:

| Rank | Track Name | Appearances |
|---|---|---|
| 1 | **Intro** | 6,676 |
| 2 | **Home** | 5,600 |
| 3 | **Closer** | 3,549 |
| 4 | **Runaway** | 3,350 |
| 5 | **Hold On** | 3,224 |
| 6 | **Radioactive** | 3,189 |
| 7 | **Forever** | 3,055 |
| 8 | **Stay** | 2,993 |
| 9 | **Alive** | 2,936 |
| 10 | **Wake Me Up** | 2,795 |

**Plain English:**
- These are **generic track names** shared by many different artists (e.g., dozens of songs are titled "Intro" or "Home"). These high counts don't represent a single hit song — they reflect many songs sharing the same common title.
- For meaningful track-level analysis, you should always use the **(artistname + trackname) combination** as the unique identifier for a song, not just the track name alone.

---

## 📋 7. Most Popular Playlist Names

| Rank | Playlist Name | Total Tracks |
|---|---|---|
| 1 | **Starred** | 1,337,164 |
| 2 | **Liked from Radio** | 180,083 |
| 3 | **Rock** | 30,496 |
| 4 | **Favoritas de la radio** | 30,425 |
| 5 | **2014** | 24,012 |
| 6 | **Christmas** | 22,442 |
| 7 | **2013** | 21,077 |
| 8 | **Work** | 18,462 |
| 9 | **Jazz** | 18,338 |
| 10 | **Indie** | 17,859 |

**Plain English:**
- **"Starred"** is Spotify's old default "like" playlist (similar to today's Liked Songs). Its massive size (1.3M tracks!) explains the outlier in playlist size distributions — it's not really a manually curated playlist but a system-generated one used by almost every user.
- **"Liked from Radio"** is another auto-generated Spotify playlist.
- After those two auto-playlists, the top names are **genre-based** (Rock, Jazz, Indie), **year-based** (2013, 2014), **mood/activity-based** (Work, Christmas) — reflecting how people actually name their playlists.
- **"Favoritas de la radio"** is the Spanish version of "Liked from Radio" — telling us the dataset has **international users**.

---

## 📈 8. Distribution Statistics

### Tracks per Artist

| Stat | Value |
|---|---|
| Average (mean) | 44.5 tracks |
| Middle value (median) | 2 tracks |
| Maximum | 36,086 tracks (Daft Punk) |
| Minimum | 1 track |

**Plain English:** The average of 44.5 is misleading. The *median* of 2 tells the real story — **most artists in the dataset appear only 1–2 times**. A few mega-popular artists drive the average way up. This is a classic "long tail" distribution — a small number of very popular artists, and a huge number of obscure ones.

---

### Tracks per Playlist

| Stat | Value |
|---|---|
| Average (mean) | 80.6 tracks |
| Middle value (median) | 20 tracks |
| Maximum | 1,337,164 tracks ("Starred") |
| Minimum | 1 track |

**Plain English:** Again, the "Starred" playlist massively skews the mean. The median of 20 tracks is more representative of a typical playlist. Most playlists are medium-sized personal collections.

---

### Playlists per User

| Stat | Value |
|---|---|
| Average (mean) | 15 playlists |
| Middle value (median) | 9 playlists |
| Maximum | 309 playlists |
| Minimum | 1 playlist |

**Plain English:** A typical user has around **9 playlists**. Some super-active users have hundreds of playlists, but most people keep it simple with under 10.

---

### Tracks per User (Total)

| Stat | Value |
|---|---|
| Average (mean) | 810 tracks |
| Middle value (median) | 358 tracks |
| Maximum | 295,292 tracks |
| Minimum | 1 track |

**Plain English:** The median user has **~358 songs** saved across all their playlists. The maximum of 295,292 is an extreme outlier — either a very dedicated music fan, a bot, or a test account. This is something worth investigating before building any recommendation system.

---

## 📦 9. Playlist Size Distribution

| Size Category | Number of Playlists | Percentage |
|---|---|---|
| **Tiny (1–5 tracks)** | 19,809 | 12.4% |
| **Small (6–20 tracks)** | 63,707 | **39.8%** |
| **Medium (21–50 tracks)** | 39,132 | 24.4% |
| **Large (51–100 tracks)** | 18,236 | 11.4% |
| **Very Large (100+ tracks)** | 19,254 | 12.0% |

**Plain English:**
- The **majority of playlists (40%) are small** with 6–20 tracks — think of a short road trip playlist or a "workout" mix.
- About **12% are tiny** (1–5 songs) — possibly recently created playlists or ones the user never built out.
- Only **12% have 100+ tracks**, and most of those are likely auto-generated playlists like "Starred".
- This shows that **people generally create focused, medium-sized playlists** for specific moods or activities.

---

## 🔍 10. Artist Popularity — Long Tail Effect

| Category | Count | Percentage |
|---|---|---|
| Artists appearing **only once** | 111,832 | **38.6%** of all artists |
| All other artists | 177,921 | 61.4% |

**Plain English:** Nearly **4 out of every 10 artists** in the dataset appear in just a single track entry. This is the classic "long tail" — a tiny elite of mainstream artists dominate, while the vast majority are niche, obscure, or independent artists with minimal representation. This is an important insight for **recommendation systems**: most artists have almost no data to learn from.

---

## ⚠️ 11. Key Issues & Things to Watch Out For

| Issue | Description | Recommendation |
|---|---|---|
| **Missing artist names** | 33,767 rows have no artist | Filter these out before analysis |
| **"Starred" outlier** | This one playlist has 1.3M tracks — 10x larger than anything else | Treat it separately or exclude from playlist-size analysis |
| **Generic track names** | "Intro", "Home", etc. are shared by many artists | Always use (artist + track) as the unique song identifier |
| **Long tail artists** | 38.6% of artists appear only once | Collaborative filtering models will struggle with these; consider minimum-frequency thresholds |
| **Power users** | One user has 295,292 tracks | Investigate as potential outlier or bot |
| **Parse errors** | 1,205 malformed rows | Drop these rows during preprocessing |
| **Auto-generated playlists** | "Starred" and "Liked from Radio" are Spotify system playlists, not user-curated | Consider excluding or flagging them separately |

---

## 💡 12. Key Takeaways for an Analyst

1. **This is a high-quality, real-world dataset** — very little missing data and genuinely organic user behavior captured from social media.

2. **The data is heavily skewed** at every level (artists, playlists, users). Always use **median, not mean**, when summarizing distributions.

3. **Genre variety is wide** — from electronic (Daft Punk) to classic rock (Rolling Stones) to hip-hop (Kanye, Eminem) to jazz — making this great for music genre classification or recommendation research.

4. **Playlist names are rich signals** — names like "Christmas", "Work", "Chill", "2014" carry context about *when* and *why* music was played. The original research paper explores this for context-aware recommendations.

5. **The dataset is ideal for:**
   - Music recommendation system development
   - Playlist-based collaborative filtering
   - Artist/genre clustering
   - Music taste profiling by user

6. **The dataset is NOT ideal for:**
   - Time-series analysis (no timestamps)
   - Audio feature analysis (no audio data)
   - Song popularity scoring (appearance count does not equal play count)

---

## 📌 Quick Reference Summary

```
Total Records     : 12,900,774
Unique Users      : 15,918
Unique Artists    : 289,753
Unique Tracks     : 2,035,902
Unique Playlists  : 160,138

Top Artist        : Daft Punk (36,086 appearances)
Top Playlist      : Starred (1,337,164 tracks)
Avg Playlists/User: 15  |  Median: 9
Avg Tracks/User   : 810 |  Median: 358
Avg Playlist Size : 81 tracks | Median: 20

Missing Data      : Only 0.26% (artist names)
Parse Errors      : 1,205 rows (~0.01%)
```

---

*Report generated by automated EDA analysis. Dataset source: Pichl et al., ICDM 2015.*
