import type { GrammarIssue } from "../types";

interface GrammarIssuesProps {
  issues: GrammarIssue[];
}

export function GrammarIssues({ issues }: GrammarIssuesProps) {
  return (
    <div className="card">
      <h2>Grammar</h2>
      {issues.length === 0 ? (
        <p className="muted" style={{ margin: 0 }}>
          No grammar issues detected.
        </p>
      ) : (
        <div className="issues-list">
          {issues.map((issue, index) => (
            <div className="issue" key={index}>
              <span>{issue.message}</span>
              {issue.suggestions.length > 0 && (
                <span className="dim">→ {issue.suggestions.join(", ")}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
