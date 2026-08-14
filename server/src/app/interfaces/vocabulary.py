from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.application.vocabulary import VocabularyService

router = APIRouter(prefix="/v1")


def _vocabulary(request: Request) -> VocabularyService:
    return request.app.state.vocabulary_service


@router.get("/vocabulary")
def list_vocabulary(vocabulary: VocabularyService = Depends(_vocabulary)) -> dict[str, Any]:
    return {"items": [{"word": item.word, "added_at": item.added_at} for item in vocabulary.items()]}


@router.delete("/vocabulary/{word}", status_code=204)
def remove_vocabulary(word: str, vocabulary: VocabularyService = Depends(_vocabulary)) -> None:
    if not vocabulary.remove(word):
        raise HTTPException(status_code=404, detail="word not found")
