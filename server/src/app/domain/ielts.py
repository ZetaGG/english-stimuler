from collections.abc import Sequence
from dataclasses import dataclass

BAND_POINTS: dict[str, tuple[tuple[float, float], ...]] = {
    "fluency": ((0.0, 1.0), (50.0, 4.0), (90.0, 5.0), (110.0, 6.0), (140.0, 7.0), (180.0, 8.0), (240.0, 9.0)),
    "lexical": ((0.0, 1.0), (0.25, 4.0), (0.40, 5.0), (0.50, 6.0), (0.60, 7.0), (0.70, 8.0), (0.80, 9.0)),
    "pronunciation": ((0.0, 1.0), (40.0, 4.0), (55.0, 5.0), (65.0, 6.0), (75.0, 7.0), (85.0, 8.0), (95.0, 9.0)),
    "grammar": ((0.0, 9.0), (0.02, 8.0), (0.05, 7.0), (0.10, 6.0), (0.20, 5.0), (0.35, 4.0), (1.0, 1.0)),
}


def _to_band(value: float, points: Sequence[tuple[float, float]]) -> float:
    if value <= points[0][0]:
        return points[0][1]
    if value >= points[-1][0]:
        return points[-1][1]
    for (x0, band0), (x1, band1) in zip(points, points[1:]):
        if x0 <= value <= x1:
            interpolated = band0 + (value - x0) / (x1 - x0) * (band1 - band0)
            return round(interpolated * 2) / 2
    raise AssertionError("unreachable")  # pragma: no cover


def fluency_band(wpm: float) -> float:
    return _to_band(wpm, BAND_POINTS["fluency"])


def lexical_band(diversity: float) -> float:
    return _to_band(diversity, BAND_POINTS["lexical"])


def pronunciation_band(score: float) -> float:
    return _to_band(score, BAND_POINTS["pronunciation"])


def grammar_band(error_ratio: float) -> float:
    return _to_band(error_ratio, BAND_POINTS["grammar"])


def overall_band(fluency: float, lexical: float, pronunciation: float, grammar: float) -> float:
    average = (fluency + lexical + pronunciation + grammar) / 4.0
    return round(average * 2) / 2


@dataclass(frozen=True)
class ComponentBands:
    fluency: float
    lexical: float
    pronunciation: float
    grammar: float
    overall: float


def evaluate_bands(
    wpm: float,
    diversity: float,
    pronunciation_score: float,
    error_ratio: float,
) -> ComponentBands:
    fluency = fluency_band(wpm)
    lexical = lexical_band(diversity)
    pronunciation = pronunciation_band(pronunciation_score)
    grammar = grammar_band(error_ratio)
    return ComponentBands(
        fluency=fluency,
        lexical=lexical,
        pronunciation=pronunciation,
        grammar=grammar,
        overall=overall_band(fluency, lexical, pronunciation, grammar),
    )
