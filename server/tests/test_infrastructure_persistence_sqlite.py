from pathlib import Path

import pytest

from app.domain.feedback import FeedbackReport
from app.domain.history import EvaluationRecord
from app.infrastructure.persistence.sqlite import SQLiteStore


def make_record(record_id: str, created_at: str = "2026-01-01T00:00:00+00:00", report: FeedbackReport | None = None) -> EvaluationRecord:
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
    )


def test_save_and_get_roundtrip_with_report(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "test.db")
    record = make_record("abc", report=FeedbackReport(summary="nice", strengths=("clear",), tips=("slow down",)))
    store.save(record)
    loaded = store.get("abc")
    assert loaded == record
    assert loaded.report is not None
    assert loaded.report.strengths == ("clear",)


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
