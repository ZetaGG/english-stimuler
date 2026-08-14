import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.application.evaluation import EvaluationService
from app.domain.metrics import WordSegment

router = APIRouter(prefix="/v1")


class SegmentIn(BaseModel):
    text: str
    start: float
    end: float


def _service(request: Request) -> EvaluationService:
    return request.app.state.evaluation_service


def _save_audio(audio: UploadFile) -> str:
    suffix = Path(audio.filename or "recording.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio.file.read())
        return tmp.name


@router.post("/evaluate")
def evaluate(
    expected_text: str = Form(...),
    audio: UploadFile = File(...),
    segments: str = Form(""),
    service: EvaluationService = Depends(_service),
) -> dict:
    audio_path = _save_audio(audio)
    try:
        if segments and segments.strip():
            result = service.evaluate(_parse_segments(segments), expected_text, audio_path)
        else:
            result = service.evaluate_audio(audio_path, expected_text)
    finally:
        os.unlink(audio_path)
    return asdict(result)


def _parse_segments(segments: str) -> list[WordSegment]:
    try:
        raw_segments = json.loads(segments)
        parsed_segments = [SegmentIn(**item) for item in raw_segments]
    except (json.JSONDecodeError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="segments must be a JSON array of {text, start, end}")
    return [WordSegment(text=item.text, start=item.start, end=item.end) for item in parsed_segments]
