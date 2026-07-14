import { useState, useRef, useEffect, useCallback } from 'react';
import { searchTracks } from '../api';
import type { Track } from '../api';

interface Props {
  onSelect: (track: Track) => void;
  placeholder?: string;
  initialValue?: string;
  rulesetId?: number;   // Fix 2: scope autocomplete to this ruleset
}

export default function SearchBar({ onSelect, placeholder = 'Search for a song or artist…', initialValue = '', rulesetId = 1 }: Props) {
  const [query, setQuery] = useState(initialValue);
  const [results, setResults] = useState<Track[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [focusedIdx, setFocusedIdx] = useState(-1);
  const abortRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const doSearch = useCallback(async (q: string) => {
    if (q.trim().length < 1) { setResults([]); setOpen(false); return; }
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();
    setLoading(true);
    try {
      const data = await searchTracks(q, 8, rulesetId, abortRef.current.signal);
      setResults(data.results);
      setOpen(true);
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== 'AbortError') setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    setFocusedIdx(-1);
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => doSearch(val), 200);
  };

  const handleSelect = (track: Track) => {
    setQuery(`${track.artistname} - ${track.trackname}`);
    setOpen(false);
    setResults([]);
    onSelect(track);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open || results.length === 0) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setFocusedIdx(i => Math.min(i + 1, results.length - 1)); }
    if (e.key === 'ArrowUp')   { e.preventDefault(); setFocusedIdx(i => Math.max(i - 1, -1)); }
    if (e.key === 'Enter' && focusedIdx >= 0) { handleSelect(results[focusedIdx]); }
    if (e.key === 'Escape') { setOpen(false); }
  };

  // Close on outside click
  const wrapRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="search-wrap" ref={wrapRef}>
      <div className="search-input-wrap">
        <span className="search-icon">{loading ? '⏳' : '🔍'}</span>
        <input
          ref={inputRef}
          className="search-input"
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder={placeholder}
          autoComplete="off"
          spellCheck={false}
        />
        {query && (
          <button className="search-clear" onClick={() => { setQuery(''); setResults([]); setOpen(false); inputRef.current?.focus(); }}>✕</button>
        )}
      </div>

      {open && (
        <div className="search-dropdown">
          {results.length === 0 ? (
            <div className="search-no-results">No results for "{query}"</div>
          ) : (
            results.map((track, i) => (
              <div
                key={track.item}
                className={`search-result-item${focusedIdx === i ? ' focused' : ''}`}
                onClick={() => handleSelect(track)}
                onMouseEnter={() => setFocusedIdx(i)}
              >
                <div className="search-result-icon">🎵</div>
                <div className="search-result-text">
                  <div className="search-result-track">{track.trackname}</div>
                  <div className="search-result-artist">{track.artistname}</div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
