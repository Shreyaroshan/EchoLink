import { useState, useCallback } from 'react';
import { getRecommendations } from '../api';
import type { Track, Recommendation } from '../api';
import SearchBar from '../components/SearchBar';
import NetworkGraph from '../components/NetworkGraph';
import RuleTable from '../components/RuleTable';
import Skeleton from '../components/Skeleton';

type SubView = 'graph' | 'table';

export default function Explorer() {
  const [selectedTrack, setSelectedTrack] = useState<Track | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subView, setSubView] = useState<SubView>('graph');
  const [excludeSameArtist, setExcludeSameArtist] = useState(true);

  const fetchRecs = useCallback(async (track: Track, excludeSame = excludeSameArtist) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRecommendations(track.item, 50, 1, 'jaccard', excludeSame);
      setRecommendations(data.recommendations);
    } catch {
      setError('Could not load rules. Is the API running at localhost:8000?');
    } finally {
      setLoading(false);
    }
  }, [excludeSameArtist]);

  const handleSelect = (track: Track) => {
    setSelectedTrack(track);
    fetchRecs(track);
  };

  const handleNodeClick = (item: string) => {
    const parts = item.split(' - ');
    const artistname = parts[0];
    const trackname = parts.slice(1).join(' - ');
    const t: Track = { item, artistname, trackname };
    setSelectedTrack(t);
    fetchRecs(t);
  };

  return (
    <div className="view">
      <h1 className="section-title">
        <span className="gradient-text">Rule Explorer</span>
      </h1>
      <p className="section-subtitle">
        Visualize song associations as a force-directed network, or browse all rules in a filterable table. 
        Click any node or row to explore its connections.
      </p>

      <div style={{ marginBottom: '1.5rem' }}>
        <SearchBar onSelect={handleSelect} placeholder="Seed a song to visualize its network…" />
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {!selectedTrack && !loading && (
        <div className="empty-state">
          <div className="empty-state-icon">🕸️</div>
          <div className="empty-state-title">Search for a song to seed the network</div>
          <div className="empty-state-sub">Songs with many rules make the most interesting graphs</div>
        </div>
      )}

      {selectedTrack && (
        <>
          {/* Sub-view toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '1.25rem' }}>
            <div style={{
              flex: 1,
              background: 'var(--surface)',
              border: '1px solid rgba(124,58,237,0.25)',
              borderRadius: '12px',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <div style={{ fontSize: '1.25rem' }}>🎵</div>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{selectedTrack.trackname}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{selectedTrack.artistname}</div>
              </div>
              {!loading && (
                <div style={{
                  marginLeft: 'auto',
                  background: 'rgba(124,58,237,0.15)',
                  border: '1px solid rgba(124,58,237,0.3)',
                  color: '#a78bfa',
                  padding: '3px 10px',
                  borderRadius: '100px',
                  fontSize: '0.75rem',
                  fontWeight: 600
                }}>
                  {recommendations.length} rules
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <div className="pill-group">
                <button className={`pill${subView === 'graph' ? ' active' : ''}`} onClick={() => setSubView('graph')}>
                  🕸 Network
                </button>
                <button className={`pill${subView === 'table' ? ' active' : ''}`} onClick={() => setSubView('table')}>
                  📋 Table
                </button>
              </div>
              <button
                onClick={() => {
                  const next = !excludeSameArtist;
                  setExcludeSameArtist(next);
                  if (selectedTrack) fetchRecs(selectedTrack, next);
                }}
                style={{
                  padding: '5px 14px',
                  borderRadius: '7px',
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 200ms',
                  background: excludeSameArtist ? 'var(--accent-grad)' : 'var(--surface-3)',
                  border: excludeSameArtist ? 'none' : '1px solid var(--border)',
                  color: excludeSameArtist ? 'white' : 'var(--text-muted)',
                  boxShadow: excludeSameArtist ? '0 2px 8px rgba(124,58,237,0.35)' : 'none',
                }}
              >
                {excludeSameArtist ? '🚫 Same artist' : '👁 All artists'}
              </button>
            </div>
          </div>

          {loading ? (
            <Skeleton count={4} />
          ) : recommendations.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">🔇</div>
              <div className="empty-state-title">No rules found for this track</div>
              <div className="empty-state-sub">Try searching for a more popular song</div>
            </div>
          ) : subView === 'graph' ? (
            <div className="fade-in">
              <NetworkGraph
                seedTrack={selectedTrack.trackname}
                seedArtist={selectedTrack.artistname}
                seedItem={selectedTrack.item}
                recommendations={recommendations}
                onNodeClick={handleNodeClick}
              />
            </div>
          ) : (
            <div className="fade-in">
              <RuleTable recommendations={recommendations} onChain={handleNodeClick} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
