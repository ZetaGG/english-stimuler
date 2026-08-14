import pytest

from app.domain.grammar import GrammarChecker, GrammarIssue


class FakeChecker(GrammarChecker):
    def check(self, text: str) -> list[GrammarIssue]:
        return [GrammarIssue(message="misspelling", offset=0, length=4)]


def test_issue_exposes_fields() -> None:
    issue = GrammarIssue(
        message="Possible typo",
        offset=3,
        length=5,
        suggestions=("word", "wrod"),
        rule_id="TYPOS",
        severity="warning",
    )
    assert issue.message == "Possible typo"
    assert issue.offset == 3
    assert issue.length == 5
    assert issue.suggestions == ("word", "wrod")
    assert issue.rule_id == "TYPOS"
    assert issue.severity == "warning"


def test_issue_defaults() -> None:
    issue = GrammarIssue(message="x", offset=0, length=1)
    assert issue.suggestions == ()
    assert issue.rule_id == ""
    assert issue.severity == "error"


def test_issue_is_frozen() -> None:
    issue = GrammarIssue(message="x", offset=0, length=1)
    with pytest.raises(Exception):
        issue.offset = 9


def test_checker_is_abstract() -> None:
    with pytest.raises(TypeError):
        GrammarChecker()  # type: ignore[abstract]


def test_concrete_checker_implements_contract() -> None:
    issues = FakeChecker().check("hello")
    assert len(issues) == 1
    assert issues[0].message == "misspelling"
