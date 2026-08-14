import json

from fastapi.testclient import TestClient

from app.application.evaluation import EvaluationResult, EvaluationService
from app.domain.feedback import FeedbackReport
from app.domain.grammar import GrammarIssue
from app.domain.ielts import ComponentBands
from app.domain.metrics import FluencyMetrics, WordSegment
from app.domain.pronunciation import ErrorType, PronunciationFeedback, PronunciationIssue
from app.main import create_app


class FakeEvaluationService(EvaluationService):
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def _result(self, segments) -> EvaluationResult:
        return EvaluationResult(
            metrics=FluencyMetrics(
                word_count=len(segments),
                duration=1.0,
                wpm=120.0,
                filler_words={},
                filler_count=0,
                awkward_pauses=[],
                lexical_diversity=1.0,
            ),
            pronunciation=PronunciationFeedback(
                overall_score=80.0,
                issues=[PronunciationIssue("hello", ErrorType.SUBSTITUTION)],
            ),
            grammar_issues=(GrammarIssue("typo", 0, 4),),
            bands=ComponentBands(fluency=6.0, lexical=7.0, pronunciation=7.5, grammar=8.0, overall=7.0),
            report=FeedbackReport(summary="Nice", strengths=("clear",), tips=("slow down",)),
        )

    def evaluate(self, segments, expected_text, audio_path):
        self.calls.append({"mode": "evaluate", "segments": list(segments), "expected_text": expected_text, "audio_path": audio_path})
        return self._result(segments)

    def evaluate_audio(self, audio_path, expected_text):
        self.calls.append({"mode": "evaluate_audio", "audio_path": audio_path, "expected_text": expected_text})
        return self._result([])


def make_client() -> tuple[TestClient, FakeEvaluationService]:
    service = FakeEvaluationService()
    app = create_app(evaluation_service=service)
    return TestClient(app), service


def segments_payload() -> str:
    return json.dumps([{"text": "hello", "start": 0.0, "end": 0.4}, {"text": "world", "start": 0.9, "end": 1.3}])


def post_evaluate(client: TestClient, *, segments: str = None) -> object:
    data = {"expected_text": "hello world"}
    if segments is not None:
        data["segments"] = segments
    elif segments is None:
        data["segments"] = segments_payload()
    return client.post(
        "/v1/evaluate",
        data=data,
        files={"audio": ("rec.wav", b"RIFF\x00\x00\x00\x00WAVE", "audio/wav")},
    )


def post_evaluate_audio_only(client: TestClient) -> object:
    return client.post(
        "/v1/evaluate",
        data={"expected_text": "hello world"},
        files={"audio": ("rec.wav", b"RIFF\x00\x00\x00\x00WAVE", "audio/wav")},
    )


def test_evaluate_returns_full_feedback() -> None:
    client, _ = make_client()
    response = post_evaluate(client)
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["word_count"] == 2
    assert body["bands"]["overall"] == 7.0
    assert body["pronunciation"]["overall_score"] == 80.0
    assert len(body["grammar_issues"]) == 1
    assert body["report"]["summary"] == "Nice"


def test_evaluate_forwards_parsed_segments_and_expected_text() -> None:
    client, service = make_client()
    post_evaluate(client)
    call = service.calls[0]
    assert call["expected_text"] == "hello world"
    assert call["segments"] == [
        WordSegment(text="hello", start=0.0, end=0.4),
        WordSegment(text="world", start=0.9, end=1.3),
    ]


def test_evaluate_saves_audio_to_wav_file() -> None:
    client, service = make_client()
    post_evaluate(client)
    assert service.calls[0]["audio_path"].endswith(".wav")


def test_evaluate_rejects_invalid_segments_json() -> None:
    client, _ = make_client()
    response = post_evaluate(client, segments="not-json")
    assert response.status_code == 422


def test_evaluate_rejects_missing_audio() -> None:
    client, _ = make_client()
    response = client.post(
        "/v1/evaluate",
        data={"expected_text": "hello", "segments": segments_payload()},
    )
    assert response.status_code == 422


def test_evaluate_report_is_null_when_service_returns_none() -> None:
    class NoReportService(FakeEvaluationService):
        def evaluate(self, segments, expected_text, audio_path):
            result = super().evaluate(segments, expected_text, audio_path)
            return EvaluationResult(
                metrics=result.metrics,
                pronunciation=result.pronunciation,
                grammar_issues=result.grammar_issues,
                bands=result.bands,
                report=None,
            )

    service = NoReportService()
    app = create_app(evaluation_service=service)
    response = post_evaluate(TestClient(app))
    assert response.status_code == 200
    assert response.json()["report"] is None


def test_evaluate_without_segments_transcribes_audio() -> None:
    client, service = make_client()
    response = post_evaluate_audio_only(client)
    assert response.status_code == 200
    call = service.calls[0]
    assert call["mode"] == "evaluate_audio"
    assert call["audio_path"].endswith(".wav")
    assert call["expected_text"] == "hello world"
    assert response.json()["metrics"]["word_count"] == 0


def test_evaluate_empty_segments_string_transcribes_audio() -> None:
    client, service = make_client()
    response = post_evaluate(client, segments="")
    assert response.status_code == 200
    assert service.calls[0]["mode"] == "evaluate_audio"
