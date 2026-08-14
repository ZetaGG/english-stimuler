import { useState } from "react";
import type { EvaluationRecord } from "../types";
import { BandBadge, bandColor } from "./BandBadge";
import { ScoreBar } from "./ScoreBar";

interface HistoryProps {
  items: EvaluationRecord[];
  total: number;
  loading: boolean;
  error: string | null;
  onDelete: (id: string) => Promise<void>;
  onBack: () => void;
}

function Detail({
  record,
  onDelete,
  onBack,
}: {
  record: EvaluationRecord;
  onDelete: (id: string) => Promise<void>;
  onBack: () => void;
}) {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    await onDelete(record.id);
  };

  return (
    <div className="section">
      <div className="section-head">
        <button className="btn-ghost btn" onClick={onBack}>
          ← History
        </button>
        <button className="btn-danger" onClick={handleDelete} disabled={deleting}>
          {deleting ? "Deleting…" : "Delete session"}
        </button>
      </div>

      <div className="hero">
        <div>
          <h1>{new Date(record.created_at).toLocaleString()}</h1>
          <p>
            Expected: <em style={{ color: "var(--text)" }}>{record.expected_text}</em>
          </p>
          {record.transcript && (
            <p className="muted" style={{ maxWidth: "60ch" }}>
              You said: “{record.transcript}”
            </p>
          )}
        </div>
        <div className="hero-band">
          <div className="band-big">{record.overall_band.toFixed(1)}</div>
          <div className="band-label">overall band</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h2>Scores</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <ScoreBar label="Pronunciation" value={record.pronunciation_score} display={`${record.pronunciation_score.toFixed(0)} / 100`} color={bandColor(record.pronunciation_band)} />
            <ScoreBar label="Fluency" value={record.fluency_band} max={9} color={bandColor(record.fluency_band)} />
            <ScoreBar label="Grammar" value={record.grammar_band} max={9} color={bandColor(record.grammar_band)} />
            <ScoreBar label="Vocabulary" value={record.lexical_band} max={9} color={bandColor(record.lexical_band)} />
          </div>
        </div>

        <div className="card">
          <h2>At a glance</h2>
          <div className="stats-grid">
            <div className="stat">
              <div className="value">{record.wpm.toFixed(0)}</div>
              <div className="label">wpm</div>
            </div>
            <div className="stat">
              <div className="value">{record.grammar_error_count}</div>
              <div className="label">grammar</div>
            </div>
            <div className="stat">
              <div className="value">{record.filler_count}</div>
              <div className="label">fillers</div>
            </div>
            <div className="stat">
              <div className="value">{record.lexical_diversity.toFixed(2)}</div>
              <div className="label">diversity</div>
            </div>
          </div>
        </div>
      </div>

      {record.report && (
        <div className="card">
          <h2>Coach feedback</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <p style={{ margin: 0, color: "var(--text)" }}>{record.report.summary}</p>
            {record.report.strengths.length > 0 && (
              <div className="report-block">
                <strong style={{ color: "var(--green)" }}>Strengths</strong>
                <ul>
                  {record.report.strengths.map((strength) => (
                    <li key={strength}>{strength}</li>
                  ))}
                </ul>
              </div>
            )}
            {record.report.tips.length > 0 && (
              <div className="report-block">
                <strong style={{ color: "var(--violet)" }}>Tips</strong>
                <ul>
                  {record.report.tips.map((tip) => (
                    <li key={tip}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function History({ items, total, loading, error, onDelete, onBack }: HistoryProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="loading">
        <span className="spinner" />
        <p>Loading your history…</p>
      </div>
    );
  }

  if (error) {
    return <div className="error-banner">{error}</div>;
  }

  const selected = items.find((item) => item.id === selectedId) ?? null;
  if (selected) {
    return <Detail record={selected} onDelete={onDelete} onBack={() => setSelectedId(null)} />;
  }

  return (
    <div className="section">
      <div className="section-head">
        <h2>History ({total})</h2>
        <button className="btn-ghost btn" onClick={onBack}>
          ← Home
        </button>
      </div>
      {items.length === 0 ? (
        <div className="empty-state">No sessions recorded yet.</div>
      ) : (
        <div className="list">
          {items.map((record) => (
            <button
              key={record.id}
              className="list-item"
              style={{ background: "transparent", border: "1px solid var(--border)", textAlign: "left", width: "100%", color: "inherit" }}
              onClick={() => setSelectedId(record.id)}
            >
              <div>
                <div className="primary" style={{ color: "var(--text)" }}>
                  {record.expected_text.length > 60 ? `${record.expected_text.slice(0, 60)}…` : record.expected_text}
                </div>
                <div className="secondary">
                  {new Date(record.created_at).toLocaleString()} · {record.wpm.toFixed(0)} wpm ·{" "}
                  {record.grammar_error_count} grammar errors · {record.filler_count} fillers
                </div>
              </div>
              <BandBadge value={record.overall_band} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
