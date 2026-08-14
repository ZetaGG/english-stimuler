import pytest

from app.domain.metrics import WordSegment
from app.domain.speech import SpeechToText


class FakeTranscriber(SpeechToText):
    def transcribe(self, audio_path: str) -> list[WordSegment]:
        return [WordSegment(text="hello", start=0.0, end=0.4)]


def test_transcriber_is_abstract() -> None:
    with pytest.raises(TypeError):
        SpeechToText()  # type: ignore[abstract]


def test_concrete_transcriber_implements_contract() -> None:
    segments = FakeTranscriber().transcribe("/tmp/a.wav")
    assert segments == [WordSegment(text="hello", start=0.0, end=0.4)]
