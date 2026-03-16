"""PRism-AI FastAPI application entry point."""
from __future__ import annotations
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routes import router
from ..config import Settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("PRism-AI starting up...")
    yield
    logger.info("PRism-AI shutting down...")


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(
        title="PRism-AI",
        description="Free & Open-Source AI-powered Pull Request Review Agent",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(router, prefix="/api/v1")

    # Serve React frontend
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    dist_dir = frontend_dir / "dist"
    
    if dist_dir.exists():
        app.mount("/assets", StaticFiles(directory=dist_dir / "assets"), name="assets")
        @app.get("/", include_in_schema=False)
        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa_dist(full_path: str = "") -> FileResponse:
            index = dist_dir / "index.html"
            return FileResponse(str(index))
    elif frontend_dir.exists():
        @app.get("/", include_in_schema=False)
        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa_dev(full_path: str = "") -> FileResponse:
            index = frontend_dir / "index.html"
            return FileResponse(str(index))

    return app


app = create_app()
