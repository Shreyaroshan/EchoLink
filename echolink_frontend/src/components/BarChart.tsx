interface Row {
  label: string;
  value: number;
  displayValue: string;
  color?: string;
}

interface Props {
  rows: Row[];
  title: string;
}

export default function BarChart({ rows, title }: Props) {
  const max = Math.max(...rows.map(r => r.value), 1);
  return (
    <div>
      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '12px' }}>
        {title}
      </div>
      <div className="chart-wrap">
        {rows.map((row) => (
          <div className="chart-row" key={row.label}>
            <div className="chart-label">{row.label}</div>
            <div className="chart-bar-track">
              <div
                className="chart-bar-fill"
                style={{
                  width: `${(row.value / max) * 100}%`,
                  background: row.color || 'var(--accent-grad)',
                }}
              >
                {row.displayValue}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
