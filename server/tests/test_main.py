import os

from app.application.evaluation import EvaluationService
from app.application.history import HistoryService
from app.application.vocabulary import VocabularyService
from app.main import create_app


def test_create_app_exposes_default_services() -> None:
    app = create_app()
    assert isinstance(app.state.evaluation_service, EvaluationService)
    assert isinstance(app.state.history_service, HistoryService)
    assert isinstance(app.state.vocabulary_service, VocabularyService)


def test_create_app_keeps_injected_fakes() -> None:
    fake_history = HistoryService.__new__(HistoryService)
    fake_vocabulary = VocabularyService.__new__(VocabularyService)
    app = create_app(history_service=fake_history, vocabulary_service=fake_vocabulary)
    assert app.state.history_service is fake_history
    assert app.state.vocabulary_service is fake_vocabulary


def test_default_db_path_creates_parent_directories(tmp_path, monkeypatch) -> None:
    target = tmp_path / "nested" / "custom.db"
    monkeypatch.setenv("DATABASE_PATH", str(target))
    create_app()
    assert target.exists()
