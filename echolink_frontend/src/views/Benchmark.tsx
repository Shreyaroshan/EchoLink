import { useEffect, useState } from 'react';
import { getBenchmark, getStats } from '../api';
import type { BenchmarkResult, StatsResult } from '../api';
import StatCard from '../components/StatCard';
import BarChart from '../components/BarChart';

export default function Benchmark() {
  const [bench, setBench] = useState<BenchmarkResult | null>(null);
  const [stats, setStats] = useState<StatsResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getBenchmark(), getStats()])
      .then(([b, s]) => { setBench(b); setStats(s); })
      .catch(() => setError('Could not load benchmark data. Is the API running at localhost:8000?'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="view">
      <div className="spinner" />
    </div>
  );

  if (error) return (
    <div className="view">
      <div className="error-banner">⚠️ {error}</div>
    </div>
  );

  const apriori = bench?.benchmark.find(b => b.algorithm === 'Apriori');
  const fpgrowth = bench?.benchmark.find(b => b.algorithm === 'FP-Growth');

  return (
    <div className="view">
      <h1 className="section-title"><span className="gradient-text">Benchmark</span> Dashboard</h1>
      <p className="section-subtitle">
        Algorithm comparison: Apriori (custom) vs FP-Growth (mlxtend).
      </p>

      {/* Fix 3: Benchmark scope disclaimer */}
      <div style={{
        background: 'rgba(251,191,36,0.08)',
        border: '1px solid rgba(251,191,36,0.3)',
        borderRadius: '12px',
        padding: '14px 18px',
        marginBottom: '1.5rem',
        fontSize: '0.85rem',
        color: 'var(--text-muted)',
        lineHeight: 1.6,
      }}>
        <strong style={{ color: '#fbbf24' }}>⚠️ Not an apples-to-apples comparison.</strong>
        {' '}Apriori ran on <strong style={{ color: 'var(--text)' }}>46,151 songs</strong> (min 20 playlist appearances).
        FP-Growth required a higher threshold due to dense-matrix memory limits, covering only{' '}
        <strong style={{ color: 'var(--text)' }}>118 songs</strong> (min 809 appearances).
        FP-Growth is 15× faster — but it's solving a much smaller problem.
        A fair speed comparison would need both running on the same song set.
      </div>

      {/* Stat Cards */}
      <div className="stat-grid">
        <StatCard icon="🎵" value={(stats?.total_tracks ?? 0).toLocaleString()} label="Unique tracks" />
        <StatCard icon="🔗" value={(stats?.total_rules ?? 0).toLocaleString()} label="Association rules" />
        <StatCard icon="⚡" value={`${bench?.summary.speedup_factor ?? '—'}×`} label="FP-Growth speedup" />
        <StatCard icon="🏆" value={bench?.summary.most_rules ?? '—'} label="Most rules generated" />
      </div>

      {/* Bar Charts side by side */}
      <div className="two-col" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <BarChart
            title="Runtime (seconds)"
            rows={[
              { label: 'Apriori',   value: apriori?.runtime_seconds ?? 0,  displayValue: `${apriori?.runtime_seconds}s` },
              { label: 'FP-Growth', value: fpgrowth?.runtime_seconds ?? 0, displayValue: `${fpgrowth?.runtime_seconds}s`,
                color: 'linear-gradient(135deg, #06b6d4, #0ea5e9)' },
            ]}
          />
        </div>
        <div className="card">
          <BarChart
            title="Rules generated"
            rows={[
              { label: 'Apriori',   value: apriori?.rule_count ?? 0,  displayValue: (apriori?.rule_count ?? 0).toLocaleString() },
              { label: 'FP-Growth', value: fpgrowth?.rule_count ?? 0, displayValue: (fpgrowth?.rule_count ?? 0).toLocaleString(),
                color: 'linear-gradient(135deg, #06b6d4, #0ea5e9)' },
            ]}
          />
        </div>
      </div>

      {/* Comparison Table */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ fontWeight: 600, marginBottom: '1rem' }}>Full Comparison</div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Algorithm</th>
                <th>Min Support</th>
                <th>Items in Scope</th>
                <th>Rules</th>
                <th>Runtime</th>
                <th>Avg Jaccard</th>
                <th>Avg Confidence</th>
                <th>Max Pair Count</th>
              </tr>
            </thead>
            <tbody>
              {bench?.benchmark.map(b => (
                <tr key={b.id}>
                  <td>
                    <span className={b.algorithm === 'Apriori' ? 'badge badge-apriori' : 'badge badge-fpgrowth'}>
                      {b.algorithm}
                    </span>
                  </td>
                  <td>≥ {b.min_support} baskets</td>
                  <td className="highlight">
                    {b.algorithm === 'Apriori' ? '46,151' : '~118'}
                  </td>
                  <td className="highlight">{b.rule_count.toLocaleString()}</td>
                  <td>{b.runtime_seconds}s</td>
                  <td>{b.avg_jaccard.toFixed(4)}</td>
                  <td>{b.avg_confidence.toFixed(4)}</td>
                  <td>{b.max_pair_count.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top tracks tables */}
      <div className="two-col">
        <div className="card">
          <div style={{ fontWeight: 600, marginBottom: '1rem' }}>
            🔗 Most Connected Tracks
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 400, marginTop: 2 }}>
              Most outgoing rules — best seeds to search
            </div>
          </div>
          <table className="data-table">
            <thead><tr><th>#</th><th>Track</th><th>Rules</th></tr></thead>
            <tbody>
              {stats?.top_connected.map((t, i) => (
                <tr key={t.item}>
                  <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                  <td>
                    <div className="highlight" style={{ fontSize: '0.82rem' }}>{t.trackname}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{t.artistname}</div>
                  </td>
                  <td><span className="rule-metric-chip">{(t.outgoing_rules ?? 0).toLocaleString()}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div style={{ fontWeight: 600, marginBottom: '1rem' }}>
            ⭐ Most Recommended Tracks
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 400, marginTop: 2 }}>
              Appear most often as a recommendation result
            </div>
          </div>
          <table className="data-table">
            <thead><tr><th>#</th><th>Track</th><th>Times</th></tr></thead>
            <tbody>
              {stats?.top_recommended.map((t, i) => (
                <tr key={t.item}>
                  <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                  <td>
                    <div className="highlight" style={{ fontSize: '0.82rem' }}>{t.trackname}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{t.artistname}</div>
                  </td>
                  <td><span className="rule-metric-chip">{(t.times_recommended ?? 0).toLocaleString()}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
