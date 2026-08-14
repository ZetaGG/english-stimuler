from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class VocabularyItem:
    word: str
    added_at: str


class VocabularyStore(ABC):
    @abstractmethod
    def add(self, words: Sequence[str], added_at: str) -> int:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def items(self) -> list[VocabularyItem]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def remove(self, word: str) -> bool:
        raise NotImplementedError  # pragma: no cover
