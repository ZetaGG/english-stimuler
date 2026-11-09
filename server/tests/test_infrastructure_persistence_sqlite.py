from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from app.domain.feedback import FeedbackReport
from app.domain.grammar import GrammarIssue
from app.domain.history import EvaluationRecord
from app.domain.pronunciation import ErrorType, PronunciationIssue, PronunciationWordIssue
from app.infrastructure.persistence.sqlite import SQLiteStore


def make_record(
    record_id: str,
    created_at: str = "2026-01-01T00:00:00+00:00",
    report: FeedbackReport | None = None,
    pronunciation_issues: tuple[PronunciationIssue, ...] = (),
    pronunciation_words: tuple[PronunciationWordIssue, ...] = (),
    grammar_issues: tuple[GrammarIssue, ...] = (),
) -> EvaluationRecord:
    return EvaluationRecord(
        id=record_id,
        created_at=created_at,
        expected_text="hello world",
        transcript="hello world",
        wpm=120.0,
        lexical_diversity=0.8,
        pronunciation_score=80.0,
        grammar_error_count=1,
        filler_count=0,
        fluency_band=6.0,
        lexical_band=7.0,
        pronunciation_band=7.5,
        grammar_band=8.0,
        overall_band=7.0,
        report=report,
        pronunciation_issues=pronunciation_issues,
        pronunciation_words=pronunciation_words,
        grammar_issues=grammar_issues,
    )


def test_save_and_get_roundtrip_with_report(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    record = make_record("abc", report=FeedbackReport(summary="nice", strengths=("clear",), tips=("slow down",)))
    store.save(record)
    loaded = store.get("abc")
    assert loaded == record
    assert loaded.report is not None
    assert loaded.report.strengths == ("clear",)


def test_save_and_get_roundtrip_with_issues(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    record = make_record(
        "abc",
        pronunciation_issues=(
            PronunciationIssue("beach", ErrorType.SUBSTITUTION, ("IY",), ("IH",), score=0.0),
            PronunciationIssue("beach", ErrorType.DELETION, ("CH",)),
        ),
        pronunciation_words=(
            PronunciationWordIssue(
                word="beach",
                target_phonemes=("B", "IY", "CH"),
                actual_phonemes=("B", "IH", "CH"),
                score=33.3,
                issues=(
                    PronunciationIssue("beach", ErrorType.SUBSTITUTION, ("IY",), ("IH",), score=0.0),
                    PronunciationIssue("beach", ErrorType.DELETION, ("CH",)),
                ),
            ),
        ),
        grammar_issues=(GrammarIssue("Possible typo", 4, 5, suggestions=("a",), rule_id="EN_A", severity="warning"),),
    )
    store.save(record)
    assert store.get("abc") == record


def test_opens_legacy_db_and_adds_missing_columns(tmp_path: Path) -> None:
    import sqlite3

    path = tmp_path / "legacy.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE evaluations (
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
        """
    )
    connection.execute(
        """
        INSERT INTO evaluations (
            id, created_at, expected_text, transcript, wpm, lexical_diversity,
            pronunciation_score, grammar_error_count, filler_count, fluency_band,
            lexical_band, pronunciation_band, grammar_band, overall_band, report
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("old", "2026-01-01T00:00:00+00:00", "hello world", "hello world", 120.0, 0.8, 80.0, 1, 0, 6.0, 7.0, 7.5, 8.0, 7.0, None),
    )
    connection.commit()
    connection.close()

    store = SQLiteStore(path)
    loaded = store.get("old")
    assert loaded is not None
    assert loaded.pronunciation_issues == ()
    assert loaded.pronunciation_words == ()
    assert loaded.grammar_issues == ()
    store.save(make_record("new"))
    assert store.count() == 2


def test_get_returns_none_for_missing(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    assert store.get("missing") is None


def test_save_and_get_without_report(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    store.save(make_record("abc"))
    assert store.get("abc").report is None


def test_list_orders_newest_first_and_paginates(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    for index in range(5):
        store.save(make_record(f"id-{index}", created_at=f"2026-01-0{index + 1}T00:00:00+00:00"))
    records = store.list(limit=2, offset=0)
    assert [record.id for record in records] == ["id-4", "id-3"]
    records = store.list(limit=2, offset=2)
    assert [record.id for record in records] == ["id-2", "id-1"]


def test_count_tracks_saved_records(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    assert store.count() == 0
    store.save(make_record("a"))
    store.save(make_record("b"))
    assert store.count() == 2


def test_delete_removes_record(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    store.save(make_record("a"))
    assert store.delete("a") is True
    assert store.get("a") is None
    assert store.delete("a") is False


def test_data_persists_across_store_instances(tmp_path: Path) -> None:
    path = tmp_path / "persist.db"
    SQLiteStore(path).save(make_record("a"))
    reopened = SQLiteStore(path)
    assert reopened.get("a").transcript == "hello world"
    assert reopened.count() == 1


def test_schema_creation_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "idem.db"
    SQLiteStore(path)
    SQLiteStore(path)


def test_close_marks_store_unusable(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    store.close()
    with pytest.raises(Exception):
        store.count()


def test_vocabulary_add_counts_only_new_words(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    assert store.add(["brown", "the", "brown"], "2026-01-01T00:00:00+00:00") == 2
    assert store.add(["lazy"], "2026-01-02T00:00:00+00:00") == 1


def test_vocabulary_items_ordered_by_added_at_desc(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    store.add(["old"], "2026-01-01T00:00:00+00:00")
    store.add(["new"], "2026-01-02T00:00:00+00:00")
    assert [item.word for item in store.items()] == ["new", "old"]


def test_vocabulary_remove(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    store.add(["brown"], "2026-01-01T00:00:00+00:00")
    assert store.remove("brown") is True
    assert store.remove("brown") is False
    assert store.items() == []


def test_concurrent_access_never_raises_or_loses_data(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    for index in range(20):
        store.save(make_record(f"seed-{index}", created_at=f"2026-01-{index + 1:02d}T00:00:00+00:00"))

    def worker(thread_id: int) -> list[str]:
        seen = []
        for iteration in range(25):
            records = store.list(limit=5, offset=0)
            seen.append(records[0].id if records else None)
            if iteration % 5 == 0:
                store.save(make_record(f"thread-{thread_id}-{iteration}", created_at=f"2026-02-{iteration + 1:02d}T00:00:00+00:00"))
            store.count()
        return seen

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(worker, range(8)))

    assert all(len(seen) == 25 and seen[0] is not None for seen in results)
    assert store.count() == 20 + 8 * 5
