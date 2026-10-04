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
from app.services.analytics_executor import execute_analysis
from app.security.pii_detector import analyze_pii
from app.services.semantic_detector import infer_semantics
from app.services.insight_explainer import build_verified_evidence_context


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

def test_golden_group_difference():
    discovered, verified, selected = run_golden_pipeline(
        "golden_group_difference.csv"
    )

    discovered_group_insights = [
        insight
        for insight in discovered
        if insight["insight_type"] == "group_difference"
    ]

    assert len(discovered_group_insights) == 1

    discovered_group = discovered_group_insights[0]

    assert discovered_group["source_columns"] == [
        "Revenue",
        "Department",
    ]

    assert discovered_group["evidence"]["highest_group"] == "West"
    assert discovered_group["evidence"]["highest_value"] == 312.5

    assert discovered_group["evidence"]["lowest_group"] == "North"
    assert discovered_group["evidence"]["lowest_value"] == 112.5

    assert discovered_group["evidence"]["absolute_difference"] == 200.0

    assert (
        discovered_group["evidence"]["statistical_test"]
        == "one_way_anova"
    )

    assert discovered_group["evidence"]["p_value"] is not None
    assert discovered_group["evidence"]["p_value"] < 0.05

    verified_group_insights = [
        insight
        for insight in verified
        if insight["insight_type"] == "group_difference"
    ]

    assert len(verified_group_insights) == 1

    verified_group = verified_group_insights[0]

    assert verified_group["verification"]["status"] == "verified"

    assert any(
        insight["insight_type"] == "group_difference"
        for insight in selected
    )

def test_golden_tiny_groups_do_not_reach_final_selection():
    discovered, verified, selected = run_golden_pipeline(
        "golden_tiny_groups.csv"
    )

    discovered_group_insights = [
        insight
        for insight in discovered
        if insight["insight_type"] == "group_difference"
    ]

    # A descriptive candidate may still be discovered because
    # the deterministic group means can be calculated.
    assert len(discovered_group_insights) == 1

    verified_group_insights = [
        insight
        for insight in verified
        if insight["insight_type"] == "group_difference"
    ]

    assert len(verified_group_insights) == 1

    group_insight = verified_group_insights[0]

    assert (
        group_insight["verification"]["status"]
        == "insufficient_data"
    )

    # Insufficient statistical evidence must never become
    # a final selected business insight.
    assert not any(
        insight["insight_type"] == "group_difference"
        for insight in selected
    )

def test_golden_constant_column_does_not_produce_correlation_insight():
    discovered, verified, selected = run_golden_pipeline(
        "golden_constant_column.csv"
    )

    assert not any(
        insight["insight_type"] == "correlation"
        for insight in discovered
    )

    assert not any(
        insight["insight_type"] == "correlation"
        for insight in verified
    )

    assert not any(
        insight["insight_type"] == "correlation"
        for insight in selected
    )

def test_golden_constant_column_has_explicit_analytics_status():
    file_path = DATA_DIR / "golden_constant_column.csv"

    result = execute_analysis(
        str(file_path),
        {
            "type": "correlation",
            "columns": ["Revenue", "Cost"],
        },
    )

    assert result["type"] == "correlation"
    assert result["sample_size"] == 6

    assert result["correlation"] is None
    assert result["p_value"] is None

    assert result["status"] == "insufficient_variation"

def test_golden_correlation_drops_missing_pairs_correctly():
    file_path = DATA_DIR / "golden_missing_correlation.csv"

    result = execute_analysis(
        str(file_path),
        {
            "type": "correlation",
            "columns": ["Revenue", "Cost"],
        },
    )

    assert result["type"] == "correlation"
    assert result["status"] == "completed"

    assert result["sample_size"] == 4
    assert result["correlation"] == 1.0
    assert result["p_value"] < 0.05

def test_golden_missing_values_still_produce_verified_correlation():
    discovered, verified, selected = run_golden_pipeline(
        "golden_missing_correlation.csv"
    )

    correlation_insights = [
        insight
        for insight in verified
        if insight["insight_type"] == "correlation"
    ]

    assert len(correlation_insights) == 1

    correlation = correlation_insights[0]

    assert correlation["verification"]["status"] == "verified"
    assert correlation["verification"]["sample_size"] == 4
    assert correlation["verification"]["correlation"] == 1.0

    assert any(
        insight["insight_type"] == "correlation"
        for insight in selected
    )

