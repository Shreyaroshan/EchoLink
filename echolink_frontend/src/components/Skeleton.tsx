interface Props {
  count?: number;
}

export default function Skeleton({ count = 5 }: Props) {
  return (
    <div>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton skeleton-card" style={{ opacity: 1 - i * 0.12 }} />
      ))}
    </div>
  );
}
