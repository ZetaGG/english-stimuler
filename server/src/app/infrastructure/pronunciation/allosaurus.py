import importlib
import unicodedata
from collections.abc import Callable, Sequence
from typing import Any

from app.domain.pronunciation import (
    PronunciationFeedback,
    PronunciationScorer,
    align_phonemes,
    build_issues,
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
        actual_phones = [normalize_phone(phone) for phone in (actual or "").split()]
        word_phonemes = self._text_to_phonemes(expected_text)
        expected_phones = [phone for _, phones in word_phonemes for phone in phones]
        edits = align_phonemes(expected_phones, actual_phones)
        return PronunciationFeedback(
            overall_score=phone_accuracy(len(expected_phones), edits),
            issues=build_issues(word_phonemes, edits),
        )
