from fastapi import FastAPI

from app.api.datasets import router as datasets_router
from app.api.analysis_runs import router as analysis_runs_router

app = FastAPI(
    title="AI Business Analytics",
    version="0.1.0",
)

app.include_router(datasets_router)
app.include_router(analysis_runs_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "backend",
    }