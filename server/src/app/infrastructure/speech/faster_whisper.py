from collections.abc import Callable
import ctypes.util

from app.domain.metrics import WordSegment
from app.domain.speech import SpeechToText


def _default_model_loader(model: str, device: str, compute_type: str):
    from faster_whisper import WhisperModel

    return WhisperModel(model, device=device, compute_type=compute_type)


def _cuda_runtime_available() -> bool:
    return bool(ctypes.util.find_library("cublas"))


def default_device() -> str:
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() == 0:
            return "cpu"
        return "cuda" if _cuda_runtime_available() else "cpu"
    except Exception:  # pragma: no cover
        return "cpu"


class FasterWhisperTranscriber(SpeechToText):
    def __init__(
        self,
        model: str = "base",
        device: str = "cuda",
        compute_type: str = "default",
        language: str = "en",
        model_loader: Callable[[str, str, str], object] | None = None,
    ) -> None:
        self._model = model
        self._device = device
        self._compute_type = compute_type
        self._language = language
        self._model_loader = model_loader or _default_model_loader
        self._loaded: object | None = None

    def _get_model(self) -> object:
        if self._loaded is None:
            try:
                self._loaded = self._model_loader(self._model, self._device, self._compute_type)
            except (OSError, RuntimeError):
                if self._device != "cuda":
                    raise
                self._loaded = self._model_loader(self._model, "cpu", self._compute_type)
        return self._loaded

    def transcribe(self, audio_path: str) -> list[WordSegment]:
        segments, _info = self._get_model().transcribe(  # type: ignore[attr-defined]
            audio_path,
            language=self._language,
            word_timestamps=True,
        )
        words: list[WordSegment] = []
        for segment in segments:
            for word in segment.words or []:
                words.append(WordSegment(text=word.word.strip(), start=word.start, end=word.end))
        return words
