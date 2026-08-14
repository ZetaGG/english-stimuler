import importlib
from collections.abc import Callable, Sequence
from typing import Any

from app.domain.pronunciation import (
    PronunciationFeedback,
    PronunciationScorer,
    align_phonemes,
    build_issues,
    phone_accuracy,
)


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


class AllosaurusPronunciationScorer(PronunciationScorer):
    def __init__(
        self,
        recognizer: Any | None = None,
        lang_id: str = "eng",
        text_to_phonemes: Callable[[str], list[tuple[str, Sequence[str]]]] = text_to_word_phonemes,
    ) -> None:
        self._recognizer = recognizer
        self._lang_id = lang_id
        self._text_to_phonemes = text_to_phonemes

    def _get_recognizer(self) -> Any:
        if self._recognizer is None:
            self._recognizer = _default_recognizer()
        return self._recognizer

    def score(self, audio_path: str, expected_text: str) -> PronunciationFeedback:
        recognizer = self._get_recognizer()
        actual = recognizer.recognize(audio_path, lang_id=self._lang_id)
        actual_phones = (actual or "").split()
        word_phonemes = self._text_to_phonemes(expected_text)
        expected_phones = [phone for _, phones in word_phonemes for phone in phones]
        edits = align_phonemes(expected_phones, actual_phones)
        return PronunciationFeedback(
            overall_score=phone_accuracy(len(expected_phones), edits),
            issues=build_issues(word_phonemes, edits),
        )
