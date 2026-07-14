import type { SortMetric } from '../api';

interface Props {
  value: SortMetric;
  onChange: (v: SortMetric) => void;
}

const OPTIONS: { value: SortMetric; label: string }[] = [
  { value: 'jaccard',    label: 'Jaccard' },
  { value: 'confidence', label: 'Confidence' },
  { value: 'pair_count', label: 'Pair Count' },
  { value: 'lift',       label: 'Lift' },
];

export default function SortControls({ value, onChange }: Props) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <span className="controls-label">Sort by</span>
      <div className="pill-group">
        {OPTIONS.map(o => (
          <button
            key={o.value}
            className={`pill${value === o.value ? ' active' : ''}`}
            onClick={() => onChange(o.value)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}
