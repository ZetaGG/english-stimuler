import importlib.util
import math
import struct
import sys
import types
import wave
from pathlib import Path

import pytest

from app.domain.pronunciation import ErrorType, PronunciationFeedback
from app.infrastructure.pronunciation.allosaurus import (
    AllosaurusPronunciationScorer,
    _default_recognizer,
    text_to_word_phonemes,
)


class FakeRecognizer:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls: list[tuple[str, str]] = []

    def recognize(self, audio_path: str, lang_id: str = "eng") -> str:
        self.calls.append((audio_path, lang_id))
        return self.output


def fake_text_to_phonemes(text: str) -> list[tuple[str, tuple[str, ...]]]:
    if "hello" in text:
        return [("hello", ("HH", "AH", "L", "OW"))]
    return []


def fake_cmudict_module(monkeypatch: pytest.MonkeyPatch, lexicon: dict) -> None:
    module = types.ModuleType("cmudict")
    module.dict = lambda: lexicon
    monkeypatch.setitem(sys.modules, "cmudict", module)


def test_scorer_returns_perfect_score_for_identical_phones() -> None:
    recognizer = FakeRecognizer("HH AH L OW")
    scorer = AllosaurusPronunciationScorer(recognizer, text_to_phonemes=fake_text_to_phonemes)
    feedback = scorer.score("/tmp/audio.wav", "hello")
    assert isinstance(feedback, PronunciationFeedback)
    assert feedback.overall_score == 100.0
    assert feedback.issues == []


def test_scorer_flags_substitution_in_word() -> None:
    recognizer = FakeRecognizer("HH EH L OW")
    scorer = AllosaurusPronunciationScorer(recognizer, text_to_phonemes=fake_text_to_phonemes)
    feedback = scorer.score("/tmp/audio.wav", "hello")
    assert feedback.overall_score == 75.0
    assert len(feedback.issues) == 1
    assert feedback.issues[0].word == "hello"
    assert feedback.issues[0].error_type is ErrorType.SUBSTITUTION
    assert feedback.issues[0].expected_phonemes == ("AH",)
    assert feedback.issues[0].actual_phonemes == ("EH",)


def test_scorer_flags_all_phones_deleted_when_audio_empty() -> None:
    recognizer = FakeRecognizer("")
    scorer = AllosaurusPronunciationScorer(recognizer, text_to_phonemes=fake_text_to_phonemes)
    feedback = scorer.score("/tmp/audio.wav", "hello")
    assert feedback.overall_score == 0.0
    assert all(issue.error_type is ErrorType.DELETION for issue in feedback.issues)


def test_scorer_uses_configured_lang_id() -> None:
    recognizer = FakeRecognizer("HH AH L OW")
    scorer = AllosaurusPronunciationScorer(recognizer, lang_id="ipa", text_to_phonemes=fake_text_to_phonemes)
    scorer.score("/tmp/audio.wav", "hello")
    assert recognizer.calls == [("/tmp/audio.wav", "ipa")]


def test_scorer_builds_default_recognizer(monkeypatch: pytest.MonkeyPatch) -> None:
    recognizer = FakeRecognizer("HH AH L OW")
    fake_app = types.ModuleType("allosaurus.app")
    fake_app.read_recognizer = lambda: recognizer
    monkeypatch.setitem(sys.modules, "allosaurus.app", fake_app)
    scorer = AllosaurusPronunciationScorer(text_to_phonemes=fake_text_to_phonemes)
    feedback = scorer.score("/tmp/audio.wav", "hello")
    assert feedback.overall_score == 100.0


def test_default_recognizer_loader_imports_allosaurus(monkeypatch: pytest.MonkeyPatch) -> None:
    recognizer = FakeRecognizer("HH AH L OW")
    fake_app = types.ModuleType("allosaurus.app")
    fake_app.read_recognizer = lambda: recognizer
    monkeypatch.setitem(sys.modules, "allosaurus.app", fake_app)
    assert _default_recognizer() is recognizer


def test_text_to_word_phonemes_maps_known_words(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_cmudict_module(monkeypatch, {"hello": [["HH", "AH0", "L", "OW1"]]})
    assert text_to_word_phonemes("hello") == [("hello", ("HH", "AH", "L", "OW"))]


def test_text_to_word_phonemes_skips_unknown_words(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_cmudict_module(monkeypatch, {"hello": [["HH", "AH0", "L", "OW1"]]})
    assert text_to_word_phonemes("hello zzyzx") == [("hello", ("HH", "AH", "L", "OW"))]


def test_text_to_word_phonemes_strips_punctuation(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_cmudict_module(monkeypatch, {"hello": [["HH", "AH0", "L", "OW1"]], "world": [["W", "ER1", "L", "D"]]})
    result = text_to_word_phonemes("Hello, world.")
    assert [word for word, _ in result] == ["Hello,", "world."]
    assert result[1][1] == ("W", "ER", "L", "D")


_AI_INSTALLED = importlib.util.find_spec("allosaurus") is not None and importlib.util.find_spec("cmudict") is not None


@pytest.mark.skipif(not _AI_INSTALLED, reason="ai extras not installed")
def test_integration_scores_a_real_wav_file(tmp_path: Path) -> None:
    wav_path = tmp_path / "sample.wav"
    with wave.open(str(wav_path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        frames = b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 220 * i / 16000))) for i in range(8000))
        f.writeframes(frames)

    scorer = AllosaurusPronunciationScorer()
    feedback = scorer.score(str(wav_path), "hello world")
    assert 0.0 <= feedback.overall_score <= 100.0
