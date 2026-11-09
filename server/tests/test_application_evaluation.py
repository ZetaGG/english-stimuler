import pytest

from app.application.evaluation import EvaluationResult, EvaluationService
from app.domain.feedback import FeedbackContext, FeedbackProvider, FeedbackReport
from app.domain.grammar import GrammarChecker, GrammarIssue
from app.domain.metrics import WordSegment
from app.domain.pronunciation import ErrorType, PronunciationFeedback, PronunciationIssue, PronunciationScorer
from app.domain.speech import SpeechToText


def make_segments(texts: list[str], gap: float = 0.5, dur: float = 0.4) -> list[WordSegment]:
    segments: list[WordSegment] = []
    t = 0.0
    for text in texts:
        segments.append(WordSegment(text=text, start=t, end=t + dur))
        t += dur + gap
    return segments


class FakeScorer(PronunciationScorer):
    def __init__(self, score: float = 80.0) -> None:
        self.score_value = score
        self.last_words: list[WordSegment] = []

    def score(self, audio_path: str, words: list[WordSegment]) -> PronunciationFeedback:
        self.last_words = list(words)
        issue = PronunciationIssue("hello", ErrorType.SUBSTITUTION)
        return PronunciationFeedback(overall_score=self.score_value, issues=[issue])


class FakeGrammarChecker(GrammarChecker):
    def __init__(self, issues: list[GrammarIssue] | None = None) -> None:
        self.issues = issues if issues is not None else []

    def check(self, text: str) -> list[GrammarIssue]:
        self.last_text = text
        return self.issues


class FakeProvider(FeedbackProvider):
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def generate(self, context: FeedbackContext) -> FeedbackReport:
        self.last_context = context
        if self.fail:
            raise RuntimeError("provider down")
        return FeedbackReport(summary="Great", strengths=("fluent",), tips=("add detail",))


def make_service(
    *, scorer: PronunciationScorer | None = None, provider_fails: bool = False
) -> tuple[EvaluationService, FakeGrammarChecker, FakeProvider]:
    grammar = FakeGrammarChecker([GrammarIssue("typo", 0, 4)])
    provider = FakeProvider(fail=provider_fails)
    service = EvaluationService(
        scorer=scorer or FakeScorer(),
        grammar_checker=grammar,
        feedback_provider=provider,
    )
    return service, grammar, provider


def test_evaluate_computes_metrics_and_bands() -> None:
    service, _, _ = make_service()
    result = service.evaluate(make_segments(["um", "the", "cat", "sat"]), "the cat sat", "/tmp/a.wav")
    assert isinstance(result, EvaluationResult)
    assert result.metrics.word_count == 4
    assert result.metrics.filler_words == {"um": 1}
    assert result.bands.overall > 0.0
    assert result.bands.pronunciation == 7.5


def test_evaluate_includes_transcript() -> None:
    service, _, _ = make_service()
    result = service.evaluate(make_segments(["hello", "world"]), "hello world", "/tmp/a.wav")
    assert result.transcript == "hello world"
    assert result.expected_text == "hello world"


def test_evaluate_runs_grammar_check_on_transcript() -> None:
    service, grammar, _ = make_service()
    result = service.evaluate(make_segments(["hello", "world"]), "hello world", "/tmp/a.wav")
    assert grammar.last_text == "hello world"
    assert len(result.grammar_issues) == 1
    assert result.grammar_issues[0].message == "typo"


def test_evaluate_includes_pronunciation_feedback() -> None:
    service, _, _ = make_service()
    result = service.evaluate(make_segments(["hello"]), "hello", "/tmp/a.wav")
    assert result.pronunciation.overall_score == 80.0
    assert len(result.pronunciation.issues) == 1


def test_evaluate_scores_pronunciation_against_transcript_not_prompt() -> None:
    scorer = FakeScorer()
    service, _, _ = make_service(scorer=scorer)
    service.evaluate(make_segments(["okay", "so", "here"]), "the cat sat on the mat", "/tmp/a.wav")
    assert [segment.text for segment in scorer.last_words] == ["okay", "so", "here"]


def test_evaluate_includes_provider_report() -> None:
    service, _, _ = make_service()
    result = service.evaluate(make_segments(["hello"]), "hello", "/tmp/a.wav")
    assert result.report is not None
    assert result.report.summary == "Great"


def test_evaluate_degrades_report_when_provider_fails() -> None:
    service, _, _ = make_service(provider_fails=True)
    result = service.evaluate(make_segments(["hello"]), "hello", "/tmp/a.wav")
    assert result.report is None
    assert result.metrics.word_count == 1
    assert result.bands.overall > 0.0


