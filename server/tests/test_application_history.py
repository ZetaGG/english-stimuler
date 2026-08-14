from datetime import datetime, timezone

import pytest

from app.application.evaluation import EvaluationResult
from app.application.history import HistoryService, ProgressStats
from app.domain.feedback import FeedbackReport
from app.domain.grammar import GrammarIssue
from app.domain.history import EvaluationRecord, EvaluationStore
from app.domain.ielts import ComponentBands
from app.domain.metrics import FluencyMetrics
from app.domain.pronunciation import PronunciationFeedback, PronunciationIssue, ErrorType


def make_result() -> EvaluationResult:
    return EvaluationResult(
        metrics=FluencyMetrics(
            word_count=3,
            duration=2.0,
            wpm=90.0,
            filler_words={"um": 1},
            filler_count=1,
            awkward_pauses=[],
            lexical_diversity=0.7,
        ),
        pronunciation=PronunciationFeedback(
            overall_score=75.0,
            issues=[PronunciationIssue("hello", ErrorType.SUBSTITUTION)],
        ),
        grammar_issues=(GrammarIssue("typo", 0, 4),),
        bands=ComponentBands(fluency=6.0, lexical=7.0, pronunciation=7.0, grammar=7.5, overall=6.9),
        report=FeedbackReport(summary="ok"),
    )


class FakeStore(EvaluationStore):
    def __init__(self) -> None:
        self.records: list[EvaluationRecord] = []

    def save(self, record: EvaluationRecord) -> None:
        self.records.append(record)

    def get(self, record_id: str) -> EvaluationRecord | None:
        return next((r for r in self.records if r.id == record_id), None)

    def list(self, limit: int = 20, offset: int = 0) -> list[EvaluationRecord]:
        return self.records[offset : offset + limit]

    def count(self) -> int:
        return len(self.records)

    def delete(self, record_id: str) -> bool:
        before = len(self.records)
        self.records = [r for r in self.records if r.id != record_id]
        return len(self.records) < before


CLOCK = lambda: datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)


def test_utc_now_default_clock_returns_aware_datetime() -> None:
    from app.application.history import utc_now

    now = utc_now()
    assert now.tzinfo is not None
    assert now.isoformat().endswith("+00:00")


def test_record_saves_evaluation_and_returns_id() -> None:
    store = FakeStore()
    service = HistoryService(store, clock=CLOCK)
    record_id = service.record(make_result(), "hello", "hello um")
    assert store.count() == 1
    saved = store.get(record_id)
    assert saved is not None
    assert saved.created_at == "2026-01-10T12:00:00+00:00"
    assert saved.wpm == 90.0
    assert saved.pronunciation_score == 75.0
    assert saved.grammar_error_count == 1
    assert saved.filler_count == 1
    assert saved.overall_band == 6.9
    assert saved.report is not None


def test_record_generates_unique_ids() -> None:
    store = FakeStore()
    service = HistoryService(store, clock=CLOCK)
    first = service.record(make_result(), "a", "a")
    second = service.record(make_result(), "b", "b")
    assert first != second


def test_recent_get_count_delete_delegate_to_store() -> None:
    store = FakeStore()
    service = HistoryService(store, clock=CLOCK)
    record_id = service.record(make_result(), "a", "a")
    assert [r.id for r in service.recent()] == [record_id]
    assert service.get(record_id) is not None
    assert service.get("nope") is None
    assert service.count() == 1
    assert service.delete(record_id) is True
    assert service.count() == 0


def test_stats_empty_returns_zeros() -> None:
    service = HistoryService(FakeStore(), clock=CLOCK)
    assert service.stats() == ProgressStats(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)


def test_stats_averages_bands_and_counts_recent() -> None:
    store = FakeStore()
    service = HistoryService(store, clock=CLOCK)
    recent = make_result()
    store.save(
        EvaluationRecord(
            id="r1",
            created_at="2026-01-05T00:00:00+00:00",
            expected_text="a",
            transcript="a",
            wpm=90.0,
            lexical_diversity=0.7,
            pronunciation_score=75.0,
            grammar_error_count=1,
            filler_count=1,
            fluency_band=6.0,
            lexical_band=7.0,
            pronunciation_band=7.0,
            grammar_band=7.5,
            overall_band=6.9,
        )
    )
    store.save(
        EvaluationRecord(
            id="r2",
            created_at="2026-01-01T00:00:00+00:00",
            expected_text="b",
            transcript="b",
            wpm=100.0,
            lexical_diversity=0.9,
            pronunciation_score=90.0,
            grammar_error_count=0,
            filler_count=0,
            fluency_band=8.0,
            lexical_band=8.0,
            pronunciation_band=8.5,
            grammar_band=9.0,
            overall_band=8.4,
        )
    )
    stats = service.stats()
    assert stats.total == 2
    assert stats.recent_count == 1
    assert stats.avg_fluency == 7.0
    assert stats.avg_lexical == 7.5
    assert stats.avg_pronunciation == 7.8
    assert stats.avg_grammar == 8.2
    assert stats.avg_overall == 7.7
