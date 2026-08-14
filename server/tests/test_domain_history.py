import pytest

from app.domain.feedback import FeedbackReport
from app.domain.history import EvaluationRecord, EvaluationStore


def test_evaluation_record_is_immutable_data_holder() -> None:
    record = EvaluationRecord(
        id="abc",
        created_at="2026-01-01T00:00:00+00:00",
        expected_text="hello",
        transcript="hello",
        wpm=120.0,
        lexical_diversity=1.0,
        pronunciation_score=80.0,
        grammar_error_count=0,
        filler_count=0,
        fluency_band=6.0,
        lexical_band=7.0,
        pronunciation_band=7.5,
        grammar_band=8.0,
        overall_band=7.0,
        report=FeedbackReport(summary="nice"),
    )
    assert record.report is not None
    assert record.report.summary == "nice"


def test_evaluation_record_defaults_report_to_none() -> None:
    record = EvaluationRecord(
        id="abc",
        created_at="2026-01-01T00:00:00+00:00",
        expected_text="hello",
        transcript="hello",
        wpm=120.0,
        lexical_diversity=1.0,
        pronunciation_score=80.0,
        grammar_error_count=0,
        filler_count=0,
        fluency_band=6.0,
        lexical_band=7.0,
        pronunciation_band=7.5,
        grammar_band=8.0,
        overall_band=7.0,
    )
    assert record.report is None


def test_evaluation_store_is_abstract() -> None:
    with pytest.raises(TypeError):
        EvaluationStore()  # type: ignore[abstract]
