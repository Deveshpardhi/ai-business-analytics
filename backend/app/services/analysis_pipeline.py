from uuid import UUID

from app.services.insight_explainer import explain_insight, mock_llm
from app.services.recommendation_engine import (
    recommend_insight,
    mock_recommendation_llm,
)
from app.services.validator import validate_dataset
from app.security.pii_detector import analyze_pii
from app.services.profiler import profile_dataset
from app.services.semantic_detector import infer_semantics
from app.services.analytics_planner import build_analytics_plan
from app.services.analytics_executor import execute_analysis
from app.services.insight_discovery import discover_insights
from app.services.insight_verifier import verify_insights
from app.services.confidence_engine import apply_confidence
from app.services.insight_scorer import score_insights
from app.services.insight_selector import select_top_insights

from app.db.database import SessionLocal
from app.models.dataset import DatasetVersion
from app.services.analysis_run_service import (
    create_analysis_run,
    update_analysis_run,
)


def add_lineage(
    insights: list[dict],
    dataset_id: str | None,
    dataset_version_id: str | None,
    analysis_run_id: str | None,
) -> list[dict]:
    results = []

    for insight in insights:
        results.append(
            {
                **insight,
                "lineage": {
                    "dataset_id": dataset_id,
                    "dataset_version_id": dataset_version_id,
                    "analysis_run_id": analysis_run_id,
                },
            }
        )

    return results


def determine_analysis_run_status(analysis_results: list[dict]) -> str:
    """Return a persisted status that reflects every requested analysis."""
    if any(result.get("status") == "failed" for result in analysis_results):
        return "partially_completed"
    return "completed"


def run_phase1_analysis(
    file_path: str,
    dataset_id: str | None = None,
    dataset_version_id: str | None = None,
) -> dict:

    if dataset_version_id is None:
        raise ValueError(
            "dataset_version_id is required to run analysis."
        )

    db = SessionLocal()
    analysis_run = None

    try:
        dataset_version_uuid = UUID(dataset_version_id)

        dataset_version = (
            db.query(DatasetVersion)
            .filter(DatasetVersion.id == dataset_version_uuid)
            .first()
        )

        if dataset_version is None:
            raise ValueError("Dataset version not found.")

        dataset_id = str(dataset_version.dataset_id)

        analysis_run = create_analysis_run(
            db,
            dataset_version_uuid,
        )

        analysis_run_id = str(analysis_run.id)

        validation = validate_dataset(file_path)

        if not validation["valid"]:
            update_analysis_run(
                db,
                analysis_run,
                status="failed",
                validation_result=validation,
            )

            return {
                "status": "failed",
                "stage": "validation",
                "validation": validation,
                "analysis_run_id": analysis_run_id,
            }

        pii_scan = analyze_pii(file_path)

        profile = profile_dataset(
            file_path,
            pii_scan["protected_columns"],
        )

        semantics = infer_semantics(
            file_path,
            pii_scan["protected_columns"],
        )

        update_analysis_run(
            db,
            analysis_run,
            status="running",
            validation_result=validation,
            pii_result=pii_scan,
            profile_result=profile,
            semantic_result=semantics,
        )

        plan = build_analytics_plan(
            profile,
            semantics,
        )

        analysis_results = []

        for analysis in plan["analyses"]:
            try:
                result = execute_analysis(
                    file_path,
                    analysis,
                    pii_scan["protected_columns"],
                )

                analysis_results.append(result)

            except Exception as exc:
                analysis_results.append(
                    {
                        "type": analysis["type"],
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        insights = discover_insights(
            analysis_results
        )

        verified_insights = verify_insights(
            insights,
            analysis_results,
        )

        confidence_insights = apply_confidence(
            verified_insights
        )

        scored_insights = score_insights(
            confidence_insights
        )

        ranked_insights = select_top_insights(
            scored_insights,
            top_n=10,
        )

        explained_insights = []

        for insight in ranked_insights:
            explanation = explain_insight(
                insight,
                mock_llm,
            )

            explained_insights.append(
                {
                    **insight,
                    "explanation": explanation,
                }
            )

        recommended_insights = []

        for insight in explained_insights:
            recommendation = recommend_insight(
                insight,
                mock_recommendation_llm,
            )

            recommended_insights.append(
                {
                    **insight,
                    "recommendation": recommendation,
                }
            )

        explained_insights = add_lineage(
            explained_insights,
            dataset_id,
            dataset_version_id,
            analysis_run_id,
        )

        recommended_insights = add_lineage(
            recommended_insights,
            dataset_id,
            dataset_version_id,
            analysis_run_id,
        )

        ranked_insights = add_lineage(
            ranked_insights,
            dataset_id,
            dataset_version_id,
            analysis_run_id,
        )

        run_status = determine_analysis_run_status(analysis_results)

        update_analysis_run(
            db,
            analysis_run,
            status=run_status,
            validation_result=validation,
            pii_result=pii_scan,
            profile_result=profile,
            semantic_result=semantics,
            plan_result=plan,
            analysis_results=analysis_results,
            discovered_insights=insights,
            verified_insights=verified_insights,
            confidence_insights=confidence_insights,
            scored_insights=scored_insights,
            ranked_insights=ranked_insights,
            explained_insights=explained_insights,
            recommended_insights=recommended_insights,
        )

        return {
            "status": run_status,
            "analysis_run_id": analysis_run_id,
            "validation": validation,
            "pii_scan": pii_scan,
            "profile": profile,
            "semantics": semantics,
            "plan": plan,
            "analysis_results": analysis_results,
            "insights": insights,
            "verified_insights": verified_insights,
            "confidence_insights": confidence_insights,
            "scored_insights": scored_insights,
            "ranked_insights": ranked_insights,
            "explained_insights": explained_insights,
            "recommended_insights": recommended_insights,
        }

    except Exception:

        if analysis_run is not None:
            update_analysis_run(
                db,
                analysis_run,
                status="failed",
            )

        raise

    finally:
        db.close()
