
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRun


def create_analysis_run(
    db: Session,
    dataset_version_id: UUID,
) -> AnalysisRun:
    analysis_run = AnalysisRun(
        dataset_version_id=dataset_version_id,
        status="running",
        validation_result={},
        pii_result={},
        profile_result={},
        semantic_result={},
        plan_result={},
        analysis_results=[],
        discovered_insights=[],
        verified_insights=[],
        confidence_insights=[],
        scored_insights=[],
        ranked_insights=[],
        explained_insights=[],
        recommended_insights=[],
    )

    db.add(analysis_run)
    db.commit()
    db.refresh(analysis_run)

    return analysis_run


def update_analysis_run(
    db: Session,
    analysis_run: AnalysisRun,
    status: str,
    validation_result: dict | None = None,
    pii_result: dict | None = None,
    profile_result: dict | None = None,
    semantic_result: dict | None = None,
    plan_result: dict | None = None,
    analysis_results: list | None = None,
    discovered_insights: list | None = None,
    verified_insights: list | None = None,
    confidence_insights: list | None = None,
    scored_insights: list | None = None,
    ranked_insights: list | None = None,
    explained_insights: list | None = None,
    recommended_insights: list | None = None,
) -> AnalysisRun:
    analysis_run.status = status

    if validation_result is not None:
        analysis_run.validation_result = validation_result

    if pii_result is not None:
        analysis_run.pii_result = pii_result

    if profile_result is not None:
        analysis_run.profile_result = profile_result

    if semantic_result is not None:
        analysis_run.semantic_result = semantic_result

    if plan_result is not None:
        analysis_run.plan_result = plan_result

    if analysis_results is not None:
        analysis_run.analysis_results = analysis_results

    if discovered_insights is not None:
        analysis_run.discovered_insights = discovered_insights

    if verified_insights is not None:
        analysis_run.verified_insights = verified_insights

    if confidence_insights is not None:
        analysis_run.confidence_insights = confidence_insights

    if scored_insights is not None:
        analysis_run.scored_insights = scored_insights

    if ranked_insights is not None:
        analysis_run.ranked_insights = ranked_insights

    if explained_insights is not None:
        analysis_run.explained_insights = explained_insights

    if recommended_insights is not None:
        analysis_run.recommended_insights = recommended_insights

    db.commit()
    db.refresh(analysis_run)

    return analysis_run
