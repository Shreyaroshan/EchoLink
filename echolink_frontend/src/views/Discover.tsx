import { useState, useCallback } from 'react';
import { getRecommendations } from '../api';
import type { Track, RecommendResult, SortMetric } from '../api';
import SearchBar from '../components/SearchBar';
import TrackCard from '../components/TrackCard';
import RecommendCard from '../components/RecommendCard';
import SortControls from '../components/SortControls';
import RulesetToggle from '../components/RulesetToggle';
import Skeleton from '../components/Skeleton';

export default function Discover() {
  const [selectedTrack, setSelectedTrack] = useState<Track | null>(null);
  const [result, setResult] = useState<RecommendResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortMetric>('jaccard');
  const [rulesetId, setRulesetId] = useState(1);
  const [limit, setLimit] = useState(10);
  const [excludeSameArtist, setExcludeSameArtist] = useState(true);

  const fetchRecs = useCallback(async (
    track: Track,
    sort: SortMetric,
    ruleset: number,
    lim: number,
    excludeSame: boolean,
  ) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRecommendations(track.item, lim, ruleset, sort, excludeSame);
      setResult(data);
    } catch {
      setError('Could not load recommendations. Is the API running at localhost:8000?');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSelect = (track: Track) => {
    setSelectedTrack(track);
    fetchRecs(track, sortBy, rulesetId, limit, excludeSameArtist);
  };

  const handleSortChange = (s: SortMetric) => {
    setSortBy(s);
    if (selectedTrack) fetchRecs(selectedTrack, s, rulesetId, limit, excludeSameArtist);
  };

  const handleRulesetChange = (id: number) => {
    setRulesetId(id);
    if (selectedTrack) fetchRecs(selectedTrack, sortBy, id, limit, excludeSameArtist);
  };

  const handleExcludeToggle = () => {
    const next = !excludeSameArtist;
    setExcludeSameArtist(next);
    if (selectedTrack) fetchRecs(selectedTrack, sortBy, rulesetId, limit, next);
  };

  const handleChain = (item: string) => {
    const parts = item.split(' - ');
    const artistname = parts[0];
    const trackname = parts.slice(1).join(' - ');
    const t: Track = { item, artistname, trackname };
    setSelectedTrack(t);
    fetchRecs(t, sortBy, rulesetId, limit, excludeSameArtist);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="view">
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="section-title">
          <span className="gradient-text">Discover</span> Music
        </h1>
        <p className="section-subtitle">
          Search any song to find what tracks are most commonly played alongside it — powered by 126K association rules mined from 161K Spotify playlists.
        </p>
        <SearchBar onSelect={handleSelect} rulesetId={rulesetId} />
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {!selectedTrack && !loading && (
        <div className="empty-state">
          <div className="empty-state-icon">🎵</div>
          <div className="empty-state-title">Search for a song to get started</div>
          <div className="empty-state-sub">Try "Daft Punk", "Radiohead", or "Coldplay"</div>
        </div>
      )}

      {selectedTrack && (
        <>
          <TrackCard track={selectedTrack} ruleCount={result?.count ?? 0} totalCount={result?.total_count} sameArtistCount={result?.same_artist_count} excludingSameArtist={excludeSameArtist} />

          <div className="controls-row">
            <RulesetToggle rulesetId={rulesetId} onChange={handleRulesetChange} />
            <SortControls value={sortBy} onChange={handleSortChange} />

            {/* Same-artist toggle */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span className="controls-label">Filter</span>
              <button
                onClick={handleExcludeToggle}
                className={`pill${excludeSameArtist ? ' active' : ''}`}
                style={{
                  background: excludeSameArtist ? undefined : 'var(--surface-3)',
                  border: excludeSameArtist ? undefined : '1px solid var(--border)',
                  color: excludeSameArtist ? undefined : 'var(--text-muted)',
                  padding: '5px 14px',
                  borderRadius: '7px',
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 200ms',
                }}
              >
                {excludeSameArtist ? '🚫 Same artist hidden' : '👁 Show all artists'}
              </button>
            </div>

            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span className="controls-label">Show</span>
              <div className="pill-group">
                {[10, 25, 50].map(n => (
                  <button key={n} className={`pill${limit === n ? ' active' : ''}`} onClick={() => {
                    setLimit(n);
                    if (selectedTrack) fetchRecs(selectedTrack, sortBy, rulesetId, n, excludeSameArtist);
                  }}>{n}</button>
                ))}
              </div>
            </div>
          </div>

          {loading ? (
            <Skeleton count={6} />
          ) : result && result.recommendations.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">🔇</div>
              <div className="empty-state-title">No recommendations found</div>
              <div className="empty-state-sub">
                {result.message ?? 'This track has no rules in the selected ruleset.'}
              </div>
            </div>
          ) : result ? (
            <div className="recs-grid fade-in">
              {result.recommendations.map((rec, i) => (
                <RecommendCard
                  key={rec.item}
                  rec={rec}
                  rank={i + 1}
                  sortBy={sortBy}
                  onClick={handleChain}
                />
              ))}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