def test_golden_time_series_sorts_dates_and_drops_missing_values():
    file_path = DATA_DIR / "golden_time_series.csv"

    result = execute_analysis(
        str(file_path),
        {
            "type": "time_series",
            "measure": "Revenue",
            "date": "Date",
        },
    )

    assert result["type"] == "time_series"
    assert result["measure"] == "Revenue"
    assert result["date"] == "Date"
    assert result["sample_size"] == 4
    assert result["method"] == "sorted_time_series"

    assert result["data"] == [
        {"Date": "2026-01-01", "Revenue": 100},
        {"Date": "2026-01-02", "Revenue": 200},
        {"Date": "2026-01-03", "Revenue": 300},
        {"Date": "2026-01-04", "Revenue": 400},
    ]

def test_golden_numeric_identifier_is_excluded_from_analytics_plan():
    file_path = DATA_DIR / "golden_identifier_exclusion.csv"
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

    assert semantics["columns"]["TransactionID"]["role"] == "identifier"
    assert semantics["columns"]["Revenue"]["role"] == "measure"
    assert semantics["columns"]["Cost"]["role"] == "measure"

    plan = build_analytics_plan(profile, semantics)

    assert "TransactionID" in plan["identifiers"]
    assert "TransactionID" not in plan["measures"]

    correlation_analyses = [
        analysis
        for analysis in plan["analyses"]
        if analysis["type"] == "correlation"
    ]

    assert correlation_analyses == [
        {
            "type": "correlation",
            "columns": ["Revenue", "Cost"],
            "description": (
                "Analyze the relationship between Revenue and Cost."
            ),
        }
    ]

def test_golden_pii_columns_are_excluded_before_analytics_planning():
    file_path = DATA_DIR / "golden_pii_protection.csv"

    pii_scan = analyze_pii(str(file_path))

    assert pii_scan["pii_detected"] is True

    assert set(pii_scan["protected_columns"]) == {
        "CustomerName",
        "Email",
        "Phone",
    }

    assert set(pii_scan["safe_columns"]) == {
        "Revenue",
        "Cost",
    }

    semantics = infer_semantics(
        str(file_path),
        pii_scan["protected_columns"],
    )

    assert "CustomerName" not in semantics["columns"]
    assert "Email" not in semantics["columns"]
    assert "Phone" not in semantics["columns"]

    assert semantics["columns"]["Revenue"]["role"] == "measure"
    assert semantics["columns"]["Cost"]["role"] == "measure"

    profile = {
        "rows": 6,
        "columns": len(semantics["columns"]),
    }

    plan = build_analytics_plan(profile, semantics)

    planned_columns = str(plan)

    assert "CustomerName" not in planned_columns
    assert "Email" not in planned_columns
    assert "Phone" not in planned_columns

    assert "Revenue" in plan["measures"]
    assert "Cost" in plan["measures"]

def test_golden_pii_protected_dataset_allows_only_safe_analytics():
    file_path = DATA_DIR / "golden_pii_protection.csv"

    pii_scan = analyze_pii(str(file_path))

    result = execute_analysis(
        str(file_path),
        {
            "type": "correlation",
            "columns": ["Revenue", "Cost"],
        },
        protected_columns=pii_scan["protected_columns"],
    )

    assert result["type"] == "correlation"
    assert result["status"] == "completed"
    assert result["columns"] == ["Revenue", "Cost"]
    assert result["sample_size"] == 6

def test_golden_llm_boundary_excludes_raw_and_unapproved_fields():
    insight = {
        "insight_type": "correlation",
        "title": "Revenue and Cost are strongly related",
        "source_columns": ["Revenue", "Cost"],
        "method": "pearson_correlation",
        "evidence": {
            "correlation": 1.0,
            "p_value": 0.0,
            "sample_size": 6,
        },
        "calculation": {
            "formula": "should not cross boundary",
        },
        "verification": {
            "status": "verified",
            "correlation": 1.0,
            "p_value": 0.0,
            "sample_size": 6,
        },
        "confidence": {
            "level": "high",
        },
        "limitations": [
            "Correlation does not imply causation.",
        ],

        # Deliberately forbidden/unapproved data
        "raw_dataset": [
            {
                "CustomerName": "Aarav Sharma",
                "Email": "aarav@example.com",
                "Phone": "9876543210",
            }
        ],
        "lineage": {
            "private": "internal",
        },
        "recommendation": {
            "private": "internal",
        },
    }

    context = build_verified_evidence_context(insight)

    assert "raw_dataset" not in context
    assert "calculation" not in context
    assert "confidence" not in context
    assert "lineage" not in context
    assert "recommendation" not in context

    serialized = str(context)

    assert "aarav@example.com" not in serialized
    assert "9876543210" not in serialized
    assert "Aarav Sharma" not in serialized