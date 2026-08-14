from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GrammarIssue:
    message: str
    offset: int
    length: int
    suggestions: tuple[str, ...] = ()
    rule_id: str = ""
    severity: str = "error"


class GrammarChecker(ABC):
    @abstractmethod
    def check(self, text: str) -> list[GrammarIssue]:
        raise NotImplementedError  # pragma: no cover
