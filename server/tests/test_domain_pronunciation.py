import pytest

from app.domain.pronunciation import (
    AlignmentOp,
    ErrorType,
    PhoneEdit,
    PronunciationFeedback,
    PronunciationIssue,
    PronunciationScorer,
    align_phonemes,
    build_issues,
    phone_accuracy,
)


class FakeScorer(PronunciationScorer):
    def score(self, audio_path: str, expected_text: str) -> PronunciationFeedback:
        return PronunciationFeedback(overall_score=80.0)


def test_error_types_are_declared() -> None:
    assert {error.value for error in ErrorType} == {
        "substitution",
        "insertion",
        "deletion",
        "mispronounced",
    }


def test_issue_is_frozen_and_exposes_fields() -> None:
    issue = PronunciationIssue(
        word="hello",
        error_type=ErrorType.SUBSTITUTION,
        expected_phonemes=("h", "ə", "l", "oʊ"),
        actual_phonemes=("h", "ɛ", "l", "oʊ"),
        score=0.4,
    )
    assert issue.word == "hello"
    assert issue.error_type == ErrorType.SUBSTITUTION
    assert issue.expected_phonemes == ("h", "ə", "l", "oʊ")
    assert issue.score == 0.4
    with pytest.raises(Exception):
        issue.score = 0.9


def test_issue_defaults_to_empty_phonemes_and_zero_score() -> None:
    issue = PronunciationIssue(word="cat", error_type=ErrorType.DELETION)
    assert issue.expected_phonemes == ()
    assert issue.actual_phonemes == ()
    assert issue.score == 0.0


def test_feedback_exposes_score_and_issues() -> None:
    feedback = PronunciationFeedback(overall_score=75.0)
    assert feedback.overall_score == 75.0
    assert feedback.issues == []


def test_feedback_accepts_issues() -> None:
    issue = PronunciationIssue(word="cat", error_type=ErrorType.MISPRONOUNCED)
    feedback = PronunciationFeedback(overall_score=60.0, issues=[issue])
    assert len(feedback.issues) == 1
    assert feedback.issues[0].word == "cat"


def test_feedback_rejects_score_out_of_range() -> None:
    with pytest.raises(ValueError):
        PronunciationFeedback(overall_score=-1.0)
    with pytest.raises(ValueError):
        PronunciationFeedback(overall_score=101.0)


def test_feedback_accepts_score_bounds() -> None:
    assert PronunciationFeedback(overall_score=0.0).overall_score == 0.0
    assert PronunciationFeedback(overall_score=100.0).overall_score == 100.0


def test_scorer_is_abstract() -> None:
    with pytest.raises(TypeError):
        PronunciationScorer()  # type: ignore[abstract]


def test_concrete_scorer_implements_contract() -> None:
    feedback = FakeScorer().score("/tmp/audio.wav", "hello world")
    assert feedback.overall_score == 80.0


def test_align_empty_sequences_yields_no_edits() -> None:
    assert align_phonemes([], []) == []


def test_align_identical_phones_yields_matches() -> None:
    edits = align_phonemes(["h", "ə", "l", "oʊ"], ["h", "ə", "l", "oʊ"])
    assert len(edits) == 4
    assert edits[:2] == [PhoneEdit(AlignmentOp.MATCH, "h", "h"), PhoneEdit(AlignmentOp.MATCH, "ə", "ə")]
    assert all(edit.op is AlignmentOp.MATCH for edit in edits)


def test_align_detects_substitution() -> None:
    edits = align_phonemes(["h", "ə", "l", "oʊ"], ["h", "ɛ", "l", "oʊ"])
    assert edits[1] == PhoneEdit(AlignmentOp.SUBSTITUTION, "ə", "ɛ")


def test_align_detects_deletion_when_phone_is_missing() -> None:
    edits = align_phonemes(["a", "b"], ["a"])
    assert PhoneEdit(AlignmentOp.DELETION, "b", None) in edits


def test_align_detects_insertion_when_phone_is_extra() -> None:
    edits = align_phonemes(["a"], ["a", "b"])
    assert PhoneEdit(AlignmentOp.INSERTION, None, "b") in edits


def test_phone_accuracy_is_perfect_when_all_match() -> None:
    edits = align_phonemes(["h", "ə", "l", "oʊ"], ["h", "ə", "l", "oʊ"])
    assert phone_accuracy(4, edits) == 100.0


def test_phone_accuracy_penalizes_substitutions() -> None:
    edits = align_phonemes(["h", "ə", "l", "oʊ"], ["h", "ɛ", "l", "oʊ"])
    assert phone_accuracy(4, edits) == 75.0


def test_phone_accuracy_empty_expected_is_zero() -> None:
    assert phone_accuracy(0, []) == 0.0


def test_build_issues_flags_substitution_on_right_word() -> None:
    word_phonemes = [("hello", ("h", "ə", "l", "oʊ")), ("world", ("w", "ɜ", "l", "d"))]
    edits = align_phonemes(
        ["h", "ə", "l", "oʊ", "w", "ɜ", "l", "d"],
        ["h", "ɛ", "l", "oʊ", "w", "ɜ", "l", "d"],
    )
    issues = build_issues(word_phonemes, edits)
    assert len(issues) == 1
    assert issues[0].word == "hello"
    assert issues[0].error_type is ErrorType.SUBSTITUTION
    assert issues[0].expected_phonemes == ("ə",)
    assert issues[0].actual_phonemes == ("ɛ",)


def test_build_issues_flags_deletion() -> None:
    word_phonemes = [("cat", ("k", "æ", "t"))]
    edits = align_phonemes(["k", "æ", "t"], ["k", "æ"])
    issues = build_issues(word_phonemes, edits)
    assert issues == [
        PronunciationIssue(
            word="cat",
            error_type=ErrorType.DELETION,
            expected_phonemes=("t",),
        )
    ]


def test_build_issues_attributes_insertion_to_following_word() -> None:
    word_phonemes = [("a", ("a",)), ("b", ("b",))]
    edits = align_phonemes(["a", "b"], ["a", "x", "b"])
    issues = build_issues(word_phonemes, edits)
    assert issues == [
        PronunciationIssue(
            word="b",
            error_type=ErrorType.INSERTION,
            actual_phonemes=("x",),
        )
    ]


def test_build_issues_ignores_trailing_insertion_with_no_word() -> None:
    word_phonemes = [("a", ("a",))]
    edits = align_phonemes(["a"], ["a", "x"])
    assert build_issues(word_phonemes, edits) == []


def test_build_issues_empty_edits_yields_nothing() -> None:
    assert build_issues([("a", ("a",))], []) == []
