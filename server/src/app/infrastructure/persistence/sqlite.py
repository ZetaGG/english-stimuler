from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from app.domain.feedback import FeedbackReport
from app.domain.grammar import GrammarIssue
from app.domain.history import EvaluationRecord, EvaluationStore
from app.domain.pronunciation import ErrorType, PronunciationIssue, PronunciationWordIssue
from app.domain.vocabulary import VocabularyItem, VocabularyStore


def _report_to_json(report: FeedbackReport | None) -> str | None:
    if report is None:
        return None
    return json.dumps(
        {
            "summary": report.summary,
            "strengths": list(report.strengths),
            "tips": list(report.tips),
        },
        ensure_ascii=False,
    )


def _report_from_json(raw: str | None) -> FeedbackReport | None:
    if not raw:
        return None
    data = json.loads(raw)
    return FeedbackReport(
        summary=data["summary"],
        strengths=tuple(data.get("strengths", [])),
        tips=tuple(data.get("tips", [])),
    )


def _pronunciation_issues_to_json(issues: Sequence[PronunciationIssue]) -> str | None:
    if not issues:
        return None
    return json.dumps(
        [
            {
                "word": issue.word,
                "error_type": issue.error_type.value,
                "expected_phonemes": list(issue.expected_phonemes),
                "actual_phonemes": list(issue.actual_phonemes),
                "score": issue.score,
            }
            for issue in issues
        ],
        ensure_ascii=False,
    )


def _pronunciation_issues_from_json(raw: str | None) -> tuple[PronunciationIssue, ...]:
    if not raw:
        return ()
    return tuple(
        PronunciationIssue(
            word=item.get("word", ""),
            error_type=ErrorType(item.get("error_type", "mispronounced")),
            expected_phonemes=tuple(item.get("expected_phonemes", [])),
            actual_phonemes=tuple(item.get("actual_phonemes", [])),
            score=item.get("score", 0.0),
        )
        for item in json.loads(raw)
    )


def _grammar_issues_to_json(issues: Sequence[GrammarIssue]) -> str | None:
    if not issues:
        return None
    return json.dumps(
        [
            {
                "message": issue.message,
                "offset": issue.offset,
                "length": issue.length,
                "suggestions": list(issue.suggestions),
                "rule_id": issue.rule_id,
                "severity": issue.severity,
            }
            for issue in issues
        ],
        ensure_ascii=False,
    )


def _grammar_issues_from_json(raw: str | None) -> tuple[GrammarIssue, ...]:
    if not raw:
        return ()
    return tuple(
        GrammarIssue(
            message=item.get("message", ""),
            offset=item.get("offset", 0),
            length=item.get("length", 0),
            suggestions=tuple(item.get("suggestions", [])),
            rule_id=item.get("rule_id", ""),
            severity=item.get("severity", "error"),
        )
        for item in json.loads(raw)
    )


def _pronunciation_words_to_json(words: Sequence[PronunciationWordIssue]) -> str | None:
    if not words:
        return None
    return json.dumps(
        [
            {
                "word": word.word,
                "target_phonemes": list(word.target_phonemes),
                "actual_phonemes": list(word.actual_phonemes),
                "score": word.score,
                "issues": [
                    {
                        "word": issue.word,
                        "error_type": issue.error_type.value,
                        "expected_phonemes": list(issue.expected_phonemes),
                        "actual_phonemes": list(issue.actual_phonemes),
                        "score": issue.score,
                    }
                    for issue in word.issues
                ],
            }
            for word in words
        ],
        ensure_ascii=False,
    )


def _pronunciation_words_from_json(raw: str | None) -> tuple[PronunciationWordIssue, ...]:
    if not raw:
        return ()
    return tuple(
        PronunciationWordIssue(
            word=item.get("word", ""),
            target_phonemes=tuple(item.get("target_phonemes", [])),
            actual_phonemes=tuple(item.get("actual_phonemes", [])),
            score=item.get("score", 0.0),
            issues=tuple(
                PronunciationIssue(
                    word=issue.get("word", ""),
                    error_type=ErrorType(issue.get("error_type", "mispronounced")),
                    expected_phonemes=tuple(issue.get("expected_phonemes", [])),
                    actual_phonemes=tuple(issue.get("actual_phonemes", [])),
                    score=issue.get("score", 0.0),
                )
                for issue in item.get("issues", [])
            ),
        )
        for item in json.loads(raw)
    )


