export default function About() {
  const metrics = [
    {
      name: 'Support',
      formula: 'pair_count / total_baskets',
      desc: 'What fraction of ALL playlists contain both songs? A support of 0.003 means the pair appears in 0.3% of all 161K playlists.',
    },
    {
      name: 'Confidence',
      formula: 'pair_count / count_A',
      desc: 'Of all playlists containing Song A, what % also contain Song B? Confidence of 0.48 means: 48% of playlists with Song A also have Song B.',
    },
    {
      name: 'Lift',
      formula: 'confidence / (count_B / total_baskets)',
      desc: 'How much more likely is this pair vs. pure random chance? Lift > 1 means the pair co-occurs more than expected. ⚠️ Misleading for rare songs — a niche track with 26 appearances can have lift > 1000 just because it\'s rare.',
    },
    {
      name: 'Jaccard',
      formula: 'pair_count / (A + B − pair_count)',
      desc: 'Of all playlists containing EITHER song, what % contain BOTH? Ranges 0–1. Not fooled by rarity. This is the primary ranking metric in EchoLink.',
    },
  ];

  const pipeline = [
    { icon: '📄', label: '3.3M rows\nRaw CSV', done: true },
    { icon: '🧹', label: 'Phase 1\nClean', done: true },
    { icon: '📦', label: '161K\nBaskets', done: true },
    { icon: '⚙️', label: 'Phase 2B\nApriori', done: true },
    { icon: '🔗', label: '126K\nRules', done: true },
    { icon: '🗄️', label: 'Phase 3\nPostgreSQL', done: true },
    { icon: '🔌', label: 'Phase 4\nFastAPI', done: true },
    { icon: '🌐', label: 'Phase 5\nReact App', active: true },
  ];

  return (
    <div className="view">
      <div className="about-hero">
        <div className="about-hero-title">
          How <span className="gradient-text">EchoLink</span> Works
        </div>
        <div className="about-hero-subtitle">
          A music recommendation engine built entirely on association rule mining — no machine learning, no user profiles, just patterns from 161,000 real Spotify playlists.
        </div>
      </div>

      {/* The idea */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ fontWeight: 700, fontSize: '1.1rem', marginBottom: '0.75rem' }}>🛒 The Supermarket Analogy</div>
        <p style={{ color: 'var(--text-muted)', lineHeight: 1.7, fontSize: '0.9rem' }}>
          Imagine observing millions of shopping baskets and noticing that chips and salsa are almost always bought together.
          That's association rule mining. EchoLink does the same thing — but instead of grocery items, the "baskets" are playlists
          and the "items" are songs. If "Get Lucky" and "Lose Yourself to Dance" appear together in 617 playlists,
          EchoLink treats that as a strong association.
        </p>
      </div>

      {/* Pipeline */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ fontWeight: 700, fontSize: '1.1rem', marginBottom: '1rem' }}>🏗️ Project Pipeline</div>
        <div className="pipeline">
          {pipeline.map((step, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
              <div className="pipeline-step">
                <div className={`pipeline-bubble ${step.active ? 'active' : 'done'}`}>
                  {step.icon}
                </div>
                <div className="pipeline-label" style={{ whiteSpace: 'pre-line' }}>
                  {step.label}
                </div>
              </div>
              {i < pipeline.length - 1 && <div className="pipeline-arrow">→</div>}
            </div>
          ))}
        </div>
      </div>

      {/* Popularity bias */}
      <div className="card" style={{ marginBottom: '1.5rem', borderColor: 'rgba(124,58,237,0.25)' }}>
        <div style={{ fontWeight: 700, fontSize: '1.1rem', marginBottom: '0.75rem' }}>⚠️ The Popularity Bias Problem</div>
        <p style={{ color: 'var(--text-muted)', lineHeight: 1.7, fontSize: '0.9rem', marginBottom: '0.75rem' }}>
          Early versions used <code style={{ background: 'var(--surface-3)', padding: '2px 6px', borderRadius: 4, fontSize: '0.82rem' }}>MIN_CONFIDENCE = 0.5</code> as
          the filter. This accidentally excluded all popular tracks. "Get Lucky" appears in 1,273 playlists — summer, pop, party, gym, road trip. 
          No single co-song consistently hits 50% even when the co-occurrence count is 617.
        </p>
        <p style={{ color: 'var(--text-muted)', lineHeight: 1.7, fontSize: '0.9rem' }}>
          <strong style={{ color: 'var(--text)' }}>Fix:</strong> Switch to an absolute pair count threshold:
          {' '}<code style={{ background: 'var(--surface-3)', padding: '2px 6px', borderRadius: 4, fontSize: '0.82rem' }}>MIN_PAIR_COUNT = 50</code>.
          A pair must appear together in at least 50 playlists — regardless of how popular either song is.
        </p>
      </div>

      {/* Metrics */}
      <div style={{ fontWeight: 700, fontSize: '1.1rem', marginBottom: '1rem' }}>📐 The 4 Quality Metrics</div>
      <div className="metric-cards" style={{ marginBottom: '2rem' }}>
        {metrics.map(m => (
          <div key={m.name} className="metric-card">
            <div className="metric-card-name">{m.name}</div>
            <div className="metric-card-formula">{m.formula}</div>
            <div className="metric-card-desc">{m.desc}</div>
          </div>
        ))}
      </div>

      {/* Fix 4: Known limitations section */}
      <div className="card" style={{ marginBottom: '1.5rem', borderColor: 'rgba(251,191,36,0.2)' }}>
        <div style={{ fontWeight: 700, fontSize: '1.1rem', marginBottom: '0.75rem' }}>🔍 Known Limitations</div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ padding: '10px 14px', background: 'var(--surface-3)', borderRadius: '10px' }}>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>Song identity is a raw text string</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              Songs are matched by their exact <code style={{ background: 'rgba(255,255,255,0.08)', padding: '1px 5px', borderRadius: 3 }}>"Artist - Track"</code> string.
              "Get Lucky" and "Get Lucky (Radio Edit)" are treated as entirely separate songs with separate rule sets.
              Song variants in the original dataset split co-occurrence signals, sometimes creating duplicate-looking results.
              Fixing this would require re-running the full pipeline with normalization applied at Phase 1.
            </div>
          </div>

          <div style={{ padding: '10px 14px', background: 'var(--surface-3)', borderRadius: '10px' }}>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>Static snapshot</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              Rules were mined from a fixed dataset collected up to a certain date.
              Songs released after that snapshot won't appear. Trends change — a song popular in the dataset year may not reflect current listening habits.
            </div>
          </div>

          <div style={{ padding: '10px 14px', background: 'var(--surface-3)', borderRadius: '10px' }}>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px' }}>FP-Growth covers only 118 songs</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              The FP-Growth ruleset only covers the 118 most popular songs (min 809 playlist appearances) due to memory constraints.
              Switching to FP-Growth for any other song will show an empty result — this is expected.
            </div>
          </div>
        </div>
      </div>

      {/* Links */}
      <div className="card" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <div style={{ fontWeight: 600, fontSize: '0.9rem', alignSelf: 'center' }}>🔗 Explore further:</div>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            padding: '8px 18px',
            background: 'rgba(124,58,237,0.15)',
            border: '1px solid rgba(124,58,237,0.3)',
            borderRadius: '8px',
            fontSize: '0.85rem',
            color: '#a78bfa',
            fontWeight: 600,
            transition: 'all 200ms',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = 'rgba(124,58,237,0.25)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'rgba(124,58,237,0.15)')}
        >
          📖 API Swagger Docs →
        </a>
      </div>
    </div>
  );
}
