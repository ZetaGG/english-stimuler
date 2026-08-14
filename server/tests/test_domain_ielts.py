import pytest

from app.domain.ielts import (
    ComponentBands,
    evaluate_bands,
    fluency_band,
    grammar_band,
    lexical_band,
    overall_band,
    pronunciation_band,
)


def test_fluency_band_at_threshold() -> None:
    assert fluency_band(110.0) == 6.0


def test_fluency_band_higher_speed_improves_band() -> None:
    assert fluency_band(140.0) == 7.0


def test_fluency_band_interpolates_and_rounds_to_half_step() -> None:
    assert fluency_band(125.0) == 6.5


def test_fluency_band_floor_and_ceiling() -> None:
    assert fluency_band(0.0) == 1.0
    assert fluency_band(10_000.0) == 9.0


def test_lexical_band_high_diversity_scores_well() -> None:
    assert lexical_band(0.7) == 8.0


def test_lexical_band_low_diversity_scores_low() -> None:
    assert lexical_band(0.3) == 4.5


def test_lexical_band_empty_speech_is_floor() -> None:
    assert lexical_band(0.0) == 1.0


def test_pronunciation_band_maps_percentage_to_band() -> None:
    assert pronunciation_band(100.0) == 9.0
    assert pronunciation_band(75.0) == 7.0
    assert pronunciation_band(55.0) == 5.0
    assert pronunciation_band(0.0) == 1.0


def test_grammar_band_few_errors_scores_high() -> None:
    assert grammar_band(0.01) == 8.5


def test_grammar_band_many_errors_scores_low() -> None:
    assert grammar_band(0.3) == 4.5


def test_grammar_band_no_errors_is_top() -> None:
    assert grammar_band(0.0) == 9.0


def test_overall_band_averages_and_rounds_to_half_step() -> None:
    assert overall_band(fluency=7.0, lexical=8.0, pronunciation=7.0, grammar=8.0) == 7.5


def test_overall_band_rounds_half_up() -> None:
    assert overall_band(fluency=6.5, lexical=6.5, pronunciation=6.5, grammar=6.5) == 6.5


def test_overall_band_extreme_components() -> None:
    assert overall_band(fluency=9.0, lexical=9.0, pronunciation=9.0, grammar=9.0) == 9.0
    assert overall_band(fluency=1.0, lexical=1.0, pronunciation=1.0, grammar=1.0) == 1.0


def test_negative_inputs_clamp_to_floor() -> None:
    assert fluency_band(-50.0) == 1.0
    assert lexical_band(-1.0) == 1.0
    assert pronunciation_band(-10.0) == 1.0


def test_grammar_band_ratio_above_one_clamps() -> None:
    assert grammar_band(5.0) == 1.0


def test_components_are_half_step_granularity() -> None:
    for band in (fluency_band(113.0), lexical_band(0.52), pronunciation_band(68.0), grammar_band(0.07)):
        assert (band * 2).is_integer(), f"{band} is not a half-step band"


def test_evaluate_bands_builds_component_bands() -> None:
    bands = evaluate_bands(wpm=140.0, diversity=0.7, pronunciation_score=80.0, error_ratio=0.01)
    assert isinstance(bands, ComponentBands)
    assert bands.fluency == 7.0
    assert bands.lexical == 8.0
    assert bands.pronunciation == 7.5
    assert bands.grammar == 8.5
    assert bands.overall == overall_band(7.0, 8.0, 7.5, 8.5)


def test_evaluate_bands_with_no_grammar_errors() -> None:
    bands = evaluate_bands(wpm=110.0, diversity=0.5, pronunciation_score=65.0, error_ratio=0.0)
    assert bands.grammar == 9.0
