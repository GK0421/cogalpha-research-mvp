"""FastAPI application factory and configuration."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cogalpha_mvp.application import (
    DatasetService,
    FactorService,
    ProjectService,
    ReportService,
    RunService,
    SettingsService,
)
from cogalpha_mvp.jobs.manager import JobManager
from cogalpha_mvp.jobs.recovery import recover_runs
from cogalpha_mvp.persistence.database import Database
from cogalpha_mvp.persistence.migrations import run_migrations
from cogalpha_mvp.product.paths import WorkspaceManager
from cogalpha_mvp.product.version import PRODUCT_NAME, PRODUCT_VERSION

logger = logging.getLogger(__name__)


class AppState:
    """Shared application state."""

    def __init__(self) -> None:
        self.workspace = WorkspaceManager()
        self.workspace.initialize()
        self.db = Database(self.workspace)
        self.db.create_tables()
        run_migrations(self.db.engine)

        self.project_service = ProjectService(self.db)
        self.dataset_service = DatasetService(self.db)
        self.factor_service = FactorService(self.db)
        self.run_service = RunService(self.db)
        self.report_service = ReportService(self.db)
        self.settings_service = SettingsService(self.db)
        self.settings_service.initialize_defaults()

        self.job_manager = JobManager(self.db, self.workspace.root, max_concurrent=1)

        # Recover interrupted runs
        recovered = recover_runs(self.run_service)
        if recovered:
            logger.info("Recovered %d interrupted runs", len(recovered))


_state: AppState | None = None


def get_state() -> AppState:
    global _state
    if _state is None:
        _state = AppState()
    return _state


def reset_state() -> None:
    global _state
    _state = None


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=PRODUCT_NAME,
        version=PRODUCT_VERSION,
        description="Local-first quantitative factor research workspace",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Security: default localhost-only CORS
    allowed_origins = [
        "http://127.0.0.1:8765",
        "http://localhost:8765",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Unified error handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred.",
                    "details": {},
                    "request_id": str(id(request)),
                }
            },
        )

    # Register routers
    from .routers import datasets, factors, health, projects, reports, results, runs, settings

    app.include_router(health.router, prefix="/api/v1", tags=["system"])
    app.include_router(projects.router, prefix="/api/v1", tags=["projects"])
    app.include_router(datasets.router, prefix="/api/v1", tags=["datasets"])
    app.include_router(factors.router, prefix="/api/v1", tags=["factors"])
    app.include_router(runs.router, prefix="/api/v1", tags=["runs"])
    app.include_router(results.router, prefix="/api/v1", tags=["results"])
    app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
    app.include_router(settings.router, prefix="/api/v1", tags=["settings"])

    return app
