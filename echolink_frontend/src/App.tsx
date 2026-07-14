import { useState, useEffect } from 'react';
import { healthCheck } from './api';
import Discover   from './views/Discover';
import Benchmark  from './views/Benchmark';
import Explorer   from './views/Explorer';
import About      from './views/About';

type Tab = 'discover' | 'benchmark' | 'explorer' | 'about';

const TABS: { id: Tab; icon: string; label: string }[] = [
  { id: 'discover',  icon: '🔍', label: 'Discover'  },
  { id: 'benchmark', icon: '📊', label: 'Benchmark' },
  { id: 'explorer',  icon: '🕸️', label: 'Explorer'  },
  { id: 'about',     icon: 'ℹ️',  label: 'About'     },
];

function getInitialTab(): Tab {
  const hash = window.location.hash.slice(1) as Tab;
  return TABS.some(t => t.id === hash) ? hash : 'discover';
}

export default function App() {
  const [tab, setTab] = useState<Tab>(getInitialTab);
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    healthCheck()
      .then(() => setOnline(true))
      .catch(() => setOnline(false));
  }, []);

  const navigate = (t: Tab) => {
    setTab(t);
    window.location.hash = t;
  };

  return (
    <div className="app-shell">
      <nav className="nav">
        <div className="nav-logo">
          <div className="nav-logo-icon">🎵</div>
          <div className="nav-logo-text">
            Echo<span>Link</span>
          </div>
        </div>

        <div className="nav-tabs">
          {TABS.map(t => (
            <button
              key={t.id}
              className={`nav-tab${tab === t.id ? ' active' : ''}`}
              onClick={() => navigate(t.id)}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        <div className="nav-status">
          <div className={`status-dot${online === false ? ' offline' : ''}`} />
          {online === null ? 'Connecting…' : online ? 'API online' : 'API offline'}
        </div>
      </nav>

      {tab === 'discover'  && <Discover  />}
      {tab === 'benchmark' && <Benchmark />}
      {tab === 'explorer'  && <Explorer  />}
      {tab === 'about'     && <About     />}
    </div>
  );
}
