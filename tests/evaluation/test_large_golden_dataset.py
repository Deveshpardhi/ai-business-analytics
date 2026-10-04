from pathlib import Path

import pandas as pd
import pytest

from app.security.pii_detector import analyze_pii
from app.services.analytics_executor import execute_analysis
from app.services.analytics_planner import build_analytics_plan
from app.services.semantic_detector import infer_semantics


from tests.evaluation.golden_large_factory import (
    ROW_COUNT,
    build_large_golden_dataset,
)

@pytest.fixture(scope="module")
def large_golden_file(tmp_path_factory):
    directory = tmp_path_factory.mktemp(
        "large_golden"
    )

    file_path = (
        directory
        / "golden_large_business_100k.csv"
    )

    df = build_large_golden_dataset()
    df.to_csv(file_path, index=False)

    return file_path


def test_large_golden_dataset_contract(
    large_golden_file,
):
    df = pd.read_csv(
        large_golden_file
    )

    assert df.shape == (
        100_000,
        20,
    )

    assert df["TransactionID"].is_unique

    assert df["TransactionID"].iloc[0] == 1
    assert df["TransactionID"].iloc[-1] == 100_000

    assert (
        df["TransactionDate"].min()
        >= "2023-01-01"
    )

    assert (
        df["TransactionDate"].max()
        <= "2025-12-31"
    )

    assert int(
        df.isna().sum().sum()
    ) == 1500


def test_large_golden_semantics_and_plan(
    large_golden_file,
):
    pii = analyze_pii(
        str(large_golden_file)
    )

    assert pii["pii_detected"] is False
    assert pii["protected_columns"] == {}

    semantics = infer_semantics(
        str(large_golden_file),
        pii["protected_columns"],
    )

    assert (
        semantics["columns"]["TransactionID"]["role"]
        == "identifier"
    )

    assert (
        semantics["columns"]["CustomerID"]["role"]
        == "identifier"
    )

    assert (
        semantics["columns"]["TransactionDate"]["role"]
        == "date"
    )

    assert (
        semantics["columns"]["Revenue"]["role"]
        == "measure"
    )

    assert (
        semantics["columns"]["Department"]["role"]
        == "dimension"
    )

    profile = {
        "rows": ROW_COUNT,
        "columns": 20,
    }

    plan = build_analytics_plan(
        profile,
        semantics,
    )

    assert "TransactionID" in plan["identifiers"]
    assert "CustomerID" in plan["identifiers"]

    assert "TransactionID" not in plan["measures"]
    assert "CustomerID" not in plan["measures"]

    for analysis in plan["analyses"]:
        assert "TransactionID" not in str(analysis)
        assert "CustomerID" not in str(analysis)


def test_large_golden_anova_underflow(
    large_golden_file,
):
    result = execute_analysis(
        str(large_golden_file),
        {
            "type": "group_comparison",
            "measure": "UnitPrice",
            "dimension": "Department",
        },
    )

    test = result["statistical_test"]

    assert result["type"] == "group_comparison"
    assert test["test"] == "one_way_anova"

    assert test["sample_size"] == 100_000
    assert test["group_count"] == 4

    assert test["p_value"] == 0.0
    assert test["p_value_underflow"] is True

    assert test["statistic"] > 1000


def test_large_golden_revenue_cost_correlation(
    large_golden_file,
):
    result = execute_analysis(
        str(large_golden_file),
        {
            "type": "correlation",
            "columns": [
                "Revenue",
                "Cost",
            ],
        },
    )

    assert result["status"] == "completed"
    assert result["sample_size"] == 100_000

    assert result["correlation"] > 0.99

    assert result["p_value"] == 0.0


def test_large_golden_time_series(
    large_golden_file,
):
    result = execute_analysis(
        str(large_golden_file),
        {
            "type": "time_series",
            "measure": "Revenue",
            "date": "TransactionDate",
        },
    )

    assert result["sample_size"] == 100_000

    assert (
        result["data"][0]["TransactionDate"]
        >= "2023-01-01"
    )

    assert (
        result["data"][-1]["TransactionDate"]
        <= "2025-12-31"
    )


