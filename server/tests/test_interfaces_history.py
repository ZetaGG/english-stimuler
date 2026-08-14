from collections.abc import Sequence

from fastapi.testclient import TestClient

from app.application.evaluation import EvaluationResult
from app.application.history import HistoryService, ProgressStats
from app.application.vocabulary import VocabularyService
from app.domain.grammar import GrammarIssue
from app.domain.history import EvaluationRecord
from app.domain.ielts import ComponentBands
from app.domain.metrics import FluencyMetrics
from app.domain.pronunciation import PronunciationFeedback
from app.domain.vocabulary import VocabularyItem
from app.main import create_app


def make_record(record_id: str) -> EvaluationRecord:
    return EvaluationRecord(
        id=record_id,
        created_at="2026-01-01T00:00:00+00:00",
        expected_text="hello",
        transcript="hello",
        wpm=120.0,
        lexical_diversity=1.0,
        pronunciation_score=80.0,
        grammar_error_count=0,
        filler_count=0,
        fluency_band=6.0,
        lexical_band=7.0,
        pronunciation_band=7.5,
        grammar_band=8.0,
        overall_band=7.0,
    )


class FakeHistory(HistoryService):
    def __init__(self) -> None:
        self.records = [make_record("r1"), make_record("r2")]

    def recent(self, limit: int = 20, offset: int = 0) -> list[EvaluationRecord]:
        return self.records[offset : offset + limit]

    def get(self, record_id: str) -> EvaluationRecord | None:
        return next((r for r in self.records if r.id == record_id), None)

    def count(self) -> int:
        return len(self.records)

    def delete(self, record_id: str) -> bool:
        before = len(self.records)
        self.records = [r for r in self.records if r.id != record_id]
        return len(self.records) < before

    def stats(self) -> ProgressStats:
        return ProgressStats(2, 1, 6.0, 7.0, 7.5, 8.0, 7.0)


class FakeVocabulary(VocabularyService):
    def __init__(self) -> None:
        self.words = [VocabularyItem("brown", "2026-01-01T00:00:00+00:00")]

    def items(self) -> list[VocabularyItem]:
        return self.words

    def remove(self, word: str) -> bool:
        before = len(self.words)
        self.words = [w for w in self.words if w.word != word]
        return len(self.words) < before


def make_history_client() -> TestClient:
    return TestClient(create_app(history_service=FakeHistory(), vocabulary_service=FakeVocabulary()))


def test_list_evaluations_returns_items_and_total() -> None:
    client = make_history_client()
    response = client.get("/v1/evaluations")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["id"] for item in body["items"]] == ["r1", "r2"]
    assert body["items"][0]["transcript"] == "hello"


def test_list_evaluations_respects_pagination() -> None:
    client = make_history_client()
    response = client.get("/v1/evaluations", params={"limit": 1, "offset": 1})
    assert [item["id"] for item in response.json()["items"]] == ["r2"]


def test_get_evaluation_returns_record() -> None:
    client = make_history_client()
    response = client.get("/v1/evaluations/r1")
    assert response.status_code == 200
    assert response.json()["id"] == "r1"


def test_get_evaluation_returns_404_for_missing() -> None:
    client = make_history_client()
    response = client.get("/v1/evaluations/missing")
    assert response.status_code == 404


def test_delete_evaluation_returns_204_and_404() -> None:
    client = make_history_client()
    assert client.delete("/v1/evaluations/r1").status_code == 204
    assert client.delete("/v1/evaluations/r1").status_code == 404


def test_stats_returns_progress_summary() -> None:
    client = make_history_client()
    response = client.get("/v1/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["recent_count"] == 1
    assert body["avg_overall"] == 7.0


def test_list_vocabulary_returns_words() -> None:
    client = make_history_client()
    response = client.get("/v1/vocabulary")
    assert response.status_code == 200
    assert response.json()["items"] == [{"word": "brown", "added_at": "2026-01-01T00:00:00+00:00"}]


def test_delete_vocabulary_returns_204_and_404() -> None:
    client = make_history_client()
    assert client.delete("/v1/vocabulary/brown").status_code == 204
    assert client.delete("/v1/vocabulary/brown").status_code == 404
