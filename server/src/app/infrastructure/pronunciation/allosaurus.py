import importlib
import os
import tempfile
import unicodedata
import wave
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from app.domain.metrics import WordSegment
from app.domain.pronunciation import (
    AlignmentOp,
    PronunciationFeedback,
    PronunciationScorer,
    PronunciationWordIssue,
    align_phonemes,
    build_word_issues,
    phone_accuracy,
)

_IPA_TO_ARPABET: dict[str, str] = {
    "a": "AA",
    "ɑ": "AA",
    "ä": "AA",
    "ɒ": "AO",
    "ɔ": "AO",
    "o": "OW",
    "e": "EH",
    "ɛ": "EH",
    "æ": "AE",
    "ɪ": "IH",
    "i": "IY",
    "ʌ": "AH",
    "ə": "AH",
    "ɐ": "AH",
    "ɵ": "AH",
    "ʊ": "UH",
    "u": "UW",
    "ʉ": "UW",
    "ɯ": "UW",
    "ɹ": "R",
    "r": "R",
    "ɾ": "R",
    "ʁ": "R",
    "ɚ": "ER",
    "ɝ": "ER",
    "ɻ": "ER",
    "b": "B",
    "d": "D",
    "ɖ": "D",
    "f": "F",
    "g": "G",
    "ɡ": "G",
    "h": "HH",
    "ɦ": "HH",
    "j": "Y",
    "ʝ": "Y",
    "k": "K",
    "l": "L",
    "m": "M",
    "ɱ": "M",
    "n": "N",
    "ɲ": "N",
    "ŋ": "NG",
    "p": "P",
    "s": "S",
    "ʃ": "SH",
    "ʂ": "SH",
    "t": "T",
    "ʈ": "T",
    "ts": "TS",
    "tʃ": "CH",
    "t͡ʃ": "CH",
    "dʒ": "JH",
    "d͡ʒ": "JH",
    "θ": "TH",
    "ð": "DH",
    "v": "V",
    "w": "W",
    "z": "Z",
    "ʒ": "ZH",
    "ʐ": "ZH",
    "ç": "HH",
    "ɸ": "F",
    "β": "V",
    "ɣ": "G",
    "ɕ": "SH",
    "ʑ": "ZH",
    "ʋ": "W",
}

_MODIFIER_START = 0x02B0
_MODIFIER_END = 0x02FF


def _strip_diacritics(symbol: str) -> str:
    decomposed = unicodedata.normalize("NFD", symbol)
    return "".join(
        ch
        for ch in decomposed
        if unicodedata.category(ch) != "Mn" and not (_MODIFIER_START <= ord(ch) <= _MODIFIER_END)
    )


def normalize_phone(phone: str) -> str:
    stripped = _strip_diacritics(phone)
    return _IPA_TO_ARPABET.get(stripped, phone)


def text_to_word_phonemes(expected_text: str) -> list[tuple[str, Sequence[str]]]:
    from cmudict import dict as load_cmudict

    lexicon = load_cmudict()
    word_phonemes: list[tuple[str, Sequence[str]]] = []
    for word in expected_text.split():
        clean = word.strip(".,!?;:\"()").lower()
        entry = lexicon.get(clean)
        if not entry:
            continue
        phones = tuple(phone.rstrip("0123456789") for phone in entry[0])
        word_phonemes.append((word, phones))
    return word_phonemes


def _default_recognizer() -> Any:
    app = importlib.import_module("allosaurus.app")
    return app.read_recognizer()


def _convert_to_wav(audio_path: str) -> str:
    """Decode a container (e.g. webm/opus) into a temporary 16 kHz mono PCM WAV file.

    PyAV (`av`) is only imported lazily because it ships with the `ai` extras,
    so importing this module must not require it.
    """
    import os
    import av
    import wave

    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    try:
        with av.open(audio_path) as container:
            stream = container.streams.audio[0]
            resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
            with wave.open(wav_path, "wb") as target:
                target.setnchannels(1)
                target.setsampwidth(2)
                target.setframerate(16000)
                for frame in container.decode(stream):
                    for resampled in resampler.resample(frame):
                        target.writeframes(resampled.to_ndarray().tobytes())
                for resampled in resampler.resample(None):
                    target.writeframes(resampled.to_ndarray().tobytes())
    except Exception:
        os.close(fd)
        Path(wav_path).unlink(missing_ok=True)
        raise
    os.close(fd)
    return wav_path