def test_evaluate_builds_feedback_context_for_provider() -> None:
    service, _, provider = make_service()
    service.evaluate(make_segments(["hello", "world"]), "hello world", "/tmp/a.wav")
    context = provider.last_context
    assert context.transcript == "hello world"
    assert context.expected_text == "hello world"
    assert context.pronunciation_score == 80.0
    assert len(context.grammar_issues) == 1


def test_evaluate_zero_grammar_errors_yields_top_grammar_band() -> None:
    grammar = FakeGrammarChecker([])
    service = EvaluationService(
        scorer=FakeScorer(),
        grammar_checker=grammar,
        feedback_provider=FakeProvider(),
    )
    result = service.evaluate(make_segments(["the", "cat"]), "the cat", "/tmp/a.wav")
    assert result.bands.grammar == 9.0


def test_evaluate_empty_segments_still_returns_result() -> None:
    service, _, _ = make_service()
    result = service.evaluate([], "the cat sat", "/tmp/a.wav")
    assert result.metrics.word_count == 0
    assert result.bands.overall >= 1.0


class FakeTranscriber(SpeechToText):
    def __init__(self, segments: list[WordSegment] | None = None) -> None:
        self.segments = segments if segments is not None else make_segments(["the", "cat", "sat"])
        self.last_path: str | None = None

    def transcribe(self, audio_path: str) -> list[WordSegment]:
        self.last_path = audio_path
        return self.segments


def test_evaluate_audio_transcribes_and_evaluates() -> None:
    transcriber = FakeTranscriber()
    grammar = FakeGrammarChecker([])
    service = EvaluationService(
        scorer=FakeScorer(),
        grammar_checker=grammar,
        feedback_provider=FakeProvider(),
        speech_to_text=transcriber,
    )
    result = service.evaluate_audio("/tmp/rec.wav", "the cat sat")
    assert transcriber.last_path == "/tmp/rec.wav"
    assert result.metrics.word_count == 3
    assert result.bands.overall > 0.0


def test_evaluate_audio_uses_transcribed_words_for_metrics() -> None:
    transcriber = FakeTranscriber(make_segments(["um", "hello", "there"]))
    service = EvaluationService(
        scorer=FakeScorer(),
        grammar_checker=FakeGrammarChecker([]),
        feedback_provider=FakeProvider(),
        speech_to_text=transcriber,
    )
    result = service.evaluate_audio("/tmp/rec.wav", "hello there")
    assert result.metrics.filler_words == {"um": 1}


def test_evaluate_audio_requires_transcriber() -> None:
    service, _, _ = make_service()
    with pytest.raises(ValueError, match="speech_to_text"):
        service.evaluate_audio("/tmp/rec.wav", "hello")


class FakeHistory:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def record(self, result, expected_text, transcript) -> str:
        self.calls.append((result, expected_text, transcript))
        return "rec-1"


class FakeVocabulary:
    def __init__(self) -> None:
        self.results: list = []

    def add_from(self, result) -> int:
        self.results.append(result)
        return 2


def test_evaluate_records_history_when_configured() -> None:
    history = FakeHistory()
    service = EvaluationService(
        scorer=FakeScorer(),
        grammar_checker=FakeGrammarChecker([]),
        feedback_provider=FakeProvider(),
        history=history,
    )
    result = service.evaluate(make_segments(["the", "cat", "sat"]), "the cat sat", "/tmp/a.wav")
    assert result.record_id == "rec-1"
    result_arg, expected, transcript = history.calls[0]
    assert expected == "the cat sat"
    assert transcript == "the cat sat"


def test_evaluate_skips_history_when_not_configured() -> None:
    service, _, _ = make_service()
    result = service.evaluate(make_segments(["the", "cat", "sat"]), "the cat sat", "/tmp/a.wav")
    assert result.record_id is None


def test_evaluate_extracts_vocabulary_when_configured() -> None:
    vocabulary = FakeVocabulary()
    service = EvaluationService(
        scorer=FakeScorer(),
        grammar_checker=FakeGrammarChecker([]),
        feedback_provider=FakeProvider(),
        vocabulary=vocabulary,
    )
    service.evaluate(make_segments(["the", "cat", "sat"]), "the cat sat", "/tmp/a.wav")
    assert vocabulary.results
    assert vocabulary.results[0].metrics.word_count == 3
