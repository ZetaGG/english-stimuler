import pytest

from app.domain.feedback import FeedbackContext, FeedbackProvider, FeedbackReport
from app.domain.grammar import GrammarIssue
from app.domain.pronunciation import ErrorType, PronunciationIssue


class FakeProvider(FeedbackProvider):
    def generate(self, context: FeedbackContext) -> FeedbackReport:
        return FeedbackReport(summary="Keep going", strengths=("clear",), tips=("slow down",))


def make_context(**overrides: object) -> FeedbackContext:
    defaults: dict[str, object] = {
        "transcript": "hello world",
        "expected_text": "hello world",
        "wpm": 120.0,
        "filler_count": 2,
        "lexical_diversity": 0.6,
        "pronunciation_score": 80.0,
        "pronunciation_issues": (PronunciationIssue("hello", ErrorType.SUBSTITUTION),),
        "grammar_issues": (GrammarIssue("typo", 0, 4),),
        "fluency_band": 6.0,
        "lexical_band": 7.0,
        "pronunciation_band": 8.0,
        "grammar_band": 8.0,
        "overall_band": 7.0,
    }
    defaults.update(overrides)
    return FeedbackContext(**defaults)  # type: ignore[arg-type]


def test_report_exposes_fields() -> None:
    report = FeedbackReport(summary="summary", strengths=("a", "b"), tips=("c",))
    assert report.summary == "summary"
    assert report.strengths == ("a", "b")
    assert report.tips == ("c",)


def test_report_defaults_to_empty_tuples() -> None:
    report = FeedbackReport(summary="summary")
    assert report.strengths == ()
    assert report.tips == ()


def test_context_carries_metrics_and_bands() -> None:
    context = make_context()
    assert context.wpm == 120.0
    assert context.filler_count == 2
    assert context.lexical_diversity == 0.6
    assert context.pronunciation_score == 80.0
    assert context.fluency_band == 6.0
    assert context.overall_band == 7.0
    assert len(context.pronunciation_issues) == 1
    assert len(context.grammar_issues) == 1


def test_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        FeedbackProvider()  # type: ignore[abstract]


def test_concrete_provider_implements_contract() -> None:
    report = FakeProvider().generate(make_context())
    assert report.summary == "Keep going"
    assert report.tips == ("slow down",)
