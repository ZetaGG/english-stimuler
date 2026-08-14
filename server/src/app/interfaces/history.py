from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.application.history import HistoryService

router = APIRouter(prefix="/v1")


def _history(request: Request) -> HistoryService:
    return request.app.state.history_service


@router.get("/evaluations")
def list_evaluations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    history: HistoryService = Depends(_history),
) -> dict[str, Any]:
    records = history.recent(limit=limit, offset=offset)
    return {"items": [asdict(record) for record in records], "total": history.count()}


@router.get("/evaluations/{record_id}")
def get_evaluation(record_id: str, history: HistoryService = Depends(_history)) -> dict[str, Any]:
    record = history.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="evaluation not found")
    return asdict(record)


@router.delete("/evaluations/{record_id}", status_code=204)
def delete_evaluation(record_id: str, history: HistoryService = Depends(_history)) -> None:
    if not history.delete(record_id):
        raise HTTPException(status_code=404, detail="evaluation not found")


@router.get("/stats")
def stats(history: HistoryService = Depends(_history)) -> dict[str, Any]:
    return asdict(history.stats())
