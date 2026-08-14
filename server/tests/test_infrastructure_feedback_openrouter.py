import json

import httpx
import pytest

from app.domain.feedback import FeedbackContext, FeedbackReport
from app.domain.grammar import GrammarIssue
from app.domain.pronunciation import ErrorType, PronunciationIssue
from app.infrastructure.feedback.openrouter import OpenRouterFeedbackProvider

TEST_KEY = "sk-or-v1-test-key"


def make_context(**overrides: object) -> FeedbackContext:
    defaults: dict[str, object] = {
        "transcript": "hello world",
        "expected_text": "hello world",
        "wpm": 120.0,
        "filler_count": 2,
        "lexical_diversity": 0.6,
        "pronunciation_score": 80.0,
        "pronunciation_issues": (PronunciationIssue("hello", ErrorType.SUBSTITUTION),),
        "grammar_issues": (GrammarIssue("typo", 0, 4),),
        "fluency_band": 6.0,
        "lexical_band": 7.0,
        "pronunciation_band": 8.0,
        "grammar_band": 8.0,
        "overall_band": 7.0,
    }
    defaults.update(overrides)
    return FeedbackContext(**defaults)  # type: ignore[arg-type]


def make_provider(
    content: str | httpx.Response,
    api_key: str = TEST_KEY,
) -> tuple[OpenRouterFeedbackProvider, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if isinstance(content, httpx.Response):
            return content
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}]},
            request=request,
        )

    provider = OpenRouterFeedbackProvider(
        api_key=api_key,
        model="openai/gpt-4o-mini",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    return provider, requests


def test_generate_posts_to_chat_completions_with_auth() -> None:
    provider, requests = make_provider('{"summary":"s","strengths":["a"],"tips":["b"]}')
    provider.generate(make_context())
    request = requests[0]
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["Authorization"] == f"Bearer {TEST_KEY}"
    payload = json.loads(request.content.decode())
    assert payload["model"] == "openai/gpt-4o-mini"
    assert payload["messages"][0]["role"] == "user"


def test_generate_parses_json_report() -> None:
    provider, _ = make_provider('{"summary":"Nice","strengths":["clear","fluent"],"tips":["slow down"]}')
    report = provider.generate(make_context())
    assert report == FeedbackReport(summary="Nice", strengths=("clear", "fluent"), tips=("slow down",))


def test_generate_handles_markdown_wrapped_json() -> None:
    provider, _ = make_provider('```json\n{"summary":"Wrapped","strengths":[],"tips":[]}\n```')
    report = provider.generate(make_context())
    assert report.summary == "Wrapped"


def test_generate_degrades_on_unparseable_content() -> None:
    provider, _ = make_provider("sorry, no json here")
    report = provider.generate(make_context())
    assert report == FeedbackReport(summary="")


def test_generate_propagates_http_errors() -> None:
    provider, _ = make_provider(httpx.Response(429, json={"error": "rate limited"}))
    with pytest.raises(httpx.HTTPStatusError):
        provider.generate(make_context())


def test_generate_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    provider = OpenRouterFeedbackProvider(api_key="", client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={}))))
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        provider.generate(make_context())


def test_generate_falls_back_to_environment_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-env-key")
    provider, requests = make_provider('{"summary":"Env","strengths":[],"tips":[]}', api_key="")
    report = provider.generate(make_context())
    assert report.summary == "Env"
    assert requests[0].headers["Authorization"] == "Bearer sk-or-v1-env-key"


def test_prompt_contains_metrics_and_bands() -> None:
    provider, requests = make_provider('{"summary":"s","strengths":[],"tips":[]}')
    provider.generate(make_context(wpm=140.0, overall_band=7.5))
    content = json.loads(requests[0].content.decode())["messages"][0]["content"]
    assert "140.0" in content
    assert "7.5" in content


def test_generate_builds_default_client_when_not_injected(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def __init__(self, timeout: int) -> None:
            self.timeout = timeout

        def post(self, url: str, *, headers: dict, json: dict) -> httpx.Response:
            payload = json["messages"][0]["content"]
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": '{"summary":"Default client","strengths":[],"tips":[]}'}}]},
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr("app.infrastructure.feedback.openrouter.httpx.Client", FakeClient)
    provider = OpenRouterFeedbackProvider(api_key=TEST_KEY)
    report = provider.generate(make_context())
    assert report.summary == "Default client"
