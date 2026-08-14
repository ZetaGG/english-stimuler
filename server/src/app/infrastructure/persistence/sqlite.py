import json
import sqlite3
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from app.domain.feedback import FeedbackReport
from app.domain.history import EvaluationRecord, EvaluationStore
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
                report TEXT
            );

            CREATE TABLE IF NOT EXISTS vocabulary (
                word TEXT PRIMARY KEY,
                added_at TEXT NOT NULL
            );
            """
        )

    def save(self, record: EvaluationRecord) -> None:
        with self._lock:
            self._connection.execute(
            """
            INSERT INTO evaluations (
                id, created_at, expected_text, transcript, wpm, lexical_diversity,
                pronunciation_score, grammar_error_count, filler_count, fluency_band,
                lexical_band, pronunciation_band, grammar_band, overall_band, report
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
