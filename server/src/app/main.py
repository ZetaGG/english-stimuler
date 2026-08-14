from dotenv import load_dotenv
from fastapi import FastAPI

from app.application.evaluation import EvaluationService
from app.infrastructure.feedback.openrouter import OpenRouterFeedbackProvider
from app.infrastructure.grammar.languagetool import LanguageToolGrammarChecker
from app.infrastructure.pronunciation.allosaurus import AllosaurusPronunciationScorer
from app.infrastructure.speech.faster_whisper import FasterWhisperTranscriber, default_device
from app.interfaces.evaluation import router as evaluation_router
from app.interfaces.health import router as health_router

load_dotenv()


def create_app(evaluation_service: EvaluationService | None = None) -> FastAPI:
    app = FastAPI(title="English Stimuler API")
    app.state.evaluation_service = evaluation_service or _default_evaluation_service()
    app.include_router(health_router)
    app.include_router(evaluation_router)
    return app


def _default_evaluation_service() -> EvaluationService:
    return EvaluationService(
        scorer=AllosaurusPronunciationScorer(),
        grammar_checker=LanguageToolGrammarChecker(),
        feedback_provider=OpenRouterFeedbackProvider(),
        speech_to_text=FasterWhisperTranscriber(device=default_device()),
    )


app = create_app()
