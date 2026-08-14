const BARS = 14;

export function Waveform() {
  return (
    <div className="waveform" aria-hidden="true">
      {Array.from({ length: BARS }, (_, i) => (
        <span key={i} style={{ animationDelay: `${(i % 7) * 0.12}s` }} />
      ))}
    </div>
  );
}
