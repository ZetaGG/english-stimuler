interface ScoreBarProps {
  label: string;
  value: number;
  max?: number;
  display?: string;
  color?: string;
}

export function ScoreBar({ label, value, max = 100, display, color = "var(--violet)" }: ScoreBarProps) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="score-row">
      <div className="score-head">
        <span className="score-label">{label}</span>
        <span className="muted">{display ?? value.toFixed(1)}</span>
      </div>
      <div className="score-track" role="meter" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
        <div className="score-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}
