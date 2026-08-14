from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum


class ErrorType(str, Enum):
    SUBSTITUTION = "substitution"
    INSERTION = "insertion"
    DELETION = "deletion"
    MISPRONOUNCED = "mispronounced"


class AlignmentOp(str, Enum):
    MATCH = "match"
    SUBSTITUTION = "substitution"
    INSERTION = "insertion"
    DELETION = "deletion"


@dataclass(frozen=True)
class PronunciationIssue:
    word: str
    error_type: ErrorType
    expected_phonemes: tuple[str, ...] = ()
    actual_phonemes: tuple[str, ...] = ()
    score: float = 0.0


@dataclass(frozen=True)
class PronunciationFeedback:
    overall_score: float
    issues: list[PronunciationIssue] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.overall_score <= 100.0:
            raise ValueError("overall_score must be between 0 and 100")


class PronunciationScorer(ABC):
    @abstractmethod
    def score(self, audio_path: str, expected_text: str) -> PronunciationFeedback:
        raise NotImplementedError  # pragma: no cover


@dataclass(frozen=True)
class PhoneEdit:
    op: AlignmentOp
    expected: str | None
    actual: str | None


def align_phonemes(expected: Sequence[str], actual: Sequence[str]) -> list[PhoneEdit]:
    match_cost, gap_cost = 0, 1

    def substitution_cost(e: str, a: str) -> int:
        return 0 if e == a else 1

    rows, cols = len(expected) + 1, len(actual) + 1
    score = [[0] * cols for _ in range(rows)]
    for i in range(1, rows):
        score[i][0] = score[i - 1][0] + gap_cost
    for j in range(1, cols):
        score[0][j] = score[0][j - 1] + gap_cost
    for i in range(1, rows):
        for j in range(1, cols):
            score[i][j] = min(
                score[i - 1][j - 1] + substitution_cost(expected[i - 1], actual[j - 1]),
                score[i - 1][j] + gap_cost,
                score[i][j - 1] + gap_cost,
            )

    edits: list[PhoneEdit] = []
    i, j = rows - 1, cols - 1
    while i > 0 or j > 0:
        if i > 0 and j > 0 and score[i][j] == score[i - 1][j - 1] + substitution_cost(expected[i - 1], actual[j - 1]):
            if expected[i - 1] == actual[j - 1]:
                edits.append(PhoneEdit(AlignmentOp.MATCH, expected[i - 1], actual[j - 1]))
            else:
                edits.append(PhoneEdit(AlignmentOp.SUBSTITUTION, expected[i - 1], actual[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and score[i][j] == score[i - 1][j] + gap_cost:
            edits.append(PhoneEdit(AlignmentOp.DELETION, expected[i - 1], None))
            i -= 1
        else:
            edits.append(PhoneEdit(AlignmentOp.INSERTION, None, actual[j - 1]))
            j -= 1
    return list(reversed(edits))


def phone_accuracy(expected_count: int, edits: Sequence[PhoneEdit]) -> float:
    if expected_count == 0:
        return 0.0
    matched = sum(1 for edit in edits if edit.op is AlignmentOp.MATCH)
    return round(100.0 * matched / expected_count, 1)


def build_issues(
    word_phonemes: Sequence[tuple[str, Sequence[str]]],
    edits: Sequence[PhoneEdit],
) -> list[PronunciationIssue]:
    lengths = [len(phonemes) for _, phonemes in word_phonemes]
    boundaries = [0]
    for length in lengths:
        boundaries.append(boundaries[-1] + length)

    def word_at(index: int) -> str | None:
        for word_index, bound in enumerate(boundaries[1:]):
            if index < bound:
                return word_phonemes[word_index][0]
        return None

    issues: list[PronunciationIssue] = []
    expected_index = 0
    for edit in edits:
        if edit.op is AlignmentOp.MATCH:
            expected_index += 1
        elif edit.op is AlignmentOp.SUBSTITUTION:
            issues.append(
                PronunciationIssue(
                    word=word_at(expected_index) or "",
                    error_type=ErrorType.SUBSTITUTION,
                    expected_phonemes=(edit.expected or "",),
                    actual_phonemes=(edit.actual or "",),
                )
            )
            expected_index += 1
        elif edit.op is AlignmentOp.DELETION:
            issues.append(
                PronunciationIssue(
                    word=word_at(expected_index) or "",
                    error_type=ErrorType.DELETION,
                    expected_phonemes=(edit.expected or "",),
                )
            )
            expected_index += 1
        else:
            following = word_at(expected_index)
            if following is not None:
                issues.append(
                    PronunciationIssue(
                        word=following,
                        error_type=ErrorType.INSERTION,
                        actual_phonemes=(edit.actual or "",),
                    )
                )
    return issues
