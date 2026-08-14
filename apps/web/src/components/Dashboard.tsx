import type { EvaluationRecord, Stats, VocabularyItem } from "../types";
import { BandBadge, bandColor } from "./BandBadge";
import { ScoreBar } from "./ScoreBar";

interface DashboardProps {
  stats: Stats | null;
  recent: EvaluationRecord[];
  vocabulary: VocabularyItem[];
  loading: boolean;
  error: string | null;
  onStartPractice: () => void;
  onViewEvaluation: (id: string) => void;
  onRemoveWord: (word: string) => void;
}

export function Dashboard({
  stats,
  recent,
  vocabulary,
  loading,
  error,
  onStartPractice,
  onViewEvaluation,
  onRemoveWord,
}: DashboardProps) {
  if (loading) {
    return (
      <div className="loading">
        <span className="spinner" />
        <p>Connecting to your coach…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-banner">
        {error} Make sure the server is running on port 8001 (`cd server && make dev`).
      </div>
    );
  }

  return (
    <div className="section">
      <div className="hero">
        <div>
          <h1>Welcome back 👋</h1>
          <p>
            {stats && stats.total > 0
              ? `You've completed ${stats.total} practice session${stats.total === 1 ? "" : "s"} — ${
                  stats.recent_count
                } in the last 7 days. Keep the streak alive!`
              : "Speak a few lines every day and your personal coach will track your progress."}
          </p>
          <button className="btn" onClick={onStartPractice}>
            Start practice →
          </button>
        </div>
        {stats && (
          <div className="hero-band">
            <div className="band-big">{stats.total > 0 ? stats.avg_overall.toFixed(1) : "—"}</div>
            <div className="band-label">overall band</div>
          </div>
        )}
      </div>

      {stats && stats.total > 0 && (
        <div className="stats-grid">
          <div className="stat">
            <div className="value">{stats.recent_count}</div>
            <div className="label">this week</div>
          </div>
          <div className="stat">
            <div className="value">{stats.total}</div>
            <div className="label">sessions</div>
          </div>
          <div className="stat">
            <div className="value">{stats.avg_fluency.toFixed(1)}</div>
            <div className="label">fluency</div>
          </div>
          <div className="stat">
            <div className="value">{stats.avg_pronunciation.toFixed(1)}</div>
            <div className="label">pronunciation</div>
          </div>
          <div className="stat">
            <div className="value">{stats.avg_grammar.toFixed(1)}</div>
            <div className="label">grammar</div>
          </div>
          <div className="stat">
            <div className="value">{stats.avg_lexical.toFixed(1)}</div>
            <div className="label">vocabulary</div>
          </div>
        </div>
      )}

      <div className="grid-2">
        <div className="card">
          <h2>Recent sessions</h2>
          {recent.length === 0 ? (
            <div className="empty-state">
              No sessions yet — <button className="btn-ghost btn" onClick={onStartPractice}>record your first one</button>
            </div>
          ) : (
            <div className="list">
              {recent.map((record) => (
                <button
                  key={record.id}
                  className="list-item"
                  style={{ background: "transparent", border: "1px solid var(--border)", textAlign: "left", width: "100%", color: "inherit" }}
                  onClick={() => onViewEvaluation(record.id)}
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

        <div className="card">
          <h2>This week</h2>
          {stats && stats.total > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <ScoreBar label="Fluency" value={stats.avg_fluency} max={9} color={bandColor(stats.avg_fluency)} />
              <ScoreBar label="Pronunciation" value={stats.avg_pronunciation} max={9} color={bandColor(stats.avg_pronunciation)} />
              <ScoreBar label="Grammar" value={stats.avg_grammar} max={9} color={bandColor(stats.avg_grammar)} />
              <ScoreBar label="Vocabulary" value={stats.avg_lexical} max={9} color={bandColor(stats.avg_lexical)} />
            </div>
          ) : (
            <p className="muted">Complete your first session to see your scores.</p>
          )}
        </div>
      </div>

      <div className="card">
        <h2>Your personal dictionary</h2>
        {vocabulary.length === 0 ? (
          <p className="muted">Words you struggle with will be collected here after each session.</p>
        ) : (
          <div className="chips">
            {vocabulary.map((item) => (
              <span className="chip" key={item.word}>
                {item.word}
                <button aria-label={`Remove ${item.word}`} onClick={() => onRemoveWord(item.word)}>
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
