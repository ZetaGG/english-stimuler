import importlib.util
import math
import struct
import sys
import types
import wave
from pathlib import Path

import pytest

from app.domain.metrics import WordSegment
from app.domain.pronunciation import ErrorType, PronunciationFeedback
from app.infrastructure.pronunciation.allosaurus import (
    AllosaurusPronunciationScorer,
    _default_recognizer,
    ensure_wav,
    normalize_phone,
    text_to_word_phonemes,
)


def make_wav(path: Path, seconds: float = 1.0, framerate: int = 16000) -> Path:
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(framerate)
        f.writeframes(b"\x00\x00" * int(framerate * seconds))
    return path


def test_normalize_phone_maps_aspirated_and_vowels() -> None:
    assert normalize_phone("kʰ") == "K"
    assert normalize_phone("ʌ") == "AH"
    assert normalize_phone("ɹ̩") == "R"
    assert normalize_phone("ə") == "AH"


def test_normalize_phone_maps_digraphs() -> None:
    assert normalize_phone("tʃ") == "CH"
    assert normalize_phone("dʒ") == "JH"


def test_normalize_phone_passes_through_unknown_and_uppercase() -> None:
    assert normalize_phone("χ") == "χ"
    assert normalize_phone("HH") == "HH"
    assert normalize_phone("OW") == "OW"


class FakeRecognizer:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls: list[tuple[str, str]] = []

    def recognize(self, audio_path: str, lang_id: str = "eng") -> str:
        self.calls.append((audio_path, lang_id))
        return self.output


class SequenceRecognizer:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)
        self.calls: list[tuple[str, str]] = []

    def recognize(self, audio_path: str, lang_id: str = "eng") -> str:
        self.calls.append((audio_path, lang_id))
        return self.outputs.pop(0)


def fake_text_to_phonemes(text: str) -> list[tuple[str, tuple[str, ...]]]:
    if "hello" in text:
        return [("hello", ("HH", "AH", "L", "OW"))]
    return []


def fake_cmudict_module(monkeypatch: pytest.MonkeyPatch, lexicon: dict) -> None:
    module = types.ModuleType("cmudict")
    module.dict = lambda: lexicon
    monkeypatch.setitem(sys.modules, "cmudict", module)


def test_scorer_returns_perfect_score_for_identical_phones(tmp_path: Path) -> None:
    recognizer = FakeRecognizer("HH AH L OW")
    scorer = AllosaurusPronunciationScorer(recognizer, text_to_phonemes=fake_text_to_phonemes)
    wav = make_wav(tmp_path / "audio.wav")
    feedback = scorer.score(str(wav), [WordSegment("hello", 0.0, 0.5)])
    assert isinstance(feedback, PronunciationFeedback)
    assert feedback.overall_score == 100.0
    assert feedback.issues == []
    assert len(feedback.words) == 1
    assert feedback.words[0].score == 100.0


def test_scorer_flags_substitution_in_word(tmp_path: Path) -> None:
    recognizer = FakeRecognizer("HH EH L OW")
    scorer = AllosaurusPronunciationScorer(recognizer, text_to_phonemes=fake_text_to_phonemes)
    wav = make_wav(tmp_path / "audio.wav")
    feedback = scorer.score(str(wav), [WordSegment("hello", 0.0, 0.5)])
    assert feedback.overall_score == 75.0
    assert len(feedback.issues) == 1
    assert feedback.issues[0].word == "hello"
    assert feedback.issues[0].error_type is ErrorType.SUBSTITUTION
    assert feedback.issues[0].expected_phonemes == ("AH",)
    assert feedback.issues[0].actual_phonemes == ("EH",)


def test_scorer_normalizes_allosaurus_ipa_output(tmp_path: Path) -> None:
    def quick_phonemes(text: str) -> list[tuple[str, tuple[str, ...]]]:
        return [("quick", ("K", "W", "IH", "K"))]

    recognizer = FakeRecognizer("kʰ w e n")
    scorer = AllosaurusPronunciationScorer(recognizer, text_to_phonemes=quick_phonemes)
    wav = make_wav(tmp_path / "audio.wav")
    feedback = scorer.score(str(wav), [WordSegment("quick", 0.0, 0.5)])
    assert feedback.overall_score == 50.0
    assert feedback.issues[0].expected_phonemes == ("IH",)
    assert feedback.issues[0].actual_phonemes == ("EH",)


def test_scorer_flags_all_phones_deleted_when_audio_empty(tmp_path: Path) -> None:
    recognizer = FakeRecognizer("")
    scorer = AllosaurusPronunciationScorer(recognizer, text_to_phonemes=fake_text_to_phonemes)
    wav = make_wav(tmp_path / "audio.wav")
    feedback = scorer.score(str(wav), [WordSegment("hello", 0.0, 0.5)])
    assert feedback.overall_score == 0.0
    assert all(issue.error_type is ErrorType.DELETION for issue in feedback.issues)


def test_scorer_uses_configured_lang_id(tmp_path: Path) -> None:
    recognizer = FakeRecognizer("HH AH L OW")
    scorer = AllosaurusPronunciationScorer(recognizer, lang_id="ipa", text_to_phonemes=fake_text_to_phonemes)
    wav = make_wav(tmp_path / "audio.wav")
    scorer.score(str(wav), [WordSegment("hello", 0.0, 0.5)])
    assert len(recognizer.calls) == 1
    path, lang_id = recognizer.calls[0]
    assert lang_id == "ipa"
    assert path.endswith(".wav")


