from collections.abc import Sequence
from dataclasses import dataclass, replace

from app.application.history import HistoryService
from app.application.vocabulary import VocabularyService
from app.domain.feedback import FeedbackContext, FeedbackProvider, FeedbackReport
from app.domain.grammar import GrammarChecker, GrammarIssue
from app.domain.ielts import ComponentBands, evaluate_bands
from app.domain.metrics import FluencyMetrics, WordSegment, compute_fluency
from app.domain.pronunciation import PronunciationFeedback, PronunciationScorer
from app.domain.speech import SpeechToText


@dataclass(frozen=True)
class EvaluationResult:
    metrics: FluencyMetrics
    pronunciation: PronunciationFeedback
    grammar_issues: tuple[GrammarIssue, ...]
    bands: ComponentBands
    report: FeedbackReport | None
    transcript: str = ""
    expected_text: str = ""
    record_id: str | None = None


class EvaluationService:
    def __init__(
        self,
        scorer: PronunciationScorer,
        grammar_checker: GrammarChecker,
        feedback_provider: FeedbackProvider,
        speech_to_text: SpeechToText | None = None,
        history: HistoryService | None = None,
        vocabulary: VocabularyService | None = None,
    ) -> None:
        self._scorer = scorer
        self._grammar_checker = grammar_checker
        self._feedback_provider = feedback_provider
        self._speech_to_text = speech_to_text
        self._history = history
        self._vocabulary = vocabulary

    def evaluate(
        self,
        segments: Sequence[WordSegment],
        expected_text: str,
        audio_path: str,
    ) -> EvaluationResult:
        fluency = compute_fluency(segments)
        transcript = " ".join(segment.text for segment in segments)
        pronunciation = self._scorer.score(audio_path, segments)
        grammar_issues = tuple(self._grammar_checker.check(transcript))
        error_ratio = len(grammar_issues) / max(fluency.word_count, 1)
        bands = evaluate_bands(
            wpm=fluency.wpm,
            diversity=fluency.lexical_diversity,
            pronunciation_score=pronunciation.overall_score,
            error_ratio=error_ratio,
        )
        context = FeedbackContext(
            transcript=transcript,
            expected_text=expected_text,
            wpm=fluency.wpm,
            filler_count=fluency.filler_count,
            lexical_diversity=fluency.lexical_diversity,
            pronunciation_score=pronunciation.overall_score,
            pronunciation_issues=tuple(pronunciation.issues),
            grammar_issues=grammar_issues,
            fluency_band=bands.fluency,
            lexical_band=bands.lexical,
            pronunciation_band=bands.pronunciation,
            grammar_band=bands.grammar,
            overall_band=bands.overall,
        )
        report: FeedbackReport | None
        try:
            report = self._feedback_provider.generate(context)
        except Exception:
            report = None
        result = EvaluationResult(
            metrics=fluency,
            pronunciation=pronunciation,
            grammar_issues=grammar_issues,
            bands=bands,
            report=report,
            transcript=transcript,
            expected_text=expected_text,
        )
        record_id = self._history.record(result, expected_text, transcript) if self._history else None
        if self._vocabulary is not None:
            self._vocabulary.add_from(result)
        return replace(result, record_id=record_id)

    def evaluate_audio(self, audio_path: str, expected_text: str) -> EvaluationResult:
        if self._speech_to_text is None:
            raise ValueError("speech_to_text is not configured")
        segments = self._speech_to_text.transcribe(audio_path)
        return self.evaluate(segments, expected_text, audio_path)