def test_large_golden_is_reproducible():
    first = build_large_golden_dataset()
    second = build_large_golden_dataset()

    pd.testing.assert_frame_equal(
        first,
        second,
    )

def test_large_golden_correlation_survives_full_pipeline(
    large_golden_file,
):
    from app.services.insight_discovery import discover_insights
    from app.services.insight_verifier import verify_insights
    from app.services.confidence_engine import apply_confidence
    from app.services.insight_scorer import score_insights
    from app.services.insight_selector import select_top_insights

    analysis_result = execute_analysis(
        str(large_golden_file),
        {
            "type": "correlation",
            "columns": [
                "Revenue",
                "Cost",
            ],
        },
    )

    analysis_results = [
        analysis_result,
    ]

    discovered = discover_insights(
        analysis_results
    )

    correlation_insights = [
        insight
        for insight in discovered
        if (
            insight["insight_type"]
            == "correlation"
            and insight["source_columns"]
            == ["Revenue", "Cost"]
        )
    ]

    assert len(correlation_insights) == 1

    verified = verify_insights(
        discovered,
        analysis_results,
    )

    verified_correlations = [
        insight
        for insight in verified
        if (
            insight["insight_type"]
            == "correlation"
            and insight["source_columns"]
            == ["Revenue", "Cost"]
        )
    ]

    assert len(verified_correlations) == 1

    insight = verified_correlations[0]

    assert (
        insight["verification"]["status"]
        == "verified"
    )

    assert (
        insight["evidence"]["sample_size"]
        == 100_000
    )

    assert (
        insight["evidence"]["correlation"]
        > 0.99
    )

    confident = apply_confidence(
        verified
    )

    scored = score_insights(
        confident
    )

    selected = select_top_insights(
        scored,
        top_n=10,
    )

    selected_correlations = [
        insight
        for insight in selected
        if (
            insight["insight_type"]
            == "correlation"
            and insight["source_columns"]
            == ["Revenue", "Cost"]
        )
    ]

    assert len(selected_correlations) == 1

def test_large_golden_group_difference_survives_full_pipeline(
    large_golden_file,
):
    from app.services.insight_discovery import discover_insights
    from app.services.insight_verifier import verify_insights
    from app.services.confidence_engine import apply_confidence
    from app.services.insight_scorer import score_insights
    from app.services.insight_selector import select_top_insights

    analysis_result = execute_analysis(
        str(large_golden_file),
        {
            "type": "group_comparison",
            "measure": "UnitPrice",
            "dimension": "Department",
        },
    )

    statistical_test = analysis_result["statistical_test"]

    assert statistical_test["test"] == "one_way_anova"
    assert statistical_test["sample_size"] == 100_000
    assert statistical_test["group_count"] == 4
    assert statistical_test["p_value"] == 0.0
    assert statistical_test["p_value_underflow"] is True

    analysis_results = [analysis_result]

    discovered = discover_insights(
        analysis_results
    )

    group_insights = [
        insight
        for insight in discovered
        if (
            insight["insight_type"]
            == "group_difference"
            and insight["source_columns"]
            == ["UnitPrice", "Department"]
        )
    ]

    assert len(group_insights) == 1

    discovered_insight = group_insights[0]

    assert (
        discovered_insight["evidence"]["statistical_test"]
        == "one_way_anova"
    )

    assert discovered_insight["evidence"]["p_value"] == 0.0

    verified = verify_insights(
        discovered,
        analysis_results,
    )

    verified_groups = [
        insight
        for insight in verified
        if (
            insight["insight_type"]
            == "group_difference"
            and insight["source_columns"]
            == ["UnitPrice", "Department"]
        )
    ]

    assert len(verified_groups) == 1

    insight = verified_groups[0]

    assert (
        insight["verification"]["status"]
        == "verified"
    )

    confident = apply_confidence(
        verified
    )

    scored = score_insights(
        confident
    )

    selected = select_top_insights(
        scored,
        top_n=10,
    )

    selected_groups = [
        insight
        for insight in selected
        if (
            insight["insight_type"]
            == "group_difference"
            and insight["source_columns"]
            == ["UnitPrice", "Department"]
        )
    ]

    assert len(selected_groups) == 1

