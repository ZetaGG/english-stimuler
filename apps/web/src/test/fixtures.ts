import type {
  EvaluationRecord,
  EvaluationResult,
  Stats,
  VocabularyItem,
} from "../types";

export const statsFixture: Stats = {
  total: 3,
  recent_count: 2,
  avg_fluency: 6.0,
  avg_lexical: 5.5,
  avg_pronunciation: 7.0,
  avg_grammar: 6.5,
  avg_overall: 6.0,
};

export const recordFixture: EvaluationRecord = {
  id: "abc123",
  created_at: "2026-08-13T20:00:00Z",
  expected_text: "Describe your favorite place to relax.",
  transcript: "My favorite place is the beach",
  wpm: 120,
  lexical_diversity: 0.6,
  pronunciation_score: 78,
  grammar_error_count: 1,
  filler_count: 2,
  fluency_band: 6.5,
  lexical_band: 6.0,
  pronunciation_band: 7.0,
  grammar_band: 6.0,
  overall_band: 6.5,
  report: {
    summary: "Good fluency overall.",
    strengths: ["Clear structure", "Natural pace"],
    tips: ["Reduce filler words"],
  },
  pronunciation_issues: [
    {
      word: "beach",
      error_type: "substitution",
      expected_phonemes: ["IY"],
      actual_phonemes: ["IH"],
      score: 0,
    },
    {
      word: "beach",
      error_type: "deletion",
      expected_phonemes: ["CH"],
      actual_phonemes: [],
      score: 0,
    },
  ],
  pronunciation_words: [
    {
      word: "the",
      target_phonemes: ["DH", "AH"],
      actual_phonemes: ["DH", "AH"],
      score: 100,
      issues: [],
    },
    {
      word: "beach",
      target_phonemes: ["B", "IY", "CH"],
      actual_phonemes: ["B", "IH", "CH"],
      score: 33.3,
      issues: [
        {
          word: "beach",
          error_type: "substitution",
          expected_phonemes: ["IY"],
          actual_phonemes: ["IH"],
          score: 0,
        },
        {
          word: "beach",
          error_type: "deletion",
          expected_phonemes: ["CH"],
          actual_phonemes: [],
          score: 0,
        },
      ],
    },
  ],
  grammar_issues: [
    {
      message: "Possible missing article",
      offset: 4,
      length: 5,
      suggestions: ["a"],
      rule_id: "ARTICLES",
      severity: "warning",
    },
  ],
};

export const resultFixture: EvaluationResult = {
  id: "xyz789",
  transcript: "My favorite place is the beach",
  expected_text: "Describe your favorite place to relax.",
  metrics: {
    word_count: 22,
    duration: 12.4,
    wpm: 106.5,
    filler_words: { um: 2 },
    filler_count: 2,
    awkward_pauses: [2.3],
    lexical_diversity: 0.62,
    pause_threshold: 2,
  },
  pronunciation: {
    overall_score: 78,
    words: [
      {
        word: "the",
        target_phonemes: ["DH", "AH"],
        actual_phonemes: ["DH", "AH"],
        score: 100,
        issues: [],
      },
      {
        word: "beach",
        target_phonemes: ["B", "IY", "CH"],
        actual_phonemes: ["B", "IH", "CH"],
        score: 33.3,
        issues: [
          {
            word: "beach",
            error_type: "substitution",
            expected_phonemes: ["IY"],
            actual_phonemes: ["IH"],
            score: 0,
          },
          {
            word: "beach",
            error_type: "deletion",
            expected_phonemes: ["CH"],
            actual_phonemes: [],
            score: 0,
          },
        ],
      },
    ],
    issues: [
      {
        word: "beach",
        error_type: "substitution",
        expected_phonemes: ["IY"],
        actual_phonemes: ["IH"],
        score: 0,
      },
      {
        word: "beach",
        error_type: "deletion",
        expected_phonemes: ["CH"],
        actual_phonemes: [],
        score: 0,
      },
    ],
  },
  grammar_issues: [
    {
      message: "Possible missing article",
      offset: 4,
      length: 5,
      suggestions: ["a"],
      rule_id: "ARTICLES",
      severity: "warning",
    },
  ],
  bands: {
    fluency: 6.5,
    lexical: 6.0,
    pronunciation: 7.0,
    grammar: 6.0,
    overall: 6.5,
  },
  report: {
    summary: "Good fluency overall.",
    strengths: ["Clear structure", "Natural pace"],
    tips: ["Reduce filler words"],
  },
};

export const vocabularyFixture: VocabularyItem[] = [
  { word: "beach", added_at: "2026-08-13T20:00:00Z" },
  { word: "environment", added_at: "2026-08-12T20:00:00Z" },
];
