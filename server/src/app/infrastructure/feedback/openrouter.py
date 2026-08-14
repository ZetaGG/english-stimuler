import json
import os
import re

import httpx

from app.domain.feedback import FeedbackContext, FeedbackProvider, FeedbackReport

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class OpenRouterFeedbackProvider(FeedbackProvider):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._client = client

    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=60)
        return self._client

    def generate(self, context: FeedbackContext) -> FeedbackReport:
        api_key = self._api_key if self._api_key else os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured")
        response = self._http().post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": self._model,
                "messages": [{"role": "user", "content": self._build_prompt(context)}],
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return self._parse_report(content)

    def _build_prompt(self, context: FeedbackContext) -> str:
        pronunciation_errors = ", ".join(f"'{issue.word}' ({issue.error_type.value})" for issue in context.pronunciation_issues)
        grammar_errors = "; ".join(f"'{issue.message}' at {issue.offset}" for issue in context.grammar_issues)
        return (
            "You are an IELTS speaking coach. Based on this attempt, give concise coaching "
            "feedback as STRICT JSON only, with exactly these keys: "
            '"summary" (2-3 sentences), "strengths" (array of 2-3 short strings), '
            '"tips" (array of 2-3 specific actionable strings). Do not add anything outside the JSON.\n\n'
            f"Expected: {context.expected_text}\n"
            f"Transcribed: {context.transcript}\n"
            f"Words per minute: {context.wpm}\n"
            f"Filler words: {context.filler_count}\n"
            f"Lexical diversity (TTR): {context.lexical_diversity}\n"
            f"Pronunciation score (0-100): {context.pronunciation_score}\n"
            f"Pronunciation issues: {pronunciation_errors or 'none'}\n"
            f"Grammar issues: {grammar_errors or 'none'}\n"
            f"IELTS bands - fluency: {context.fluency_band}, lexical: {context.lexical_band}, "
            f"pronunciation: {context.pronunciation_band}, grammar: {context.grammar_band}, "
            f"overall: {context.overall_band}"
        )

    def _parse_report(self, content: str) -> FeedbackReport:
        text = content.strip()
        block = _JSON_BLOCK_RE.search(text)
        if block:
            text = block.group(1).strip()
        if not text.startswith("{"):
            text = text[text.find("{") : text.rfind("}") + 1]
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return FeedbackReport(summary="")
        return FeedbackReport(
            summary=str(parsed.get("summary", "")),
            strengths=tuple(str(item) for item in parsed.get("strengths", [])),
            tips=tuple(str(item) for item in parsed.get("tips", [])),
        )
