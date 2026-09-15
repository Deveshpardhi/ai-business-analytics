from pathlib import Path

import pandas as pd

from app.services.analytics_executor import execute_analysis
from app.services.analytics_planner import build_analytics_plan
from app.services.confidence_engine import apply_confidence
from app.services.insight_discovery import discover_insights
from app.services.insight_scorer import score_insights
from app.services.insight_selector import select_top_insights
from app.services.insight_verifier import verify_insights
from app.services.semantic_detector import detect_column_role


DATA_DIR = Path(__file__).parent / "data"


def run_golden_pipeline(filename):
    file_path = DATA_DIR / filename
    df = pd.read_csv(file_path)

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

    analysis_results = [
        execute_analysis(str(file_path), analysis)
        for analysis in plan["analyses"]
    ]

    discovered = discover_insights(analysis_results)
    verified = verify_insights(discovered, analysis_results)
    confidence = apply_confidence(verified)
    scored = score_insights(confidence)
    selected = select_top_insights(scored, top_n=10)

    return discovered, verified, selected


def test_golden_no_correlation():
    discovered, verified, selected = run_golden_pipeline(
        "golden_no_correlation.csv"
    )

    assert not any(
        insight["insight_type"] == "correlation"
        for insight in discovered
    )

    assert not any(
        insight["insight_type"] == "correlation"
        for insight in verified
    )

    assert all(
        insight["verification"]["status"] == "verified"
        for insight in selected
    )


def test_golden_strong_correlation():
    discovered, verified, selected = run_golden_pipeline(
        "golden_strong_correlation.csv"
    )

    correlation_insights = [
        insight
        for insight in verified
        if insight["insight_type"] == "correlation"
    ]

    assert len(correlation_insights) == 1

    correlation = correlation_insights[0]

    assert correlation["verification"]["status"] == "verified"
    assert correlation["verification"]["sample_size"] == 12
    assert correlation["verification"]["correlation"] > 0.98
    assert correlation["verification"]["significance"] == (
        "statistically_significant"
    )

    assert any(
        insight["insight_type"] == "correlation"
        for insight in selected
    )


def test_golden_outlier():
    discovered, verified, selected = run_golden_pipeline(
        "golden_outlier.csv"
    )

    outlier_insights = [
        insight
        for insight in verified
        if insight["insight_type"] == "outlier"
    ]

    assert len(outlier_insights) == 1

    outlier = outlier_insights[0]

    assert outlier["verification"]["status"] == "verified"
    assert outlier["verification"]["measure"] == "Salary"
    assert outlier["verification"]["outlier_count"] == 1
    assert outlier["verification"]["outliers"] == [250000]

    assert any(
        insight["insight_type"] == "outlier"
        for insight in selected
    )