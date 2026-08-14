import socket

import httpx
import pytest

from app.domain.grammar import GrammarIssue
from app.infrastructure.grammar.languagetool import LanguageToolGrammarChecker


def make_transport(json_body: dict, status: int = 200) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=json_body, request=request)

    return httpx.MockTransport(handler)


def make_checker(transport: httpx.MockTransport) -> LanguageToolGrammarChecker:
    return LanguageToolGrammarChecker(base_url="http://lt:8010", client=httpx.Client(transport=transport))


def test_check_posts_text_and_language() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.content.decode()
        return httpx.Response(200, json={"matches": []}, request=request)

    checker = make_checker(httpx.MockTransport(handler))
    assert checker.check("hello") == []
    assert captured["url"] == "http://lt:8010/v2/check"
    assert "text=hello" in captured["body"]
    assert "language=en-US" in captured["body"]


def test_check_parses_matches_into_issues() -> None:
    body = {
        "matches": [
            {
                "message": "Possible spelling mistake",
                "offset": 0,
                "length": 4,
                "replacements": [{"value": "word"}, {"value": "wrod"}],
                "rule": {"id": "MORFOLOGIK_RULE_EN_US", "issueType": "misspelling"},
            }
        ]
    }
    checker = make_checker(make_transport(body))
    issues = checker.check("word")
    assert issues == [
        GrammarIssue(
            message="Possible spelling mistake",
            offset=0,
            length=4,
            suggestions=("word", "wrod"),
            rule_id="MORFOLOGIK_RULE_EN_US",
            severity="misspelling",
        )
    ]


def test_check_handles_empty_matches() -> None:
    assert make_checker(make_transport({"matches": []})).check("perfect") == []


def test_check_propagates_http_errors() -> None:
    checker = make_checker(make_transport({"error": "boom"}, status=500))
    with pytest.raises(httpx.HTTPStatusError):
        checker.check("hello")


def test_check_uses_default_base_url() -> None:
    captured: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(str(request.url))
        return httpx.Response(200, json={"matches": []}, request=request)

    checker = LanguageToolGrammarChecker(client=httpx.Client(transport=httpx.MockTransport(handler)))
    checker.check("hello")
    assert captured == ["http://localhost:8010/v2/check"]


def _languagetool_is_reachable() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 8010), timeout=1.0):
            return True
    except OSError:
        return False


@pytest.mark.skipif(not _languagetool_is_reachable(), reason="LanguageTool container not running")
def test_integration_checks_real_text() -> None:
    checker = LanguageToolGrammarChecker()
    issues = checker.check("He dont like thes books.")
    assert any("don't" in issue.suggestions for issue in issues)
