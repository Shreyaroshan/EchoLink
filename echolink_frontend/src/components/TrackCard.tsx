import type { Track } from '../api';

interface Props {
  track: Track;
  ruleCount: number;          // returned this page
  totalCount?: number;        // Fix 7: total rules in DB for this track+ruleset
  sameArtistCount?: number;
  excludingSameArtist?: boolean;
}

export default function TrackCard({ track, ruleCount, totalCount, sameArtistCount, excludingSameArtist }: Props) {

  return (
    <div className="track-hero fade-in">
      <div className="track-hero-icon">🎵</div>
      <div className="track-hero-info">
        <div className="track-hero-name">{track.trackname}</div>
        <div className="track-hero-artist">{track.artistname}</div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
        <div className="track-hero-badge">
          {ruleCount} shown
          {totalCount !== undefined && totalCount !== ruleCount && (
            <span style={{ opacity: 0.7, fontWeight: 400 }}> of {totalCount}</span>
          )}
        </div>
        {excludingSameArtist && (sameArtistCount ?? 0) > 0 && (
          <div style={{
            fontSize: '0.7rem',
            color: 'var(--text-muted)',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid var(--border)',
            padding: '3px 10px',
            borderRadius: '100px',
          }}>
            +{sameArtistCount} same-artist hidden
          </div>
        )}
      </div>
    </div>
  );
}
