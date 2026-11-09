import type { PronunciationWordIssue } from "../types";

const PHONEME_HINTS: Record<string, string> = {
  AA: 'a (as in "father")',
  AE: 'a (as in "cat")',
  AH: 'u (as in "but")',
  AO: 'o (as in "law")',
  AW: 'ow (as in "cow")',
  AY: 'i (as in "hide")',
  EH: 'e (as in "bed")',
  ER: 'er (as in "her")',
  EY: 'ay (as in "say")',
  IH: 'i (as in "sit")',
  IY: 'ee (as in "see")',
  OW: 'o (as in "go")',
  OY: 'oy (as in "toy")',
  UH: 'oo (as in "book")',
  UW: 'oo (as in "two")',
  B: 'b (as in "be")',
  CH: 'ch (as in "cheese")',
  D: 'd (as in "do")',
  DH: 'th (as in "they")',
  F: 'f (as in "fee")',
  G: 'g (as in "go")',
  HH: 'h (as in "he")',
  JH: 'j (as in "jump")',
  K: 'k (as in "key")',
  L: 'l (as in "lee")',
  M: 'm (as in "me")',
  N: 'n (as in "no")',
  NG: 'ng (as in "sing")',
  P: 'p (as in "pee")',
  R: 'r (as in "red")',
  S: 's (as in "sea")',
  SH: 'sh (as in "she")',
  T: 't (as in "tea")',
  TH: 'th (as in "thin")',
  V: 'v (as in "vee")',
  W: 'w (as in "we")',
  Y: 'y (as in "yes")',
  Z: 'z (as in "zoo")',
  ZH: 'zh (as in "vision")',
};

function hint(phone: string): string {
  const clean = phone.replace(/[0-9]/g, "").toUpperCase();
  return PHONEME_HINTS[clean] ?? `"${clean}"`;
}

function describeSubstitution(expected: string, actual: string): string {
  return `say ${hint(expected)} instead of ${hint(actual)}`;
}

function describeDeletion(expected: string): string {
  return `add the missing sound ${hint(expected)}`;
}

function describeInsertion(actual: string): string {
  return `remove the extra sound ${hint(actual)}`;
}

const ERROR_TYPE_LABELS: Record<string, string> = {
  substitution: "said a different sound",
  deletion: "missed a sound",
  insertion: "added an extra sound",
  mispronounced: "mispronounced the word",
};

function kindLabel(errorType: string): string {
  return ERROR_TYPE_LABELS[errorType] ?? errorType.replace("_", " ");
}

function WordRow({ word }: { word: PronunciationWordIssue }) {
  const examples = word.issues.map((issue) => {
    if (issue.expected_phonemes.length > 0 && issue.actual_phonemes.length > 0) {
      return describeSubstitution(issue.expected_phonemes[0], issue.actual_phonemes[0]);
    }
    if (issue.expected_phonemes.length > 0) {
      return describeDeletion(issue.expected_phonemes[0]);
    }
    return describeInsertion(issue.actual_phonemes[0]);
  });
  const kinds = [...new Set(word.issues.map((issue) => kindLabel(issue.error_type)))];
  const wrongTargets = new Set(word.issues.map((issue) => issue.expected_phonemes[0]).filter(Boolean));

  return (
    <div className="issue">
      <span>
        <span className="word">{word.word}</span>{" "}
        <span className="type">
          {word.issues.length} {word.issues.length === 1 ? "sound off" : "sounds off"}
        </span>
      </span>
      {kinds.length > 0 && <span className="dim">{kinds.join(" · ")}</span>}
      <span className="dim">
        Say it as:{" "}
        {word.target_phonemes.map((phone, index) => (
          <span key={index}>
            {index > 0 && " · "}
            <span style={wrongTargets.has(phone) ? { color: "var(--violet)", fontWeight: 600 } : undefined}>
              {hint(phone)}
            </span>
          </span>
        ))}
      </span>
      {examples.length > 0 && <span className="dim">{examples.slice(0, 3).join(" · ")}</span>}
    </div>
  );
}

interface PronunciationIssuesProps {
  words: PronunciationWordIssue[];
}

export function PronunciationIssues({ words }: PronunciationIssuesProps) {
  const wrong = words.filter((word) => word.issues.length > 0);
  const correct = words.length - wrong.length;

  return (
    <div className="card">
      <h2>Pronunciation</h2>
      <p className="muted" style={{ marginTop: 0 }}>
        These are words from what you said. Each line shows the sound that didn't match and how to fix it. Sounds are
        described with a similar word, e.g. ee (as in "see").
      </p>
      {words.length > 0 && (
        <p className="muted" style={{ margin: 0 }}>
          You pronounced {correct} of {words.length} words correctly.
        </p>
      )}
      {wrong.length === 0 ? (
        <p className="muted" style={{ marginBottom: 0 }}>
          Your pronunciation was clear. Nothing to fix.
        </p>
      ) : (
        <>
          <div className="issues-list">
            {wrong.map((word) => (
              <WordRow key={word.word} word={word} />
            ))}
          </div>
          <p className="muted" style={{ marginBottom: 0 }}>
            Tip: listen to these words and repeat them slowly.
          </p>
        </>
      )}
    </div>
  );
}
