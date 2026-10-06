from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.analysis import AnalysisRun
from app.services.report_exporter import (
    build_csv_export,
    build_xlsx_export,
)

router = APIRouter(prefix="/analysis-runs", tags=["Analysis Runs"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{analysis_run_id}")
def get_analysis_run(
    analysis_run_id: UUID,
    db: Session = Depends(get_db),
):
    analysis_run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.id == analysis_run_id)
        .first()
    )

    if analysis_run is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis run not found",
        )

    return {
        "id": str(analysis_run.id),
        "dataset_version_id": str(analysis_run.dataset_version_id),
        "status": analysis_run.status,
        "validation_result": analysis_run.validation_result,
        "pii_result": analysis_run.pii_result,
        "profile_result": analysis_run.profile_result,
        "semantic_result": analysis_run.semantic_result,
        "plan_result": analysis_run.plan_result,
        "analysis_results": analysis_run.analysis_results,
        "discovered_insights": analysis_run.discovered_insights,
        "verified_insights": analysis_run.verified_insights,
        "confidence_insights": analysis_run.confidence_insights,
        "scored_insights": analysis_run.scored_insights,
        "ranked_insights": analysis_run.ranked_insights,
        "created_at": analysis_run.created_at,
        "explained_insights": analysis_run.explained_insights,
        "recommended_insights": analysis_run.recommended_insights,
    }


@router.get("/{analysis_run_id}/export/{export_format}")
def export_analysis_run(
    analysis_run_id: UUID,
    export_format: str,
    db: Session = Depends(get_db),
):
    analysis_run = (
        db.query(AnalysisRun)
        .filter(
            AnalysisRun.id
            == analysis_run_id
        )
        .first()
    )

    if analysis_run is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis run not found",
        )

    export_format = (
        export_format
        .strip()
        .lower()
    )

    base_filename = (
        f"signal-ledger-"
        f"{analysis_run.id}"
    )

    if export_format == "csv":
        content = build_csv_export(
            analysis_run.ranked_insights,
            analysis_run.explained_insights,
            analysis_run.recommended_insights,
        )

        return Response(
            content=content,
            media_type=(
                "text/csv; "
                "charset=utf-8"
            ),
            headers={
                "Content-Disposition": (
                    f'attachment; filename="'
                    f'{base_filename}.csv"'
                ),
                "X-Export-Scope": (
                    "ranked-verified-insights"
                ),
            },
        )

    if export_format == "xlsx":
        content = build_xlsx_export(
            run_id=analysis_run.id,
            dataset_version_id=(
                analysis_run
                .dataset_version_id
            ),
            status=analysis_run.status,
            created_at=(
                analysis_run.created_at
            ),
            ranked_insights=(
                analysis_run
                .ranked_insights
            ),
            explained_insights=(
                analysis_run
                .explained_insights
            ),
            recommended_insights=(
                analysis_run
                .recommended_insights
            ),
        )

        return Response(
            content=content,
            media_type=(
                "application/"
                "vnd.openxmlformats-"
                "officedocument."
                "spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": (
                    f'attachment; filename="'
                    f'{base_filename}.xlsx"'
                ),
                "X-Export-Scope": (
                    "ranked-verified-insights"
                ),
            },
        )

    raise HTTPException(
        status_code=400,
        detail=(
            "Unsupported export format. "
            "Use csv or xlsx."
        ),
    )



from app.models.dataset import DatasetVersion


@router.get("/dataset-version/{dataset_version_id}")
def get_analysis_runs_for_dataset_version(
    dataset_version_id: UUID,
    db: Session = Depends(get_db),
):
    dataset_version = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.id == dataset_version_id)
        .first()
    )

    if dataset_version is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset version not found",
        )

    analysis_runs = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.dataset_version_id == dataset_version_id)
        .order_by(AnalysisRun.created_at.desc())
        .all()
    )

    return {
        "dataset_version_id": str(dataset_version_id),
        "count": len(analysis_runs),
        "analysis_runs": [
            {
                "id": str(run.id),
                "status": run.status,
                "created_at": run.created_at,
            }
            for run in analysis_runs
        ],
    }