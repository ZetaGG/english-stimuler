import importlib.util
import sys
import types

import pytest

from app.domain.metrics import WordSegment
from app.domain.speech import SpeechToText
from app.infrastructure.speech.faster_whisper import FasterWhisperTranscriber, default_device


def fake_ctranslate2(monkeypatch: pytest.MonkeyPatch, device_count: int) -> None:
    module = types.ModuleType("ctranslate2")
    module.get_cuda_device_count = lambda: device_count
    monkeypatch.setitem(sys.modules, "ctranslate2", module)


def test_default_device_returns_cpu_without_cuda_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ctranslate2(monkeypatch, device_count=0)
    assert default_device() == "cpu"


def test_default_device_returns_cpu_when_cuda_runtime_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ctranslate2(monkeypatch, device_count=1)
    monkeypatch.setattr("app.infrastructure.speech.faster_whisper._cuda_runtime_available", lambda: False)
    assert default_device() == "cpu"


def test_default_device_returns_cuda_when_runtime_present(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ctranslate2(monkeypatch, device_count=1)
    monkeypatch.setattr("app.infrastructure.speech.faster_whisper._cuda_runtime_available", lambda: True)
    assert default_device() == "cuda"


class FakeWord:
    def __init__(self, word: str, start: float, end: float) -> None:
        self.word = word
        self.start = start
        self.end = end


class FakeSegment:
    def __init__(self, text: str, start: float, end: float) -> None:
        self.text = text
        self.start = start
        self.end = end
        self.words = [FakeWord(w, 0.1 + i, 0.4 + i) for i, w in enumerate(text.split())]


class FakeModel:
    def __init__(self, segments: list[FakeSegment]) -> None:
        self.segments = segments
        self.calls: list[tuple] = []

    def transcribe(self, audio_path: str, **kwargs) -> tuple[list[FakeSegment], object]:
        self.calls.append((audio_path, kwargs))
        return self.segments, object()


def fake_faster_whisper(monkeypatch: pytest.MonkeyPatch, model: FakeModel) -> None:
    module = types.ModuleType("faster_whisper")
    module.WhisperModel = lambda *args, **kwargs: model
    monkeypatch.setitem(sys.modules, "faster_whisper", module)


def test_transcriber_is_speech_to_text() -> None:
    assert issubclass(FasterWhisperTranscriber, SpeechToText)


def test_transcribe_maps_words_to_segments(monkeypatch: pytest.MonkeyPatch) -> None:
    model = FakeModel([FakeSegment("hello world", 0.0, 1.2)])
    fake_faster_whisper(monkeypatch, model)
    transcriber = FasterWhisperTranscriber(model="base", device="cpu", model_loader=None)
    result = transcriber.transcribe("/tmp/a.wav")
    assert result == [
        WordSegment(text="hello", start=0.1, end=0.4),
        WordSegment(text="world", start=1.1, end=1.4),
    ]


def test_transcribe_strips_leading_spaces_from_word_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    model = FakeModel([FakeSegment("hello world", 0.0, 1.2)])
    model.segments[0].words = [FakeWord(" The", 0.0, 0.2), FakeWord(" quick", 0.2, 0.5)]
    fake_faster_whisper(monkeypatch, model)
    transcriber = FasterWhisperTranscriber(model="base", device="cpu", model_loader=None)
    result = transcriber.transcribe("/tmp/a.wav")
    assert result == [
        WordSegment(text="The", start=0.0, end=0.2),
        WordSegment(text="quick", start=0.2, end=0.5),
    ]


def test_transcribe_requests_word_timestamps_and_english(monkeypatch: pytest.MonkeyPatch) -> None:
    model = FakeModel([])
    fake_faster_whisper(monkeypatch, model)
    transcriber = FasterWhisperTranscriber(model="base", device="cpu", language="en", model_loader=None)
    transcriber.transcribe("/tmp/a.wav")
    audio_path, kwargs = model.calls[0]
    assert audio_path == "/tmp/a.wav"
    assert kwargs["language"] == "en"
    assert kwargs["word_timestamps"] is True


def test_transcribe_handles_segments_without_words(monkeypatch: pytest.MonkeyPatch) -> None:
    segment = FakeSegment("just text", 0.0, 1.0)
    segment.words = None
    model = FakeModel([segment])
    fake_faster_whisper(monkeypatch, model)
    transcriber = FasterWhisperTranscriber(model="base", device="cpu", model_loader=None)
    assert transcriber.transcribe("/tmp/a.wav") == []


def test_transcribe_builds_model_with_configured_device(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def loader(model_name: str, device: str, compute_type: str):
        captured.update(model_name=model_name, device=device, compute_type=compute_type)
        return FakeModel([])

    transcriber = FasterWhisperTranscriber(model="small", device="cuda", compute_type="float16", model_loader=loader)
    transcriber.transcribe("/tmp/a.wav")
    assert captured == {"model_name": "small", "device": "cuda", "compute_type": "float16"}


def test_transcribe_falls_back_to_cpu_when_cuda_load_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[tuple] = []

    def loader(model_name: str, device: str, compute_type: str):
        captured.append((model_name, device, compute_type))
        if device == "cuda":
            raise RuntimeError("Library libcublas.so.12 is not found")
        return FakeModel([])

    transcriber = FasterWhisperTranscriber(model="base", device="cuda", model_loader=loader)
    assert transcriber.transcribe("/tmp/a.wav") == []
    assert captured == [
        ("base", "cuda", "default"),
        ("base", "cpu", "default"),
    ]


def test_transcribe_reports_cpu_load_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def loader(model_name: str, device: str, compute_type: str):
        raise RuntimeError("boom")

    transcriber = FasterWhisperTranscriber(model="base", device="cpu", model_loader=loader)
    with pytest.raises(RuntimeError, match="boom"):
        transcriber.transcribe("/tmp/a.wav")


_AI_INSTALLED = importlib.util.find_spec("faster_whisper") is not None


@pytest.mark.skipif(not _AI_INSTALLED, reason="ai extras not installed")
def test_integration_transcribes_a_real_wav() -> None:
    import wave

    import struct

    path = "/tmp/opencode/stt_sample.wav"
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(b"".join(struct.pack("<h", 0) for _ in range(16000)))
    transcriber = FasterWhisperTranscriber(device="cpu")
    segments = transcriber.transcribe(path)
    assert isinstance(segments, list)
    assert all(isinstance(s, WordSegment) and s.start <= s.end for s in segments)
