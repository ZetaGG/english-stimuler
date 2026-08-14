from fastapi import FastAPI

from app.interfaces.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="English Stimuler API")
    app.include_router(health_router)
    return app


app = create_app()
