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
        # Mount the assets directory for scripts/styles
        if (dist_dir / "assets").exists():
            app.mount("/assets", StaticFiles(directory=dist_dir / "assets"), name="assets")
        
        # Serve other static files (favicon, icons, etc.) from dist root
        @app.get("/{file_name}", include_in_schema=False)
        async def serve_static_file(file_name: str) -> Any:
            file_path = dist_dir / file_name
            if file_path.is_file():
                return FileResponse(str(file_path))
            # If not a file, fall back to SPA index.html
            return FileResponse(str(dist_dir / "index.html"))

        @app.get("/", include_in_schema=False)
        async def serve_index() -> FileResponse:
            return FileResponse(str(dist_dir / "index.html"))

        # Catch-all for SPA routing
        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str) -> FileResponse:
            return FileResponse(str(dist_dir / "index.html"))
    
    return app


app = create_app()
