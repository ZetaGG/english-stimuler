import pytest

from app.domain.metrics import words_per_minute


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
