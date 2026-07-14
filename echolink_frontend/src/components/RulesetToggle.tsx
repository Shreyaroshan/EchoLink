interface Props {
  rulesetId: number;
  onChange: (id: number) => void;
}

export default function RulesetToggle({ rulesetId, onChange }: Props) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <span className="controls-label">Ruleset</span>
      <div className="pill-group">
        <button className={`pill${rulesetId === 1 ? ' active' : ''}`} onClick={() => onChange(1)}>Apriori</button>
        <button className={`pill${rulesetId === 2 ? ' active' : ''}`} onClick={() => onChange(2)}>FP-Growth</button>
      </div>
    </div>
  );
}
