interface Props {
  icon: string;
  value: string | number;
  label: string;
}

export default function StatCard({ icon, value, label }: Props) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