def _to_record(row: sqlite3.Row) -> EvaluationRecord:
    return EvaluationRecord(
        id=row["id"],
        created_at=row["created_at"],
        expected_text=row["expected_text"],
        transcript=row["transcript"],
        wpm=row["wpm"],
        lexical_diversity=row["lexical_diversity"],
        pronunciation_score=row["pronunciation_score"],
        grammar_error_count=row["grammar_error_count"],
        filler_count=row["filler_count"],
        fluency_band=row["fluency_band"],
        lexical_band=row["lexical_band"],
        pronunciation_band=row["pronunciation_band"],
        grammar_band=row["grammar_band"],
        overall_band=row["overall_band"],
        report=_report_from_json(row["report"]),
        pronunciation_issues=_pronunciation_issues_from_json(row["pronunciation_issues"]),
        pronunciation_words=_pronunciation_words_from_json(row["pronunciation_words"]),
        grammar_issues=_grammar_issues_from_json(row["grammar_issues"]),
    )


class SQLiteStore(EvaluationStore, VocabularyStore):
    def __init__(self, db_path: str | Path) -> None:
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(str(db_path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS evaluations (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                expected_text TEXT NOT NULL,
                transcript TEXT NOT NULL,
                wpm REAL NOT NULL,
                lexical_diversity REAL NOT NULL,
                pronunciation_score REAL NOT NULL,
                grammar_error_count INTEGER NOT NULL,
                filler_count INTEGER NOT NULL,
                fluency_band REAL NOT NULL,
                lexical_band REAL NOT NULL,
                pronunciation_band REAL NOT NULL,
                grammar_band REAL NOT NULL,
                overall_band REAL NOT NULL,
                report TEXT,
                pronunciation_issues TEXT,
                pronunciation_words TEXT,
                grammar_issues TEXT
            );

            CREATE TABLE IF NOT EXISTS vocabulary (
                word TEXT PRIMARY KEY,
                added_at TEXT NOT NULL
            );
            """
        )
        with self._lock:
            columns = {row["name"] for row in self._connection.execute("PRAGMA table_info(evaluations)")}
            if "pronunciation_issues" not in columns:
                self._connection.execute("ALTER TABLE evaluations ADD COLUMN pronunciation_issues TEXT")
            if "pronunciation_words" not in columns:
                self._connection.execute("ALTER TABLE evaluations ADD COLUMN pronunciation_words TEXT")
            if "grammar_issues" not in columns:
                self._connection.execute("ALTER TABLE evaluations ADD COLUMN grammar_issues TEXT")
            self._connection.commit()

    def save(self, record: EvaluationRecord) -> None:
        with self._lock:
            self._connection.execute(
            """
            INSERT INTO evaluations (
                id, created_at, expected_text, transcript, wpm, lexical_diversity,
                pronunciation_score, grammar_error_count, filler_count, fluency_band,
                lexical_band, pronunciation_band, grammar_band, overall_band, report,
                pronunciation_issues, pronunciation_words, grammar_issues
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.created_at,
                record.expected_text,
                record.transcript,
                record.wpm,
                record.lexical_diversity,
                record.pronunciation_score,
                record.grammar_error_count,
                record.filler_count,
                record.fluency_band,
                record.lexical_band,
                record.pronunciation_band,
                record.grammar_band,
                record.overall_band,
                _report_to_json(record.report),
                _pronunciation_issues_to_json(record.pronunciation_issues),
                _pronunciation_words_to_json(record.pronunciation_words),
                _grammar_issues_to_json(record.grammar_issues),
            ),
        )
        self._connection.commit()

    def get(self, record_id: str) -> EvaluationRecord | None:
        with self._lock:
            row = self._connection.execute(
            "SELECT * FROM evaluations WHERE id = ?", (record_id,)
        ).fetchone()
        return _to_record(row) if row else None

    def list(self, limit: int = 20, offset: int = 0) -> list[EvaluationRecord]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM evaluations ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [_to_record(row) for row in rows]

    def count(self) -> int:
        with self._lock:
            return int(self._connection.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0])

    def delete(self, record_id: str) -> bool:
        with self._lock:
            cursor = self._connection.execute("DELETE FROM evaluations WHERE id = ?", (record_id,))
            self._connection.commit()
        return cursor.rowcount > 0

    def add(self, words: Sequence[str], added_at: str) -> int:
        added = 0
        with self._lock:
            for word in words:
                cursor = self._connection.execute(
                    "INSERT OR IGNORE INTO vocabulary (word, added_at) VALUES (?, ?)",
                    (word, added_at),
                )
                added += cursor.rowcount
            self._connection.commit()
        return added

    def items(self) -> list[VocabularyItem]:
        with self._lock:
            rows = self._connection.execute("SELECT word, added_at FROM vocabulary ORDER BY added_at DESC, word").fetchall()
        return [VocabularyItem(word=row["word"], added_at=row["added_at"]) for row in rows]

    def remove(self, word: str) -> bool:
        with self._lock:
            cursor = self._connection.execute("DELETE FROM vocabulary WHERE word = ?", (word,))
            self._connection.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        with self._lock:
            self._connection.close()
