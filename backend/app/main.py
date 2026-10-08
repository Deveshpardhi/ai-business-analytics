import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analysis_runs import (
    router as analysis_runs_router,
)
from app.api.datasets import (
    router as datasets_router,
)
from app.core.config import settings
from app.core.logging import configure_logging


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Keep this temporarily because existing LLM
# provider adapters still read some values through
# environment lookups.
load_dotenv(PROJECT_ROOT / ".env")

configure_logging(settings.log_level)

logger = logging.getLogger(__name__)

logger.info(
    "Application configuration validated",
    extra={
        "event": "application_startup",
        "provider": settings.llm_provider,
        "llm_auto_limit":
            settings.llm_auto_explanation_limit,
        "cors_origin_count":
            len(settings.cors_origins),
    },
)


app = FastAPI(
    title="AI Business Analytics",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(datasets_router)
app.include_router(analysis_runs_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "backend",
    }
