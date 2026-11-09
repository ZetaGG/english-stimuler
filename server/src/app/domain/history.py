from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.feedback import FeedbackReport
from app.domain.grammar import GrammarIssue
from app.domain.pronunciation import PronunciationIssue, PronunciationWordIssue


@dataclass(frozen=True)
class EvaluationRecord:
    id: str
    created_at: str
    expected_text: str
    transcript: str
    wpm: float
    lexical_diversity: float
    pronunciation_score: float
    grammar_error_count: int
    filler_count: int
    fluency_band: float
    lexical_band: float
    pronunciation_band: float
    grammar_band: float
    overall_band: float
    report: FeedbackReport | None = None
    pronunciation_issues: tuple[PronunciationIssue, ...] = ()
    pronunciation_words: tuple[PronunciationWordIssue, ...] = ()
    grammar_issues: tuple[GrammarIssue, ...] = ()


class EvaluationStore(ABC):
    @abstractmethod
    def save(self, record: EvaluationRecord) -> None:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get(self, record_id: str) -> EvaluationRecord | None:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def list(self, limit: int = 20, offset: int = 0) -> list[EvaluationRecord]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def delete(self, record_id: str) -> bool:
        raise NotImplementedError  # pragma: no cover
