from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from project.app.celery.setup import create_celery


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Actions before starting the application
    yield
    # Actions after stopping the application


def create_app() -> FastAPI:
    app = FastAPI(
        title="Binary Brute Force Team",
        description="Multi-agent system for STEM interactive content",
        lifespan=lifespan,
    )

    # Mount static files
    static_path = Path(__file__).parent / "app" / "static"
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Configure templates
    templates_path = Path(__file__).parent / "app" / "templates"
    app.state.templates = Jinja2Templates(directory=str(templates_path))

    # Import and register routers
    from project.app.routers import health_check_router
    from project.app.routers.agents import router as agents_router
    from project.app.routers.chat import router as chat_router
    from project.app.routers.educational import router as educational_router
    from project.app.routers.frontend import router as frontend_router

    app.include_router(health_check_router)
    app.include_router(frontend_router)
    app.include_router(agents_router)
    app.include_router(chat_router)
    app.include_router(educational_router)

    # Initialize Celery
    app.celery_app = create_celery()

    return app
