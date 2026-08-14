from dataclasses import dataclass


@dataclass(frozen=True)
class WordSegment:
    text: str
    start: float
    end: float
