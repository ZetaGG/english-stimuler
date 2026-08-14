from datetime import datetime, timezone
from collections.abc import Sequence

from app.application.evaluation import EvaluationResult
from app.application.history import utc_now
from app.application.vocabulary import VocabularyService
from app.domain.grammar import GrammarIssue
from app.domain.ielts import ComponentBands
from app.domain.metrics import FluencyMetrics
from app.domain.pronunciation import PronunciationFeedback, PronunciationIssue, ErrorType
from app.domain.vocabulary import VocabularyItem, VocabularyStore


class FakeStore(VocabularyStore):
    def __init__(self) -> None:
        self.words: dict[str, str] = {}

    def add(self, words: Sequence[str], added_at: str) -> int:
        new = [w for w in words if w not in self.words]
        for word in new:
            self.words[word] = added_at
        return len(new)

    def items(self) -> list[VocabularyItem]:
        return [VocabularyItem(word=w, added_at=t) for w, t in sorted(self.words.items(), key=lambda kv: kv[1], reverse=True)]

    def remove(self, word: str) -> bool:
        if word in self.words:
            del self.words[word]
            return True
        return False


CLOCK = lambda: datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)


def make_result() -> EvaluationResult:
    return EvaluationResult(
        metrics=FluencyMetrics(
            word_count=3,
            duration=2.0,
            wpm=90.0,
            filler_words={"um": 2},
            filler_count=2,
            awkward_pauses=[],
            lexical_diversity=0.7,
        ),
        pronunciation=PronunciationFeedback(
            overall_score=75.0,
            issues=[
                PronunciationIssue("brown", ErrorType.SUBSTITUTION),
                PronunciationIssue("  quick  ", ErrorType.DELETION),
                PronunciationIssue("brown", ErrorType.INSERTION),
                PronunciationIssue("The", ErrorType.DELETION),
                PronunciationIssue("dog.", ErrorType.SUBSTITUTION),
            ],
        ),
        grammar_issues=(GrammarIssue("typo", 0, 4),),
        bands=ComponentBands(fluency=6.0, lexical=7.0, pronunciation=7.0, grammar=7.5, overall=6.9),
        report=None,
    )


def test_add_from_extracts_pronunciation_issues_and_fillers() -> None:
    store = FakeStore()
    service = VocabularyService(store, clock=CLOCK)
    added = service.add_from(make_result())
    assert added == 5
    assert set(store.words) == {"brown", "quick", "um", "the", "dog"}
    assert store.words["brown"] == "2026-01-10T12:00:00+00:00"


def test_add_from_normalizes_case_and_punctuation() -> None:
    store = FakeStore()
    service = VocabularyService(store, clock=CLOCK)
    service.add_from(make_result())
    assert "The" not in store.words
    assert "the" in store.words
    assert "dog" in store.words
    assert "dog." not in store.words


def test_add_from_normalizes_and_deduplicates() -> None:
    store = FakeStore()
    service = VocabularyService(store, clock=CLOCK)
    service.add_from(make_result())
    second = service.add_from(make_result())
    assert second == 0
    assert len(store.words) == 5


def test_items_and_remove_delegate_to_store() -> None:
    store = FakeStore()
    service = VocabularyService(store, clock=CLOCK)
    service.add_from(make_result())
    assert [item.word for item in service.items()] == ["brown", "dog", "quick", "the", "um"]
    assert service.remove("um") is True
    assert service.remove("um") is False
