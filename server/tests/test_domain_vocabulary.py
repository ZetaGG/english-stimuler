import pytest

from app.domain.vocabulary import VocabularyItem, VocabularyStore


def test_vocabulary_item_is_immutable_data_holder() -> None:
    item = VocabularyItem(word="brown", added_at="2026-01-01T00:00:00+00:00")
    assert item.word == "brown"


def test_vocabulary_store_is_abstract() -> None:
    with pytest.raises(TypeError):
        VocabularyStore()  # type: ignore[abstract]
