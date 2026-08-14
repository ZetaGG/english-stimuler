from typing import Any

import httpx

from app.domain.grammar import GrammarChecker, GrammarIssue

DEFAULT_BASE_URL = "http://localhost:8010"


class LanguageToolGrammarChecker(GrammarChecker):
    def __init__(self, base_url: str = DEFAULT_BASE_URL, client: httpx.Client | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client

    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30)
        return self._client

    def check(self, text: str) -> list[GrammarIssue]:
        response = self._http().post(
            f"{self._base_url}/v2/check",
            data={"text": text, "language": "en-US"},
        )
        response.raise_for_status()
        return [self._to_issue(match) for match in response.json().get("matches", [])]

    def _to_issue(self, match: dict[str, Any]) -> GrammarIssue:
        rule = match.get("rule") or {}
        message = match.get("message") or match.get("shortMessage") or ""
        return GrammarIssue(
            message=message,
            offset=int(match.get("offset", 0)),
            length=int(match.get("length", 0)),
            suggestions=tuple(replacement.get("value", "") for replacement in match.get("replacements", [])),
            rule_id=str(rule.get("id", "")),
            severity=str(rule.get("issueType", "") or "error"),
        )