def test_large_golden_constant_column_is_not_selected(
    large_golden_file,
    tmp_path,
):
    from app.services.insight_discovery import discover_insights
    from app.services.insight_verifier import verify_insights
    from app.services.confidence_engine import apply_confidence
    from app.services.insight_scorer import score_insights
    from app.services.insight_selector import select_top_insights

    df = pd.read_csv(large_golden_file)

    # Add a numeric column with zero variance.
    df["ConstantMetric"] = 100.0

    file_path = tmp_path / "large_constant_metric.csv"
    df.to_csv(file_path, index=False)

    analysis_result = execute_analysis(
        str(file_path),
        {
            "type": "correlation",
            "columns": [
                "Revenue",
                "ConstantMetric",
            ],
        },
    )

    assert analysis_result["type"] == "correlation"
    assert analysis_result["sample_size"] == 100_000

    assert analysis_result["status"] == "insufficient_variation"
    assert analysis_result["correlation"] is None
    assert analysis_result["p_value"] is None

    analysis_results = [analysis_result]

    discovered = discover_insights(
        analysis_results
    )

    correlation_insights = [
        insight
        for insight in discovered
        if insight["insight_type"] == "correlation"
    ]

    assert correlation_insights == []

    verified = verify_insights(
        discovered,
        analysis_results,
    )

    confident = apply_confidence(
        verified
    )

    scored = score_insights(
        confident
    )

    selected = select_top_insights(
        scored,
        top_n=10,
    )

    selected_correlations = [
        insight
        for insight in selected
        if insight["insight_type"] == "correlation"
    ]

    assert selected_correlations == []

def test_large_golden_correlation_drops_missing_pairs_correctly(
    large_golden_file,
    tmp_path,
):
    df = pd.read_csv(large_golden_file)

    # Introduce deterministic missing values into Revenue and Cost.
    revenue_missing = df.index[:1000]
    cost_missing = df.index[1000:2500]

    df.loc[revenue_missing, "Revenue"] = pd.NA
    df.loc[cost_missing, "Cost"] = pd.NA

    file_path = tmp_path / "large_missing_pairs.csv"
    df.to_csv(file_path, index=False)

    result = execute_analysis(
        str(file_path),
        {
            "type": "correlation",
            "columns": [
                "Revenue",
                "Cost",
            ],
        },
    )

    assert result["type"] == "correlation"
    assert result["status"] == "completed"

    # 1000 missing Revenue rows
    # + 1500 different missing Cost rows
    # = 2500 invalid pairs
    assert result["sample_size"] == 97_500

    assert result["correlation"] > 0.99
    assert result["p_value"] == 0.0

def test_large_golden_planner_is_reproducible():
    from app.security.pii_detector import analyze_pii
    from app.services.semantic_detector import infer_semantics
    from app.services.analytics_planner import build_analytics_plan

    first_df = build_large_golden_dataset()
    second_df = build_large_golden_dataset()

    first_path = Path("tests/evaluation/.tmp_large_first.csv")
    second_path = Path("tests/evaluation/.tmp_large_second.csv")

    try:
        first_df.to_csv(first_path, index=False)
        second_df.to_csv(second_path, index=False)

        first_pii = analyze_pii(str(first_path))
        second_pii = analyze_pii(str(second_path))

        first_semantics = infer_semantics(
            str(first_path),
            first_pii["protected_columns"],
        )

        second_semantics = infer_semantics(
            str(second_path),
            second_pii["protected_columns"],
        )

        first_plan = build_analytics_plan(
            {
                "rows": 100_000,
                "columns": 20,
            },
            first_semantics,
        )

        second_plan = build_analytics_plan(
            {
                "rows": 100_000,
                "columns": 20,
            },
            second_semantics,
        )

        assert first_semantics == second_semantics
        assert first_plan == second_plan

        assert first_plan["measures"] == [
            "UnitsSold",
            "UnitPrice",
            "Discount",
            "Revenue",
            "Cost",
            "Profit",
        ]

        assert first_plan["dimensions"] == [
            "Gender",
            "Region",
            "Department",
            "ProductCategory",
            "Product",
            "SalesChannel",
            "Returned",
        ]

        assert first_plan["dates"] == [
            "TransactionDate",
        ]

        assert first_plan["identifiers"] == [
            "TransactionID",
            "CustomerID",
        ]

        counts = {}

        for analysis in first_plan["analyses"]:
            analysis_type = analysis["type"]
            counts[analysis_type] = (
                counts.get(analysis_type, 0) + 1
            )

        assert counts == {
            "descriptive_statistics": 6,
            "group_comparison": 42,
            "time_series": 6,
            "correlation": 45,
        }

        assert len(first_plan["analyses"]) == 99

    finally:
        first_path.unlink(missing_ok=True)
        second_path.unlink(missing_ok=True)

