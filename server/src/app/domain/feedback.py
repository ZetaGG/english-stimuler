from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.domain.grammar import GrammarIssue
from app.domain.pronunciation import PronunciationIssue


@dataclass(frozen=True)
class FeedbackReport:
    summary: str
    strengths: tuple[str, ...] = ()
    tips: tuple[str, ...] = ()


@dataclass(frozen=True)
class FeedbackContext:
    transcript: str
    expected_text: str
    wpm: float
    filler_count: int
    lexical_diversity: float
    pronunciation_score: float
    pronunciation_issues: tuple[PronunciationIssue, ...]
    grammar_issues: tuple[GrammarIssue, ...]
    fluency_band: float
    lexical_band: float
    pronunciation_band: float
    grammar_band: float
    overall_band: float


class FeedbackProvider(ABC):
    @abstractmethod
    def generate(self, context: FeedbackContext) -> FeedbackReport:
        raise NotImplementedError  # pragma: no cover
