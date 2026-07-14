import type { Recommendation } from '../api';
import type { SortMetric } from '../api';

interface Props {
  rec: Recommendation;
  rank: number;
  onClick: (item: string) => void;
  sortBy: SortMetric;
}

const fmt = (n: number, digits = 3) => n.toFixed(digits);

export default function RecommendCard({ rec, rank, onClick, sortBy }: Props) {
  const primaryLabel =
    sortBy === 'jaccard'    ? `Jacc ${fmt(rec.jaccard)}` :
    sortBy === 'confidence' ? `Conf ${fmt(rec.confidence)}` :
    sortBy === 'lift'       ? `Lift ${fmt(rec.lift, 1)}` :
    `Count ${rec.pair_count.toLocaleString()}`;

  // Jaccard bar always shown as visual
  const barPct = Math.min(rec.jaccard * 100 / 0.6, 100); // cap at 60% jaccard for visual range

  return (
    <div className="rec-card fade-in" onClick={() => onClick(rec.item)}>
      <div className="rec-rank">#{rank}</div>
      <div className="rec-icon">🎵</div>
      <div className="rec-info">
        <div className="rec-track">{rec.trackname}</div>
        <div className="rec-artist">{rec.artistname}</div>
      </div>
      <div className="rec-metrics">
        <div className="rec-jaccard-bar-wrap">
          <div className="rec-jaccard-bar" style={{ width: `${barPct}%` }} />
        </div>
        <div className="rec-metric-row">
          <div className="rec-metric"><strong>{primaryLabel}</strong></div>
          {sortBy !== 'pair_count' && (
            <div className="rec-metric">Count <strong>{rec.pair_count.toLocaleString()}</strong></div>
          )}
          {sortBy !== 'confidence' && (
            <div className="rec-metric">Conf <strong>{fmt(rec.confidence)}</strong></div>
          )}
        </div>
      </div>
      <div className="rec-arrow">›</div>
    </div>
  );
}
