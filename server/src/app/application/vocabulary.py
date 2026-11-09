from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from app.application.history import utc_now
from app.domain.metrics import normalize_word
from app.domain.vocabulary import VocabularyItem, VocabularyStore

if TYPE_CHECKING:  # pragma: no cover
    from app.application.evaluation import EvaluationResult


class VocabularyService:
    def __init__(self, store: VocabularyStore, clock: Any = utc_now) -> None:
        self._store = store
        self._clock = clock

    def add_from(self, result: EvaluationResult) -> int:
        words: set[str] = set()
        for issue in result.pronunciation.issues:
            normalized = normalize_word(issue.word)
            if normalized:
                words.add(normalized)
        words.update(result.metrics.filler_words)
        return self._store.add(sorted(words), self._clock().isoformat())

    def items(self) -> list[VocabularyItem]:
        return self._store.items()

    def remove(self, word: str) -> bool:
        return self._store.remove(word)
