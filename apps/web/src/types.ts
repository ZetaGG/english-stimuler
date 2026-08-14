export interface HealthStatus {
  status: string;
}

export interface Stats {
  total: number;
  recent_count: number;
  avg_fluency: number;
  avg_lexical: number;
  avg_pronunciation: number;
  avg_grammar: number;
  avg_overall: number;
}

export interface Report {
  summary: string;
  strengths: string[];
  tips: string[];
}

export interface EvaluationRecord {
  id: string;
  created_at: string;
  expected_text: string;
  transcript: string;
  wpm: number;
  lexical_diversity: number;
  pronunciation_score: number;
  grammar_error_count: number;
  filler_count: number;
  fluency_band: number;
  lexical_band: number;
  pronunciation_band: number;
  grammar_band: number;
  overall_band: number;
  report: Report | null;
}

export interface EvaluationsPage {
  items: EvaluationRecord[];
  total: number;
}

export interface VocabularyItem {
  word: string;
  added_at: string;
}

export interface Bands {
  fluency: number;
  lexical: number;
  pronunciation: number;
  grammar: number;
  overall: number;
}

export interface PronunciationIssue {
  word: string;
  error_type: string;
  expected_phonemes: string[];
  actual_phonemes: string[];
  score: number;
}

export interface GrammarIssue {
  message: string;
  offset: number;
  length: number;
  suggestions: string[];
  rule_id: string;
  severity: string;
}

export interface EvaluationResult {
  id: string;
  metrics: {
    word_count: number;
    duration: number;
    wpm: number;
    filler_words: Record<string, number>;
    filler_count: number;
    awkward_pauses: number[];
    lexical_diversity: number;
    pause_threshold: number;
  };
  pronunciation: {
    overall_score: number;
    issues: PronunciationIssue[];
  };
  grammar_issues: GrammarIssue[];
  bands: Bands;
  report: Report | null;
}

export type Screen = "dashboard" | "practice" | "history";