def ensure_wav(audio_path: str) -> str:
    """Return the path as-is when it is already a WAV, otherwise convert it to WAV."""
    if Path(audio_path).suffix.lower() in (".wav", ".wave"):
        return audio_path
    return _convert_to_wav(audio_path)


class AllosaurusPronunciationScorer(PronunciationScorer):
    def __init__(
        self,
        recognizer: Any | None = None,
        lang_id: str = "eng",
        text_to_phonemes: Callable[[str], list[tuple[str, Sequence[str]]]] = text_to_word_phonemes,
        pad: float = 0.05,
        min_slice: float = 0.05,
    ) -> None:
        self._recognizer = recognizer
        self._lang_id = lang_id
        self._text_to_phonemes = text_to_phonemes
        self._pad = pad
        self._min_slice = min_slice

    def _get_recognizer(self) -> Any:
        if self._recognizer is None:
            self._recognizer = _default_recognizer()
        return self._recognizer

    def score(self, audio_path: str, words: Sequence[WordSegment]) -> PronunciationFeedback:
        recognizer = self._get_recognizer()
        wav_path = ensure_wav(audio_path)
        try:
            return self._score_words(recognizer, wav_path, words)
        finally:
            if wav_path != audio_path:
                Path(wav_path).unlink(missing_ok=True)

    def _score_words(
        self,
        recognizer: Any,
        wav_path: str,
        words: Sequence[WordSegment],
    ) -> PronunciationFeedback:
        with wave.open(wav_path, "rb") as source:
            params = source.getparams()
            frames = source.readframes(params.nframes)
        duration = params.nframes / params.framerate

        results: list[tuple[str, tuple[str, ...], tuple[str, ...], list, tuple]] = []
        for segment in words:
            entries = self._text_to_phonemes(segment.text)
            if not entries:
                continue
            expected = tuple(entries[0][1])
            start, end = self._slice_bounds(segment, words, duration)
            if end - start < self._min_slice:
                continue
            slice_path = self._write_slice(frames, params, start, end)
            try:
                actual_raw = recognizer.recognize(slice_path, lang_id=self._lang_id)
                actual = tuple(_filter_silence(normalize_phone(phone) for phone in (actual_raw or "").split()))
            except Exception:
                continue
            finally:
                Path(slice_path).unlink(missing_ok=True)
            edits = align_phonemes(expected, actual)
            results.append((segment.text, expected, actual, edits, tuple(build_word_issues(segment.text, expected, actual))))

        total_expected = sum(len(expected) for _, expected, _, _, _ in results)
        total_matched = sum(sum(1 for edit in edits if edit.op is AlignmentOp.MATCH) for _, _, _, edits, _ in results)
        overall = round(100.0 * total_matched / total_expected, 1) if total_expected else 0.0
        word_feedbacks = [
            PronunciationWordIssue(
                word=text,
                target_phonemes=expected,
                actual_phonemes=actual,
                score=phone_accuracy(len(expected), edits),
                issues=issues,
            )
            for text, expected, actual, edits, issues in results
        ]
        issues = [issue for word in word_feedbacks for issue in word.issues]
        return PronunciationFeedback(overall_score=overall, words=word_feedbacks, issues=issues)

    def _slice_bounds(self, segment: WordSegment, words: Sequence[WordSegment], duration: float) -> tuple[float, float]:
        prev_end: float | None = None
        next_start: float | None = None
        for other in words:
            if other is segment:
                continue
            if other.end <= segment.start:
                prev_end = other.end if prev_end is None else max(prev_end, other.end)
            elif other.start >= segment.end:
                next_start = other.start if next_start is None else min(next_start, other.start)
        start = (prev_end + segment.start) / 2.0 if prev_end is not None else segment.start - self._pad
        end = (segment.end + next_start) / 2.0 if next_start is not None else segment.end + self._pad
        return max(0.0, start), min(duration, end)

    def _write_slice(self, frames: bytes, params: Any, start: float, end: float) -> str:
        fd, slice_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        byte_start = int(start * params.framerate) * params.sampwidth
        byte_end = int(end * params.framerate) * params.sampwidth
        with wave.open(slice_path, "wb") as target:
            target.setnchannels(params.nchannels)
            target.setsampwidth(params.sampwidth)
            target.setframerate(params.framerate)
            target.writeframes(frames[byte_start:byte_end])
        return slice_path


_SILENCE_TOKENS = frozenset({"", "sil", "silence", "spn", "sp"})


def _filter_silence(phones: Sequence[str]) -> list[str]:
    return [phone for phone in phones if phone not in _SILENCE_TOKENS]