def test_large_golden_planner_is_reproducible(
    tmp_path,
):
    first_df = build_large_golden_dataset()
    second_df = build_large_golden_dataset()

    first_path = tmp_path / "large_first.csv"
    second_path = tmp_path / "large_second.csv"

    first_df.to_csv(first_path, index=False)
    second_df.to_csv(second_path, index=False)

    first_pii = analyze_pii(str(first_path))
    second_pii = analyze_pii(str(second_path))

    first_semantics = infer_semantics(
        str(first_path),
        first_pii["protected_columns"],
    )

    second_semantics = infer_semantics(
        str(second_path),
        second_pii["protected_columns"],
    )

    first_plan = build_analytics_plan(
        {
            "rows": 100_000,
            "columns": 20,
        },
        first_semantics,
    )

    second_plan = build_analytics_plan(
        {
            "rows": 100_000,
            "columns": 20,
        },
        second_semantics,
    )

    assert first_semantics == second_semantics
    assert first_plan == second_plan

    counts = {}

    for analysis in first_plan["analyses"]:
        analysis_type = analysis["type"]
        counts[analysis_type] = (
            counts.get(analysis_type, 0) + 1
        )

    assert counts == {
        "descriptive_statistics": 6,
        "group_comparison": 42,
        "time_series": 6,
        "correlation": 45,
    }

    assert len(first_plan["analyses"]) == 99

def test_large_golden_core_analytics_finish_within_reasonable_time(
    large_golden_file,
):
    """
    Performance smoke test.

    This is intentionally not a strict benchmark.
    It exists to catch severe performance regressions.
    """
    import time

    analyses = [
        {
            "type": "descriptive_statistics",
            "measure": "Revenue",
        },
        {
            "type": "group_comparison",
            "measure": "UnitPrice",
            "dimension": "Department",
        },
        {
            "type": "correlation",
            "columns": [
                "Revenue",
                "Cost",
            ],
        },
        {
            "type": "time_series",
            "measure": "Revenue",
            "date": "TransactionDate",
        },
    ]

    start = time.perf_counter()

    results = [
        execute_analysis(
            str(large_golden_file),
            analysis,
        )
        for analysis in analyses
    ]

    elapsed = time.perf_counter() - start

    assert len(results) == 4

    # Generous CI-safe upper bound.
    assert elapsed < 5.0


def test_large_golden_numeric_semantic_roles_are_stable(
    large_golden_file,
):
    """
    Numeric business fields that are not primary measures
    should retain their current generic numeric role.
    """
    pii = analyze_pii(
        str(large_golden_file)
    )

    semantics = infer_semantics(
        str(large_golden_file),
        pii["protected_columns"],
    )

    expected_numeric = [
        "Age",
        "CustomerSatisfaction",
        "DeliveryDays",
        "EmployeeCount",
    ]

    for column in expected_numeric:
        assert (
            semantics["columns"][column]["role"]
            == "numeric"
        )

    expected_measures = [
        "UnitsSold",
        "UnitPrice",
        "Discount",
        "Revenue",
        "Cost",
        "Profit",
    ]

    for column in expected_measures:
        assert (
            semantics["columns"][column]["role"]
            == "measure"
        )


