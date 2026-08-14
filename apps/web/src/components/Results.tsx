import type { EvaluationResult } from "../types";
import { bandColor } from "./BandBadge";
import { ScoreBar } from "./ScoreBar";

interface ResultsProps {
  result: EvaluationResult;
  onReset: () => void;
  onHome: () => void;
}

export function Results({ result, onReset, onHome }: ResultsProps) {
  const { bands, metrics, pronunciation, grammar_issues, report } = result;
  const fillerWords = Object.entries(metrics.filler_words);

  return (
    <div className="section">
      <div className="hero">
        <div>
          <h1>Session complete 🎉</h1>
          <p>
            {metrics.word_count} words in {metrics.duration.toFixed(1)}s at {metrics.wpm.toFixed(0)} wpm. Here's your
            report.
          </p>
          <div className="section-head" style={{ marginTop: 14 }}>
            <button className="btn btn-teal" onClick={onReset}>
              Practice again
            </button>
            <button className="btn-ghost btn" onClick={onHome}>
              Back to home
            </button>
          </div>
        </div>
        <div className="hero-band">
          <div className="band-big">{bands.overall.toFixed(1)}</div>
          <div className="band-label">overall band</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h2>Scores</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <ScoreBar label="Pronunciation" value={pronunciation.overall_score} display={`${pronunciation.overall_score.toFixed(0)} / 100`} color={bandColor(bands.pronunciation)} />
            <ScoreBar label="Fluency" value={bands.fluency} max={9} color={bandColor(bands.fluency)} />
            <ScoreBar label="Grammar" value={bands.grammar} max={9} color={bandColor(bands.grammar)} />
            <ScoreBar label="Vocabulary" value={bands.lexical} max={9} color={bandColor(bands.lexical)} />
          </div>
        </div>

        <div className="card">
          <h2>Fluency details</h2>
          <div className="stats-grid">
            <div className="stat">
              <div className="value">{metrics.wpm.toFixed(0)}</div>
              <div className="label">wpm</div>
            </div>
            <div className="stat">
              <div className="value">{metrics.filler_count}</div>
              <div className="label">fillers</div>
            </div>
            <div className="stat">
              <div className="value">{metrics.lexical_diversity.toFixed(2)}</div>
              <div className="label">diversity</div>
            </div>
            <div className="stat">
              <div className="value">{grammar_issues.length}</div>
              <div className="label">grammar</div>
            </div>
          </div>
          {fillerWords.length > 0 && (
            <div className="chips" style={{ marginTop: 14 }}>
              {fillerWords.map(([word, count]) => (
                <span className="chip" key={word}>
                  "{word}" ×{count}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {report && (
        <div className="card">
          <h2>Coach feedback</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <p style={{ margin: 0, color: "var(--text)" }}>{report.summary}</p>
            {report.strengths.length > 0 && (
              <div className="report-block">
                <strong style={{ color: "var(--green)" }}>Strengths</strong>
                <ul>
                  {report.strengths.map((strength) => (
                    <li key={strength}>{strength}</li>
                  ))}
                </ul>
              </div>
            )}
            {report.tips.length > 0 && (
              <div className="report-block">
                <strong style={{ color: "var(--violet)" }}>Tips</strong>
                <ul>
                  {report.tips.map((tip) => (
                    <li key={tip}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid-2">
        {pronunciation.issues.length > 0 && (
          <div className="card">
            <h2>Pronunciation</h2>
            <div className="issues-list">
              {pronunciation.issues.map((issue, index) => (
                <div className="issue" key={`${issue.word}-${index}`}>
                  <span>
                    <span className="word">{issue.word || "(word)"}</span>{" "}
                    <span className="type">{issue.error_type.replace("_", " ")}</span>
                  </span>
                  {issue.expected_phonemes.length > 0 && (
                    <span className="dim">
                      /{issue.expected_phonemes.join("")}/ → /{issue.actual_phonemes.join("")}/
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {grammar_issues.length > 0 && (
          <div className="card">
            <h2>Grammar</h2>
            <div className="issues-list">
              {grammar_issues.map((issue, index) => (
                <div className="issue" key={index}>
                  <span>{issue.message}</span>
                  {issue.suggestions.length > 0 && (
                    <span className="dim">→ {issue.suggestions.join(", ")}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
