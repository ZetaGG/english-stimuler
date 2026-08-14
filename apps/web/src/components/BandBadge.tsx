export function bandTone(value: number): "good" | "fair" | "bad" {
  if (value >= 7) return "good";
  if (value >= 5) return "fair";
  return "bad";
}

export function bandColor(value: number): string {
  if (value >= 7) return "var(--green)";
  if (value >= 5) return "var(--gold-bright)";
  return "var(--red)";
}

export function BandBadge({ value }: { value: number }) {
  return <span className={`band-badge ${bandTone(value)}`}>Band {value.toFixed(1)}</span>;
}