def test_large_golden_generic_numeric_columns_are_not_measures(
    large_golden_file,
):
    pii = analyze_pii(
        str(large_golden_file)
    )

    semantics = infer_semantics(
        str(large_golden_file),
        pii["protected_columns"],
    )

    plan = build_analytics_plan(
        {
            "rows": 100_000,
            "columns": 20,
        },
        semantics,
    )

    for column in [
        "Age",
        "CustomerSatisfaction",
        "DeliveryDays",
        "EmployeeCount",
    ]:
        assert column not in plan["measures"]

    assert plan["measures"] == [
        "UnitsSold",
        "UnitPrice",
        "Discount",
        "Revenue",
        "Cost",
        "Profit",
    ]


def test_large_golden_identifiers_never_enter_correlation_plan(
    large_golden_file,
):
    pii = analyze_pii(
        str(large_golden_file)
    )

    semantics = infer_semantics(
        str(large_golden_file),
        pii["protected_columns"],
    )

    plan = build_analytics_plan(
        {
            "rows": 100_000,
            "columns": 20,
        },
        semantics,
    )

    correlations = [
        analysis
        for analysis in plan["analyses"]
        if analysis["type"] == "correlation"
    ]

    assert correlations

    for analysis in correlations:
        columns = analysis["columns"]

        assert "TransactionID" not in columns
        assert "CustomerID" not in columns


def test_large_golden_correlation_plan_has_no_duplicate_pairs(
    large_golden_file,
):
    pii = analyze_pii(
        str(large_golden_file)
    )

    semantics = infer_semantics(
        str(large_golden_file),
        pii["protected_columns"],
    )

    plan = build_analytics_plan(
        {
            "rows": 100_000,
            "columns": 20,
        },
        semantics,
    )

    correlations = [
        analysis
        for analysis in plan["analyses"]
        if analysis["type"] == "correlation"
    ]

    normalized_pairs = [
        tuple(sorted(analysis["columns"]))
        for analysis in correlations
    ]

    assert len(normalized_pairs) == len(
        set(normalized_pairs)
    )

    assert len(correlations) == 45


def test_correlation_with_one_valid_pair_is_insufficient_data(
    tmp_path,
):
    df = pd.DataFrame(
        {
            "Revenue": [
                100.0,
                None,
                None,
                None,
            ],
            "Cost": [
                80.0,
                90.0,
                None,
                None,
            ],
        }
    )

    file_path = (
        tmp_path
        / "correlation_one_valid_pair.csv"
    )

    df.to_csv(
        file_path,
        index=False,
    )

    result = execute_analysis(
        str(file_path),
        {
            "type": "correlation",
            "columns": [
                "Revenue",
                "Cost",
            ],
        },
    )

    assert result["type"] == "correlation"
    assert result["sample_size"] == 1
    assert result["correlation"] is None
    assert result["p_value"] is None
    assert result["status"] == "insufficient_data"


def test_correlation_with_zero_valid_pairs_is_insufficient_data(
    tmp_path,
):
    df = pd.DataFrame(
        {
            "Revenue": [
                100.0,
                200.0,
                None,
            ],
            "Cost": [
                None,
                None,
                300.0,
            ],
        }
    )

    file_path = (
        tmp_path
        / "correlation_zero_valid_pairs.csv"
    )

    df.to_csv(
        file_path,
        index=False,
    )

    result = execute_analysis(
        str(file_path),
        {
            "type": "correlation",
            "columns": [
                "Revenue",
                "Cost",
            ],
        },
    )

    assert result["sample_size"] == 0
    assert result["correlation"] is None
    assert result["p_value"] is None
    assert result["status"] == "insufficient_data"


