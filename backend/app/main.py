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


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Keep this temporarily because existing LLM
# provider adapters still read some values through
# environment lookups.
load_dotenv(PROJECT_ROOT / ".env")


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
