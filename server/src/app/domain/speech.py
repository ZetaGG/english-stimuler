from abc import ABC, abstractmethod

from app.domain.metrics import WordSegment


class SpeechToText(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> list[WordSegment]:
        raise NotImplementedError  # pragma: no cover