def test_constant_columns_on_both_sides_are_insufficient_variation(
    tmp_path,
):
    df = pd.DataFrame(
        {
            "Revenue": [
                100.0,
                100.0,
                100.0,
                100.0,
            ],
            "Cost": [
                50.0,
                50.0,
                50.0,
                50.0,
            ],
        }
    )

    file_path = (
        tmp_path
        / "both_constant.csv"
    )

    df.to_csv(
        file_path,
        index=False,
    )

    result = execute_analysis(
        str(file_path),
        {
            "type": "correlation",
            "columns": [
                "Revenue",
                "Cost",
            ],
        },
    )

    assert result["sample_size"] == 4
    assert result["correlation"] is None
    assert result["p_value"] is None

    assert (
        result["status"]
        == "insufficient_variation"
    )


def test_large_golden_missing_counts_are_exact(
    large_golden_file,
):
    df = pd.read_csv(
        large_golden_file
    )

    expected_missing = {
        "Age": 250,
        "Gender": 250,
        "Discount": 250,
        "CustomerSatisfaction": 250,
        "DeliveryDays": 250,
        "EmployeeCount": 250,
    }

    for column, expected in expected_missing.items():
        assert (
            int(df[column].isna().sum())
            == expected
        )

    protected_key_columns = [
        "TransactionID",
        "TransactionDate",
        "CustomerID",
        "Revenue",
        "Cost",
        "Profit",
    ]

    for column in protected_key_columns:
        assert df[column].isna().sum() == 0

    assert int(
        df.isna().sum().sum()
    ) == 1500


def test_large_golden_transaction_ids_are_complete_sequence(
    large_golden_file,
):
    df = pd.read_csv(
        large_golden_file
    )

    ids = df["TransactionID"]

    assert len(ids) == 100_000
    assert ids.is_unique
    assert ids.min() == 1
    assert ids.max() == 100_000

    assert ids.tolist() == list(
        range(1, 100_001)
    )


def test_large_golden_date_contract(
    large_golden_file,
):
    df = pd.read_csv(
        large_golden_file
    )

    dates = pd.to_datetime(
        df["TransactionDate"],
        errors="raise",
    )

    assert dates.notna().all()

    assert (
        dates.min().strftime("%Y-%m-%d")
        >= "2023-01-01"
    )

    assert (
        dates.max().strftime("%Y-%m-%d")
        <= "2025-12-31"
    )

    assert dates.dt.year.min() == 2023
    assert dates.dt.year.max() == 2025


def test_large_golden_no_pii_is_deterministic(
    large_golden_file,
):
    first = analyze_pii(
        str(large_golden_file)
    )

    second = analyze_pii(
        str(large_golden_file)
    )

    assert first == second

    assert first["pii_detected"] is False
    assert first["protected_columns"] == {}

    assert len(
        first["safe_columns"]
    ) == 20


def test_large_golden_analysis_results_are_deterministic(
    large_golden_file,
):
    analyses = [
        {
            "type": "descriptive_statistics",
            "measure": "Revenue",
        },
        {
            "type": "group_comparison",
            "measure": "UnitPrice",
            "dimension": "Department",
        },
        {
            "type": "correlation",
            "columns": [
                "Revenue",
                "Cost",
            ],
        },
    ]

    for analysis in analyses:
        first = execute_analysis(
            str(large_golden_file),
            analysis,
        )

        second = execute_analysis(
            str(large_golden_file),
            analysis,
        )

        assert first == second

def test_large_golden_anova_underflow_is_reproducible(
    large_golden_file,
):
    analysis = {
        "type": "group_comparison",
        "measure": "UnitPrice",
        "dimension": "Department",
    }

    first = execute_analysis(
        str(large_golden_file),
        analysis,
    )

    second = execute_analysis(
        str(large_golden_file),
        analysis,
    )

    first_test = first["statistical_test"]
    second_test = second["statistical_test"]

    assert first_test == second_test

    assert first_test["p_value"] == 0.0
    assert (
        first_test["p_value_underflow"]
        is True
    )

    assert first_test["sample_size"] == 100_000
    assert first_test["group_count"] == 4