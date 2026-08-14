from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
import re

from app.domain.models import WordSegment

FILLER_WORDS: frozenset[str] = frozenset({"um", "uh", "er", "ah", "eh", "hmm", "uhm", "erm"})

_WORD_CLEAN_RE = re.compile(r"[^a-z']")


def normalize_word(word: str) -> str:
    return _WORD_CLEAN_RE.sub("", word.strip().lower())


def words_per_minute(word_count: int, duration_seconds: float) -> float:
    if word_count < 0:
        raise ValueError("word_count must be non-negative")
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    return round(word_count / (duration_seconds / 60.0), 1)


def count_filler_words(words: Iterable[str], filler_words: frozenset[str] = FILLER_WORDS) -> dict[str, int]:
    counts: dict[str, int] = {}
    for word in words:
        normalized = normalize_word(word)
        if normalized in filler_words:
            counts[normalized] = counts.get(normalized, 0) + 1
    return dict(sorted(counts.items()))


def detect_awkward_pauses(segments: Sequence[WordSegment], min_gap: float = 2.0) -> list[float]:
    pauses: list[float] = []
    for current, following in zip(segments, segments[1:]):
        gap = following.start - current.end
        if gap > min_gap:
            pauses.append(round(gap, 3))
    return pauses


def lexical_diversity(words: Iterable[str]) -> float:
    tokens = [normalize_word(word) for word in words if normalize_word(word)]
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


@dataclass(frozen=True)
class FluencyMetrics:
    word_count: int
    duration: float
    wpm: float
    filler_words: dict[str, int]
    filler_count: int
    awkward_pauses: list[float]
    lexical_diversity: float
    pause_threshold: float = field(default=2.0)


def compute_fluency(
    segments: Sequence[WordSegment],
    filler_words: frozenset[str] = FILLER_WORDS,
    pause_threshold: float = 2.0,
) -> FluencyMetrics:
    if not segments:
        return FluencyMetrics(
            word_count=0,
            duration=0.0,
            wpm=0.0,
            filler_words={},
            filler_count=0,
            awkward_pauses=[],
            lexical_diversity=0.0,
            pause_threshold=pause_threshold,
        )
    duration = segments[-1].end - segments[0].start
    words = [segment.text for segment in segments]
    filler_counts = count_filler_words(words, filler_words)
    return FluencyMetrics(
        word_count=len(segments),
        duration=round(duration, 3),
        wpm=words_per_minute(len(segments), duration),
        filler_words=filler_counts,
        filler_count=sum(filler_counts.values()),
        awkward_pauses=detect_awkward_pauses(segments, pause_threshold),
        lexical_diversity=lexical_diversity(words),
        pause_threshold=pause_threshold,
    )
