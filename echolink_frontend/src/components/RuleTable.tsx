import { useState, useMemo } from 'react';
import type { Recommendation, SortMetric } from '../api';

interface Props {
  recommendations: Recommendation[];
  onChain: (item: string) => void;
}

const SORT_OPTIONS: { value: SortMetric; label: string }[] = [
  { value: 'jaccard',    label: 'Jaccard' },
  { value: 'confidence', label: 'Confidence' },
  { value: 'pair_count', label: 'Pair Count' },
  { value: 'lift',       label: 'Lift' },
];

export default function RuleTable({ recommendations, onChain }: Props) {
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<SortMetric>('jaccard');
  const [minJacc, setMinJacc] = useState(0);

  const filtered = useMemo(() => {
    return recommendations
      .filter(r => {
        const q = search.toLowerCase();
        return (r.trackname.toLowerCase().includes(q) || r.artistname.toLowerCase().includes(q));
      })
      .filter(r => r.jaccard >= minJacc)
      .sort((a, b) => b[sortBy] - a[sortBy]);
  }, [recommendations, search, sortBy, minJacc]);

  return (
    <div>
      <div className="rule-filters">
        <input
          className="rule-filter-input"
          placeholder="Filter by track or artist…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select
          className="rule-filter-select"
          value={sortBy}
          onChange={e => setSortBy(e.target.value as SortMetric)}
        >
          {SORT_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>Sort: {o.label}</option>
          ))}
        </select>
        <select
          className="rule-filter-select"
          value={minJacc}
          onChange={e => setMinJacc(Number(e.target.value))}
        >
          <option value={0}>Min Jaccard: any</option>
          <option value={0.05}>≥ 0.05</option>
          <option value={0.1}>≥ 0.10</option>
          <option value={0.2}>≥ 0.20</option>
          <option value={0.3}>≥ 0.30</option>
        </select>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
          {filtered.length} rule{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="rule-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Consequent (Recommendation)</th>
              <th>Jaccard</th>
              <th>Confidence</th>
              <th>Lift</th>
              <th>Pair Count</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                  No rules match your filter
                </td>
              </tr>
            ) : filtered.map((rec, i) => (
              <tr key={rec.item}>
                <td style={{ color: 'var(--text-muted)', width: '32px' }}>{i + 1}</td>
                <td>
                  <div className="highlight" style={{ fontSize: '0.875rem' }}>{rec.trackname}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{rec.artistname}</div>
                </td>
                <td>
                  <span className="rule-metric-chip">{rec.jaccard.toFixed(3)}</span>
                </td>
                <td>{rec.confidence.toFixed(3)}</td>
                <td>{rec.lift.toFixed(1)}</td>
                <td>{rec.pair_count.toLocaleString()}</td>
                <td>
                  <button className="chain-btn" onClick={() => onChain(rec.item)}>
                    Explore →
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