def test_scorer_builds_default_recognizer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    recognizer = FakeRecognizer("HH AH L OW")
    fake_app = types.ModuleType("allosaurus.app")
    fake_app.read_recognizer = lambda: recognizer
    monkeypatch.setitem(sys.modules, "allosaurus.app", fake_app)
    scorer = AllosaurusPronunciationScorer(text_to_phonemes=fake_text_to_phonemes)
    wav = make_wav(tmp_path / "audio.wav")
    feedback = scorer.score(str(wav), [WordSegment("hello", 0.0, 0.5)])
    assert feedback.overall_score == 100.0


def test_scorer_isolates_words(tmp_path: Path) -> None:
    def two_words(text: str) -> list[tuple[str, tuple[str, ...]]]:
        lexicon = {"cat": ("K", "AE", "T"), "sat": ("S", "AE", "T")}
        entry = lexicon.get(text)
        return [(text, entry)] if entry else []

    recognizer = SequenceRecognizer(["K AE T", "S EH T"])
    scorer = AllosaurusPronunciationScorer(recognizer, text_to_phonemes=two_words)
    wav = make_wav(tmp_path / "audio.wav")
    feedback = scorer.score(
        str(wav),
        [WordSegment("cat", 0.0, 0.4), WordSegment("sat", 0.5, 0.9)],
    )
    assert feedback.words[0].word == "cat"
    assert feedback.words[0].issues == ()
    assert feedback.words[0].score == 100.0
    assert feedback.words[1].word == "sat"
    assert len(feedback.words[1].issues) == 1
    assert feedback.words[1].issues[0].error_type is ErrorType.SUBSTITUTION
    assert feedback.overall_score == round(100.0 * 5 / 6, 1)


def test_scorer_skips_words_without_phonemes_or_timing(tmp_path: Path) -> None:
    recognizer = FakeRecognizer("HH AH L OW")
    scorer = AllosaurusPronunciationScorer(recognizer, text_to_phonemes=fake_text_to_phonemes)
    wav = make_wav(tmp_path / "audio.wav")
    feedback = scorer.score(
        str(wav),
        [WordSegment("hello", 0.0, 0.5), WordSegment("zzyzx", 0.5, 0.8)],
    )
    assert [word.word for word in feedback.words] == ["hello"]

    feedback = scorer.score(str(wav), [WordSegment("hello", 0.5, 0.4)])
    assert feedback.words == []
    assert feedback.overall_score == 0.0


def test_scorer_cleans_up_slice_files(tmp_path: Path) -> None:
    recognizer = FakeRecognizer("HH AH L OW")
    scorer = AllosaurusPronunciationScorer(recognizer, text_to_phonemes=fake_text_to_phonemes)
    wav = make_wav(tmp_path / "audio.wav")
    scorer.score(str(wav), [WordSegment("hello", 0.0, 0.5)])
    for path, _ in recognizer.calls:
        assert not Path(path).exists(), "slice temp file must be cleaned up"


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


def test_ensure_wav_returns_wav_path_untouched(tmp_path: Path) -> None:
    wav_path = tmp_path / "audio.wav"
    wav_path.write_bytes(b"RIFFxxxxWAVE")
    assert ensure_wav(str(wav_path)) == str(wav_path)


_AV_INSTALLED = importlib.util.find_spec("av") is not None


def write_webm(path: Path) -> None:
    import av
    import numpy as np

    frame_samples = 640  # 40 ms at 16 kHz (valid libopus frame size)
    samples = np.frombuffer(
        b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 220 * i / 16000))) for i in range(frame_samples * 4)),
        dtype="<i2",
    ).reshape(1, -1)
    with av.open(str(path), "w", format="webm") as container:
        stream = container.add_stream("libopus", rate=16000)
        for offset in range(0, samples.shape[1], frame_samples):
            frame = av.AudioFrame.from_ndarray(samples[:, offset : offset + frame_samples], format="s16", layout="mono")
            frame.sample_rate = 16000
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)


@pytest.mark.skipif(not _AV_INSTALLED, reason="ai extras not installed")
def test_ensure_wav_converts_webm_and_cleans_up(tmp_path: Path) -> None:
    import wave

    source = tmp_path / "recording.webm"
    write_webm(source)

    converted = ensure_wav(str(source))
    try:
        assert converted.endswith(".wav")
        assert converted != str(source)
        with wave.open(converted) as f:
            assert f.getframerate() == 16000
            assert f.getnchannels() == 1
            assert f.getsampwidth() == 2
    finally:
        Path(converted).unlink(missing_ok=True)


@pytest.mark.skipif(not _AV_INSTALLED, reason="ai extras not installed")
def test_scorer_converts_non_wav_before_recognize(tmp_path: Path) -> None:
    source = tmp_path / "recording.webm"
    write_webm(source)

    recognizer = FakeRecognizer("HH AH L OW")
    scorer = AllosaurusPronunciationScorer(recognizer, text_to_phonemes=fake_text_to_phonemes)
    scorer.score(str(source), [WordSegment("hello", 0.0, 0.5)])

    assert len(recognizer.calls) == 1
    wav_path = recognizer.calls[0][0]
    assert wav_path.endswith(".wav")
    assert not Path(wav_path).exists(), "slice temp file must be cleaned up"


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
    feedback = scorer.score(
        str(wav_path),
        [WordSegment("hello", 0.0, 0.25), WordSegment("world", 0.25, 0.5)],
    )
    assert 0.0 <= feedback.overall_score <= 100.0
