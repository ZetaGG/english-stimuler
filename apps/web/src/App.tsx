import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import { Dashboard } from "./components/Dashboard";
import { History } from "./components/History";
import { Practice } from "./components/Practice";
import { Results } from "./components/Results";
import type { EvaluationRecord, EvaluationResult, Screen, Stats, VocabularyItem } from "./types";

function App() {
  const [screen, setScreen] = useState<Screen>("dashboard");
  const [lastResult, setLastResult] = useState<EvaluationResult | null>(null);

  const [stats, setStats] = useState<Stats | null>(null);
  const [recent, setRecent] = useState<EvaluationRecord[]>([]);
  const [vocabulary, setVocabulary] = useState<VocabularyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [historyItems, setHistoryItems] = useState<EvaluationRecord[]>([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyLoading, setHistoryLoading] = useState(false);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, recentData, vocabData] = await Promise.all([
        api.stats(),
        api.listEvaluations(5, 0),
        api.listVocabulary(),
      ]);
      setStats(statsData);
      setRecent(recentData.items);
      setVocabulary(vocabData.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reach the server.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const page = await api.listEvaluations(100, 0);
      setHistoryItems(page.items);
      setHistoryTotal(page.total);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const handleStartPractice = () => {
    setLastResult(null);
    setScreen("practice");
  };

  const handleResult = (result: EvaluationResult) => {
    setLastResult(result);
    setScreen("practice");
    void loadDashboard();
  };

  const handleDelete = async (id: string) => {
    await api.deleteEvaluation(id);
    void loadHistory();
    void loadDashboard();
  };

  const handleRemoveWord = async (word: string) => {
    await api.removeVocabulary(word);
    void loadDashboard();
  };

  const openHistory = () => {
    setScreen("history");
    void loadHistory();
  };

  const goHome = () => {
    setLastResult(null);
    setScreen("dashboard");
    void loadDashboard();
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-dot" aria-hidden="true" />
          <span>
            English <em>Stimuler</em>
          </span>
        </div>
        <nav className="nav" aria-label="Main">
          <button
            className={`nav-btn ${screen === "dashboard" ? "active" : ""}`}
            onClick={goHome}
            aria-current={screen === "dashboard" ? "page" : undefined}
          >
            Dashboard
          </button>
          <button
            className={`nav-btn ${screen === "practice" ? "active" : ""}`}
            onClick={handleStartPractice}
            aria-current={screen === "practice" ? "page" : undefined}
          >
            Practice
          </button>
          <button
            className={`nav-btn ${screen === "history" ? "active" : ""}`}
            onClick={openHistory}
            aria-current={screen === "history" ? "page" : undefined}
          >
            History
          </button>
        </nav>
      </header>

      <main>
        {screen === "dashboard" && (
          <Dashboard
            stats={stats}
            recent={recent}
            vocabulary={vocabulary}
            loading={loading}
            error={error}
            onStartPractice={handleStartPractice}
            onViewEvaluation={openHistory}
            onRemoveWord={handleRemoveWord}
          />
        )}

        {screen === "practice" &&
          (lastResult ? (
            <Results result={lastResult} onReset={handleStartPractice} onHome={goHome} />
          ) : (
            <Practice onSubmit={handleResult} />
          ))}

        {screen === "history" && (
          <History
            items={historyItems}
            total={historyTotal}
            loading={historyLoading}
            error={error}
            onDelete={handleDelete}
            onBack={goHome}
          />
        )}
      </main>
    </div>
  );
}

export default App;
