// EchoLink API client
// All calls go through this file — change BASE to switch environments.

const BASE = 'http://localhost:8000';

// ── Types ──────────────────────────────────────────────────────────────

export interface Track {
  item: string;
  artistname: string;
  trackname: string;
}

export interface Recommendation extends Track {
  confidence: number;
  jaccard: number;
  lift: number;
  pair_count: number;
  support: number;
}

export interface SearchResult {
  query: string;
  ruleset_id: number;  // Fix 2: which ruleset the search was scoped to
  count: number;
  results: Track[];
}

export interface RecommendResult {
  track: Track;
  ruleset: { id: number; algorithm: string };
  sort_by: string;
  exclude_same_artist: boolean;
  same_artist_count: number;
  total_count: number;   // Fix 7: total rules in DB for this track+ruleset (before paging)
  count: number;         // rules returned this page
  recommendations: Recommendation[];
  message?: string;
}

export interface BenchmarkEntry {
  id: number;
  algorithm: string;
  min_support: number;
  min_pair_count: number;
  min_confidence: number;
  runtime_seconds: number;
  rule_count: number;
  avg_jaccard: number;
  avg_confidence: number;
  avg_lift: number;
  max_jaccard: number;
  max_pair_count: number;
}

export interface BenchmarkResult {
  benchmark: BenchmarkEntry[];
  summary: {
    fastest_algorithm: string | null;
    most_rules: string | null;
    speedup_factor: number | null;
  };
}

export interface ConnectedTrack extends Track {
  outgoing_rules?: number;
  times_recommended?: number;
}

export interface StatsResult {
  total_tracks: number;
  total_rules: number;
  rulesets: RulesetMeta[];
  top_recommended: ConnectedTrack[];
  top_connected: ConnectedTrack[];
}

export interface RulesetMeta {
  id: number;
  algorithm: string;
  min_support: number;
  min_pair_count: number;
  min_confidence: number;
  min_jaccard: number;
  runtime_seconds: number;
  rule_count: number;
  run_date: string;
  notes: string;
}

export interface Rule {
  antecedent: string;
  consequent: string;
  support: number;
  confidence: number;
  lift: number;
  jaccard: number;
  pair_count: number;
  count_a: number;
  count_b: number;
}

export type SortMetric = 'jaccard' | 'confidence' | 'pair_count' | 'lift';

// ── API functions ──────────────────────────────────────────────────────

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`);
  return res.json();
}

export function healthCheck() {
  return get<{ status: string; rule_count: number }>('/');
}

export function searchTracks(q: string, limit = 10, rulesetId = 1, signal?: AbortSignal) {
  const params = new URLSearchParams({ q, limit: String(limit), ruleset_id: String(rulesetId) });
  return fetch(`${BASE}/search?${params}`, { signal })
    .then(r => { if (!r.ok) throw new Error('Search failed'); return r.json() as Promise<SearchResult>; });
}

export function getRecommendations(
  track: string,
  limit = 10,
  rulesetId = 1,
  sortBy: SortMetric = 'jaccard',
  excludeSameArtist = true,
) {
  const params = new URLSearchParams({
    track,
    limit: String(limit),
    ruleset_id: String(rulesetId),
    sort_by: sortBy,
    exclude_same_artist: String(excludeSameArtist),
  });
  return get<RecommendResult>(`/recommend?${params}`);
}

export function getBenchmark() {
  return get<BenchmarkResult>('/benchmark');
}

export function getStats() {
  return get<StatsResult>('/stats');
}

export function getRulesets() {
  return get<{ rulesets: RulesetMeta[] }>('/rulesets');
}
