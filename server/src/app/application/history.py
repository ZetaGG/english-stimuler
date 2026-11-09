from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
import uuid

from app.domain.history import EvaluationRecord, EvaluationStore

if TYPE_CHECKING:  # pragma: no cover
    from app.application.evaluation import EvaluationResult


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


Clock = Callable[[], datetime]


@dataclass(frozen=True)
class ProgressStats:
    total: int
    recent_count: int
    avg_fluency: float
    avg_lexical: float
    avg_pronunciation: float
    avg_grammar: float
    avg_overall: float


class HistoryService:
    def __init__(self, store: EvaluationStore, clock: Clock = utc_now) -> None:
        self._store = store
        self._clock = clock

    def record(self, result: EvaluationResult, expected_text: str, transcript: str) -> str:
        record = EvaluationRecord(
            id=uuid.uuid4().hex,
            created_at=self._clock().isoformat(),
            expected_text=expected_text,
            transcript=transcript,
            wpm=result.metrics.wpm,
            lexical_diversity=result.metrics.lexical_diversity,
            pronunciation_score=result.pronunciation.overall_score,
            grammar_error_count=len(result.grammar_issues),
            filler_count=result.metrics.filler_count,
            fluency_band=result.bands.fluency,
            lexical_band=result.bands.lexical,
            pronunciation_band=result.bands.pronunciation,
            grammar_band=result.bands.grammar,
            overall_band=result.bands.overall,
            report=result.report,
            pronunciation_issues=tuple(result.pronunciation.issues),
            pronunciation_words=tuple(result.pronunciation.words),
            grammar_issues=result.grammar_issues,
        )
        self._store.save(record)
        return record.id

    def recent(self, limit: int = 20, offset: int = 0) -> list[EvaluationRecord]:
        return self._store.list(limit=limit, offset=offset)

    def get(self, record_id: str) -> EvaluationRecord | None:
        return self._store.get(record_id)

    def count(self) -> int:
        return self._store.count()

    def delete(self, record_id: str) -> bool:
        return self._store.delete(record_id)

    def stats(self) -> ProgressStats:
        records = self._store.list(limit=100000)
        total = len(records)

        def average(attribute: str) -> float:
            if total == 0:
                return 0.0
            return round(sum(getattr(record, attribute) for record in records) / total, 1)

        since = (self._clock() - timedelta(days=7)).isoformat()
        recent_count = sum(1 for record in records if record.created_at >= since)
        return ProgressStats(
            total=total,
            recent_count=recent_count,
            avg_fluency=average("fluency_band"),
            avg_lexical=average("lexical_band"),
            avg_pronunciation=average("pronunciation_band"),
            avg_grammar=average("grammar_band"),
            avg_overall=average("overall_band"),
        )
