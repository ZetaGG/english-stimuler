import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.application.evaluation import EvaluationService
from app.application.history import HistoryService
from app.application.vocabulary import VocabularyService
from app.infrastructure.feedback.openrouter import OpenRouterFeedbackProvider
from app.infrastructure.grammar.languagetool import LanguageToolGrammarChecker
from app.infrastructure.persistence.sqlite import SQLiteStore
from app.infrastructure.pronunciation.allosaurus import AllosaurusPronunciationScorer
from app.infrastructure.speech.faster_whisper import FasterWhisperTranscriber, default_device
from app.interfaces.evaluation import router as evaluation_router
from app.interfaces.health import router as health_router
from app.interfaces.history import router as history_router
from app.interfaces.vocabulary import router as vocabulary_router

load_dotenv()

DEFAULT_DB_PATH = "data/english_stimuler.db"


def create_app(
    evaluation_service: EvaluationService | None = None,
    history_service: HistoryService | None = None,
    vocabulary_service: VocabularyService | None = None,
) -> FastAPI:
    app = FastAPI(title="English Stimuler API")
    if evaluation_service is None or history_service is None or vocabulary_service is None:
        defaults = _default_services()
        evaluation_service = evaluation_service or defaults[0]
        history_service = history_service or defaults[1]
        vocabulary_service = vocabulary_service or defaults[2]
    app.state.evaluation_service = evaluation_service
    app.state.history_service = history_service
    app.state.vocabulary_service = vocabulary_service
    app.include_router(health_router)
    app.include_router(evaluation_router)
    app.include_router(history_router)
    app.include_router(vocabulary_router)
    return app


def _db_path() -> str:
    path = os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path


def _default_services() -> tuple[EvaluationService, HistoryService, VocabularyService]:
    store = SQLiteStore(_db_path())
    history = HistoryService(store)
    vocabulary = VocabularyService(store)
    evaluation = EvaluationService(
        scorer=AllosaurusPronunciationScorer(),
        grammar_checker=LanguageToolGrammarChecker(),
        feedback_provider=OpenRouterFeedbackProvider(),
        speech_to_text=FasterWhisperTranscriber(device=default_device()),
        history=history,
        vocabulary=vocabulary,
    )
    return evaluation, history, vocabulary


app = create_app()
