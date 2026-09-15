import pandas as pd

from app.services.semantic_detector import detect_column_role
from app.services.analytics_planner import build_analytics_plan
from app.services.analytics_executor import execute_analysis
from app.services.insight_discovery import discover_insights
from app.services.insight_verifier import verify_insights
from app.services.confidence_engine import apply_confidence
from app.services.insight_scorer import score_insights
from app.services.insight_selector import select_top_insights


def test_phase1_pipeline_end_to_end(tmp_path):
    file_path = tmp_path / "business_dataset.csv"

    df = pd.DataFrame({
        "EmployeeID": [
            1001, 1002, 1003, 1004, 1005, 1006,
            1007, 1008, 1009, 1010, 1011, 1012
        ],
        "Age": [
            22, 24, 26, 28, 30, 32,
            34, 36, 38, 40, 42, 44
        ],
        "Department": [
            "HR", "HR", "HR", "IT", "IT", "IT",
            "Finance", "Finance", "Finance", "Marketing",
            "Marketing", "Marketing"
        ],
        "Salary": [
            45000, 47000, 49000,
            60000, 62000, 64000,
            52000, 54000, 56000,
            70000, 72000, 74000
        ],
        "JoiningDate": [
            "2025-01-01", "2025-01-02", "2025-01-03",
            "2025-01-04", "2025-01-05", "2025-01-06",
            "2025-01-07", "2025-01-08", "2025-01-09",
            "2025-01-10", "2025-01-11", "2025-01-12"
        ],
    })

    df.to_csv(file_path, index=False)

    # 1. Semantic detection
    assert detect_column_role(
        "EmployeeID",
        df["EmployeeID"]
    ) == "identifier"

    assert detect_column_role(
        "JoiningDate",
        df["JoiningDate"]
    ) == "date"

    # 2. Build analytics plan
    profile = {
        "rows": len(df),
        "columns": len(df.columns),
    }

    semantics = {
        "columns": {
            column: {
                "role": detect_column_role(column, df[column]),
                "dtype": str(df[column].dtype),
            }
            for column in df.columns
        }
    }

    plan = build_analytics_plan(profile, semantics)

    correlation_analyses = [
        analysis
        for analysis in plan["analyses"]
        if analysis["type"] == "correlation"
    ]

    assert all(
        "EmployeeID" not in analysis["columns"]
        for analysis in correlation_analyses
    )

    assert any(
        analysis["type"] == "time_series"
        and analysis["measure"] == "Salary"
        and analysis["date"] == "JoiningDate"
        for analysis in plan["analyses"]
    )

    # 3. Execute all planned analyses
    analysis_results = []

    for analysis in plan["analyses"]:
        result = execute_analysis(
            str(file_path),
            analysis,
        )
        analysis_results.append(result)

    # 4. Time series must execute successfully
    time_series_results = [
        result
        for result in analysis_results
        if result["type"] == "time_series"
    ]

    assert len(time_series_results) == 1
    assert time_series_results[0]["sample_size"] == 12

    # 5. Discover insights
    discovered_insights = discover_insights(
        analysis_results
    )

    assert len(discovered_insights) > 0

    # 6. Verify insights
    verified_insights = verify_insights(
        discovered_insights,
        analysis_results,
    )

    # 7. Calculate confidence
    confidence_insights = apply_confidence(
        verified_insights
    )

    # 8. Score insights
    scored_insights = score_insights(
        confidence_insights
    )

    # 9. Only verified insights may reach final ranking
    ranked_insights = select_top_insights(
        scored_insights,
        top_n=10,
    )

    assert len(ranked_insights) > 0

    assert all(
        insight.get("verification", {}).get("status") == "verified"
        for insight in ranked_insights
    )


def test_unverified_insight_cannot_reach_final_selection():
    insights = [
        {
            "insight_type": "correlation",
            "title": "Invalid correlation",
            "source_columns": ["Age", "Salary"],
            "method": "pearson_correlation",
            "evidence": {
                "correlation": 0.99,
                "p_value": 0.001,
                "sample_size": 12,
            },
            "calculation": {},
            "verification": {
                "status": "failed",
            },
            "confidence": {},
            "limitations": [],
        },
        {
            "insight_type": "correlation",
            "title": "Valid correlation",
            "source_columns": ["Age", "Salary"],
            "method": "pearson_correlation",
            "evidence": {
                "correlation": 0.90,
                "p_value": 0.001,
                "sample_size": 12,
            },
            "calculation": {},
            "verification": {
                "status": "verified",
            },
            "confidence": {},
            "limitations": [],
        },
    ]

    confidence_insights = apply_confidence(insights)
    scored_insights = score_insights(confidence_insights)

    selected = select_top_insights(
        scored_insights,
        top_n=10,
    )

    assert len(selected) == 1
    assert selected[0]["title"] == "Valid correlation"
    assert all(
        insight["verification"]["status"] == "verified"
        for insight in selected
    )