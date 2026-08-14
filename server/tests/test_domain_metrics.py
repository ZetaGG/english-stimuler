import pytest

from app.domain.metrics import (
    WordSegment,
    count_filler_words,
    compute_fluency,
    detect_awkward_pauses,
    lexical_diversity,
    words_per_minute,
)


def make_segments(texts: list[str], start: float = 0.0, gap: float = 0.5, dur: float = 0.4) -> list[WordSegment]:
    segments: list[WordSegment] = []
    t = start
    for text in texts:
        segments.append(WordSegment(text=text, start=t, end=t + dur))
        t += dur + gap
    return segments


def test_calculates_wpm_for_one_minute_of_speech() -> None:
    assert words_per_minute(word_count=100, duration_seconds=60.0) == 100.0


def test_scales_wpm_with_duration() -> None:
    assert words_per_minute(word_count=60, duration_seconds=120.0) == 30.0


def test_zero_words_yields_zero() -> None:
    assert words_per_minute(word_count=0, duration_seconds=60.0) == 0.0


def test_rejects_negative_word_count() -> None:
    with pytest.raises(ValueError):
        words_per_minute(word_count=-1, duration_seconds=60.0)


def test_rejects_non_positive_duration() -> None:
    with pytest.raises(ValueError):
        words_per_minute(word_count=10, duration_seconds=0.0)


def test_counts_single_filler_words() -> None:
    assert count_filler_words(["um", "uh", "hello"]) == {"um": 1, "uh": 1}


def test_normalizes_case_and_punctuation_in_fillers() -> None:
    assert count_filler_words(["Um,", "hello", "uh."]) == {"um": 1, "uh": 1}


def test_ignores_words_not_in_filler_set() -> None:
    assert count_filler_words(["well", "like", "so"]) == {}


def test_empty_words_yield_empty_filler_counts() -> None:
    assert count_filler_words([]) == {}


def test_returns_fillers_in_alphabetical_order() -> None:
    assert list(count_filler_words(["uh", "um"]).keys()) == ["uh", "um"]


def test_detects_no_awkward_pauses_when_gaps_are_small() -> None:
    segments = make_segments(["the", "cat", "sat"], gap=0.5)
    assert detect_awkward_pauses(segments, min_gap=2.0) == []


def test_detects_pause_duration_over_threshold() -> None:
    segments = make_segments(["hello", "world"], gap=3.0)
    assert detect_awkward_pauses(segments, min_gap=2.0) == [3.0]


def test_detects_only_pauses_over_threshold() -> None:
    segments = make_segments(["a", "b", "c"], gap=3.0)
    assert detect_awkward_pauses(segments, min_gap=2.0) == [3.0, 3.0]


def test_single_segment_has_no_pauses() -> None:
    assert detect_awkward_pauses(make_segments(["only"]), min_gap=2.0) == []


def test_empty_segments_have_no_pauses() -> None:
    assert detect_awkward_pauses([], min_gap=2.0) == []


def test_lexical_diversity_ratio_of_unique_to_total() -> None:
    assert lexical_diversity(["the", "the", "a"]) == pytest.approx(2 / 3)


def test_lexical_diversity_all_unique_is_one() -> None:
    assert lexical_diversity(["one", "two", "three"]) == 1.0


def test_lexical_diversity_empty_is_zero() -> None:
    assert lexical_diversity([]) == 0.0


def test_compute_fluency_aggregates_all_metrics() -> None:
    segments = make_segments(["um", "the", "cat", "sat", "uh", "down"], gap=0.5)
    metrics = compute_fluency(segments, pause_threshold=2.0)
    assert metrics.word_count == 6
    assert metrics.filler_words == {"uh": 1, "um": 1}
    assert metrics.filler_count == 2
    assert metrics.awkward_pauses == []
    assert metrics.lexical_diversity == pytest.approx(1.0)
    assert metrics.wpm == pytest.approx(words_per_minute(6, metrics.duration), rel=1e-6)


def test_compute_fluency_with_pause_over_threshold() -> None:
    segments = make_segments(["hello", "world"], gap=3.5)
    metrics = compute_fluency(segments, pause_threshold=2.0)
    assert metrics.awkward_pauses == [3.5]


def test_compute_fluency_empty_segments_is_zero() -> None:
    metrics = compute_fluency([])
    assert metrics.word_count == 0
    assert metrics.wpm == 0.0
    assert metrics.filler_count == 0
    assert metrics.awkward_pauses == []
    assert metrics.lexical_diversity == 0.0
